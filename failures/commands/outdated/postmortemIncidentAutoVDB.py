import argparse
import logging
import textwrap

import json

from django.db.models import Q

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT
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


class PostmortemIncidentAutoVDBCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Create postmortems for SE failure incidents present in the database. If no arguments are provided, create postmortems for all
            SE failure incidents that do not have a postmortem; otherwise, if --all is provided, create postmortems for all
            SE failure incidents. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Create postmortems for all incidents even if they already have a postmortem.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key.",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--incidents",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--experiment",
            type=bool,
            default=False,
            help="Marks articles as part of the experiment.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        '''
        1. Incidents = Queryset
        2. Count tokens for all articles in incident
        3a. If tokens > 14.5k:
            4a. check if articles for incident are already stored in VDB
            4b. prompt with chunks from VDB
        3b. If tokens < 14.5k:
            4a. combine all articles and prompt with all articles
        5. 
        
        
        
        '''

        logging.info("\nCreating postmortems for incidents.")

        model_parameters = {"model": "gpt-3.5-turbo", "temperature": 0, "context_window": 16385}

        query_all = args.all
        query_key = args.key

        # IF TESTING: Only fetching incidents related to article testing set
        if args.articles:
            incidents = Incident.objects.filter(articles__in=args.articles).distinct()
        elif args.incidents:
            incidents = Incident.objects.filter(id__in=args.incidents).distinct()
        elif query_all or query_key:
            incidents = Incident.objects.all()
        else:
            incidents = Incident.objects.all(Q(new_article=True) | Q(complete_report=False) | Q(complete_report=None))

        #TODO: create flags for incidents: (1) new article: use that incident in queryset + redo all questions, (2) incomplete postmortem: use that incident in queryset, 
            # if new article delete existing postmortem info 
            # Use this to create appropriate queryset up here rather than going through all incidents 


        ### Importing prompts
        failure_synonyms = FAILURE_SYNONYMS

        postmortem_questions = POSTMORTEM_QUESTIONS.copy() 
        taxonomy_questions = TAXONOMY_QUESTIONS.copy()
        taxonomy_definitions = TAXONOMY_DEFINITIONS.copy()

        cps_keys = CPS_KEYS.copy()

        prompt_additions = PROMPT_ADDITIONS.copy()

        ### If queryset is for an experiment mark it as such
        if args.experiment is True:
            incidents.update(experiment=True)

        ### Check if a specific question is to be queried
        if query_key != 'None':
            if query_key in postmortem_questions.keys():
                postmortem_questions = {}
                postmortem_questions[query_key] = POSTMORTEM_QUESTIONS[query_key]
            else: 
                postmortem_questions = {}
            
            if query_key in taxonomy_questions.keys():
                taxonomy_questions={}
                taxonomy_questions[query_key] = TAXONOMY_QUESTIONS[query_key]
            else:
                taxonomy_questions = {}
        
        ### ChatGPT
        chatGPT = ChatGPT()
        
        ### Set up for incidents > 16k context window
        # Vector DB setup
        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal
        embedding_function = OpenAIEmbeddings()
        vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 0)
        

        ### Set up for counting tokens in incident
        encoding = tiktoken.encoding_for_model(model_parameters["model"])


        ### System instructions for LLM to conduct failure analysis
        content = "You will help conduct failure analysis on software failure incidents reported by news articles."
        system_message = [
                {"role": "system", 
                "content": content}
                ]
        
        ## For open ended postmorterm questions & for Step 1 of taxonomy questions: To 'answer' information directly from articles
        prompt_template_articles_instruction = "Use the following news articles reporting on a software failure incident to answer the Question." + "\n" + "Note that software failure could mean a " + failure_synonyms + "." \
                + "\n"+ "Cite the Article # for articles used to answer the question in the format: [#, #, ...]. If you can't answer the question using the articles, return 'unknown'." + "\n"
        
        ## For Step 1 of taxonomy questions: To 'extract' the information extracted from articles to answer questions
        prompt_template_extract_task = "Extract information from the articles about the software failure incident related to:\n"

        ## For Step 2 of taxonomy questions: To 'make decisions' using the extracted information about the taxonomy
        prompt_template_decision_instruction = "Use the following Extracted Information from news articles reporting on a software failure incident to answer the Questions." + "\n" + "Note that software failure could mean a " + failure_synonyms + "." \
                + "\n"+ "If you can't answer the questions using the information, answer with 'unknown'." + "\n"
        prompt_template_decision_task = "Using the Extracted Information answer the following questions:\n"
        prompt_template_JSON_format = "\nReturn answers in the following JSON format:\n"


        successful_postmortem_creations = 0
        for incident in incidents:
            logging.info("Creating postmortem for incident %s.", incident.id)

            ### Get related articles
            incident_articles = incident.articles.all()

            ### Count total number of tokens for all articles in an incident
            if incident.tokens == None or incident.new_article == True:  
                incident_tokens = 0

                for article in incident_articles:
                    if article.tokens == None:
                        article.tokens = len(encoding.encode(article.body))

                    incident_tokens += article.tokens
                
                incident.tokens = incident_tokens

            
            
            ### If incident token length is less than the model's context window, then directly prompt the model with the articles
            if incident.tokens <= model_parameters["context_window"] - 1500: 

                
                # Add Articles for the Incident into a prompt template
                prompt_incident = ""
                for article in incident_articles:
                    prompt_incident += "\n" +"<Article " + str(article.id) + ">"
                    prompt_incident += article.body
                    prompt_incident += "</Article " + str(article.id) + ">" +"\n"
                

                ### Answer open ended postmortem questions
                for question_key in list(postmortem_questions.keys()): #[list(questions.keys())[i] for i in [0,1,2,10,11,12]]:
            
                    # Check if the question has already been answered
                    answer_set = True
                    if not getattr(incident, question_key):
                        answer_set = False

                    # Ask LLM
                    if query_all or query_key == question_key or incident.new_article == True or answer_set == False or args.experiment is True: 
                        logging.info("Querying question: " + str(question_key))

                        ### Construct prompt
                        prompt_question = "\n<Question>" + prompt_additions[question_key]["before"] + postmortem_questions[question_key] + prompt_additions[question_key]["after"] + "</Question>"

                        final_prompt = prompt_template_articles_instruction + prompt_incident + prompt_question

                        messages = system_message.copy()

                        messages.append(
                                        {"role": "user", "content": final_prompt},
                                        )
                        
                        model_parameters_temp = model_parameters.copy()
                        model_parameters_temp["messages"] = messages.copy()

                        logging.info(type(model_parameters_temp))
                        logging.info(model_parameters_temp)
                
                        reply = chatGPT.run(model_parameters_temp)

                        setattr(incident, question_key, reply)


                ### Answer choice-based taxonomy questions
                for question_key in list(taxonomy_questions.keys()): #[list(questions.keys())[i] for i in [0,1,2,10,11,12]]:

                    # If question is for CPS, and the system for incident is not CPS, then don't answer
                    if question_key in cps_keys and "cps" not in incident.cps_option: #incident.cps != True:
                            continue

                    question_rationale_key = question_key + "_rationale"
                    question_option_key = question_key + "_option"
                
                    # Check if the question has already been answered
                    answer_set = True
                    if not getattr(incident, question_option_key):
                        answer_set = False

                    # Ask LLM 
                    if query_all or query_key == question_key or incident.new_article == True or answer_set == False or args.experiment is True: 
                        logging.info("Querying question: " + str(question_key))

                        ### Construct prompt to Ask LLM to extract relevent information from articles to help make the decision about the taxonomy
                        messages = system_message.copy()

                        prompt_question = "\n<Question>" + prompt_template_extract_task + prompt_additions[question_key]["rationale"]["before"] + taxonomy_definitions[question_key] + prompt_additions[question_key]["rationale"]["after"] + "</Question>"
                        
                        final_prompt = prompt_template_articles_instruction + prompt_incident + prompt_question

                        messages.append(
                                        {"role": "user", "content": final_prompt},
                                        )
                        
                        model_parameters_temp = model_parameters.copy()
                        model_parameters_temp["messages"] = messages.copy()

                        logging.info(type(model_parameters_temp))
                        logging.info(model_parameters_temp)

                
                        reply = chatGPT.run(model_parameters_temp)

                        setattr(incident, question_rationale_key, reply)

                        
                        ### Construct prompt to Ask LLM to make the decision about the taxonomy using the extracted information
                        messages = system_message.copy()

                        extracted_info = "<Extracted Information>" + reply + "</Extracted Information>"
                        
                        prompt_question = "\n<Questions>" + prompt_template_decision_task + prompt_additions[question_key]["decision"]["before"] + taxonomy_questions[question_key] + prompt_template_JSON_format + prompt_additions[question_key]["decision"]["after"] + "</Questions>"

                        final_prompt = prompt_template_decision_instruction + extracted_info + prompt_question

                        messages.append(
                                        {"role": "user", "content": final_prompt},
                                        )
                        
                        model_parameters_temp = model_parameters.copy()
                        model_parameters_temp["messages"] = messages.copy()

                        model_parameters_temp["response_format"] = {"type": "json_object"}

                        logging.info(type(model_parameters_temp))
                        logging.info(model_parameters_temp)
                
                        reply = chatGPT.run(model_parameters_temp)

                        ### Error handling for JSON format is implemented in ChatGPT class

                        ### Convert JSON to string with options that are true in csv format
                        if reply is not None:
                            reply = json.loads(reply)\
                            # Extract keys where the corresponding values are True
                            true_keys = [key for key, value in reply.items() if value]
                            # Convert the list of keys into a string
                            reply = ', '.join(true_keys)

                        setattr(incident, question_option_key, reply)



            
            
            ### If incident token length is greater than the model's context window, then store articles in Vector DB, do RAG, then prompt with relevent chunks
            else:
                # Do vectorDB + chatgpt
                logging.info("Skipping article for now: Needs VectorDB to be on.")
                continue

            ### Check if report is complete
            complete_report = True

            for question_key in list(POSTMORTEM_QUESTIONS.keys()):
                if not getattr(incident, question_key):
                    complete_report = False
                    break
            
            for question_key in list(TAXONOMY_QUESTIONS.keys()):
                
                # If question is for CPS, and the system for incident is not CPS, then don't check for its completion
                if question_key in cps_keys and "cps" not in incident.cps_option: #incident.cps != True:  ###"\"cps\": true"
                    continue

                question_option_key = question_key + "_option"
                if not getattr(incident, question_option_key) or complete_report == False:
                    complete_report = False
                    break
            
            if complete_report == True:
                incident.complete_report = True
            else:
                incident.complete_report = False

            ### All new articles for the incidents would have contributed to the incident
            incident.article_new = False
            
            
            
            incident.save()

            logging.info("Succesfully created postmortem for incident %s: %s.", incident.id, incident.title)
            successful_postmortem_creations += 1
            

        logging.info("Successfully created postmortems for %d incidents.", successful_postmortem_creations)

            
            
            



















'''
        # Prompt template for chunks from Vector DB
        prompt_template_VDB = "Use the following pieces of context about a software failure to answer the question." + "\n" + "Note that software failure could mean a " + failure_synonyms + "." \
        + """
        If you don't know the answer, return unknown. 

        Context: {context}

        Question: {question}
        """

        # LangChain setup 
        ChatGPT_LC = ChatOpenAI(model_name=inputs["model"], temperature=inputs["temperature"])

        JsonParser = PydanticOutputParser(pydantic_object=JsonResponse)
        RetryParser = OutputFixingParser.from_llm(parser=JsonParser, llm=ChatOpenAI(model_name=inputs["model"], temperature=inputs["temperature"]))
        

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

                if query_all or query_key == question_key or answer_set == False: 

                    logging.info("Querying question: " + str(question_key))
                    
                    #question_template = template + "\nQuestion: " + questions[question_key]

                    if taxonomy_q: # For JSON parser instructions
                        formatted_template = template + "\n{format_instructions}"
                        QA_CHAIN_PROMPT = PromptTemplate(template=formatted_template, input_variables=["context", "question"], partial_variables={"format_instructions": JsonParser.get_format_instructions()})
                    else:
                        QA_CHAIN_PROMPT = PromptTemplate.from_template(template=template)

                    qa_chain = RetrievalQA.from_chain_type(
                        ChatGPT_LC,
                        retriever=vectorDB.as_retriever(search_kwargs={"filter":{"incidentID":incident.id}}), #TDOD: How does additional instructions in the question influence the vectorDB retriever? (ex: summarize, under 10 words, etc)
                        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT}, 
                        return_source_documents=True,
                    )

                    try:
                        response = qa_chain({"query": questions[question_key]})
                    except Exception as e:
                        logging.info(f"Issue with langchain query. Exception: {str(e)}. Skipping question.")
                        continue


                    logging.info(str(response))

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
    option: str = Field(description="Choose option that answers the question")

'''