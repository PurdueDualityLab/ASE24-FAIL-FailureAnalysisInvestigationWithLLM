from sklearn.metrics import homogeneity_score, completeness_score, v_measure_score
import argparse
import logging
import textwrap
import pandas as pd

from failures.articles.models import Article, SearchQuery


class EvaluateMergeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate merge command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM at merging the articles into clusters of incidents. This will return
            a V-Measure which is a harmonic mean between a homogeneity score and a completeness score. If no arguments are
            provided, all articles that have a corresponding manual classificaiton will be used to score performacne and only
            V-Measure will be logged.
            If --all is provided then more metrics will be output (V-Measure, Homogeneity Score, Completeness Score, etc.)
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Lists all metrics.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Define the file path
        file_path = "./tests/manual_evaluation/Classification_Auto_Dev.xlsx"

        # Define the columns to read
        columns_to_read = ["id", "Describes Failure? (0: False | 1: True)", "incident"]

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
        df = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]
        df = df[df['Describes Failure? (0: False | 1: True)'].isin([0, 1])]
        df = df[df['incident'].apply(lambda x: isinstance(x, float) and x >= 0)]

        # Get a list of article IDs from the manual database
        article_ids = df['id'].tolist()

        # Query for articles matching manual db IDs
        matching_articles = Article.objects.filter(id__in=article_ids)

        # Map id to incident for ground truth and predicted
        ground_truth_mapping = {row['id']: int(row['incident']) for _, row in df.iterrows()}
        predicted_mapping = {article.id: article.incident.id for article in matching_articles}

        # Get common ids
        common_ids = set(ground_truth_mapping.keys()) & set(predicted_mapping.keys())

        # Create lists for true labels and predicted labels based on common IDS
        true_labels = [ground_truth_mapping[article_id] for article_id in common_ids]
        predicted_labels = [predicted_mapping[article_id] for article_id in common_ids]


        # Calculate homogeneity, completeness, and V-Measure
        if common_ids:
            # Calculate homogeneity score
            homogeneity = homogeneity_score(true_labels, predicted_labels)

            # Calculate completeness score
            completeness = completeness_score(true_labels, predicted_labels)

            # Calculate V-measure
            v_measure = v_measure_score(true_labels, predicted_labels)

            # Log results
            if args.all:
                logging.info(f"Homogeneity Score: {homogeneity:.2f}")
                logging.info(f"Completeness Score: {completeness:.2f}")
            logging.info(f"V-Measure Score: {v_measure:.2f}")
        else:
            logging.info("No common IDs found between ground truth and predicted data.")