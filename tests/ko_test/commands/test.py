import argparse
import logging
import textwrap
import pandas as pd
from datetime import datetime
import os
import matplotlib.pyplot as plt
import numpy as np
# from nltk.tokenize import word_tokenize
# import nltk
import tiktoken

# nltk.download('punkt')  # Download the tokenizer data

from failures.articles.models import Article_Ko, Article, Incident


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
        story_article_tuples = [
            (57170, 3),
            (3942, 4),
            (32384, 12),
            (57598, 72),
            (52863, 3),
            (48515, 9),
            (6093, 1),
            (52863, 12),
            (49946, 7),
            (25477, 3),
            (33937, 3),
            (57598, 26),
            (4900, 9),
            (48113, 4),
            (57598, 61),
            (27465, 1),
            (55532, 2),
            (11814, 1),
            (50398, 12),
            (15868, 3),
            (32384, 1),
            (10747, 1),
            (5849, 1),
            (51848, 1),
            (33022, 2),
            (3244, 3),
            (32524, 9),
            (15868, 23),
            (14717, 5),
            (57598, 3),
            (1119, 5),
            (49758, 2),
            (56840, 6),
            (4900, 8),
            (36160, 6),
            (9680, 7),
            (37319, 1),
            (46410, 7),
            (40232, 15),
            (51163, 1),
            (2435, 5),
            (4577, 3),
            (12133, 2),
            (51848, 8),
            (37564, 5),
            (20278, 10),
            (5849, 13),
            (39242, 4),
            (44888, 3),
            (50804, 20),
            (17892, 17),
            (30722, 2),
            (50398, 1),
            (57598, 33),
            (33317, 5),
            (15868, 47),
            (52863, 45),
            (57598, 55),
            (56840, 16),
            (15868, 4)
        ]

        # Define the file path
        file_path = "./tests/ko_test/data/Ko_Stories_Consensus.csv"

        # Define the columns to read
        columns_to_read = ["storyID", "articleID", "DjangoArticleID", "Consensus"]

        # Read the Excel file into a Pandas DataFrame
        try:
            df = pd.read_csv(file_path, usecols=columns_to_read)
            logging.info("Data loaded successfully.")
        except FileNotFoundError:
            logging.info(f"Error: The file '{file_path}' was not found.")
            return metrics
        except Exception as e:
            logging.info(f"An error occurred: {str(e)}")
            return metrics

        # # Filter out rows with missing values in 'DjangoArticleID'
        # df = df.dropna(subset=['DjangoArticleID'])

        df_filtered = df[df[['storyID', 'articleID']].apply(tuple, axis=1).isin(story_article_tuples)]

        article_ko_ids = df_filtered['DjangoArticleID'].tolist()

        describes_failure_true_count = Article_Ko.objects.filter(describes_failure=True, id__in=article_ko_ids).count()

        # Query Article_Ko objects with describes_failure=False
        describes_failure_false_count = Article_Ko.objects.filter(describes_failure=False, id__in=article_ko_ids).count()

        # Total number of articles
        total_articles = len(article_ko_ids)

        # Calculate percentages
        percent_describes_failure_true = (describes_failure_true_count / total_articles) * 100
        percent_describes_failure_false = (describes_failure_false_count / total_articles) * 100

        # Print statistics
        print("Statistics on describes_failure field:")
        print(f"Total articles: {total_articles}")
        print(f"Number of articles describing failure: {describes_failure_true_count} ({percent_describes_failure_true:.2f}%)")
        print(f"Number of articles not describing failure: {describes_failure_false_count} ({percent_describes_failure_false:.2f}%)")


        return
        # Retrieve and delete all articles from the database (preventing duplicates)
        # all_articles = Article_Ko.objects.filter(describes_failure=True)

        # all_ko = len(Article_Ko.objects.all())

        # num_articles = len(all_articles)

        # num_off_topic = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=False))

        # num_relevant = len(Article_Ko.objects.filter(describes_failure=True, relevant_to_story=True))

        # print("Number of Ko articles with 3 raters: " + str(all_ko))

        # print("Number of Ko articles ingested into DB: " + str(num_articles))

        # print("Number of off-topic Ko articles ingested into DB: " + str(num_off_topic))

        # print("Number of relevant Ko articles ingested into DB: " + str(num_relevant))

        # Get all the incidents
        incidents = Incident.objects.all()
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        incident_token_counts = []

        for incident in incidents:
            related_articles = incident.articles.all()

            incident_tokens = 0

            for article in related_articles:
                incident_tokens += len(encoding.encode(article.body))

            incident_token_counts.append(incident_tokens)

        # Calculate statistics
        max_token_count = max(incident_token_counts)
        min_token_count = min(incident_token_counts)
        median_token_count = np.median(incident_token_counts)
        greater_than_16k_count = sum(count > 16000 for count in incident_token_counts)

        # Report statistics
        print(f"Max Token Count: {max_token_count}")
        print(f"Min Token Count: {min_token_count}")
        print(f"Median Token Count: {median_token_count}")
        print(f"Number of incidents with more than 16k tokens: {greater_than_16k_count}")
        print(f"Total number of incidents: {len(incidents)}")

        # Plot histogram
        plt.hist(incident_token_counts, bins=20, edgecolor='black')
        plt.title('Distribution of Token Counts in Incidents')
        plt.xlabel('Token Count')
        plt.ylabel('Frequency')
        plt.savefig('tests/ko_test/data/auto/incident_tokens.png')


        # print(incident_token_counts)

        return
        incidents = Incident.objects.all()

        # Create a list of the number of articles per incident
        article_counts_per_incident = [incident.articles.count() for incident in incidents]

        # Plot the original histogram
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.hist(article_counts_per_incident, bins=range(min(article_counts_per_incident), max(article_counts_per_incident) + 1), edgecolor='black')
        plt.xlabel('Number of Articles per Incident')
        plt.ylabel('Number of Incidents')
        plt.title('Histogram of Articles per Incident (Original)')

        # Filter incidents with only one article
        incidents_filtered = [incident for incident in incidents if incident.articles.count() > 1]

        # Create a list of the number of articles per incident for the filtered histogram
        article_counts_per_incident_filtered = [incident.articles.count() for incident in incidents_filtered]

        # Plot the filtered histogram
        plt.subplot(1, 2, 2)
        plt.hist(article_counts_per_incident_filtered, bins=range(min(article_counts_per_incident_filtered), max(article_counts_per_incident_filtered) + 1), edgecolor='black')
        plt.xlabel('Number of Articles per Incident')
        plt.ylabel('Number of Incidents')
        plt.title('Histogram of Articles per Incident (Excluding Incidents with One Article)')

        # Save and show the plot
        plt.savefig('tests/ko_test/data/auto/histograms_comparison.png')

        # Print additional statistics
        total_incidents = len(incidents)
        total_articles = sum(article_counts_per_incident)
        incidents_with_more_than_one_article = sum(count > 1 for count in article_counts_per_incident)
        incidents_with_more_than_two_articles = sum(count > 2 for count in article_counts_per_incident)
        incidents_with_more_than_three_articles = sum(count > 3 for count in article_counts_per_incident)

        percent_incidents_more_than_one_article = (incidents_with_more_than_one_article / total_incidents) * 100
        percent_incidents_one_or_less_articles = ((total_incidents - incidents_with_more_than_one_article) / total_incidents) * 100
        percent_incidents_more_than_two_articles = (incidents_with_more_than_two_articles / total_incidents) * 100
        percent_incidents_two_or_less_articles = ((total_incidents - incidents_with_more_than_two_articles) / total_incidents) * 100
        percent_incidents_more_than_three_articles = (incidents_with_more_than_three_articles / total_incidents) * 100
        percent_incidents_three_or_less_articles = ((total_incidents - incidents_with_more_than_three_articles) / total_incidents) * 100


        print(f"Total Incidents: {total_incidents}")
        print(f"Total Articles: {total_articles}")
        print(f"Incidents with more than 1 article: {incidents_with_more_than_one_article} ({percent_incidents_more_than_one_article:.2f}%)")
        print(f"Incidents with 1 or less articles: {total_incidents - incidents_with_more_than_one_article} ({percent_incidents_one_or_less_articles:.2f}%)")
        print(f"Incidents with more than 2 articles: {incidents_with_more_than_two_articles} ({percent_incidents_more_than_two_articles:.2f}%)")
        print(f"Incidents with 2 or less articles: {total_incidents - incidents_with_more_than_two_articles} ({percent_incidents_two_or_less_articles:.2f}%)")
        print(f"Incidents with more than 3 articles: {incidents_with_more_than_three_articles} ({percent_incidents_more_than_three_articles:.2f}%)")
        print(f"Incidents with 3 or less articles: {total_incidents - incidents_with_more_than_three_articles} ({percent_incidents_three_or_less_articles:.2f}%)")


        return

        article_word_counts_df = [[len(article.body.split(' ')), article] for article in Article.objects.filter(describes_failure=True)]
        article_word_counts_df.sort(key=lambda x: x[0])
        article_ko_word_counts_df = [[len(article_ko.body.split(' ')), article_ko] for article_ko in Article_Ko.objects.filter(describes_failure=True)]
        article_ko_word_counts_df.sort(key=lambda x: x[0])

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

