import argparse
import logging
import textwrap
import pandas as pd

from failures.articles.models import Article, SearchQuery


class EvaluateTaxonomyCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the evaluate taxonomy command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Evaluate the performance of the LLM at determining the taxonomy of a given article about software failure.
            If no arguments are provided, all articles that have been classified will be used to score performance.
            If --all is provided then more metrics will be outputted (# Right, # Wrong, # False Positive, # False Negative,
            # Evaluated).
            If --list is provided then a list of all articles that did not match will be outputted.
            If --articles is provided, then the list of articles input will be evaluated on their classification
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
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the evaluation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Creating metrics to return
        metrics = {}
        
        # Define the file path
        file_path = "./tests/manual_evaluation/perfect_merge.xlsx" #UPDATE

        # Define the columns to read
        columns_to_read = ["id", "Describes Failure? (0: False | 1: True)"] #UPDATE

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_excel(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return metrics
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return metrics

        # Filter rows where 'id' is not a positive integer and 'Describes Failure?' is not 0 or 1 #UPDATE
        df = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)]
        df = df[df['Describes Failure? (0: False | 1: True)'].isin([0, 1])]

        # Check --articles
        if args.articles:
            df = df[df['id'].apply(lambda x: x in args.articles)]

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
        incorrectly_taxonomized_articles = []

        # Iterate through articles and count matches
        for article in matching_articles:
            article_id = article.id
            ground_truth = df[df['id'] == article.id]['Describes Failure? (0: False | 1: True)'].values[0]
            if article.describes_failure and article.describes_failure == ground_truth:
                total_match += 1
            else:
                if args.list:
                    incorrectly_taxonomized_articles.append(
                        f"Article ID: {article.id}, "
                        f"Title: {article.title}, "
                        f"Ground Truth: {'Is a failure' if ground_truth == 1 else 'Is not a failure'}, "
                        f"Classified As: {'Is a failure' if article.describes_failure and article.describes_failure == 1 else 'Is not a failure'}"
                    )
                # Update false positives and negatives
                if article.describes_failure and article.describes_failure == 1 and ground_truth == 0:
                    false_positives += 1
                elif article.describes_failure and article.describes_failure == 0 and ground_truth == 1:
                    false_negatives += 1

        # Checking to see if there are any matching articles
        if total_articles > 0:

            accuracy_percentage = (total_match / total_articles) * 100
            logging.info(f"Accuracy: {accuracy_percentage:.2f}% ({total_match}/{total_articles})")

            # Checking if --list
            if args.list:
                logging.info('List of incorrectly classified articles:')
                for article in incorrectly_taxonomized_articles:
                    logging.info(article)

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

            metrics = {
                "Classify: Accuracy (Percentage)": f"{accuracy_percentage:.2f}%",
                "Classify: Accuracy (Fraction)": f"{total_match}/{total_articles}",
                "Classify: False Positive (Percentage)": f"{false_positive_rate:.2f}%",
                "Classify: False Positive (Fraction)": f"{false_positive_fraction}",
                "Classify: False Negative (Percentage)": f"{false_negative_rate:.2f}%",
                "Classify: False Negative (Fraction)": f"{false_negative_fraction}",
                "Classify: Wrong (Percentage)": f"{wrong_percentage:.2f}%",
                "Classify: Wrong (Fraction)": f"{wrong_classifications}/{total_articles}",
                "Classify: Total Evaluated": str(total_articles) 
            }
        else:
            logging.info("Evaluate Classification Command: No common IDs found between ground truth and predicted data.")


        return metrics