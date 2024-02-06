import argparse
import logging
import textwrap
import time

import re

from failures.articles.models import Article
from failures.networks.models import ZeroShotClassifier, ClassifierChatGPT
from failures.parameters.models import Parameter

import chromadb
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings

class FixesCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the classify command

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure
        """

        parser.description = textwrap.dedent(
            """
            Classify the articles present in the database as either describing a software failure or not. If no arguments are
            provided, classify all articles that do not have a classification; otherwise, if --all is provided, classify
            all articles. If an article does not have a body, it will not be classified. 
            --sample is used for testing.
            --temp sets the ChatGPT temperature
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Classify all articles even if they already have a classification.",
        )
        parser.add_argument(
            "--sample",
            type=int,
            help="Dictates the number of samples",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--temp",
            type=float,
            default=0, 
            help="Sets the temperature for ChatGPT",
        )
        parser.add_argument(
            "--year",
            type=int,
            help="To run command for a specific published year of articles.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article classification process based on provided arguments.

        Args: 
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser for the configuration
        """

        logging.info("\nFixing published date reported in article.body for all articles.")
        
        #TODO: Redo publish date for all incidents, with the earliest date of all articles in each incident


        # Gets list of article to classify
        queryset = (
            Article.objects.filter(scrape_successful=True)
        )

        pattern = re.compile(r"Published on .*?\.") 

        articles_fixed = 0

        for article in queryset:
            
            logging.info("Fixing date for %s.", article)

            current_body = article.body
            correct_date = str(article.published)

            updated_body = re.sub(pattern, f"Published on {correct_date}.", current_body, count=1)

            article.body = updated_body

            article.save(update_fields=['body'])

            logging.info("\nOld body: %s.", current_body[:100])
            logging.info("\nNew body: %s.", article.body[:100])

            if articles_fixed == 20:
                break

        logging.info("Successfully fixed body with published dates for %d articles.", articles_fixed)