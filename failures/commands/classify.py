import argparse
import logging
import textwrap
import time

from failures.articles.models import Article
from failures.networks.models import ZeroShotClassifier, ClassifierChatGPT
from failures.parameters.models import Parameter


class ClassifyCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the classify command

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure
        """

        parser.description = textwrap.dedent(
            """
            Classify the articles present in the database as either describing a software failure or not. If no arguments are
            provided, classify all articles that do not have a classification; otherwise, if --all is provided, classify
            all articles. If an article does not have a body, it will not be classified. --sample is used for testing.
            --temp sets the ChatGPT temperature
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Classify all articles even if they already have a classification.",
        )
        parser.add_argument(
            "--sample",
            type=int,
            help="Dictates the number of samples",
        )
        parser.add_argument(
            "--articles",
            nargs="+",  # Accepts one or more values
            type=int,    # Converts the values to integers
            help="A list of integers.",
        )
        parser.add_argument(
            "--temp",
            type=float,
            default=1,
            help="Sets the temperature for ChatGPT",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Run the article classification process based on provided arguments.

        Args: 
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser for the configuration
        """
        
        # Gets list of article to classify
        queryset = (
            Article.objects.filter(scrape_successful=True, id__in=args.articles) if args.articles else
            Article.objects.filter(scrape_successful=True) if args.all else
            Article.objects.filter(describes_failure=None, scrape_successful=True)
        )
        logging.info("\nClassifying articles.")
        
        # Initializes ChatGPT Classifier
        classifierChatGPT = ClassifierChatGPT()

        # Handles inputs and temperature
        temperature = args.temp if 0 <= args.temp <= 1 else 1
        inputs = {"model": "gpt-3.5-turbo", "temperature": temperature}
        logging.info("Classifying articles using temperature %s.", "{:.2f}".format(temperature))
        
        failure_positive_classifications_ChatGPT = 0
        analyzable_positive_classifications_ChatGPT = 0

        for article in queryset:
            #if article.body == "": #or article.scrape_successful is False:
            #    continue
            
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



