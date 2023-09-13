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

        questions = {
        "summary":          Parameter.get("summary", "Summarize the software failure incident in under 100 words. Include information about the failed system, when the failure occured, the entity(s) responsible for failure, and the entity(s) impacted by failure."),
        }

        failure_synonyms = "\nRemember, software failure could mean a software hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect"

        questions_chat = {}
        for question_key in questions.keys():
            if "option" in questions[question_key]:
                questions_chat[question_key] = failure_synonyms + "\nAnswer the question using the article: " + questions[question_key] + " \n MUST ONLY RETURN ANSWER IN JSON FORMAT: {\"explanation\": \"explanation\", \"option\": \"option number\"}. Don't provide anything outside the format."
            elif "word" or "words" in questions[question_key]:
                questions_chat[question_key] = failure_synonyms + "\nAnswer the question using the article: " + questions[question_key]
            elif "summary" in question_key:
                questions_chat[question_key] = failure_synonyms + "\n" + questions[question_key]
            else:
                questions_chat[question_key] = failure_synonyms + "\nAnswer the question within 100 words using the article: " + questions[question_key]

        incidents = list(Incident.objects.prefetch_related('articles'))


        #postmortem_keys = ["summary", "time", "system", "ResponsibleOrg", "ImpactedOrg"]
        #weights = [0.20, 0.20, 0.20, 0.20, 0.20]

        postmortem_keys = ["summary"]
        weights = [1]

        embedder = EmbedderGPT()
        classifierChatGPT = ClassifierChatGPT()

        logging.info("\n\nMerging Articles.")

        for article_new in queryset:

            logging.info("\nSearching for incident for article: %s.", article_new)

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
                    
                    ''' TODO: Clean up
                    if "boeing" in article_new.headline.lower() and "boeing" in article_incident.headline.lower():
                        logging.info("Boeing article similarity: %s.", mean_score)
                    
                    if "volkswagen" in article_new.headline.lower() and "volkswagen" in article_incident.headline.lower():
                        logging.info("volkswagen article similarity: %s.", mean_score)

                    if "bear" in article_new.headline.lower() and "bear" in article_incident.headline.lower():
                        logging.info("russia bear article similarity: %s.", mean_score)
                    '''
                    

                    if mean_score > 0.85:
                        logging.info("High similarity score of " + str(mean_score) + " in incident: " + str(incident))

                        #TODO: Measure false positive rate with just cosine similarity
                        #TODO: Implement asking LLM if incident is same


                        #Confirm with LLM
                        content = "You will help decide whether two paragraphs descibe the same software failure incident (software failure could mean a software hack, bug, fault, error, exception, crash, glitch, defect, incident, flaw, mistake, anomaly, or side effect)"

                        messages = [
                                {"role": "system", 
                                "content": content}
                                ]

                        prompt = "Does this paragraph: \n" \
                                + article_new.summary \
                                + " \n describe the same software failure incident(s) as this paragraph: \n" \
                                + article_incident.summary \
                                + "\n ?" \
                                + "\n Answer with just True or False"

                        messages.append(
                                        {"role": "user", "content": prompt },
                                        )

                        similar_found = classifierChatGPT.run(messages)

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
                logging.info("Incident match not found, creating new incident: %s.", article_new.title)

                incident = Incident.objects.create(title=article_new.title)

                article_new.incident = incident
                article_new.save()

                incidents.append(incident)