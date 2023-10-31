import argparse
import logging
import textwrap

import re

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT
from failures.parameters.models import Parameter

from failures.commands.PROMPTS import QUESTIONS, FAILURE_SYNONYMS, TAXONOMY_OPTIONS

import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser, DatetimeOutputParser
from langchain.pydantic_v1 import BaseModel, Field, validator
from langchain.output_parsers import DatetimeOutputParser
from langchain.output_parsers import OutputFixingParser


class PostmortemIncidentCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Create postmortems for articles that report on SE failures present in the database. If no arguments are provided, create postmortems for all
            SE failure articles that do not have a postmortem; otherwise, if --all is provided, create postmortems for all
            SE failure articles. If an article does not have a body, a postmortems will not be created for it.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Create postmortems for all articles even if they already have a postmortem.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key for all articles.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nCreating postmortems.")

        inputs = {"model": "gpt-3.5-turbo", "temperature": 1}

        query_all = args.all
        query_key = args.key


        incidents = Incident.objects.all()

        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal

        embedding_function = OpenAIEmbeddings()
        
        vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)
        
        
        questions = QUESTIONS       
        taxonomy_options = TAXONOMY_OPTIONS
        failure_synonyms = FAILURE_SYNONYMS

        if query_key != 'None':
            questions = questions[query_key]


        template = "Use the following pieces of context about a software failure incident to answer the question." + "\n" + "Note that software failure could mean a " + failure_synonyms + "." \
        + """
        If you don't know the answer, return unknown (option -1). 
        Context: {context}
        Question: {question}
        """
        ChatGPT_LC = ChatOpenAI(model_name=inputs["model"], temperature=inputs["temperature"])

        JsonParser = PydanticOutputParser(pydantic_object=JsonResponse)
        RetryParser = OutputFixingParser.from_llm(parser=JsonParser, llm=ChatOpenAI(model_name=inputs["model"], temperature=inputs["temperature"]))
        TimeParser = DatetimeOutputParser()

        successful_postmortem_creations = 0
        for incident in incidents:
            logging.info("Creating postmortem for incident %s.", incident.id)

            for question_key in list(questions.keys()): #[list(questions.keys())[i] for i in [0,1,2,10,11,12]]:
                #Check if the question has already been answered
                answer_set = True
                taxonomy_q = False #To use json parser
                if question_key in taxonomy_options.keys():
                    question_option_key = question_key + "_option"
                    question_rationale_key = question_key + "_rationale"
                    if not getattr(incident, question_option_key):
                        answer_set = False
                    taxonomy_q = True
                else:
                    if not getattr(incident, question_key):
                        answer_set = False

                if query_all or (query_key in question_key) or not answer_set: 

                    logging.info("Querying question: " + str(question_key))
                    
                    #question_template = template + "\nQuestion: " + questions[question_key]

                    if taxonomy_q: # For JSON parser instructions
                        formatted_template = template + "\n{format_instructions}"
                        QA_CHAIN_PROMPT = PromptTemplate(template=formatted_template, input_variables=["context", "question"], partial_variables={"format_instructions": JsonParser.get_format_instructions()})
                    else:
                        #if "time" in question_key: # For datetime parser instructions
                        #    formatted_template = template + "\n{format_instructions}" + ""
                        #    QA_CHAIN_PROMPT = PromptTemplate(template=formatted_template, input_variables=["context", "question"], partial_variables={"format_instructions": TimeParser.get_format_instructions()})
                        #else:
                        #    QA_CHAIN_PROMPT = PromptTemplate.from_template(template=template)
                        QA_CHAIN_PROMPT = PromptTemplate.from_template(template=template)

                    qa_chain = RetrievalQA.from_chain_type( # HOW TO FILTER BY INCIDENT
                        ChatGPT_LC,
                        retriever=vectorDB.as_retriever(search_kwargs={"filter":{"incidentID":incident.id}}), #TDOD: How does additional instructions in the question influence the vectorDB retriever? (ex: summarize, under 10 words, etc)
                        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}, 
                        return_source_documents=True,
                    )

                    try:
                        response = qa_chain({"query": questions[question_key]})
                    except:
                        logging.info("Issue with langchain query, skipping question")
                        continue

                    logging.info("Sources: " + str(response["source_documents"]))

                    # Extract unique articleIDs from source documents
                    source_articleIDs = [doc.metadata['articleID'] for doc in response["source_documents"]]
                    source_articleIDs = f" [{', '.join(map(str, set(source_articleIDs)))}]"


                    if taxonomy_q: # If its a taxonomy question, parse for JSON
                        try:
                            parsedResult = JsonParser.parse(response["result"])
                        except:
                            logging.info("Misformatted JSON returned for " +question_key+ " for incident: "+str(incident.id) + ". Trying again.")
                            try:
                                parsedResult = RetryParser.parse(response["result"])
                            except:
                                logging.info("On Retry: Misformatted JSON returned for " +question_key+ " for incident: "+str(incident.id))
                                explanation = response["result"]
                                setattr(incident, question_rationale_key, explanation)
                                continue

                        explanation = parsedResult.explanation + source_articleIDs
                        option_number = str(parsedResult.option)

                        try:
                            option_value = taxonomy_options[question_key][option_number]
                        except:
                            logging.info("KeyError: Wrong option")
                            setattr(incident, question_rationale_key, "Option: " + option_number + " ; "+ explanation)
                            continue

                        setattr(incident, question_option_key, option_value)
                        setattr(incident, question_rationale_key, explanation)
                        
                        logging.info(explanation)
                        logging.info(option_value)
                    else:
                        #if "time" in question_key: # If its time question, parse for datetime
                        #    try:
                        #        reply = str(TimeParser.parse(response["result"]))
                        #    except:
                        #        reply = response["result"]
                        #        logging.info("Misformatted parsing returned for " +question_key+ " for incident: "+str(incident.id))
                        #else:
                        #    reply = response["result"]
                        reply = response["result"] + source_articleIDs
                            
                        setattr(incident, question_key, reply)
                        logging.info(reply)

                    
            incident.save() #TODO: Also track sources

            #incident.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, taxonomy_options, args.all, args.key)
            logging.info("Succesfully created postmortem for incident %s: %s.", incident.id, incident.title)
            successful_postmortem_creations += 1
            
            #if successful_postmortem_creations > 1:
                #break

        logging.info("Successfully created postmortems for %d articles.", successful_postmortem_creations)


# Define your desired data structure.
class JsonResponse(BaseModel):
    explanation: str = Field(description="Provide explanation for the option that answers the question")
    option: int = Field(description="Choose option number that answers the question")