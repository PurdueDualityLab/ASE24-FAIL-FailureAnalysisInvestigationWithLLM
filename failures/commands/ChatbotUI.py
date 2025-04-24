import sys
import os
import json
import logging
import django
import chainlit as cl
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

from failures.articles.models import Incident, Article

# Bot class
class IncidentChatbotUI:
    def __init__(self):
        self.vector_db = None
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.5)
        self.memory = ConversationBufferMemory()
        self.conversation_chain = ConversationChain(memory=self.memory, llm=self.llm)

    async def initialize_vector_db(self):
        import chromadb
        chroma_client = chromadb.HttpClient(host="chroma", port=8000)
        self.vector_db = Chroma(client=chroma_client, collection_name="articlesVDB",
                                embedding_function=OpenAIEmbeddings())
        logging.info("Chroma vector DB ready.")

    async def retrieve_articles(self, query, k=25):
        docs = self.vector_db.similarity_search(query=query, k=k)
        return {doc.metadata["articleID"]: doc.page_content for doc in docs}

    async def generate_fmea_from_articles(self, articles, user_description):
        # Get related incidents
        incident_ids = set()
        for article_id in articles:
            try:
                article = Article.objects.get(id=article_id)
                if article.incident:
                    incident_ids.add(article.incident.id)
            except Article.DoesNotExist:
                logging.warning(f"Missing article {article_id}")

        field_map = {
            "id": "ID", "summary": "Summary", "system": "System",
            "SEcauses": "Software Causes", "NSEcauses": "Non-Software Causes",
            "impacts": "Impacts", "preventions": "Preventions", "fixes": "Fixes",
        }

        incidents_qs = Incident.objects.filter(id__in=incident_ids).values(*field_map.keys())
        incidents = [{field_map[k]: v for k, v in i.items()} for i in incidents_qs]
        incidents_json = json.dumps(incidents, indent=2)

        prompt = f"""
Here is a list of past incidents that happened with systems similar to a user provided system:

---\n{incidents_json}\n---

Here is a description of a system a user is trying to design:

---\nDescription: {user_description}\n---

Create a Software FMEA for the user provided system.
Include the following columns:
Item/Function, Potential Failure Mode, Potential Causes, Potential Effects of Failure,
Severity (S), Occurrence (O), Detection (D), RPN, RPN Rationale, Recommended Mitigations.

Cite incident ID(s) for the failure mode, causes, effects, and mitigations.
Explain rationale for S, O, D, and the resulting RPN.
"""
        return self.conversation_chain.predict(input=prompt)

    async def process_query(self, user_query):
        articles = await self.retrieve_articles(user_query)
        if not articles:
            return "No relevant articles found."
        return await self.generate_fmea_from_articles(articles, user_query)


# Chainlit handlers
bot = IncidentChatbotUI()

@cl.on_chat_start
async def start():
    await bot.initialize_vector_db()
    await cl.Message(content="Welcome! Please describe your system.").send()

@cl.on_message
async def message(msg: cl.Message):
    response = await bot.process_query(msg.content)
    await cl.Message(content=response).send()
