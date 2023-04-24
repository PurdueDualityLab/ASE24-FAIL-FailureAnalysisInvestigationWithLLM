import argparse
import logging
import textwrap

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT, EmbedderGPT
from failures.parameters.models import Parameter

class MergeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Merge postmortems for articles that report on SE failures present in the database. 
            """
        )


    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        queryset = (
            Article.objects.filter(describes_failure=True, incident__isnull=True)
        )

        incidents = Incident.objects.prefetch_related('articles')

        postmortem_keys = ["summary"]
        embedder = EmbedderGPT()

        for article_new in queryset:

            article_new.create_postmortem_embeddings_GPT(embedder, postmortem_keys, False)

            similar_found = False
            
            for incident in incidents:
                for article_incident in incident.articles.all():
                    incident_similarity = article_new.cosine_similarity(article_incident)
                    if incident_similarity > 0.8:
                        similar_found = True

            
            if similar_found is False:
                





        logging.info("\nCreating postmortems.")
        
        chatGPT = ChatGPT()

        successful_failure_creations = 0
        for article in queryset:
            if article.body == "" or article.describes_failure is not True:
                logging.info("Article is empty or does not describe failure %s.", article)
                continue
            logging.info("Creating failure for article %s.", article)
            article.postmortem_from_article_ChatGPT(chatGPT, questions_chat, taxonomy_options, args.all)
            #Failure.postmortem_from_article_ChatGPT(chatGPT, article, questions_chat, taxonomy_options)
            logging.info("Succesfully created failure for article %s.", article)
            successful_failure_creations += 1

        logging.info("Successfully created failures for %d articles.", successful_failure_creations)
