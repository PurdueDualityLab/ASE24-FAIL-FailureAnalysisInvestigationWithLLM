import argparse
import logging

from failures.articles.models import Article


class ScrapeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "--keyword",
            type=str,
            help="Keyword to search for",
        )
        parser.add_argument(
            "--start-year",
            type=int,
            help="Start year",
        )
        parser.add_argument(
            "--end-year",
            type=int,
            help="End year",
        )
        parser.add_argument(
            "--sources",
            type=str,
            nargs="+",
            help="Sources to search",
        )
        parser.add_argument(
            "--body",
            action="store_true",
            help="Scrape article body",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        if args.body:
            articles = Article.objects.filter(body="").all()
            for article in articles:
                article.scrape_body()
        else:
            Article.create_from_google_news_rss_feed(
                keyword=args.keyword,
                start_year=args.start_year,
                end_year=args.end_year,
                sources=args.sources,
            )
