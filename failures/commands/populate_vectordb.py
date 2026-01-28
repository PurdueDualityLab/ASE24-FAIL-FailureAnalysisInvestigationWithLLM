import argparse
import logging
import textwrap
import math

from failures.articles.models import Incident
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from django.conf import settings

class PopulateVectorDBCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Populate the Chroma vector database with articles from all incidents.
            This ensures that FailBot has data to query even if the incidents
            are small enough to fit in the context window (skipping the default RAG pipeline).
            """
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            default=False,
            help="Reset the collection before populating.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        logging.info("Starting Vector DB population...")

        # Initialize Chroma Client
        chroma_client = chromadb.HttpClient(host="chroma", port="8001")
        embedding_function = OpenAIEmbeddings()
        
        collection_name = "articlesVDB"

        # Optional Reset
        if args.reset:
            try:
                chroma_client.delete_collection(collection_name)
                logging.info(f"Deleted collection: {collection_name}")
            except Exception as e:
                logging.warning(f"Could not delete collection (might not exist): {e}")

        # Get or Create Collection logic is handled by LangChain's Chroma wrapper usually, 
        # but let's instantiate it.
        vectorDB = Chroma(
            client=chroma_client,
            collection_name=collection_name,
            embedding_function=embedding_function
        )

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)

        # Get all incidents that have articles
        incidents = Incident.objects.prefetch_related('articles').all()
        
        count = 0
        for incident in incidents:
            logging.info(f"Processing Incident ID: {incident.id} - {incident.title}")
            
            for article in incident.articles.all():
                if not article.body:
                    logging.warning(f"Skipping Article {article.id}: No body content.")
                    continue
                
                # Check if already stored (optional, but good for idempotency if not resetting)
                # But since we want to force populate for FailBot, we might just overwrite or ignore
                # For now, let's just add it. Chroma handles deduplication by ID if provided, 
                # but we are generating splits, so new IDs are generated. 
                # If we want to avoid dups without reset, we'd need to check existence.
                # Assuming --reset or fresh start for now effectively.

                metadata = [{"incidentID": incident.id, "articleID": article.id}]
                
                # Create documents
                docs = text_splitter.create_documents([article.body], metadatas=metadata)
                
                # Assign order metadata
                for order, doc in enumerate(docs):
                    doc.metadata["order"] = order

                # Add to Chroma
                if docs:
                    vectorDB.add_documents(docs)
                    logging.info(f"Added {len(docs)} chunks for Article {article.id}")
                else:
                    logging.warning(f"No chunks created for Article {article.id}")

            count += 1

        logging.info(f"Finished populating Vector DB with {count} incidents.")
