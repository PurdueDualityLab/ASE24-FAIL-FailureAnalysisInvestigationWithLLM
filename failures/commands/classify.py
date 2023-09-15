import argparse
import logging
import textwrap
import time

from failures.articles.models import Article
from failures.networks.models import ZeroShotClassifier, ClassifierChatGPT
from failures.parameters.models import Parameter


class ClassifyCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Classify the articles present in the database as either describing a software failure or not. If no arguments are
            provided, classify all articles that do not have a classification; otherwise, if --all is provided, classify
            all articles. If an article does not have a body, it will not be classified.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Classify all articles even if they already have a classification.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        
        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(describes_failure=None)
        )

        logging.info("\nClassifying articles.")
        
        classifierChatGPT = ClassifierChatGPT()
        inputs = {"model": "gpt-3.5-turbo", "temperature": 1}
        


        failure_positive_classifications_ChatGPT = 0
        analyzable_positive_classifications_ChatGPT = 0

        for article in queryset:
            if article.body == "":
                continue
            
            logging.info("Classifying %s.", article)


            if article.classify_as_failure_ChatGPT(classifierChatGPT, inputs):
                failure_positive_classifications_ChatGPT += 1
                logging.info("ChatGPT Classifier: Classification met as software failure for article: " + str(article))


                #Does the article have enough information to conduct failure analysis

                if article.classify_as_analyzable_ChatGPT(classifierChatGPT, inputs):
                    analyzable_positive_classifications_ChatGPT += 1
                    logging.info("ChatGPT Classifier: Classification met as eligible for failure analysis for article: " + str(article))



        logging.info("ChatGPT successfully classified %d articles as describing a software failure.", failure_positive_classifications_ChatGPT)
        logging.info("ChatGPT successfully classified %d articles as eligible for failure analysis.", analyzable_positive_classifications_ChatGPT)



