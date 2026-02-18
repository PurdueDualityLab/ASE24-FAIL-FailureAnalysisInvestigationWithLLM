import argparse
import logging
import os
import textwrap

from failures.articles.models import Article

import chromadb
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class BackfillChromaCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Backfill the Chroma articlesVDB collection from Article rows in the database.
            """
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            default=False,
            help="Drop and recreate the articlesVDB collection before backfilling.",
        )
        parser.add_argument(
            "--chunk-size",
            type=int,
            default=500,
            help="Chunk size for article splitting.",
        )
        parser.add_argument(
            "--chunk-overlap",
            type=int,
            default=0,
            help="Chunk overlap for article splitting.",
        )
        parser.add_argument(
            "--chroma-host",
            type=str,
            default=os.getenv("CHROMA_HOST", "chroma"),
            help="Chroma host.",
        )
        parser.add_argument(
            "--chroma-port",
            type=int,
            default=int(os.getenv("CHROMA_PORT", "8001")),
            help="Chroma port.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        logging.info("Starting Chroma backfill")

        client = chromadb.HttpClient(host=args.chroma_host, port=args.chroma_port)

        if args.reset:
            try:
                client.delete_collection("articlesVDB")
                logging.info("Deleted existing articlesVDB collection")
            except Exception:
                logging.info("No existing articlesVDB collection to delete")

        vector_db = Chroma(
            client=client,
            collection_name="articlesVDB",
            embedding_function=OpenAIEmbeddings(),
        )
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )

        processed_articles = 0
        total_chunks = 0

        queryset = (
            Article.objects.filter(incident__isnull=False)
            .exclude(body__isnull=True)
            .exclude(body="")
            .only("id", "incident_id", "body")
        )

        for article in queryset.iterator():
            docs = splitter.create_documents(
                [article.body],
                metadatas=[{"articleID": article.id, "incidentID": article.incident_id}],
            )
            for order, doc in enumerate(docs):
                doc.metadata["order"] = order

            if not docs:
                continue

            vector_db.add_documents(docs)
            processed_articles += 1
            total_chunks += len(docs)

            Article.objects.filter(id=article.id).update(article_stored=True)

        count = vector_db._collection.count()
        logging.info(
            "Chroma backfill complete: processed_articles=%d total_chunks=%d collection_count=%d",
            processed_articles,
            total_chunks,
            count,
        )
