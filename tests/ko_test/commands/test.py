import argparse
import logging
import textwrap
import pandas as pd
from datetime import datetime
import os

from failures.articles.models import Article_Ko


class TestCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the scrape command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Scrape articles from Google News RSS feeds. If no arguments are provided, use all search
            queries present in the database; otherwise, use the provided arguments to create a new search query.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article scraping process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # # Retrieve and delete all articles from the database (preventing duplicates)
        all_articles = Article_Ko.objects.filter(describes_failure=True)

        num_articles = len(all_articles)

        num_off_topic = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=False))

        num_relevant = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=True))

        print("Number of Ko articles ingested into DB: " + str(num_articles))

        print("Number of off-topic Ko articles ingested into DB: " + str(num_off_topic))

        print("Number of relevant Ko articles ingested into DB: " + str(num_relevant))

