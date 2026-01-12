import logging
import datetime
from typing import Optional, List, Dict, Any, Union

import chainlit as cl
import chainlit.data as cl_data
import chainlit.types as cl_types
from chainlit.data import BaseDataLayer
from chainlit.step import StepDict
from chainlit.element import Element, ElementDict
from chainlit.types import Feedback
from chainlit.user import PersistedUser
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q
from django.db.utils import IntegrityError

from failures.chat.models import ChainlitThread, ChainlitStep, ChainlitElement, ChainlitFeedback

User = get_user_model()
logger = logging.getLogger(__name__)

class DjangoDataLayer(BaseDataLayer):
    """
    Chainlit Data Layer implementation using Django ORM.
    """

    async def build_debug_url(self) -> str:
        return ""

    async def get_user(self, identifier: str) -> Optional[PersistedUser]:
        try:
            user = await User.objects.aget(username=identifier)
            return PersistedUser(
                id=str(user.id),
                identifier=user.username,
                createdAt=user.date_joined.isoformat()
            )
        except User.DoesNotExist:
            return None

    async def create_user(self, user: cl.User) -> Optional[PersistedUser]:
        return await self.get_user(user.identifier)

    async def list_threads(
        self, pagination: cl_types.Pagination, filter: cl_types.ThreadFilter
    ) -> cl_types.PaginatedResponse[cl_types.ThreadDict]:
        
        logger.info(f"List threads called with filter: {filter} and pagination: {pagination}")
        qs = ChainlitThread.objects.all().select_related("user")

        if filter.userId:
            logger.info(f"Filtering by userId: {filter.userId}")
            qs = qs.filter(user__id=filter.userId)
        
        if filter.search:
            qs = qs.filter(name__icontains=filter.search)
        
        if filter.feedback is not None:
            if filter.feedback == 1:
                qs = qs.filter(steps__feedbacks__value=1).distinct()
            elif filter.feedback == -1:
                qs = qs.filter(steps__feedbacks__value=0).distinct()

        qs = qs.order_by("-created_at")

        limit = pagination.first or 20
        
        if pagination.cursor:
             try:
                 cursor_dt = datetime.datetime.fromisoformat(pagination.cursor)
                 qs = qs.filter(created_at__lt=cursor_dt)
             except ValueError:
                 pass

        threads_data = []
        
        threads_list = [t async for t in qs[:limit + 1]]
        has_next_page = len(threads_list) > limit
        if has_next_page:
            threads_list = threads_list[:limit]
        
        end_cursor = None
        if threads_list:
            end_cursor = threads_list[-1].created_at.isoformat()

        for thread in threads_list:
            user_data = None
            if thread.user:
                user_data = {"identifier": thread.user.username}
            
            threads_data.append({
                "id": thread.id,
                "createdAt": thread.created_at.isoformat(),
                "name": thread.name,
                "userId": str(thread.user.id) if thread.user else None,
                "user": user_data,
                "tags": thread.tags,
                "metadata": thread.metadata,
            })
        
        logger.info(f"Returning {len(threads_data)} threads. IDs: {[t['id'] for t in threads_data]}")

        return cl_types.PaginatedResponse(
            data=threads_data,
            pageInfo=cl_types.PageInfo(hasNextPage=has_next_page, endCursor=end_cursor, startCursor=None)
        )

    async def get_thread(self, thread_id: str) -> Optional[cl_types.ThreadDict]:
        logger.info(f"get_thread called for ID: '{thread_id}'")
        try:
            # First verify existence without select_related to isolate issues
            exists = await ChainlitThread.objects.filter(id=thread_id).aexists()
            if not exists:
                logger.warning(f"Thread '{thread_id}' does not exist in DB.")
                return None
            
            thread = await ChainlitThread.objects.select_related("user").aget(id=thread_id)
            logger.info(f"Found thread: {thread.id}, Name: {thread.name}")
        except ChainlitThread.DoesNotExist:
            logger.warning(f"Thread '{thread_id}' not found (raised DoesNotExist).")
            return None
        except Exception as e:
            logger.error(f"Error fetching thread '{thread_id}': {e}", exc_info=True)
            return None

        try:
            steps_data = []
            async for step in thread.steps.all().order_by("created_at"):
                feedbacks = []
                async for fb in step.feedbacks.all():
                    feedbacks.append({
                        "id": fb.id,
                        "forId": fb.for_id,
                        "value": fb.value,
                        "comment": fb.comment
                    })
                
                steps_data.append({
                    "id": step.id,
                    "name": step.name,
                    "type": step.type,
                    "threadId": thread.id,
                    "parentId": step.parent_id,
                    "disableFeedback": step.disable_feedback,
                    "streaming": step.streaming,
                    "input": step.input,
                    "output": step.output,
                    "createdAt": step.created_at.isoformat(),
                    "start": step.start.isoformat() if step.start else None,
                    "end": step.end.isoformat() if step.end else None,
                    "generation": step.generation,
                    "showInput": step.show_input,
                    "language": step.language,
                    "indent": step.indent,
                    "feedback": feedbacks[0] if feedbacks else None
                })
            
            logger.info(f"Thread {thread_id} has {len(steps_data)} steps.")

            elements_data = []
            async for el in thread.elements.all():
                elements_data.append({
                    "id": el.id,
                    "threadId": thread.id,
                    "type": el.type,
                    "url": el.url,
                    "chainlitKey": el.chainlit_key,
                    "name": el.name,
                    "display": el.display,
                    "size": el.size,
                    "language": el.language,
                    "page": el.page,
                    "props": el.props,
                })

            userId = str(thread.user.id) if thread.user else None
            logger.info(f"Thread {thread_id} returning userId: {userId} (should match Session User ID)")

            # Sanitize parentIds to ensure tree integrity
            step_ids = set(s['id'] for s in steps_data)
            for step in steps_data:
                if step['parentId'] and step['parentId'] not in step_ids:
                    logger.warning(f"Step {step['id']} has missing parent {step['parentId']}. Resetting to root.")
                    step['parentId'] = None

            if steps_data:
                logger.info(f"First step: ID={steps_data[0]['id']}, ParentID={steps_data[0]['parentId']}")
                types = [s['type'] for s in steps_data]
                logger.info(f"Step types in thread: {types}")
                
                # Check for potential tree issues (logging only, as we fixed them above)
                # missing_parents check is now redundant but kept for confirmation
                missing_parents = [s['id'] for s in steps_data if s['parentId'] and s['parentId'] not in step_ids]
                if missing_parents:
                    logger.error(f"Logic error: Steps with missing parents still exist: {missing_parents}")



            return {
                "id": thread.id,
                "createdAt": thread.created_at.isoformat(),
                "name": thread.name,
                "userId": userId,
                "user": {"identifier": thread.user.username} if thread.user else None,
                "tags": thread.tags,
                "metadata": thread.metadata,
                "steps": steps_data,
                "elements": elements_data,
            }
        except Exception as e:
            logger.error(f"Error constructing response for thread '{thread_id}': {e}", exc_info=True)
            return None

    async def update_thread(self, thread_id: str, name: Optional[str] = None, user_id: Optional[str] = None, metadata: Optional[Dict] = None, tags: Optional[List[str]] = None):
        logger.info(f"Update thread: {thread_id}, user_id: {user_id}, name: {name}")
        defaults = {}
        if name is not None:
            defaults["name"] = name
        if metadata is not None:
            defaults["metadata"] = metadata
        if tags is not None:
            defaults["tags"] = tags
        
        user = None
        if user_id:
            try:
                user = await User.objects.aget(pk=user_id)
                defaults["user"] = user
            except (User.DoesNotExist, ValueError):
                logger.warning(f"User with ID {user_id} not found during thread update")
                pass

        await ChainlitThread.objects.aupdate_or_create(
            id=thread_id,
            defaults=defaults
        )

    async def delete_thread(self, thread_id: str):
        await ChainlitThread.objects.filter(id=thread_id).adelete()

    async def get_thread_author(self, thread_id: str) -> str:
        try:
            thread = await ChainlitThread.objects.select_related("user").aget(id=thread_id)
            if thread.user:
                return thread.user.username
        except ChainlitThread.DoesNotExist:
            pass
        return ""

    async def create_step(self, step_dict: StepDict):
        thread_id = step_dict.get("threadId")
        if not thread_id:
            return

        try:
            thread = await ChainlitThread.objects.aget(id=thread_id)
        except ChainlitThread.DoesNotExist:
            try:
                thread = await ChainlitThread.objects.acreate(id=thread_id)
            except IntegrityError:
                thread = await ChainlitThread.objects.aget(id=thread_id)

        created_at = step_dict.get("createdAt")
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        
        start = step_dict.get("start")
        if isinstance(start, str):
            start = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
            
        end = step_dict.get("end")
        if isinstance(end, str):
            end = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))

        show_input_val = step_dict.get("showInput", True)
        if isinstance(show_input_val, str):
            show_input_bool = True
        else:
            show_input_bool = bool(show_input_val)

        await ChainlitStep.objects.acreate(
            id=step_dict.get("id"),
            name=step_dict.get("name"),
            type=step_dict.get("type"),
            thread=thread,
            parent_id=step_dict.get("parentId"),
            disable_feedback=step_dict.get("disableFeedback", False),
            streaming=step_dict.get("streaming", False),
            input=step_dict.get("input"),
            output=step_dict.get("output"),
            created_at=created_at or timezone.now(),
            start=start,
            end=end,
            generation=step_dict.get("generation"),
            show_input=show_input_bool,
            language=step_dict.get("language"),
            indent=step_dict.get("indent", 0)
        )

    async def update_step(self, step_dict: StepDict):
        step_id = step_dict.get("id")
        update_fields = {}
        
        if "input" in step_dict: update_fields["input"] = step_dict["input"]
        if "output" in step_dict: update_fields["output"] = step_dict["output"]
        if "generation" in step_dict: update_fields["generation"] = step_dict["generation"]
        if "start" in step_dict:
             start = step_dict["start"]
             if isinstance(start, str): start = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
             update_fields["start"] = start
        if "end" in step_dict:
             end = step_dict["end"]
             if isinstance(end, str): end = datetime.datetime.fromisoformat(end.replace("Z", "+00:00"))
             update_fields["end"] = end
        if "language" in step_dict: update_fields["language"] = step_dict["language"]
        if "streaming" in step_dict: update_fields["streaming"] = step_dict["streaming"]
        
        if update_fields:
            await ChainlitStep.objects.filter(id=step_id).aupdate(**update_fields)

    async def delete_step(self, step_id: str):
        await ChainlitStep.objects.filter(id=step_id).adelete()

    async def create_element(self, element: Element):
        thread_id = element.thread_id
        if not thread_id:
            return
        
        try:
            thread = await ChainlitThread.objects.aget(id=thread_id)
        except ChainlitThread.DoesNotExist:
            return

        await ChainlitElement.objects.acreate(
            id=element.id,
            thread=thread,
            type=element.type,
            url=element.url,
            chainlit_key=element.chainlit_key,
            name=element.name,
            display=element.display,
            size=getattr(element, "size", None),
            language=getattr(element, "language", None),
            page=getattr(element, "page", None),
            props=getattr(element, "props", {}),
        )

    async def get_element(self, thread_id: str, element_id: str) -> Optional[ElementDict]:
        try:
            el = await ChainlitElement.objects.aget(id=element_id, thread_id=thread_id)
            return {
                "id": el.id,
                "threadId": el.thread.id,
                "type": el.type,
                "url": el.url,
                "chainlitKey": el.chainlit_key,
                "name": el.name,
                "display": el.display,
                "size": el.size,
                "language": el.language,
                "page": el.page,
                "props": el.props,
            }
        except ChainlitElement.DoesNotExist:
            return None

    async def update_element(self, element_dict: ElementDict):
        element_id = element_dict.get("id")
        update_fields = {}
        for k in ["url", "chainlitKey", "name", "display", "size", "language", "page", "props"]:
            if k in element_dict:
                key = "chainlit_key" if k == "chainlitKey" else k
                update_fields[key] = element_dict[k]
        
        if update_fields:
            await ChainlitElement.objects.filter(id=element_id).aupdate(**update_fields)

    async def delete_element(self, element_id: str, thread_id: Optional[str] = None):
        await ChainlitElement.objects.filter(id=element_id).adelete()

    async def upsert_feedback(self, feedback: Feedback) -> str:
        step_id = feedback.forId
        step = None
        if step_id:
            try:
                step = await ChainlitStep.objects.aget(id=step_id)
            except ChainlitStep.DoesNotExist:
                pass
        
        feedback_id = feedback.id or ""
        
        defaults = {
            "for_id": step_id,
            "value": feedback.value,
            "comment": feedback.comment,
            "step": step
        }
        
        if feedback_id:
            await ChainlitFeedback.objects.aupdate_or_create(
                id=feedback_id,
                defaults=defaults
            )
            return feedback_id
        else:
            new_feedback = await ChainlitFeedback.objects.acreate(**defaults)
            return new_feedback.id

    async def delete_feedback(self, feedback_id: str) -> bool:
        count, _ = await ChainlitFeedback.objects.filter(id=feedback_id).adelete()
        return count > 0
