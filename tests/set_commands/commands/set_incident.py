import argparse
import logging
import textwrap
import pandas as pd
import csv

from failures.articles.models import Article, Incident

class SetIncidentCommand:
    INPUT_FILE_PATH = "tests/set_commands/manual_states/desired_state.csv"

    def __init__(self):
        pass

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the set incident command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Set the article's incident to the desired state.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the set incident state command.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        logging.info("Updating article's incident attributes.")

        # Define the columns to read
        columns_to_read = ["article_id", "incident"]

        # Read the Excel file into a Pandas DataFrame
        file_path = self.INPUT_FILE_PATH
        try:
            df = pd.read_csv(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return 

        
        # Iterate over each row in the DataFrame
        for index, row in df.iterrows():
            article_id = row["article_id"]
            incident = row["incident"]

            if type(incident) is not int:
                continue

            print(incident)

            continue

            # Fetch the Article object from the database
            try:
                article = Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                logging.warning(f"Article with ID {article_id} does not exist.")
                continue

            # Update the describes_failure attribute
            article.describes_failure = describes_failure
            article.save()

        logging.info("Article's incident attributes done updating.")

        return
