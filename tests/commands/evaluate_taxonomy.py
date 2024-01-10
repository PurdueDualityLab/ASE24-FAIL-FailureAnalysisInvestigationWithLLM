import argparse
import logging
import textwrap
import pandas as pd
from sklearn.metrics import confusion_matrix

from failures.articles.models import Article, SearchQuery, Incident


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

        # Query for incident IDs matching manual db IDs
        incident_ids = list(
            Article.objects.filter(id__in=args.articles)
            .exclude(incident__isnull=True)
            .values_list('incident_id', flat=True)
            .distinct()
        )

        # Get incidents
        incidents = Incident.objects.filter(id__in=incident_ids)
        
        # Define the file path
        file_path = "./tests/manual_evaluation/experiment_data_manual_articles_Analyst-B.xlsx" #UPDATE

        # Define the columns to read
        columns_to_read = [
            # "id", # UPDATE WITH MANUAL
            "Incident ID",
            # "Describes Failure", # Comment back in when manual set is complete
            # "Analyzable Failure", # Comment back in when manual set is complete
            "Phase Option",
            "Boundary Option",
            "Nature Option",
            "Dimension Option",
            "Objective Option",
            "Intent Option",
            "Capability Option",
            "Duration Option",
            "Domain Option",
            "CPS Option",
            "Perception Option",
            "Communication Option",
            "Application Option",
            "Behaviour Option"
        ]

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
        # df = df[df['id'].apply(lambda x: isinstance(x, int) and x >= 0)] # UPDATE WITH MANUAL
        df = df[df['Incident ID'].apply(lambda x: isinstance(x, int) and x >= 0)]
        # df = df[df['Describes Failure'] == 1 & df['Analyzable Failure'] == 1]

        # Check --articles
        # if args.articles:
        #     # df = df[df['id'].apply(lambda x: x in args.articles)] # UPDATE WITH MANUAL
        #     df = df[df['Incident ID'].apply(lambda x: x in args.articles)]
        df = df[df['Incident ID'].apply(lambda x: x in incident_ids)]

        # List of taxonomies to iterate over
        taxonomies = [
            "Phase Option",
            "Boundary Option",
            "Nature Option",
            "Dimension Option",
            "Objective Option",
            "Intent Option",
            "Capability Option",
            "Duration Option",
            "Domain Option",
            "CPS Option",
            "Perception Option",
            "Communication Option",
            "Application Option",
            "Behaviour Option"
        ]

        for taxonomy in taxonomies:
            # Extract relevant column from the dataframe
            df_taxonomy_values = df[taxonomy].tolist()
            # print(df_taxonomy_values)
            # return

            # Extract corresponding field values from the incidents
            incidents_taxonomy_values = list(incidents.values_list(taxonomy, flat=True))

            # Compute confusion matrix
            cm = confusion_matrix(incidents_taxonomy_values, df_taxonomy_values)

            # Store or print the confusion matrix as needed
            metrics[taxonomy] = cm

        # Return the metrics


        return metrics

        