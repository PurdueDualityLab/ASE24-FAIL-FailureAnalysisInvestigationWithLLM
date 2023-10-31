import argparse
import logging
import textwrap
import pandas as pd
import random

from failures.articles.models import Article, SearchQuery


class GenerateArticleIdsCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the generate article ids command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Generates a random list of articles to use for testing. 
            The command will generate a list of article IDs then store the articles and respective incidents in 
            experiment_data_auto_incidents.csv, and experiment_data_auto_articles.csv. The command will also find articles that 
            describe software failures and are analyzeable and those that are not. 


            """
        )
        parser.add_argument(
            "--countIncidents",
            type=int,  # Converts the values to integers
            help="Determines the number of article IDs to generate",
        )
        parser.add_argument(
            "--seed",
            type=int,  # Converts the values to integers
            help="The seed for randomly generating article IDs.",
        )
        parser.add_argument(
            "--countFailures",
            type=int,    # Converts the values to integers
            help="Determines the number IDs for articles classified as reporting on software failure AND classified analyzable.",
        )
        parser.add_argument(
            "--countNonFailures",
            type=int,    # Converts the values to integers
            help="Determines the number IDs for articles classified as not reporting on software failure.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Generates random list of article IDs given parameters and stores to to CSV files. 

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Set random seed
        if args.seed:
            random.seed(args.seed)

        # Handling args count
        if(args.countIncidents <= 0):
            args.countIncidents = 20

        
        

        print(len(df))
        print(len(matching_articles))
        print(df['id'].values.tolist())


        return 0
