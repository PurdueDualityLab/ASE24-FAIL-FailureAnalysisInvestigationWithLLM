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
from failures.commands.merge import MergeCommand
from failures.commands.vectordb import VectordbCommand
from failures.commands.postmortemIncident import PostmortemIncidentCommand
from failures.commands.cluster import ClusterCommand
from tests.commands.evaluate_classification import EvaluateClassificationCommand
from tests.commands.evaluate_identification import EvaluateIdentificationCommand
from tests.commands.evaluate_merge import EvaluateMergeCommand

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
            default=-1,
            help="Sets the temperature for ChatGPT",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all articles incorrectly classified.",
        )
        parser.add_argument(
            "--noEval",
            action="store_true",
            help="Starts testing the pipeline at classify (Defualt).",
        )
        parser.add_argument(
            "--startClassify",
            action="store_true",
            help="Starts testing the pipeline at classify (Defualt).",
        )
        parser.add_argument(
            "--startMerge",
            action="store_true",
            help="Starts testing the pipeline at merge.",
        )
        parser.add_argument(
            "--startVectorDB",
            action="store_true",
            help="Starts testing the pipeline at vectorDB.",
        )
        parser.add_argument(
            "--startPostmortemInicdent",
            action="store_true",
            help="Starts testing the pipeline at postmortemIncident.",
        )
        parser.add_argument(
            "--startCluster",
            action="store_true",
            help="Starts testing the pipeline at cluster.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key for all articles.",
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
        else:
            num_sample = len(args.articles)
        
        # Get 20 random articles if articles not explicitly defined
        if not args.articles:
            article_ids = random.sample(list(article_ids), num_sample)
            args.articles = article_ids

        # Set temperatures
        if 0.0 <= args.temp <= 1.0:
            temperatures = [args.temp]
            logging.info("Evaluation pipeline for temperature: " + str(args.temp))
        else:
            temperatures = [0.1 * x for x in range(0, 11)]

        # Create Dataframe to store evaluation
        # column_names = list(['Temperature','Accuracy (Percentage)', 'Sample Size', 'Accuracy (Fraction)', 'False Positive (Percentage)', 'False Positive (Fraction)', 'False Negative (Percentage)', 'False Negative (Fraction)', 'Wrong (Percentage)', 'Wrong (Fraction)', 'Total Evaluated'])
        # df = pd.DataFrame(columns=column_names)
        dfs = []

        # Get starting point for testing
        start = 0
        if args.startClassify:
            start = 0 # Redundant
        elif args.startMerge:
            start = 1
        elif args.startVectorDB:
            start = 2
        elif args.startPostmortemInicdent:
            start = 3
        elif args.startCluster:
            start = 4

        logging.info("Temperatures: " + str(temperatures))
        for temperature in temperatures:
            args.temp = temperature

            # Blank metrics
            all_metrics = {}
            classification_metrics = {}
            identification_metrics = {}

            # CLASSIFICATION & EVALUATION
            if start <= 0:
                logging.info("Classifying articles for " + str(temperature) + " temperature.")
                # run command
                classify = ClassifyCommand()
                classify.run(args, parser)

                if not args.noEval:
                    # classify
                    evaluate_classify = EvaluateClassificationCommand()
                    classification_metrics = evaluate_classify.run(args, parser)

                    # Identify
                    evaluate_identify = EvaluateIdentificationCommand()
                    identification_metrics = evaluate_identify.run(args, parser)

            # MERGING & EVALUATION
            if start <= 1:
                logging.info("Merging articles for " + str(temperature) + " temperature.")
                # run command
                merge = MergeCommand()
                merge.run(args, parser)

                if not args.noEval:
                    # merge
                    evaluate_merge = EvaluateMergeCommand()
                    merge_metrics = evaluate_merge.run(args, parser)

            # VECTORDB & EVALUATION
            if start <= 2:
                logging.info("Vectorizing articles.")
                # run command
                vectorDB = VectordbCommand()
                vectorDB.run(args, parser)

                if not args.noEval:
                    # PUT EVALUATION HERE IF NEEDED #
                    # vector
                    pass

            # POSTMORTEM INCIDENT & EVALUATION
            if start <= 3:
                logging.info("Analyzing postmortem for " + str(temperature) + " temperature.")
                args.all = True
                postmortem = PostmortemIncidentCommand()
                postmortem.run(args, parser)

                if not args.noEval:
                    # PUT EVALUATION HERE IF NEEDED #
                    # postmortem incident
                    pass

            # CLUSTER & EVALUATION
            if start <= 4:
                logging.info("Clustering incidents for " + str(temperature) + " temperature.")
                cluster = ClusterCommand()
                cluster.run(args, parser)

                if not args.noEval:
                    # PUT EVALUATION HERE IF NEEDED #
                    # cluster
                    pass

            # Adding addtional metrics then appending excel sheet
            all_metrics["Temperature"] = str(args.temp)
            all_metrics["Sample Size"] = str(num_sample)
            if classification_metrics:
                all_articles.update(classification_metrics)
            if identification_metrics:
                all_metrics.update(identification_metrics)
            if merge_metrics:
                all_metrics.update(merge_metrics)

            # Convert to dataframe
            df_temp = pd.DataFrame([all_metrics])
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
            csv_path = f'./tests/performance/temperature{temperature:.1f}.csv'
            article_df.to_csv(csv_path, index=False)
            logging.info("Wrote to " + csv_path)

        # Convert dataframe to CSV
        df = pd.concat(dfs, ignore_index=True)
        csv_path = './tests/performance/temperature.csv'
        df.to_csv(csv_path, index=False)