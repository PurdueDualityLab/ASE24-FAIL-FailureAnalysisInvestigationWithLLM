import argparse
import logging
import textwrap

from failures.articles.models import Article, Failure
from failures.networks.models import QuestionAnswerer, ChatGPT
from failures.parameters.models import Parameter

class MergeCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Create embeddings for articles present in the database. If no arguments are provided, create embeddings for all
            articles that do not have an embedding; otherwise, if --all is provided, create embeddings for all
            articles. If an article does not have a body, an embedding will not be created for it.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Create embeddings for all articles even if they already have an embedding.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        #Pre-process prompts:
        questions = {
        "title":        Parameter.get("title", "Provide a 10 word title for this incident (return just the title)."),
        "summary":      Parameter.get("summary", "Summarize the failure incident."),
        "system":       Parameter.get("system", "What failed in the incident?"),
        "time":         Parameter.get("time", "When did the incident happen?"),
        "SEcauses":     Parameter.get("se-causes", "What were the software causes of the incident?"),
        "NSEcauses":    Parameter.get("nse-causes", "What were the non-software causes of the incident?"),
        "impacts":      Parameter.get("impacts", "What happened due to the incident?"),
        "mitigations":  Parameter.get("mitigations", "What could have prevented the incident?"),
        "phase":        Parameter.get("phase", "Was the failure due to 'system design' (option 0) or 'operation' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "boundary":     Parameter.get("boundary", "Was the failure due to faults from 'within the system' (option 0) or from 'outside the system' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "nature":       Parameter.get("nature", "Was the failure due to 'human actions' (option 0) or 'non human actions' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "dimension":    Parameter.get("dimension", "Was the failure due to 'hardware' (option 0) or 'software' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "objective":    Parameter.get("objective", "Was the failure due to 'malicious' (option 0) or 'non-malicious' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "intent":       Parameter.get("intent", "Was the failure due to 'deliberate' (option 0) or 'accidental' (option 1) fault or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "capability":   Parameter.get("capability", "Was the failure 'accidental' (option 0) or due to 'development incompetence' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "duration":     Parameter.get("duration", "Was the failure 'permanent' (option 0) or 'temporary' (option 1) or 'intermittent' (option 2) or 'unknown' (option -1)?"),
        "domain":       Parameter.get("domain", "What application domain is the system: 'automotive' (option 0) or 'critical infrastructure' (option 1) or 'healthcare' (option 2) or 'energy' (option 3) or 'transportation' (option 4) or 'infrastructure' (option 5) or 'aerospace' (option 6) or 'telecommunications' (option 7) or 'unknown' (option -1)?"),
        "cps":          Parameter.get("cps", "Does the system contain software that controls physical components (cyber physical system) or is it an IoT system: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?"),
        "perception":   Parameter.get("perception", "Was the failure due to 'sensors' (option 0) or 'actuators' (option 1) or 'processing unit' (option 2) or 'network communication' (option 3) or 'embedded software' (option 4) or 'unknown' (option -1)?"),
        "communication":Parameter.get("communication", "Was there a failure at the communication level? If False, (option false). If True, then was the failure at the 'link level' (option 1) or 'connectivity level' (option 2) or 'unknown' (option -1)?"),
        "application":  Parameter.get("application", "Was there a failure at the application level: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?"),
        "behaviour":    Parameter.get("behaviour", "Was the failure due to a 'crash' (option 0) or 'omission' (option 1) or 'timing' (option 2) or 'value' (option 3) or 'Byzantine' fault (option 4) or 'unknown' (option -1)?")
        }

        questions_chat = {}
        for question_key in questions.keys():
            if "option" in questions[question_key]:
                questions_chat[question_key] = "Answer the question using the article: " + questions[question_key] + " \n MUST ONLY RETURN ANSWER IN JSON FORMAT: {\"explanation\": \"explanation\", \"option\": \"option number\"}. Don't provide anything outside the format."
            else:
                questions_chat[question_key] = "Answer the question using the article: " + questions[question_key]


        logging.info("Creating failures.")
        Chat_GPT = ChatGPT()
        queryset = Article.objects.all()
        successful_failure_creations = 0
        for article in queryset:
            if article.body == "" or article.describes_failure is not True:
                logging.info("Article is empty or does not describe failure %s.", article)
                continue
            logging.info("Creating failure for article %s.", article)
            Failure.postmortem_from_article_ChatGPT(article, questions_chat, Chat_GPT)
            logging.info("Succesfully created failure for article %s.", article)
            successful_failure_creations += 1

        logging.info("Successfully created failures for %d articles.", successful_failure_creations)
