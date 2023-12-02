import argparse
import logging
import textwrap

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT, EmbedderGPT,  ClassifierChatGPT
from failures.parameters.models import Parameter

from failures.commands.PROMPTS import QUESTIONS, FAILURE_SYNONYMS

class MergeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the merge command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
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
            default=False,
            help="Redo incident merging for all articles that describe SE failures.",
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
            default=-1,
            help="Sets the temperature for ChatGPT",
        )


    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser, articles = None):
        """
        Run the incident merging process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        # Delete all incidents
        if args.all and not args.articles:
            incidents = Incident.objects.all()
            # Ensures that the articles are not deleted
            for incident in incidents:
                Article.objects.filter(incident=incident).update(incident=None)
            
            incidents.delete()

        if args.articles:
            logging.info("Merge: Setting incidents for testing set equal to null.")
            queryset = (
                # Article.objects.filter(describes_failure=True, analyzable_failure=True, incident__isnull=True, id__in=args.articles)
                Article.objects.filter(describes_failure=True, analyzable_failure=True, id__in=args.articles) # Removed incident__isnull=True
            )
            queryset.update(incident=None)
        else:
            queryset = (
                Article.objects.filter(describes_failure=True, analyzable_failure=True, incident__isnull=True)
            )

        #TODO: SORT BY PUBLISHED DATE FIRST!!!

        questions = {key: QUESTIONS[key] for key in ["title", "summary"]}

        questions_chat = questions
        
        incidents = list(Incident.objects.prefetch_related('articles'))

        #postmortem_keys = ["summary", "time", "system", "ResponsibleOrg", "ImpactedOrg"]
        #weights = [0.20, 0.20, 0.20, 0.20, 0.20]

        postmortem_keys = ["summary"]
        weights = [1]

        chatGPT = ChatGPT()
        embedder = EmbedderGPT()
        classifierChatGPT = ClassifierChatGPT()
        temp = args.temp if 0 <= args.temp <= 1 else 1
        inputs = {"model": "gpt-3.5-turbo", "temperature": temp}

        logging.info("\n\nMerging Articles.")

        for article_new in queryset:

            logging.info("\nSearching for incident for article: %s.", article_new)

            # Create embeddings for the new article's postmortem information
            article_new.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, args.all, "summary")

            article_new.create_postmortem_embeddings_GPT(embedder, postmortem_keys, False)

            similar_found = False #TODO: what happens when = None (ex: due to api error), it could cause article not to merge and create new incident, in this case it should skip the article, initialize with none?
            
            for incident in incidents:
                logging.info("Searching within incident: %s.", incident)
                for article_incident in incident.articles.all():
                    
                    mean_score = 0
                    sum_scores = 0
                    for ind, postmortem_key in enumerate(postmortem_keys):
                        # Calculate similarity between articles based on embeddings
                        incident_similarity = article_new.cosine_similarity(article_incident, postmortem_key + "_embedding") 
                        sum_scores += incident_similarity * weights[ind]
                    
                    mean_score = sum_scores #/len(postmortem_keys)                    

                    if mean_score > 0.85:
                        logging.info("High similarity score of " + str(mean_score) + " in incident: " + str(incident))

                        #TODO: Measure false positive rate with just cosine similarity


                        #Confirm with LLM
                        content = "You will classify whether two paragraphs descibe the same software failure incident (software failure could mean a " + FAILURE_SYNONYMS + ")"

                        messages = [
                                {"role": "system", 
                                "content": content}
                                ]

                        prompt = "Does the provided paragraph 1 and paragraph 2 describe the same software failure incident(s)?\n" \
                                + "\nParagraph 1: " + article_new.summary \
                                + "\nParagraph 2: " + article_incident.summary \
                                + "\nAnswer with just True or False."

                        messages.append(
                                        {"role": "user", "content": prompt },
                                        )
                        
                        inputs["messages"] = messages
                        similar_found = classifierChatGPT.run(inputs)

                        if similar_found is True:
                            logging.info("Found incident match with a score of " + str(mean_score) + " in incident: " + str(incident))
                            article_new.incident = incident
                            article_new.save()

                            break

                        elif similar_found is None:
                            logging.info("Similar found is None, skipping article for now.")
                            break


                        #similar_found = True
                        #article_new.incident = incident
                        #article_new.save()
                        #break
                
                if similar_found is True or similar_found is None:
                    break

            if similar_found is False:
                article_new.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, args.all, "title")

                logging.info("Incident match not found, creating new incident: %s.", article_new.title)

                incident = Incident.objects.create(title=article_new.title)

                article_new.incident = incident
                article_new.save()

                incidents.append(incident)

        logging.info("Articles merged!")