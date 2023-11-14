import argparse
import logging
import textwrap
from bs4 import BeautifulSoup
import requests
import time

class RisksDigestScraper:
    BASE_URL = "http://catless.ncl.ac.uk/Risks"

    VOLUME_YEAR_MAPPING = {
        1: (1985, 1986),
        2: (1986, 1986),
        3: (1986, 1986),
        4: (1986, 1987),
        5: (1987, 1987),
        6: (1987, 1988),
        7: (1988, 1988),
        8: (1989, 1989),
        9: (1989, 1990),
        10: (1990, 1991),
        11: (1991, 1991),
        12: (1991, 1991),
        13: (1992, 1992),
        14: (1992, 1993),
        15: (1993, 1994),
        16: (1994, 1995),
        17: (1995, 1996),
        18: (1996, 1997),
        19: (1997, 1998),
        20: (1998, 2000),
        21: (2000, 2002),
        22: (2002, 2003),
        23: (2003, 2005),
        24: (2005, 2007),
        25: (2008, 2010),
        26: (2010, 2012),
        27: (2012, 2014),
        28: (2014, 2015),
        29: (2015, 2016),
        30: (2016, 2018),
        31: (2019, 2020),
        32: (2020, 2021),
        33: (2022, 2023)
    }

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the Risks Digest scraper.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Scrape articles from RISKS Digest within a specific range of years.
            """
        )
        parser.add_argument(
            "start_year",
            type=int,
            help="Start year for scraping RISKS Digest articles.",
        )
        parser.add_argument(
            "end_year",
            type=int,
            help="End year for scraping RISKS Digest articles.",
        )

    def scrape_articles(self, args: argparse.Namespace):
        valid_articles = self.get_valid_articles(args.start_year, args.end_year)
        for article_link in valid_articles:
            print(article_link)

    def get_valid_articles(self, start_year, end_year):
        """
        Get valid article links from RISKS Digest within the specified range of years.

        Args:
            start_year (int): Start year for scraping RISKS Digest articles.
            end_year (int): End year for scraping RISKS Digest articles.

        Returns:
            list: List of valid article URLs.
        """
        article_links = []

        # Iterate through the volume-year mapping
        for volume, (volume_start_year, volume_end_year) in self.VOLUME_YEAR_MAPPING.items():
            # Check if the volume overlaps with the specified year range
            if volume_start_year <= end_year and volume_end_year >= start_year:
                # Iterate through the issues of the volume (assuming maximum 99 issues per volume)
                for issue in range(1, 100):
                    # Construct the article URL
                    article_url = f"{self.BASE_URL}/{volume:02}/{issue:02}"
                    # Send a request to the article URL with a timeout of 5 seconds
                    response = requests.get(article_url, timeout=5)

                    # Check if the response is successful (status code 200)
                    if response.status_code == 200:
                        # Parse the HTML content of the page
                        soup = BeautifulSoup(response.content, "html.parser")

                        # Add logic to validate articles based on the structure of the page
                        # Example validation: Check for specific elements or keywords indicating valid articles
                        if soup.find("div", class_="article-content"):
                            # If the article is valid, add its URL to the list of valid article links
                            article_links.append(article_url)
                    elif response.status_code == 401:
                        # Pause for 60 seconds because we have been querying too fast
                        time.sleep(60)
                    else:
                        # Log the error if the response is not successful
                        logging.error(
                            f"Error while requesting {article_url}: {response.status_code}"
                        )

        # Return the list of valid article URLs
        return article_links


    def run(self, args: argparse.Namespace):
        return self.scrape_articles(args)

# Example usage in a different module:
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="RISKS Digest Scraper")
#     scraper = RisksDigestScraper()
#     scraper.prepare_parser(parser)
#     args = parser.parse_args()
#     scraper.run(args)
