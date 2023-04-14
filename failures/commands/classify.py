import argparse
import logging
import textwrap
import time

from failures.articles.models import Article
from failures.networks.models import ZeroShotClassifier
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

        failure_terms = ["failure"] #, "hack", "bug", "flaw", "fault", "error", "glitch", "mistake", "exception", "crash", "defect", "incident", "side effect", "anomaly"] #TODO: Create a global struct

        positive_classifications = 0
        for article in queryset:
            if article.body == "":
                continue
            
            classifier = ZeroShotClassifier()
            logging.info("Classifying %s.", article)

            for term in failure_terms:
                positive_term = "software " + term
                negative_term = "not software " + term
                
                if article.classify_as_failure(classifier, [positive_term,negative_term]):
                    positive_classifications += 1
                    logging.info("Classification met as " + positive_term + " for article: " + str(article))
                    break;
                
                time.sleep(3)


        logging.info("Successfully classified %d articles as describing a software failure.", positive_classifications)


    
        #TODO: Cleanup
        '''
        classifier = ZeroShotClassifier([Parameter.get("FAILURE_POSITIVE_CLASSIFICATION_CLASS", "software failure"),
                                         Parameter.get("FAILURE_NEGATIVE_CLASSIFICATION_CLASS", "not a software failure")]
                                        )
        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(describes_failure=None)
        )
        positive_classifications = 0
        negative_classifications = 0
        for article in queryset:
            logging.info("Classifying %s.", article)
            if article.body == "":
                continue
            if article.classify_as_failure(classifier):
                positive_classifications += 1
            else:
                negative_classifications += 1

        logging.info("Successfully classified %d articles as describing a software failure.", positive_classifications)
        logging.info("Successfully classified %d articles as not describing a software failure.", negative_classifications)
        '''
