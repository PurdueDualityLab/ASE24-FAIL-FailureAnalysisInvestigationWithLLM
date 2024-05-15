import argparse
import logging
import textwrap

import csv
import datetime
from collections import defaultdict
import matplotlib.pyplot as plt

from failures.articles.models import Incident

from failures.commands.PROMPTS import TAXONOMY_QUESTIONS


class ResultsCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Report results for paper from the database.
            """
        
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nReporting Results.")

        start_date = datetime(2010, 1, 1)
        end_date = datetime(2022, 12, 31, 23, 59, 59)

        incidents = Incident.objects.filter(published__range=(start_date, end_date))

        fields = list(TAXONOMY_QUESTIONS.keys())

        # Create a defaultdict to hold the counts for each field
        field_counts = {field: defaultdict(int) for field in fields}

        # Process each incident
        for incident in incidents:
            for field in fields:
                field_value = getattr(incident, field, "")
                if field_value:  # Check if the field value is not empty or None
                    values = [v.strip() for v in field_value.split(",") if v.strip()]  # Split and strip whitespace
                    for value in values:
                        field_counts[field][value] += 1

            fig, ax = plt.subplots(len(field_counts), 1, figsize=(10, len(field_counts) * 5), sharex=True)

        if len(field_counts) == 1:
            ax = [ax]

        for idx, (field, counts) in enumerate(field_counts.items()):
            labels = list(counts.keys())
            values = list(counts.values())

            ax[idx].barh(labels, values, color='skyblue')
            ax[idx].set_title(field.replace("_", " ").title())
            ax[idx].set_xlabel('Counts')
            ax[idx].set_ylabel('Values')

        #plt.tight_layout()
        #plt.show()
        plt.savefig('results/TaxonomyDistributionOverYears.png')

        


            

        


        