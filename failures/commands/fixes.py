import argparse
import logging
import textwrap
import time

import pandas as pd

import re

from failures.articles.models import Article, Incident
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
            To fix any parts of the database.
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
        parser.add_argument(
            "--experiment",
            type=bool,
            default=False,
            help="Marks articles as part of the experiment.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article classification process based on provided arguments.

        Args: 
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser for the configuration
        """

        ### To set experiment flag to True
        '''
        incidents = Incident.objects.filter(articles__in=args.articles).distinct()
        articles = Article.objects.filter(id__in=args.articles)

        ### If queryset is for an experiment mark it as such
        if args.experiment is True:
            incidents.update(experiment=True)
            articles.update(experiment=True)
        
        '''



        '''
        ### To print incident IDs for articles in experiment set
        incidents = Incident.objects.filter(articles__in=args.articles).distinct()
        articles = Article.objects.filter(id__in=args.articles)


        # Create a DataFrame to store the data
        data = {'Article ID': [], 'Incident ID': []}

        # Populate the DataFrame with article and incident IDs
        for article in articles:
            incident_ids = incidents.filter(articles=article).values_list('id', flat=True)
            data['Article ID'].extend([article.id] * len(incident_ids))
            data['Incident ID'].extend(incident_ids)

        # Convert the data to a DataFrame
        df = pd.DataFrame(data)

        # Save the DataFrame to a CSV file
        csv_file_path = 'tests/fetched_data/articles2incidents.csv'  # Provide the desired file path
        df.to_csv(csv_file_path, index=False)
        
        '''


        #For incident 31, copy over the lasts parts of merge for that article


        



        #TODO: Redo publish date for all incidents, with the earliest date of all articles in each incident

        ### Fixes an error with how the published date is appended to the body of the articles
        '''
        logging.info("\nFixing published date reported in article.body for all articles.")
        
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
        '''