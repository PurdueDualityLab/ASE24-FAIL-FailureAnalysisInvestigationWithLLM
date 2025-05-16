from failures.articles.models import Incident
from failures.articles.models import Article

import logging
import argparse
import json
from pydantic import BaseModel
from typing import List

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

#For structured output of incident list
class IncidentIDList(BaseModel):
    incident_ids: List[int]

class IncidentChatbotCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = "Chatbot for incident analysis using Chroma vector database and OpenAI models."

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        logging.info("Chroma client initialized successfully")

        # Chroma client initialization
        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001")
        logging.info("Chroma client initialized successfully")

        # OpenAI embeddings and Chroma vector DB setup
        embedding_function = OpenAIEmbeddings()
        self.vector_db = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)

        # Initialize the LLM and memory
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Use ConversationBufferMemory to maintain the conversation history
        self.memory = ConversationBufferMemory()

        # Set up the conversation chain starting from the FMEA
        self.conversation_chain = ConversationChain(memory=self.memory, llm=self.llm)

        # Start the chat
        self.start_chat()


    # TODO: change from retrieve articles to incidents,  - This is to better simulate the stages of the pipeline
    # just return the incident ids. 
    # update dependencies and include new function that does similarity score

    def RAG_relevant_incidents(self, query, similarity_threshold=0.7):
        try:
            logging.info(f"📋 Retrieving articles for query using {similarity_threshold} threshold: {query}")
            # Perform similarity search with relevance scores
            results_with_scores = self.vector_db.similarity_search_with_relevance_scores(query,50)

            for doc, score in results_with_scores:
                    logging.info(f"incidentID: {doc.metadata['incidentID']}, score: {score:.6f}")

            # Filter results based on the similarity threshold
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

            # Get incidents from article metadata
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

            # Retrieve detailed incident information
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

        except Exception as e:
            logging.error(f"Error retrieving relevant incidents with RAG: {e}")
            return {}


    def generate_fmea_from_articles(self, incidents: list, user_description: str):
        """
        Generates a Software FMEA table using incidents linked to the retrieved articles.
        """
        try:

            incidents_json = json.dumps(incidents, indent=2)

            # Step 3: Prompt structure to match fmeatest.py
            prompt_SimilarIncidents = "Here is a list of past incidents that happened with systems similar to a user provided system:"
            prompt_FMEA_instructions = (
                "Create a Software FMEA for the user provided system.\n"
                "Include the following columns:\n"
                "Item/Function, Potential Failure Mode, Potential Causes, Potential Effects of Failure,\n"
                "Severity (S), Occurrence (O), Detection (D), RPN, RPN Rationale, Recommended Mitigations.\n\n"
                "Ground the FMEA with the knowledge of past incidents with similar systems.\n"
                "Cite incident ID(s) for the failure mode, causes, effects, and mitigations.\n"
                "Within the RPN Rationale column, provide a rationale for S, O, D, and the resulting RPN.\n"
                "If you know additional relevant incidents, include failure modes from them too and cite them."
            )
            prompt_SystemDescriptionUser_instructions = "Here is a description of a system a user is trying to design:"
            prompt_SystemDescriptionUser = f"Description: {user_description}"

            # Full prompt
            prompt = (
                f"{prompt_SimilarIncidents}\n\n---\n\n{incidents_json}\n\n---\n\n"
                f"{prompt_SystemDescriptionUser_instructions}\n\n---\n\n{prompt_SystemDescriptionUser}\n\n---\n\n"
                f"{prompt_FMEA_instructions}"
            )

            logging.info(prompt)

            logging.info("Generating FMEA grounded in article-linked incidents...")
            response = self.conversation_chain.predict(input=prompt)
            logging.info(f"FMEA Response:\n{response}")


            return response

        except Exception as e:
            logging.error(f"Error generating FMEA: {e}")
            return " An error occurred while generating the FMEA."


    def filter_relevant_incidents_with_llm(self, incidents: list, user_description: str) -> list:
        """
        Uses the LLM to filter out only the incidents relevant to the user's system.
        """
        try:

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
                "Return a list of the incident IDs that are most relevant to the new system, based on similarity in technologies, causes, or context.\n"
                "Only return a JSON array of the relevant incident IDs, in this format:\n"
                "{\"incident_ids\": [...]}"
            )

            # To get incident ids as json list
            structured_llm = self.llm.with_structured_output(IncidentIDList, method="json_mode")

            incident_ids_obj = structured_llm.invoke(prompt)

            logging.info(f"🔍 Incident filtering response: {incident_ids_obj}")

            # Extract the list of incident IDs
            filtered_incident_ids = incident_ids_obj.incident_ids

            # Ensure it's a list before filtering
            if isinstance(filtered_incident_ids, list):
                incidents = [inc for inc in incidents if inc["ID"] in filtered_incident_ids]
            else:
                incidents = []

            print("Using LLM, filtered these incidents as most relevant:\n")
            logging.info("Using LLM, filtered these incidents as most relevant:\n")
            for inc in incidents:
                logging.info(f"- ID: {inc['ID']}, Title: {inc['Title']}")  
                print(f"- ID: {inc['ID']}, Title: {inc['Title']}")  

            return incidents

        except Exception as e:
            print(f"Error during incident filtering with LLM: {e}")
            logging.error(f"Error during incident filtering with LLM: {e}")
            return []


    def start_chat(self):
        """
        Starts the chatbot for interactive user queries.
        """
        print("Chatbot started! Type 'exit' to quit.")
        print("\n👋 Welcome! I am a Failure Aware ChatBot. To get started, please describe the system you're designing:\n")
        while True:
            #user_query = input("You: ")
            # if user_query.lower() in ["exit", "quit"]:
            #     print("Chatbot stopped.")
            #     break
            user_query = """I am designing a Smart Diabetic Monitor. It is an IoT-based wearable system designed to continuously track and manage blood glucose levels for diabetic patients. The device integrates a Continuous Glucose Monitor (CGM) sensor, a mobile application, and an alert system to provide real-time insights and actionable alerts.
                        Key Components:
                        CGM Sensor: Implanted or wearable biosensor that continuously measures interstitial glucose levels.
                        Microcontroller (MCU): Interfaces with the sensor, processes readings, and transmits data securely.
                        Bluetooth/Wi-Fi Module: Enables real-time communication with the user’s smartphone or cloud.
                        Mobile App: Displays glucose trends, logs insulin intake and meals, and provides personalized recommendations.
                        Alert System: Sends critical alerts (sound, vibration, push notifications) when glucose levels are too high or too low.
                        Cloud Platform: Stores historical data, supports machine learning analysis, and allows caregiver/physician access.
                        Battery Module: Rechargeable power supply ensuring continuous monitoring."""

            relevant_incidents = self.RAG_relevant_incidents(user_query)
            filtered_incidents = self.filter_relevant_incidents_with_llm(relevant_incidents, user_query)
            fmea_output = self.generate_fmea_from_articles(filtered_incidents, user_query)
            print(f"\n📋 Generated FMEA:\n\n{fmea_output}")
            return
