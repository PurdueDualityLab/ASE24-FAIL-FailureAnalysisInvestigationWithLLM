import argparse
import logging
import textwrap

from failures.articles.models import Article, Incident
from failures.networks.models import EmbedderGPT, ChatGPT
from failures.parameters.models import Parameter

import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.metrics import silhouette_score

import matplotlib
import matplotlib.pyplot as plt


class ClusterCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Cluster postmortems for articles that report on SE failures present in the database. If no arguments are provided, 
            create embeddings for articles describing SE failures if they're not already created; otherwise, if --all is provided, create 
            embeddings for articles describing SE failures. 
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Create embeddings for all articles even if they already have embeddings.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        #TODO: args.all should not be used here but rather for individual postmortem key embeddings: similar to postmortem command
        incidents = Incident.objects.all()

        postmortem_keys = ["SEcauses"] #["summary","SEcauses","NSEcauses","impacts","mitigations"]

        logging.info("\nCreating embeddings for postmortem information.")

        embedder = EmbedderGPT()

        for incident in incidents:
            logging.info("Creating embeddings for incident %s.", incident)

            for postmortem_key in postmortem_keys:
                answer_set = True

                postmortem_embedding_key = postmortem_key + "_embedding"
                if not getattr(incident, postmortem_embedding_key):
                    answer_set = False
                
                if args.all or not answer_set: 

                    logging.info("Getting embedding for: " + postmortem_embedding_key)
                    
                    embeddings = embedder.run(getattr(incident, postmortem_key))

                    setattr(incident, postmortem_embedding_key, json.dumps(embeddings))
                
            incident.save()

        #df = pd.DataFrame(list(queryset.values('id', 'summary_embedding', 'SEcauses_embedding', 'NSEcauses_embedding','impacts_embedding','mitigations_embedding')))

        cluster(incidents, postmortem_keys)


def cluster(queryset, postmortem_keys):

    chatGPT = ChatGPT()
    inputs = {"model": "gpt-3.5-turbo", "temperature": 1}

    postmortem_embedding_keys = [key+"_embedding" for key in postmortem_keys]

    queryset_list = list(queryset.values('id', *postmortem_keys, *postmortem_embedding_keys))

    for item in queryset_list:
        for postmortem_embedding_key in postmortem_embedding_keys:
            item[postmortem_embedding_key] = json.loads(item[postmortem_embedding_key])

    
    df = pd.DataFrame(queryset_list)

    for postmortem_key in postmortem_keys:

        logging.info("Loading embedding data for " + postmortem_key)

        postmortem_embedding_key = postmortem_key + "_embedding"

        logging.info("Converting embedding data to np matrices")
        matrix = np.vstack(df[postmortem_embedding_key].values)
        logging.info("matrix shape: " + str(matrix.shape))

        optimal_k = find_optimal_k(matrix, 10)

        kmeans = KMeans(n_clusters=optimal_k, init="k-means++", random_state=42)

        kmeans.fit(matrix)

        labels = kmeans.labels_

        postmortem_cluster_key = postmortem_key + "_cluster"

        df[postmortem_cluster_key] = labels


        logging.info("Generating themes for " + postmortem_key)
        num_samples = 3

        themes = []
        for i in range(optimal_k):
            postmortem_descriptions = "\n".join(
                df[df[postmortem_cluster_key] == i][postmortem_key].sample(num_samples, random_state=42).values
            )

            messages = [
            {"role": "system", 
            "content": "You will identify similarities between software postmortem descriptions."}
            ]

            prompt = "What do the following software postmortem descriptions have in common? (Answer in under 10 words)" + postmortem_descriptions

            messages.append(
                            {"role": "user", "content": prompt},
                            )

            inputs["messages"] = messages
            reply = chatGPT.run(inputs)

            themes.append(reply)

            logging.info("Theme and Cluster " + str(i) + " : " + reply)

            sample_cluster_rows = df[df[postmortem_cluster_key] == i].sample(num_samples, random_state=42)
            for j in range(num_samples):
                logging.info("Article ID: " + str(sample_cluster_rows["id"].values[j]) + " ; " + postmortem_key + ": " + sample_cluster_rows[postmortem_key].values[j])

            print("-" * 100)

        #t-SNE dimensionality reduction
        tsne = TSNE(n_components=2, perplexity=15, random_state=42, init="random", learning_rate=200)
        vis_dims2 = tsne.fit_transform(matrix)

        x = [x for x, y in vis_dims2]
        y = [y for x, y in vis_dims2]

        # create a list of colors based on the number of clusters
        colors = plt.cm.tab20(np.linspace(0, 1, optimal_k))

        fig, ax = plt.subplots()

        for category, color in zip(range(optimal_k), colors):
            xs = np.array(x)[df[postmortem_cluster_key] == category]
            ys = np.array(y)[df[postmortem_cluster_key] == category]
            ax.scatter(xs, ys, color=color, alpha=0.3, label=themes[category])

            avg_x = xs.mean()
            avg_y = ys.mean()

            ax.scatter(avg_x, avg_y, marker="x", color=color, s=100)

        ax.legend(bbox_to_anchor =(0.5,-0.27), loc='lower center')

        filename = postmortem_key+"_clustered"+".png"
        fig.savefig(filename)


def find_optimal_k(data, max_k):
    optimal_k = 0
    optimal_score = -1
    
    for k in range(2, max_k+1):

        kmeans = KMeans(n_clusters=k, init="k-means++", random_state=42).fit(data)
        labels = kmeans.predict(data)
        score = silhouette_score(data, labels)

        logging.info("For " + str(k) + " clusters, silhouette_score: " + str(score))

        if score > optimal_score:
            optimal_score = score
            optimal_k = k
    
    logging.info("Optimal k: " + str(optimal_k)) 
    
    return optimal_k


