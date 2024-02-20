import argparse
import logging
import textwrap
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np

from failures.articles.models import Article_Ko, Article


class TestCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the scrape command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Scrape articles from Google News RSS feeds. If no arguments are provided, use all search
            queries present in the database; otherwise, use the provided arguments to create a new search query.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article scraping process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # # Retrieve and delete all articles from the database (preventing duplicates)
        all_articles = Article_Ko.objects.filter(describes_failure=True)

        num_articles = len(all_articles)

        num_off_topic = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=False))

        num_relevant = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=True))

        print("Number of Ko articles ingested into DB: " + str(num_articles))

        print("Number of off-topic Ko articles ingested into DB: " + str(num_off_topic))

        print("Number of relevant Ko articles ingested into DB: " + str(num_relevant))

        # Get article lengths
        article_lengths = [len(article.body.split(' ')) for article in Article.objects.all()]
        article_ko_lengths = [len(article_ko.body.split(' ')) for article_ko in Article_Ko.objects.all()]

        # Create a box and whisker plot
        plt.boxplot([article_lengths, article_ko_lengths], labels=['Article', 'Article_Ko'])
        plt.title('Box and Whisker Plot of Article Body Lengths')
        plt.ylabel('Length of Body')
        plt.show()

        # Calculate statistics
        def print_statistics(name, data):
            print(f"\nStatistics for {name}:")
            print(f"Mean: {np.mean(data)}")
            print(f"Median: {np.median(data)}")
            print(f"Standard Deviation: {np.std(data)}")
            print(f"Lower Quartile (Q1): {np.percentile(data, 25)}")
            print(f"Upper Quartile (Q3): {np.percentile(data, 75)}")
            print(f"Interquartile Range: {np.percentile(data, 75) - np.percentile(data, 25)}")
            print(f"Maximum: {np.max(data)}")
            print(f"Minimum: {np.min(data)}")

        print_statistics("Article", article_word_counts)
        print_statistics("Article_Ko", article_ko_word_counts)

