import argparse
import logging
import textwrap
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
from nltk.tokenize import word_tokenize
import nltk
# nltk.download('punkt')  # Download the tokenizer data

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
        # all_articles = Article_Ko.objects.filter(describes_failure=True)

        # num_articles = len(all_articles)

        # num_off_topic = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=False))

        # num_relevant = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=True))

        # print("Number of Ko articles ingested into DB: " + str(num_articles))

        # print("Number of off-topic Ko articles ingested into DB: " + str(num_off_topic))

        # print("Number of relevant Ko articles ingested into DB: " + str(num_relevant))

        article_word_counts_df = [[len(article.body.split(' ')), article] for article in Article.objects.filter(describes_failure=True)].sort(key=lambda x: x[0])
        article_ko_word_counts_df = [[len(article_ko.body.split(' ')), article_ko] for article_ko in Article_Ko.objects.filter(describes_failure=True)].sort(key=lambda x: x[0])

        print(article_word_counts_df[0][1].body)
        print("\n\n\n\n\nnext\n\n\n\n\n\n\n\n")
        print(article_ko_word_counts_df[0][1].body)

        return

        # Get article lengths
        article_word_counts_df = [len(article.body.split(' ')) for article in Article.objects.filter(describes_failure=True)]
        article_word_counts_non_df = [len(article.body.split(' ')) for article in Article.objects.all()]
        article_ko_word_counts_df = [len(article_ko.body.split(' ')) for article_ko in Article_Ko.objects.filter(describes_failure=True)]
        article_ko_word_counts_non_df = [len(article_ko.body.split(' ')) for article_ko in Article_Ko.objects.all()]

        # return

        # Create a box and whisker plot
        percentiles = [10, 90]

        # Combine the data for Article and Article_Ko
        combined_data = [article_word_counts_df, article_word_counts_non_df,
                        article_ko_word_counts_df, article_ko_word_counts_non_df]

        # Create labels for the boxplot
        labels = ['Article (DF)', 'Article (Non-DF)', 'Article_Ko (DF)', 'Article_Ko (Non-DF)']

        plt.boxplot(combined_data, labels=labels, showfliers=False, whis=percentiles)
        plt.title('Box and Whisker Plot of Article Body Lengths (Whiskers 10-90%)')
        plt.ylabel('Length of Body')
        plt.savefig('tests/ko_test/data/auto/word_length_box_and_whisker_outliers_10-90.png')

        # return

        def cohens_d(group1, group2):
            """
            Calculate Cohen's d for comparing the means of two groups.

            Parameters:
                group1 (array-like): Data for group 1.
                group2 (array-like): Data for group 2.

            Returns:
                float: Cohen's d effect size.
            """
            mean_diff = np.mean(group1) - np.mean(group2)
            pooled_std = np.sqrt((np.std(group1, ddof=1) ** 2 + np.std(group2, ddof=1) ** 2) / 2)

            effect_size = mean_diff / pooled_std
            return effect_size

        # Calculate statistics
        def print_statistics(name, data, threshold=500):
            above_threshold = np.sum(np.array(data) > threshold)
            below_threshold = np.sum(np.array(data) <= threshold)

            total_count = len(data)
            percent_above_threshold = (above_threshold / total_count) * 100
            percent_below_threshold = (below_threshold / total_count) * 100

            print(f"\nStatistics for {name}:")
            print(f"Mean: {np.mean(data)}")
            print(f"Median: {np.median(data)}")
            print(f"Standard Deviation: {np.std(data)}")
            print(f"Lower Quartile (Q1): {np.percentile(data, 25)}")
            print(f"Upper Quartile (Q3): {np.percentile(data, 75)}")
            print(f"Interquartile Range: {np.percentile(data, 75) - np.percentile(data, 25)}")
            print(f"Maximum: {np.max(data)}")
            print(f"Minimum: {np.min(data)}")
            print(f"Percent above {threshold} words: {percent_above_threshold:.2f}%")
            print(f"Percent below or equal to {threshold} words: {percent_below_threshold:.2f}%")

        print_statistics("Article DF", article_word_counts_df)
        print_statistics("Article non-DF", article_word_counts_non_df)
        print_statistics("Article_Ko DF", article_ko_word_counts_df)
        print_statistics("Article_Ko non-DF", article_ko_word_counts_non_df)
        return

        cohen_d_value = cohens_d(article_word_counts, article_ko_word_counts)
        print(f"\nCohen's d: {cohen_d_value}")

        # return

        # Create a figure with subplots
        fig, (ax_article, ax_article_ko) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # Plot histogram for Article
        ax_article.hist(article_lengths, bins=30, density=True, alpha=0.7, label='Article', color='blue')

        # Create smooth distribution line (kernel density estimate) for Article
        kde_smooth_article = np.linspace(min(article_lengths), max(article_lengths), 1000)
        kde_article = np.exp(-(kde_smooth_article - np.mean(article_lengths))**2 / (2 * np.var(article_lengths))) / \
                    np.sqrt(2 * np.pi * np.var(article_lengths))
        ax_article.plot(kde_smooth_article, kde_article, label='Smooth Distribution', color='blue')

        ax_article.set(title='Distribution of Article Body Lengths',
                    ylabel='Frequency')
        ax_article.legend()

        # Plot histogram for Article_Ko
        ax_article_ko.hist(article_ko_lengths, bins=30, density=True, alpha=0.7, label='Article_Ko', color='orange')

        # Create smooth distribution line (kernel density estimate) for Article_Ko
        kde_smooth_article_ko = np.linspace(min(article_ko_lengths), max(article_ko_lengths), 1000)
        kde_article_ko = np.exp(-(kde_smooth_article_ko - np.mean(article_ko_lengths))**2 /
                                (2 * np.var(article_ko_lengths))) / \
                        np.sqrt(2 * np.pi * np.var(article_ko_lengths))
        ax_article_ko.plot(kde_smooth_article_ko, kde_article_ko, label='Smooth Distribution', color='orange')

        ax_article_ko.set(xlabel='Length of Body',
                        ylabel='Frequency')
        ax_article_ko.legend()

        # Adjust layout for better visibility
        plt.tight_layout()

        # Show the combined plot
        plt.savefig('tests/ko_test/data/auto/word_count_distribution2.png')
        plt.show()

