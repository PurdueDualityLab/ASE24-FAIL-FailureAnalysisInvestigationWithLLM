import argparse
import logging
import textwrap

import csv
import pandas as pd
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from failures.articles.models import Article, Incident

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

        start_year = 2010
        end_year = 2022

        # Get the list of distinct years
        years = list(range(start_year,end_year+1)) #list(Article.objects.values_list('published__year', flat=True).distinct())

        stats = {}
        for year in years:
            count_all = Article.objects.filter(published__year=year).count()
            count_scrape_successful = Article.objects.filter(scrape_successful=True, published__year=year).count()
            count_describes_failure = Article.objects.filter(describes_failure=True, published__year=year).count()
            count_analyzable_failure = Article.objects.filter(analyzable_failure=True, published__year=year).count()
            count_incidents = Incident.objects.filter(published__year=year).count()

            stats[year] = {
                'All': count_all,
                'Scrape Successful': count_scrape_successful,
                'Describes Failure': count_describes_failure,
                'Analyzable Failure': count_analyzable_failure,
                'Incidents': count_incidents
            }

        # Prepare data for the Sankey diagram
        labels = []
        source = []
        target = []
        value = []

        label_to_index = {}
        index = 0

        # Create labels for years and stats categories
        for year in years:
            labels.append(f"Year {year}")
            label_to_index[f"Year {year}"] = index
            index += 1

        for category in ['All', 'Scrape Successful', 'Describes Failure', 'Analyzable Failure', 'Incidents']:
            labels.append(category)
            label_to_index[category] = index
            index += 1

        # Create source, target, and value lists for Sankey
        for year in years:
            if year in stats:
                for category, count in stats[year].items():
                    source.append(label_to_index[f"Year {year}"])
                    target.append(label_to_index[category])
                    value.append(count)

        # Create the Sankey plot
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
            ),
            link=dict(
                source=source,
                target=target,
                value=value
            ))])

        # Update layout and save the figure
        fig.write_image("results/IncidentsOverYears.png")

        '''
        # Convert the stats dictionary to a DataFrame
        df = pd.DataFrame.from_dict(stats, orient='index').sort_index()

        logging.info(df)

        # Plotting the stacked bar chart
        ax = df.plot(kind='bar', stacked=True, figsize=(14, 8))

        # Adding labels and title
        ax.set_xlabel('Year')
        ax.set_ylabel('Count')
        ax.set_title('Incident Statistics Over the Years')
        ax.legend(title='Categories', bbox_to_anchor=(1.05, 1), loc='upper left')

        # Save the plot as a PNG file
        plt.tight_layout()
        plt.savefig('results/IncidentsOverYears.png')
        plt.close()

        '''


        '''
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)

        incidents = Incident.objects.filter(published__range=(start_date, end_date))

        fields = list(TAXONOMY_QUESTIONS.keys())

        # Create a defaultdict to hold the counts for each field
        field_counts = {field: defaultdict(int) for field in fields}

        # Process each incident
        for incident in incidents:
            for field in fields:
                field_value = getattr(incident, f"{field}_option", "")
                if field_value:  # Check if the field value is not empty or None
                    values = [v.strip() for v in field_value.split(",") if v.strip()]  # Split and strip whitespace
                    for value in values:
                        field_counts[field][value] += 1

        # Convert the dictionary to a DataFrame
        data = {field: dict(counts) for field, counts in field_counts.items()}
        df = pd.DataFrame(data).fillna(0).astype(int)

        # Transpose the DataFrame for easier plotting
        df = df.T
        df.index.name = 'Fields'

        # Plotting the stacked bar chart
        ax = df.plot(kind='barh', stacked=True, figsize=(14, 8))

        # Adding labels and title
        ax.set_xlabel('Count')
        ax.set_ylabel('Fields')
        ax.set_title('Distribution of Keys for Each Field in Incidents')
        ax.legend(title='Options', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.savefig('results/TaxonomyDistributionOverYears.png')
        '''