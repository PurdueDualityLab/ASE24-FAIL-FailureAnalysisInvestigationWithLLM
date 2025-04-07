import argparse
import logging
import textwrap

import json
import math

from django.db.models import Q, Min

from failures.articles.models import Article, Incident
from failures.networks.models import ChatGPT
from failures.parameters.models import Parameter

from failures.commands.PROMPTS import FAILURE_SYNONYMS, POSTMORTEM_QUESTIONS, TAXONOMY_QUESTIONS, TAXONOMY_DEFINITIONS, CPS_KEYS, PROMPT_ADDITIONS

import tiktoken

import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser, DatetimeOutputParser
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.output_parsers import DatetimeOutputParser
from langchain.output_parsers import OutputFixingParser


class fmeatestCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Runs the Failure Aware Chatbot
            """
        )
        

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nExperimenting with ChatBot.")

        ### ChatGPT
        chatGPT = ChatGPT()

        #model_parameters = {"model": "gpt-3.5-turbo", "temperature": 0, "context_window": 16385}
        model_parameters = {"model": "gpt-4o-mini", "temperature": 0, "context_window": 128000} 

        system_dict = dict(Incident.objects.values_list('id', 'system'))

        ### System instructions for LLM to conduct failure analysis
        content = "Given a dictionary of systems and a user provided system, you will return ids of systems from the dictionary that are most similar to the user provided system."
        system_message = [
                {"role": "system", 
                "content": content}
                ]
        
        prompt_SystemDescriptionUser_instructions = "Here is a description of a system a user is trying to design:"


        # Prompt user for system description
        print("\n👋 Welcome! I am a Failure Aware ChatBot. Please describe the system you're designing.")
        user_input = input("🛠️  System Description:\n> ")

        '''
        prompt_SystemDescriptionUser = """
        Description: I am designing a Smart Diabetic Monitor. It is an IoT-based wearable system designed to continuously track and manage blood glucose levels for diabetic patients. The device integrates a Continuous Glucose Monitor (CGM) sensor, a mobile application, and an alert system to provide real-time insights and actionable alerts.

        Key Components:

        CGM Sensor: Implanted or wearable biosensor that continuously measures interstitial glucose levels.

        Microcontroller (MCU): Interfaces with the sensor, processes readings, and transmits data securely.

        Bluetooth/Wi-Fi Module: Enables real-time communication with the user’s smartphone or cloud.

        Mobile App: Displays glucose trends, logs insulin intake and meals, and provides personalized recommendations.

        Alert System: Sends critical alerts (sound, vibration, push notifications) when glucose levels are too high or too low.

        Cloud Platform: Stores historical data, supports machine learning analysis, and allows caregiver/physician access.

        Battery Module: Rechargeable power supply ensuring continuous monitoring.
        """
        '''

        prompt_SystemDescriptionUser = f"Description: {user_input}"

        prompt_SystemDict_instructions = "Below is a dictionary of descriptions of systems and their components. It is in the format: {id:\"systems and components\"}."

        prompt_SystemSelection_instructions = "From the dictionary find systems that are similar in terms of functionality to the user provided system. Return the similar systems in JSON format: {\"id\":\"systems and components\"}"
        
        prompt_SystemSelection = prompt_SystemDescriptionUser_instructions + "\n\n---\n\n" + prompt_SystemDescriptionUser + "\n\n---\n\n" + prompt_SystemDict_instructions + "\n\n---\n\n" + str(system_dict) + "\n\n---\n\n" + prompt_SystemSelection_instructions

        messages = system_message.copy()
        messages.append(
                {"role": "user", "content": prompt_SystemSelection},
                )
        
        model_parameters_temp = model_parameters.copy()
        model_parameters_temp["messages"] = messages.copy()
        model_parameters_temp["response_format"] = {"type": "json_object"}

        reply = chatGPT.run(model_parameters_temp)

        logging.info(model_parameters_temp)

        logging.info(reply)

        if reply is not None:
            similar_systems = json.loads(reply)
        else:
            logging.info("Incorrect JSON output")

        similar_systems = {int(k): v for k, v in similar_systems.items()}

        print("\n✅ Similar systems found:")
        for k, v in similar_systems.items():
            print(f"- Incident #{k}:\n---\n{v}\n---")
            print("\n")

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

        similar_incidents = Incident.objects.filter(id__in=similar_systems.keys()).values(*field_mapping.keys())

        # Remap keys
        similar_incidents = [
            {field_mapping[k]: v for k, v in incident.items()}
            for incident in similar_incidents
        ]

        # Convert to list of dicts
        similar_incidents_str = list(similar_incidents)

        # Convert to pretty JSON-style string
        similar_incidents_str = json.dumps(similar_incidents_str, indent=2)

        prompt_SimilarIncidents = "Here is a list of past incidents that happened with systems similar to a user provided system:"

        prompt_FMEA_instructions =   "Create a software FMEA for the user provided system.\n" \
                        "Include the following columns: Item/Function, Potential Failure Mode, Potential Causes, Potential Effects of Failure, Severity (S), Occurrence (O), Detection (D), RPN, RPN Rationale, Recommended Mitigations.\n" \
                        "Ground the FMEA with the knowledge of past incidents with similar systems. Cite incident ID(s) for the failure mode, causes, effects, and mitigations. Within the Rationale column, provide a rationale for S, O, D, and RPN.\n" \
                        "If you know additional incidents with similar systems, include failure modes from them as well, and cite the incidents."
        
        prompt_FMEA = prompt_SimilarIncidents + "\n\n---\n\n" + similar_incidents_str + "\n\n---\n\n" + prompt_SystemDescriptionUser_instructions + "\n\n---\n\n" + prompt_SystemDescriptionUser + "\n\n---\n\n" + prompt_FMEA_instructions

        content = "Given a list of past incidents and a user provided system description, you will create a Software FMEA for the user provided system grounded by past failures."
        system_message = [
                {"role": "system", 
                "content": content}
                ]

        messages = system_message.copy()
        messages.append(
                {"role": "user", "content": prompt_FMEA},
                )
        
        model_parameters_temp = model_parameters.copy()
        model_parameters_temp["messages"] = messages.copy()

        reply = chatGPT.run(model_parameters_temp)

        logging.info(model_parameters_temp)

        print("\n📋 Generated FMEA:\n")
        print(reply)
        logging.info(reply)
