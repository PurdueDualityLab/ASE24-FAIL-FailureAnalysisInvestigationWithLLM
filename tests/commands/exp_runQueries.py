import argparse
import logging
import textwrap
from typing import Optional

import feedparser
import pandas as pd
import datetime
import requests

import subprocess

from failures.articles.models import Article, SearchQuery

from failures.commands.scrape import ScrapeCommand
from failures.commands.classifyAnalyzable import ClassifyAnalyzableCommand
from failures.commands.classifyFailure import ClassifyFailureCommand
from failures.commands.merge import MergeCommand


class exp_RunQueriesCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        # add description
        parser.description = textwrap.dedent(
            """
            Collect and populate articles from Google News RSS feed for conducting experiments.
            """
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nExperiment: Collecting articles")

        scrape_parser = argparse.ArgumentParser()
        classifyFailure_parser = argparse.ArgumentParser()
        classifyAnalyzable_parser = argparse.ArgumentParser()
        merge_parser = argparse.ArgumentParser()

        Scrape_Command = ScrapeCommand()
        Scrape_Command.prepare_parser(scrape_parser)

        ClassifyFailure_Command = ClassifyFailureCommand()
        ClassifyFailure_Command.prepare_parser(classifyFailure_parser)
        classifyFailure_options = []
        classifyFailure_args = classifyFailure_parser.parse_args(classifyFailure_options)

        ClassifyAnalyzable_Command = ClassifyAnalyzableCommand()
        ClassifyAnalyzable_Command.prepare_parser(classifyAnalyzable_parser)
        classifyAnalyzable_options = []
        classifyAnalyzable_args = classifyAnalyzable_parser.parse_args(classifyAnalyzable_options)

        Merge_Command = MergeCommand()
        Merge_Command.prepare_parser(merge_parser)
        merge_options = []
        merge_args = merge_parser.parse_args(merge_options)


        # Define arrays of keywords and date ranges
        keywords = [
            "software fail",
            "software hack",
            "software bug",
            "software fault",
            "software error",
            "software exception",
            "software crash",
            "software glitch",
            "software defect",
            "software incident",
            "software flaw",
            "software mistake",
            "software anomaly",
            "software side effect"
        ]

        start_years = list(range(2022, 2023)) #after%3A2019-8-01%20before%3A2019-9-01 # Check 2017 to 2019 logs for all months
        end_years = list(range(2022, 2023))
        start_months = list(range(7, 13)) #1, 13)) 
        end_months = list(range(8, 14)) #2, 14)) 

        sources = [
            "wired.com", 
            "nytimes.com",
            "cnn.com", 
            "dailymail.co.uk",
            "theguardian.com",
            "bbc.com",
            "foxnews.com", #https://pressgazette.co.uk/media-audience-and-business-data/media_metrics/most-popular-websites-news-world-monthly-2/, https://pressgazette.co.uk/media-audience-and-business-data/media_metrics/most-popular-websites-news-world-monthly-2/
            "apnews.com",
            "washingtonpost.com",
            "cnet.com",
            "reuters.com", #Identification of sources of failures and their propagation in critical infrastructures from 12 years of public failure reports 
        ]

        # Iterate through all combinations of keywords, years, and months
        for start_year, end_year in zip(start_years, end_years):
            for start_month, end_month in zip(start_months, end_months):

                if end_month == 13: #For December 01 to January 01
                    start_month = 12
                    end_month = 1
                    end_year = end_year + 1
                    
                
                for keyword in keywords:
                    for source in sources:

                        scrape_options = ["--sources", source,
                            "--keyword", keyword,
                            "--start-year", str(start_year),
                            "--end-year", str(end_year),
                            "--start-month", str(start_month),
                            "--end-month", str(end_month),
                        ]

                        scrape_args = scrape_parser.parse_args(scrape_options)

                        Scrape_Command.run(scrape_args, scrape_parser)

                ClassifyFailure_Command.run(classifyFailure_args, classifyFailure_parser)
                ClassifyAnalyzable_Command.run(classifyAnalyzable_args, classifyAnalyzable_parser)
                Merge_Command.run(merge_args, merge_parser)

            


        # Disjoint from the rest of the infra
        '''
        df = pd.DataFrame(columns=["Headline", "Published", "Url", "Keyword", "Source", "SearchQuery ID"])

        # Iterate through all combinations of keywords, years, and months
        for start_year, end_year in zip(start_years, end_years):
            for start_month, end_month in zip(start_months, end_months):
                for source in sources:
                    for keyword in keywords:

                        search_query = SearchQuery.objects.create(
                        keyword=keyword,
                        start_year=start_year,
                        end_year=end_year,
                        start_month=start_month,
                        end_month=end_month,
                        sources=source,
                        )

                        rss_url = format_google_news_rss_url(keyword, start_year, end_year, start_month, end_month, source)
                        logging.info("RSS url: " + str(rss_url))
                        
                        feed = feedparser.parse(rss_url)
                        for entry in feed.entries:
                            if "opinion" in entry["title"].lower():
                                continue
                            headline=entry["title"],
                            source=entry["source"]["href"],
                            published=datetime.datetime.strptime(entry["published"], "%a, %d %b %Y %H:%M:%S %Z")
                            url = entry.link
                            
                            # Check if the link already exists in the DataFrame
                            existing_row = df[df["Url"] == url]

                            if not existing_row.empty:
                                # Update the existing row's "Keyword" column
                                df.loc[existing_row.index, "Keyword"] = df.loc[existing_row.index, "Keyword"] + ", " + keyword
                            else:
                                # Append data to the DataFrame
                                df = df.append({"Headline": headline, "Source": source, "Published": published, "Url": url, "Keyword": keyword, "Source": source, "SearchQuery ID": search_query.id}, ignore_index=True)

        # Save the DataFrame to a CSV file
        df.to_csv("all_articles.csv", index=False)

        # Load the DataFrame from CSV
        df = pd.read_csv("all_articles.csv")

        # Randomly select 300 articles
        random_selection = df.sample(n=300, random_state=1)  # Set random_state for reproducibility

        for index, row in random_selection.iterrows():

            dest_url = requests.get(row['Url']) 
            dest_url = dest_url.url

            if not Article.objects.filter(url=dest_url).exists():
                article = Article(
                    headline=row['Headline'],
                    published=row['Published'],
                    url=dest_url,
                    keyword=row['Keyword'],
                    # map other fields as needed
                )
            else: 
                article = Article.objects.get(url=dest_url)

            article.search_queries.add(SearchQuery.objects.get(id=row['SearchQuery ID'])) 

            article.save()
        
        '''


'''
def format_google_news_rss_url(
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        start_month: Optional[int] = None,
        end_month: Optional[int] = None,
        sources: Optional[list[str]] = None,
    ) -> str:
        keyword = keyword.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={keyword}"
        if start_year:
            url += f"%20after%3A{start_year}-{start_month}-01"
        if end_year:
            url += f"%20before%3A{end_year}-{end_month}-01" #TODO: Remove 15
        for i, source in enumerate(sources):
            if i > 0:
                url += "%20OR"
            url += f"%20site%3Ahttps%3A%2F%2F{source}"
        url += "&hl=en-US&gl=US&ceid=US%3Aen"

        return url
'''