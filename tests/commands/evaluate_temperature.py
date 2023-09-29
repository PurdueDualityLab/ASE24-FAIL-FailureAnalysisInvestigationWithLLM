import argparse
import logging
import textwrap
import pandas as pd
from openpyxl import load_workbook
from django.core import serializers
import random
import os
import csv

from failures.articles.models import Article, SearchQuery
from failures.commands.classify import ClassifyCommand
from tests.commands.evaluate_classification import EvaluateClassificationCommand

class EvaluateTemperatureCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate different temperatures.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM using different temperatures. If no arguments are provided then 
            sample set of size 20 is going to be taken from the database and tested at different temperatures. 
            If --all is provided then all of the articles in the database are going to be used. 
            --sample = (int) can be used to set the number of samples taken to test with.
            --articles = [(ints)] can be used to determine which articles are sampled (this will override --sample).
            """
        )
        # Need to implement
        parser.add_argument(
            "--all",
            action="store_true",
            help="Lists all metrics.",
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
            help="Sets the temperature for ChatGPT",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all articles incorrectly classified.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Define the file path
        file_path = "./tests/manual_evaluation/perfect_merge.xlsx"

        # Define the columns to read
        columns_to_read = ["id"]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_excel(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return

        # Filter rows where 'id' is not a positive integer and 'Describes Failure?' is not 0 or 1
        article_ids = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]['id'].tolist()

        # Get number of samples
        if not args.articles:
            num_sample = args.sample if args.sample else 20
            num_sample = min(len(article_ids), num_sample)
        
        # Get 20 random articles if articles not explicitly defined
        if not args.articles:
            article_ids = random.sample(list(article_ids), num_sample)
            args.articles = article_ids
        if args.temp:
            temperatures = [args.temp]
        else:
            temperatures = [0.1 * x for x in range(0, 11)]

        # Create Dataframe to store evaluation
        # column_names = list(['Temperature','Accuracy (Percentage)', 'Sample Size', 'Accuracy (Fraction)', 'False Positive (Percentage)', 'False Positive (Fraction)', 'False Negative (Percentage)', 'False Negative (Fraction)', 'Wrong (Percentage)', 'Wrong (Fraction)', 'Total Evaluated'])
        # df = pd.DataFrame(columns=column_names)
        dfs = []

        for temperature in temperatures:
            args.temp = temperature

            # CLASSIFICATION
            classify = ClassifyCommand()
            classify.run(args, parser)

            # EVALUATION
            evaluate_classify = EvaluateClassificationCommand()
            classification_metrics = evaluate_classify.run(args, parser)

            # Identification
            # Merge

            # Adding addtional metrics then appending excel sheet
            classification_metrics["Temperature"] = str(args.temp)
            classification_metrics["Sample Size"] = str(num_sample)

            # Convert to dataframe
            df_temp = pd.DataFrame([classification_metrics])
            dfs.append(df_temp)

            # Get all information about articles recently classified and store in dataframe
            articles = Article.objects.filter(id__in=args.articles)
            serialized_data = serializers.serialize('python', articles)
            article_data_list = []

            for entry in serialized_data:
                article_data = entry['fields']
                article_data['Article ID'] = entry['pk']
                article_data_list.append(article_data)

            article_df = pd.DataFrame(article_data_list)
        

            # Create dataframe and store in CSV
            csv_path = f'./tests/performance/temperature{temperature}.csv'
            article_df.to_csv(csv_path, index=False)

        # Convert dataframe to CSV
        df = pd.concat(dfs, ignore_index=True)
        csv_path = './tests/performance/temperature.csv'
        df.to_csv(csv_path, index=False)