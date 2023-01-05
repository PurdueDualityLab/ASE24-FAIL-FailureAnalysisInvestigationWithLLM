import argparse
import logging
import textwrap

from failures.articles.models import Article
from failures.networks.models import Embedder


class EmbedCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Create embeddings for articles present in the database. If no arguments are provided, create embeddings for all
            articles that do not have an embedding; otherwise, if --all is provided, create embeddings for all
            articles. If an article does not have a body, an embedding will not be created for it.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Create embeddings for all articles even if they already have an embedding.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        embedder = Embedder()
        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(embedding=None)
        )
        successful_embeddings = 0
        for article in queryset:
            logging.info("Embedding %s.", article)
            if article.body == "":
                continue
            article.create_embedding(embedder)
            successful_embeddings += 1

        logging.info("Successfully created embeddings for %d articles.", successful_embeddings)
