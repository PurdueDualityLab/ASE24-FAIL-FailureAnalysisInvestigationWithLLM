import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from failures.articles.models import Article, Incident

import json
import logging
from typing import List

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from pydantic import BaseModel
import chainlit as cl

from asgiref.sync import sync_to_async

# --- Setup ---

chroma_client = chromadb.HttpClient(host="chroma", port="8001")
embedding_function = OpenAIEmbeddings()
vector_db = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
memory = ConversationBufferMemory()
conversation_chain = ConversationChain(memory=memory, llm=llm)

# For structured output of incident list
class IncidentIDList(BaseModel):
    incident_ids: List[int]

# --- Core Functions ---

def RAG_relevant_incidents(query, similarity_threshold=0.7):
    logging.info(f"📋 Retrieving articles for query using {similarity_threshold} threshold: {query}")
    results_with_scores = vector_db.similarity_search_with_relevance_scores(query, 50)

    for doc, score in results_with_scores:
        logging.info(f"incidentID: {doc.metadata['incidentID']}, score: {score:.6f}")

    filtered_results = [
        doc for doc, score in results_with_scores if score >= similarity_threshold
    ]

    if filtered_results:
        logging.info(f"Found {len(filtered_results)} relevant articles above the similarity threshold.")
        for doc in filtered_results:
            logging.info(f"Retrieved Article ID: {doc.metadata.get('articleID', 'No ID')}")
            logging.info(f"Article content snippet: {doc.page_content[:50]}...")
    else:
        logging.info("No relevant articles found above the similarity threshold.")

    articles = {doc.metadata["articleID"]: doc.page_content for doc in filtered_results}

    incident_ids = set()
    for article_id in articles:
        try:
            article = Article.objects.get(id=article_id)
            if article.incident:
                incident_ids.add(article.incident.id)
        except Article.DoesNotExist:
            logging.info(f"Article with ID {article_id} not found.")

    print(f"Incident ID's for FMEA table {incident_ids}")
    logging.info(f"Incidents ID found: {incident_ids}")
    if not incident_ids:
        logging.info("No incidents found linked to the retrieved articles.")

    field_mapping = {
                "id": "ID",
                "title": "Title",
                "summary": "Summary",
                "system": "System",
                "SEcauses": "Software Causes",
                "NSEcauses": "Non-Software Causes",
                "impacts": "Impacts",
                "preventions": "Preventions",
                "fixes": "Fixes",
    }

    incidents_qs = Incident.objects.filter(id__in=incident_ids).values(*field_mapping.keys())
    incidents = [{field_mapping[k]: v for k, v in incident.items()} for incident in incidents_qs]

    print("Using RAG, found these incidents as relevant:\n")
    for inc in incidents:
        print(f"- ID: {inc['ID']}, Title: {inc['Title']}")  

    return incidents


def filter_relevant_incidents_with_llm(incidents, user_description):
    """
    Uses the LLM to filter out only the incidents relevant to the user's system.
    """

    incident_summaries = [
        {"ID": inc.get("ID", "No ID"), "Summary": inc.get("Summary", "No summary")}
        for inc in incidents
    ]
    prompt = (
        "Given a set of past software incidents, you will determine which are relevant to a new system being designed.\n"
        "Here is a description of the new system:\n"
        f"{user_description}\n\n"
        "Below is a list of past incident summaries:\n"
        f"{json.dumps(incident_summaries, indent=2)}\n\n"
        "Return a list of the incident IDs that are most relevant to the new system.\n"
        "Only return a JSON object in this format:\n"
        "{\"incident_ids\": [...]}"
    )

    structured_llm = llm.with_structured_output(IncidentIDList, method="json_mode")
    incident_ids_obj = structured_llm.invoke(prompt)

    logging.info(f"🔍 Incident filtering response: {incident_ids_obj}")

    filtered_ids = incident_ids_obj.incident_ids

    incidents = [inc for inc in incidents if inc["ID"] in filtered_ids]

    print("Using LLM, filtered these incidents as most relevant:\n")
    logging.info("Using LLM, filtered these incidents as most relevant:\n")
    for inc in incidents:
        logging.info(f"- ID: {inc['ID']}, Title: {inc['Title']}")  
        print(f"- ID: {inc['ID']}, Title: {inc['Title']}")  

    return incidents


def generate_fmea_from_articles(incidents, user_description):
    """
    Generates a Software FMEA table using incidents linked to the retrieved articles.
    """
    incidents_json = json.dumps(incidents, indent=2)

    prompt = (
        "Here is a list of past incidents that happened with systems similar to a user provided system:"
        "\n---\n"
        "Past incidents:"
        f"{incidents_json}"
        "\n---\n\n"
        "Here is a description of a system a user is trying to design:\n\n"
        f"Description: {user_description}\n\n\n"
        "Create a Software FMEA for the user provided system.\n"
        "Include the following columns: Item/Function, Potential Failure Mode, Causes, Effects, Severity (S), Occurrence (O), Detection (D), RPN, RPN Rationale, Mitigations.\n"
        "Ground the FMEA with the knowledge of the past similar incidents"
        "Cite incident ID(s) for the failure mode, causes, effects, and mitigations." 
        "Justify S, O, D values, and provide the rationale within the RPN Rationale column.\n"
        "If applicable, add more failure modes and cite relevant incidents beyond the provided past incidents."
    )

    logging.info("Generating FMEA grounded in article-linked incidents...")
    response = conversation_chain.invoke({"input": prompt})["response"]
    logging.info(f"FMEA Response:\n{response}")
    
    return response


# --- Chainlit App ---
@cl.on_chat_start
async def start():
    cl.user_session.set("state", "initial")
    actions = [
        cl.Action(name="create_fmea", value="fmea", label="Create an FMEA", payload={}),
        cl.Action(name="chat_db", value="chat", label="Chat with the Failures database", payload={}),
    ]
    await cl.Message(
        content="Welcome to FailBot! Would you like me to create an FMEA for your system or would you like to chat with the Failures database?",
        actions=actions
    ).send()

@cl.action_callback("create_fmea")
async def on_create_fmea(action):
    cl.user_session.set("state", "awaiting_fmea_description")
    await cl.Message(
        content="To get started, please describe the system you're designing:"
    ).send()

@cl.action_callback("chat_db")
async def on_chat_db(action):
    cl.user_session.set("state", "chat_mode")
    await cl.Message(
        content="You can now chat with the Failures database. What would you like to know? You can also ask me to create an FMEA at any time."
    ).send()

@cl.on_message
async def on_message(message: cl.Message):
    state = cl.user_session.get("state")

    if state == "awaiting_fmea_description":
        system_description = message.content
        cl.user_session.set("system_description", system_description)
        
        await cl.Message(content="🔍 Retrieving relevant incidents from FailDB...").send()
        incidents = await sync_to_async(RAG_relevant_incidents)(system_description)

        await cl.Message(content=f"🔎 Found {len(incidents)} incidents. Filtering with LLM for most relevant incidents...").send()
        filtered_incidents = await sync_to_async(filter_relevant_incidents_with_llm)(incidents, system_description)

        filtered_incidents_str = "\n".join([f"- ID: {inc['ID']}, Title: {inc['Title']}" for inc in filtered_incidents])
        await cl.Message(content=f"📋 **Filtered Incidents:**\n{filtered_incidents_str}").send()

        await cl.Message(content=f"📊 Generating FMEA from {len(filtered_incidents)} filtered incidents...").send()
        fmea_output = await sync_to_async(generate_fmea_from_articles)(filtered_incidents, system_description)

        cl.user_session.set("fmea_context", fmea_output)
        cl.user_session.set("state", "fmea_generated")

        await cl.Message(
            content=f"📋 **Generated FMEA:**\n\n{fmea_output}",
            actions=[cl.Action(name="restart", value="restart", label="🔄 Start Over", payload={})]
        ).send()
    
    elif state == "chat_mode":
        user_message = message.content.lower()
        if "create fmea" in user_message or "generate fmea" in user_message:
            cl.user_session.set("state", "awaiting_fmea_description")
            await cl.Message(
                content="It looks like you want to create an FMEA. To get started, please describe the system you're designing:"
            ).send()
            return

        await cl.Message(content="🔍 Searching the Failures database...").send()
        incidents = await sync_to_async(RAG_relevant_incidents)(message.content)
        
        if not incidents:
            response = (await sync_to_async(conversation_chain.invoke)({'input': message.content}))['response']
            await cl.Message(content=response).send()
            return

        incidents_json = json.dumps(incidents, indent=2)
        prompt = (
            "You are a chatbot assistant for a database of software failures. "
            "A user has asked a question. Use the following relevant incidents from the database to answer the user's question.\n"
            "User question: "
            f"{message.content}\n\n"
            "Relevant incidents:\n"
            f"{incidents_json}\n\n"
            "Answer the user's question based on the provided incidents. If the incidents are not relevant, say that you couldn't find an answer in the database. "
            "Cite incident IDs when you use information from them."
        )
        
        response = (await sync_to_async(conversation_chain.invoke)({'input': prompt}))['response']
        await cl.Message(content=response).send()

    elif state == "fmea_generated":
        follow_up = message.content
        response = (await sync_to_async(conversation_chain.invoke)({'input': follow_up}))['response']
        await cl.Message(content=response).send()
        
    else: # state is "initial" or None
        actions = [
            cl.Action(name="create_fmea", value="fmea", label="Create an FMEA", payload={}),
            cl.Action(name="chat_db", value="chat", label="Chat with the Failures database", payload={}),
        ]
        await cl.Message(
            content="Please choose an option. Would you like me to create an FMEA for your system or would you like to chat with the Failures database?",
            actions=actions
        ).send()

@cl.action_callback("restart")
async def on_restart(action):
    cl.user_session.set("system_description", None)
    cl.user_session.set("fmea_context", None)
    memory.clear()
    cl.user_session.set("state", "initial")
    actions = [
        cl.Action(name="create_fmea", value="fmea", label="Create an FMEA", payload={}),
        cl.Action(name="chat_db", value="chat", label="Chat with the Failures database", payload={}),
    ]
    await cl.Message(
        content="🔄 Restarted! Would you like me to create an FMEA for your system or would you like to chat with the Failures database?",
        actions=actions
    ).send()


#TODO:
# - Display relevant incidents and link them to the website