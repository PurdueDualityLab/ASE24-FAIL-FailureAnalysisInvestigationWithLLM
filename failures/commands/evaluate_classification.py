import argparse
import logging
import textwrap
import pandas as pd

from failures.articles.models import Article, SearchQuery


class EvaluateClassificationCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate classification command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM predicting whether or not a given article is a software failure.
            If no arguments are provided, all articles that have been classified will be used to score performance.
            If --all is provided then more metrics will be outputted (# Right, # Wrong, # False Positive, # False Negative,
            # Evaluated).
            If --list is provided then a list of all articles that did not match will be outputted.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Lists all metrics.",
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
        file_path = "./manual_evaluation/Classification_Auto_Dev.xlsx"

        # Define the columns to read
        columns_to_read = ["id", "Describes Failure? (0: False | 1: True)"]

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

        # Get a list of article IDs from the manual database
        article_ids = df['id'].tolist()

        # Query for articles matching manual db IDs
        matching_articles = Article.objects.filter(id__in=article_ids)

        # Calculate accuracy and additional metrics
        total_match = 0
        total_articles = len(matching_articles)
        false_positives = 0
        false_negatives = 0

        # List of incorrectly classified articles (if --list)
        incorrectly_classified_articles = []

        # Iterate through articles and count matches
        for article in matching_articles:
            article_id = article.id
            ground_truth = df[df['id'] == article.id]['Describes Failure? (0: False | 1: True)'].values[0]
            if article.describes_failure == ground_truth:
                total_match += 1
            else:
                if args.list:
                    incorrectly_classified_articles.append(
                        f"Article ID: {article.id}, "
                        f"Title: {article.title}, "
                        f"Ground Truth: {'Is a failure' if ground_truth == 1 else 'Is not a failure'}, "
                        f"Classified As: {'Is a failure' if article.describes_failure == 1 else 'Is not a failure'}"
                    )
                # If --all then update false positives and negatives
                if args.all:
                    if article.describes_failure == 1 and ground_truth == 0:
                        false_positives += 1
                    elif article.describes_failure == 0 and ground_truth == 1:
                        false_negatives += 1
            

        accuracy_percentage = (total_match / total_articles) * 100
        logging.info(f"Accuracy: {accuracy_percentage:.2f}% ({total_match}/{total_articles})")

        # Checking if --list
        if args.list:
            logging.info('List of incorrectly classified articles:')
            for article in incorrectly_classified_articles:
                logging.info(article)

        # Checkign if --all
        if args.all:
            # Calculate false positive and false negative rates as both fractions and percentages
            false_positive_rate = (false_positives / total_articles) * 100
            false_negative_rate = (false_negatives / total_articles) * 100
            false_positive_fraction = f"{false_positives}/{total_articles}"
            false_negative_fraction = f"{false_negatives}/{total_articles}"

            # Calculate the number and percentage of correct and wrong classifications
            correct_classifications = total_match
            wrong_classifications = total_articles - total_match
            wrong_percentage = (wrong_classifications / total_articles) * 100

            logging.info(f"False Positives: {false_positive_rate:.2f}% ({false_positive_fraction})")
            logging.info(f"False Negatives: {false_negative_rate:.2f}% ({false_negative_fraction})")
            logging.info(f"Wrong: {wrong_percentage:.2f}% ({wrong_classifications}/{total_articles})")
            logging.info(f"Total Evaluated: {total_articles}")
