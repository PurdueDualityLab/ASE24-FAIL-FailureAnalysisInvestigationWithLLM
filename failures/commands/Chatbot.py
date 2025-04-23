import logging
import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import argparse
import json
from failures.articles.models import Incident
from failures.articles.models import Article

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
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

        # Use ConversationBufferMemory to maintain the conversation history
        self.memory = ConversationBufferMemory()

        # Set up the conversation chain
        self.conversation_chain = ConversationChain(memory=self.memory, llm=self.llm)

        # Start the chat
        self.start_chat()

    # def retrieve_articles(self, query, num_chunks=25):
    #     """
    #     Retrieves relevant articles from the vector database for a general query.
    #     """
    #     try:
    #         logging.info(f"Retrieving articles for query: {query}")
    #         docs = self.vector_db.similarity_search(query=query, k=num_chunks)
    #         if docs:
    #             # Log details about retrieved articles
    #             logging.info(f"Found {len(docs)} relevant articles.")
    #             for doc in docs:
    #                 logging.info(f"Retrieved Article ID: {doc.metadata.get('articleID', 'No ID')}")
    #                 logging.info(f"Article content snippet: {doc.page_content[:50]}...")  # Display first 200 characters of the article content
    #         else:
    #             logging.info("No relevant articles found.")
                
    #         return {doc.metadata["articleID"]: doc.page_content for doc in docs}

    #     except Exception as e:
    #         logging.error(f"Error retrieving articles: {e}")
    #         return {}

    def retrieve_articles(self, query, similarity_threshold=0.7):
        try:
            logging.info(f"📋 Retrieving articles for query using {similarity_threshold} threshold: {query}")
            # Perform similarity search with relevance scores
            results_with_scores = self.vector_db.similarity_search_with_relevance_scores(query,50)
            print(results_with_scores)
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
            return {doc.metadata["articleID"]: doc.page_content for doc in filtered_results}

        except Exception as e:
            logging.error(f"Error retrieving articles: {e}")
            return {}

    def build_prompt(self, articles):
        """
        Builds the prompt for ChatGPT using the retrieved articles and a taxonomy prompt.
        """
        prompt = "Analyze the following articles for a software failure:\n"
        for article_id, content in articles.items():
            prompt += f"\n<ARTICLE {article_id}>\n{content}\n</ARTICLE>\n"
        prompt += "\nWhat are the taxonomy details for this incident?"
        return prompt

    def process_query(self, user_query):
        """
        Processes a user query to analyze articles from the vector DB and provide an answer.
        """
        try:
            # Fetch relevant articles using similarity search
            articles = self.retrieve_articles(user_query)

            if not articles:
                return "No relevant articles found."

            # Build the prompt for the LLM
            prompt = self.build_prompt(articles)

            # Use the conversation chain to predict the response, automatically handling memory
            response = self.conversation_chain.predict(input=prompt)

            # Log the response from the bot
            logging.info(f"Bot response: {response}")

            return response

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return "An error occurred while processing the query."
        
    def generate_fmea_from_articles(self, articles: dict, user_description: str):
        """
        Generates a Software FMEA table using incidents linked to the retrieved articles.
        """
        try:
            # Step 1: Get incidents from article metadata
            incident_ids = set()
            for article_id in articles:
                try:
                    article = Article.objects.get(id=article_id)
                    if article.incident:
                        incident_ids.add(article.incident.id)
                except Article.DoesNotExist:
                    logging.log(f"Article with ID {article_id} not found.")
            print(f"Incident ID's for FMEA table {incident_ids}")
            logging.info(f"Incidents ID found: {incident_ids}")
            if not incident_ids:
                logging.log("No incidents found linked to the retrieved articles.")

            # Step 2: Retrieve detailed incident information
            field_mapping = {
                "id": "ID",
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
            incidents_json = json.dumps(incidents, indent=2)
            print(f"incident_ids = {incident_ids}")        
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
            print(prompt)


            return response

        except Exception as e:
            logging.error(f"Error generating FMEA: {e}")
            return " An error occurred while generating the FMEA."


    def start_chat(self):
        """
        Starts the chatbot for interactive user queries.
        """
        print("Chatbot started! Type 'exit' to quit.")
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
            articles = self.retrieve_articles(user_query)
            fmea_output = self.generate_fmea_from_articles(articles, user_query)
            print(f"\n📋 Generated FMEA:\n\n{fmea_output}")
            return



