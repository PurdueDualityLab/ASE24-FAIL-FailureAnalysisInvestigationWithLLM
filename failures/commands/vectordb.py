import os
import argparse
import logging
import textwrap

from django.db.models import Q
from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT, EmbedderGPT,  ClassifierChatGPT
from failures.parameters.models import Parameter

import chromadb
from chromadb.config import Settings
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader

class VectordbCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Vectorize and store article bodies into vector database. If no arguments are provided, 
            only new articles and incidents will be vectorized and stored; otherwise, 
            if --all is provided, all articles will be re-vectorized and re-stored into the database. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Redo vectorization and storage for all incidents.",
        )


    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        
        logging.info("\nUpdating Vector Database.")
        
        if args.all:
            incidents = Incident.objects.all()
        else:
            incidents = (
                    Incident.objects.filter(
                        Q(incident_updated=True) | ~Q(incident_stored=True)
                    )
                    )

        #persist_directory = "/home/dananday/Research/failures/failures" #TODO: How do you set up the DB with docker?
        embedding_function = OpenAIEmbeddings()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 0)

        #vectorDB = Chroma("articlesVDB", embedding=embedding, persist_directory=persist_directory) #TODO: How do you set up the DB with docker?

        chroma_client = chromadb.HttpClient(host="172.17.0.1", port="8001") #TODO: host.docker.internal

        #chroma_client.heartbeat()

        #collection = chroma_client.create_collection("articlesVDB")

        
        vectorDB = Chroma(client=chroma_client, collection_name="articlesVDB", embedding_function=embedding_function)

        count1 = 0
        count2 = 0
        # Iterate through incidents
        for incident in incidents:

            logging.info("Incident ID: "+ str(incident.id))
            
            # Get related articles for the current incident
            if args.all:
                articles = Article.objects.filter(incident=incident)
            else:
                articles = Article.objects.filter( Q(incident=incident,article_stored=False) | Q(incident=incident,article_stored__isnull=True) )
            
            # Iterate through articles for the current incident
            for article in articles:
                logging.info("Article ID: "+ str(article.id))
                #logging.info(f"Article Body: {article.body}")

                metadata = [{"incidentID": incident.id, "articleID": article.id}]
                
                #all_splits = text_splitter.split_documents(article.body)

                updated_ids = vectorDB.add_texts(texts=article.body, metadatas=metadata) #metadata cannot be passed, but it could be a part of documents, look into how to structure documents
                
                #vectordb = Chroma.from_documents(documents=all_splits, embedding=embedding, persist_directory=persist_directory)
                article.article_stored = True
                article.save()
                
                count1 = count1 + 1
                if count1 > 1:
                    break
            
            incident.incident_updated = False
            incident.incident_stored = True
            incident.save()
            
            count2 = count2 + 1
            if count2 > 1:
                break
            
        
        logging.info("Stored: " + str(vectorDB.get(updated_ids)) + " in VectorDB")
        