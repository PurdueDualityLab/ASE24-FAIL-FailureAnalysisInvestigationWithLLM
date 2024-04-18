import argparse
import logging
import textwrap
import re
import math
import pandas as pd

from failures.articles.models import Incident

class ClusterCommand:
    POSTMORTEM_FIELDS = ["SEcauses", "impacts"]

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the cluster command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """

        parser.description = textwrap.dedent(
            """
            Cluster postmortem data into themes and subthemes. 
            """
        )
        parser.add_argument(
            "--fields",
            nargs='+',
            choices=self.POSTMORTEM_FIELDS,
            default=self.POSTMORTEM_FIELDS,
            help="A list of incident fields to perform clustering on.",
        )
        parser.add_argument(
            "--ids",
            nargs='+',
            type=int,
            help="List of incident ids.",
        )
        # parser.add_argument(
        #     "--all",
        #     action="store_true",
        #     default=False,
        #     help="Create embeddings for all articles even if they already have embeddings.",
        # )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser, articles = None):
        """
        Run the article clustering process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        # Get fields to cluster
        postmortem_keys = args.fields
        logging.info(f"Clustering postmortem information for fields: {postmortem_keys}")

        # Get incidents
        if args.ids:
            incidents = Incident.objects.filter(id__in=args.ids, complete_report=True)
        else:
            incidents = Incident.objects.filter(complete_report=True)
        logging.info(f"Clustering information from {len(incidents)} articles.")

        # Pre-process data to be clustered
        pre_process_data(incidents, postmortem_keys)

        # TODO: Data is now clean and ready to be passed into what is on SEcauses colab.
        # TODO: Check on incident queryset to see if it is working

def pre_process_data(incidents, postmortem_keys) -> dict:
    # Convert incident data to a list of dictionaries
    incidents_list = list(incidents.values('id', *postmortem_keys))

    # Create a DataFrame from the queryset data
    incidents_df = pd.DataFrame(incidents_list)

    # Dictionary to store cleaned data
    cleaned_data = {}

    # Clean data
    for postmortem_key in postmortem_keys:
        clean_key = []
        for (id, raw_data) in zip(incidents_df["id"], incidents_df[postmortem_key]):
            raw_data = re.split(r'\d+\.\s*', raw_data) # Split on numbered list
            raw_data = [re.sub(r'\s*\[(?:Article\s+)?\d+(?:,\s*\d+)*\]\s*[\n.]?$', '.', data) for data in raw_data] # Remove numberings and article citations
            clean_key.extend(raw_data[1:])  # Skip the first empty item

        # Store back to output dictionary
        cleaned_data[postmortem_key] = clean_key

    return cleaned_data


        