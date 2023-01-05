import argparse
import logging
import textwrap

from failures.articles.models import Article
from failures.networks.models import Summarizer


class SummarizeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Summarize articles present in the database. If no arguments are provided, summarize all
            articles that do not have a summary; otherwise, if --all is provided, summarize all
            articles. If an article does not have a body, it will not be summarized.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Summarize all articles even if they already have a summary.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        summarizer = Summarizer()
        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(summary="")
        )
        successful_summaries = 0
        for article in queryset:
            logging.info("Summarizing %s.", article)
            if article.body == "":
                continue
            if article.summarize_body(summarizer):
                successful_summaries += 1

        logging.info("Successfully summarized %d articles.", successful_summaries)
