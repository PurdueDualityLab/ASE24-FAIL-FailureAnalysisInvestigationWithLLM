import argparse
import logging
import textwrap

from failures.articles.models import Article
from failures.networks.models import Summarizer, ChatGPT


class SummarizeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Summarize articles present in the database. If no arguments are provided, summarize all
            articles that do not have a summary; otherwise, if --all is provided, summarize all
            articles. If an article does not have a body, it will not be summarized.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Summarize all articles even if they already have a summary.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        '''
        summarizer = Summarizer()
        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(article_summary="")
        )
        successful_summaries = 0
        for article in queryset:
            logging.info("Summarizing %s.", article)
            if article.body == "":
                continue
            if article.summarize_body(summarizer):
                successful_summaries += 1

        logging.info("Successfully summarized %d articles.", successful_summaries)
        '''

        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(article_summary="")
        )


        chatGPT = ChatGPT()
        inputs = {"model": "gpt-3.5-turbo", "temperature": 1}


        successful_summaries = 0
        for article in queryset:
            if article.body == "":
                continue

            logging.info("Summarizing %s.", article)
            article_text = article.body.split()[:2750]

            content = "You will summarize the article: \n" + ' '.join(article_text)

            messages = [
                    {"role": "system", 
                    "content": content}
                    ]
            
            prompt = "In under a 100 words, summarize the article (if present in the article, retain information relevant to software failures - software failure could mean a software hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect).\nBut don't explicitly state software failure." 
            
            messages.append(
                        {"role": "user", "content": prompt },
                        )
            
            inputs["messages"] = messages

            reply = chatGPT.run(inputs)

            if reply is not None:
                article.article_summary = reply
                article.save()

                successful_summaries += 1

        logging.info("Successfully summarized %d articles.", successful_summaries)