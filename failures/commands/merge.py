import argparse
import logging
import textwrap

from failures.articles.models import Article, Failure
from failures.networks.models import QuestionAnswerer


class MergeCommand:
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
        question_answerer = QuestionAnswerer()
        queryset = Article.objects.all()
        successful_failure_creations = 0
        for article in queryset:
            logging.info("Creating failure from %s.", article)
            if article.body == "":
                continue
            Failure.create_from_article(article, question_answerer)
            successful_failure_creations += 1

        logging.info("Successfully created failures for %d articles.", successful_failure_creations)
