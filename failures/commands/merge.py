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
            Merge postmortems for articles that report on SE failures present in the database. If no arguments are provided, 
            only new articles will be merged into incidents; otherwise, if --all is provided, all articles will be remerged
            into new incidents. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Redo incident merging for all articles that describe SE failures.",
        )


    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        #Delete all incidents
        if args.all:
            incidents = Incident.objects.all()
            #Ensures that the articles are not deleted
            for incident in incidents:
                Article.objects.filter(incident=incident).update(incident=None)
            
            incidents.delete()

        queryset = (
            Article.objects.filter(describes_failure=True, incident__isnull=True)
        )

        #incidents = Incident.objects.prefetch_related('articles')

        incidents = list(Incident.objects.prefetch_related('articles'))


        postmortem_keys = ["summary"]
        embedder = EmbedderGPT()

        logging.info("\n\nMerging Articles.")

        for article_new in queryset:

            logging.info("\nSearching for incident for article: %s.", article_new)

            article_new.create_postmortem_embeddings_GPT(embedder, postmortem_keys, False)

            similar_found = False
            
            for incident in incidents:
                logging.info("Searching within incident: %s.", incident)
                for article_incident in incident.articles.all():
                    incident_similarity = article_new.cosine_similarity(article_incident)
                    
                    if "boeing" in article_new.headline.lower() and "boeing" in article_incident.headline.lower():
                        logging.info("Boeing article similarity: %s.", incident_similarity)
                    
                    if "volkswagen" in article_new.headline.lower() and "volkswagen" in article_incident.headline.lower():
                        logging.info("volkswagen article similarity: %s.", incident_similarity)

                    if "bear" in article_new.headline.lower() and "bear" in article_incident.headline.lower():
                        logging.info("russia bear article similarity: %s.", incident_similarity)


                    if incident_similarity > 0.9:
                        logging.info("Found incident match with a score of " + str(incident_similarity) + " in incident: " + str(incident))

                        similar_found = True
                        article_new.incident = incident
                        article_new.save()
                        break
                
                if similar_found is True:
                    break

            if similar_found is False:
                logging.info("Incident match not found, creating new incident: %s.", article_new)

                incident = Incident.objects.create()
                incident.title = article_new.title

                article_new.incident = incident
                article_new.save()

                incidents.append(incident)