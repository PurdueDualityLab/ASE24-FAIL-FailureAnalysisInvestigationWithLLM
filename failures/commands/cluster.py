import argparse
import logging
import textwrap

from failures.articles.models import Article
from failures.networks.models import EmbedderGPT, ChatGPT
from failures.parameters.models import Parameter
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

class ClusterCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Cluster postmortems for articles that report on SE failures present in the database. If no arguments are provided, 
            create embeddings for all articles that do not have a postmortem; otherwise, if --all is provided, create 
            embeddings for all articles. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Create embeddings for all articles even if they already have embeddings.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        queryset = (
            Article.objects.all() if args.all else Article.objects.filter(describes_failure=True)
        )

        postmortem_keys = ["summary","SEcauses","NSEcauses","impacts","mitigations"]

        logging.info("\nCreating embeddings for postmortem information.")

        embedder = EmbedderGPT()

        for article in queryset:
            logging.info("Creating embeddings for article %s.", article)

            article.create_postmortem_embeddings_GPT(embedder, postmortem_keys, args.all)


