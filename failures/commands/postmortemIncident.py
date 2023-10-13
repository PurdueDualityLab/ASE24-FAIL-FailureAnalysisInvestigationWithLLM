import argparse
import logging
import textwrap

import re

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT
from failures.parameters.models import Parameter

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
        
        
        #TODO: Move this to a data struct file, and import whereever its used 
        questions = {
        "title":            Parameter.get("title", "Provide a 10 word title for the software failure incident (return just the title)."),
        "summary":          Parameter.get("summary", "Summarize the software failure incident. Include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s). (answer in under 250 words)"),
        "time":             Parameter.get("time", "When did the software failure incident happen? If possible, calculate using article published date and relative time mentioned in article."),
        "system":           Parameter.get("system", "What system failed in the software failure incident? (answer in under 10 words)"),
        "ResponsibleOrg":   Parameter.get("ResponsibleOrg", "Which entity(s) was responsible for causing the software failure? (answer in under 10 words)"),
        "ImpactedOrg":      Parameter.get("ImpactedOrg", "Which entity(s) was impacted by the software failure? (answer in under 10 words)"),
        "SEcauses":         Parameter.get("SEcauses", "What were the software causes of the failure incident?"),
        "NSEcauses":        Parameter.get("NSEcauses", "What were the non-software causes of the failure incident?"),
        "impacts":          Parameter.get("impacts", "What happened due to the software failure incident?"),
        "mitigations":      Parameter.get("mitigations", "What could have prevented the software failure incident?"), 
        "phase":            Parameter.get("phase", "Was the software failure due to 'system design' (option 0) or 'operation' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "boundary":         Parameter.get("boundary", "Was the software failure due to faults from 'within the system' (option 0) or from 'outside the system' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "nature":           Parameter.get("nature", "Was the software failure due to 'human actions' (option 0) or 'non human actions' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "dimension":        Parameter.get("dimension", "Was the software failure due to 'hardware' (option 0) or 'software' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "objective":        Parameter.get("objective", "Was the software failure due to 'malicious' (option 0) or 'non-malicious' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "intent":           Parameter.get("intent", "Was the software failure due to 'deliberate' (option 0) or 'accidental' (option 1) fault or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "capability":       Parameter.get("capability", "Was the software failure 'accidental' (option 0) or due to 'development incompetence' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "duration":         Parameter.get("duration", "Was the software failure 'permanent' (option 0) or 'temporary' (option 1) or 'intermittent' (option 2) or 'unknown' (option -1)?"),
        "domain":           Parameter.get("domain", "What application domain is the system: 'automotive' (option 0) or 'critical infrastructure' (option 1) or 'healthcare' (option 2) or 'energy' (option 3) or 'transportation' (option 4) or 'infrastructure' (option 5) or 'aerospace' (option 6) or 'telecommunications' (option 7) or 'consumer device' (option 8) or 'unknown' (option -1)?"),
        "cps":              Parameter.get("cps", "Does the system contain software that controls physical components (cyber physical system) or is it an IoT system: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?"),
        "perception":       Parameter.get("perception", "Was the software failure due to 'sensors' (option 0) or 'actuators' (option 1) or 'processing unit' (option 2) or 'network communication' (option 3) or 'embedded software' (option 4) or 'unknown' (option -1)?"),
        "communication":    Parameter.get("communication", "Was there a software failure at the communication level? If false, (option false). If true, then was the failure at the 'link level' (option 1) or 'connectivity level' (option 2) or 'unknown' (option -1)?"),
        "application":      Parameter.get("application", "Was there a software failure at the application level: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?"),
        "behaviour":        Parameter.get("behaviour", "Was the software failure due to a 'crash' (option 0) or 'omission' (option 1) or 'timing' (option 2) or 'value' (option 3) or 'Byzantine' fault (option 4) or 'unknown' (option -1)?")
        }
        
        #if query_key != 'None':
        #    questions = questions[query_key]
        
        taxonomy_options = {
            "phase": {"0": "system design", "1": "operation", "2": "both", "3": "neither", "-1": "unknown"},
            "boundary": {"0": "within the system", "1": "outside the system", "2": "both", "3": "neither", "-1": "unknown"},
            "nature": {"0": "human actions", "1": "non human actions", "2": "both", "3": "neither", "-1": "unknown"},
            "dimension": {"0": "hardware", "1": "software", "2": "both", "3": "neither", "-1": "unknown"},
            "objective": {"0": "malicious", "1": "non-malicious", "2": "both", "3": "neither", "-1": "unknown"},
            "intent": {"0": "deliberate", "1": "accidental", "2": "both", "3": "neither", "-1": "unknown"},
            "capability": {"0": "accidental", "1": "development incompetence", "2": "both", "3": "neither", "-1": "unknown"},
            "duration": {"0": "permanent", "1": "temporary", "2": "intermittent", "3": "unknown"},
            "domain": {"0": "automotive", "1": "critical infrastructure", "2": "healthcare", "3": "energy", "4": "transportation", "5": "infrastructure", "6": "aerospace", "7": "telecommunications", "8": "consumer device", "-1": "unknown"},
            "cps": {"true": "true", "false": "false", "-1": "unknown"},
            "perception": {"0": "sensors", "1": "actuators", "2": "processing unit", "3": "network communication", "4": "embedded software", "-1": "unknown"},
            "communication": {"false": "False", "1": "link level", "2": "connectivity level", "-1": "unknown"},
            "application": {"true": "true", "false": "false", "-1": "unknown"},
            "behaviour": {"0": "crash", "1": "omission", "2": "timing", "3": "value", "4": "byzantine fault", "-1": "unknown"}
        }

        failure_synonyms = "software hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect"


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