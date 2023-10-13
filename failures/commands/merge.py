import argparse
import logging
import textwrap

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT, EmbedderGPT,  ClassifierChatGPT
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
            default=False,
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
            Article.objects.filter(describes_failure=True, analyzable_failure=True, incident__isnull=True)
        )

        questions = {
            "title":            Parameter.get("title", "Provide a 10 word title for the software failure incident (return just the title)."),
            "summary":          Parameter.get("summary", "Summarize the software failure incident. Include information about when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity(s), and the impacted entity(s). (answer in under 250 words)"),
        }

        questions_chat = questions
        

        incidents = list(Incident.objects.prefetch_related('articles'))


        #postmortem_keys = ["summary", "time", "system", "ResponsibleOrg", "ImpactedOrg"]
        #weights = [0.20, 0.20, 0.20, 0.20, 0.20]

        postmortem_keys = ["summary"]
        weights = [1]

        chatGPT = ChatGPT()
        embedder = EmbedderGPT()
        classifierChatGPT = ClassifierChatGPT()
        inputs = {"model": "gpt-3.5-turbo", "temperature": 0}

        logging.info("\n\nMerging Articles.")

        for article_new in queryset:

            logging.info("\nSearching for incident for article: %s.", article_new)

            article_new.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, args.all, "summary")

            article_new.create_postmortem_embeddings_GPT(embedder, postmortem_keys, False)

            similar_found = False
            
            for incident in incidents:
                logging.info("Searching within incident: %s.", incident)
                for article_incident in incident.articles.all():
                    
                    mean_score = 0
                    sum_scores = 0
                    for ind, postmortem_key in enumerate(postmortem_keys):
                        incident_similarity = article_new.cosine_similarity(article_incident, postmortem_key + "_embedding") 
                        sum_scores += incident_similarity * weights[ind]
                    
                    mean_score = sum_scores #/len(postmortem_keys)                    

                    if mean_score > 0.85:
                        logging.info("High similarity score of " + str(mean_score) + " in incident: " + str(incident))

                        #TODO: Measure false positive rate with just cosine similarity
                        #TODO: Implement asking LLM if incident is same


                        #Confirm with LLM
                        content = "You will classify whether two paragraphs descibe the same software failure incident (software failure could mean a software hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect)"

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

                        #similar_found = True
                        #article_new.incident = incident
                        #article_new.save()
                        #break
                
                if similar_found is True:
                    break

            if similar_found is False:
                article_new.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, {}, args.all, "title")

                logging.info("Incident match not found, creating new incident: %s.", article_new.title)

                incident = Incident.objects.create(title=article_new.title)

                article_new.incident = incident
                article_new.save()

                incidents.append(incident)