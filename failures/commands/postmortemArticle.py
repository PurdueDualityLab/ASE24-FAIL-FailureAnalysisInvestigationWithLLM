import argparse
import logging
import textwrap

from failures.articles.models import Article, Incident
from failures.networks.models import QuestionAnswerer, ChatGPT
from failures.parameters.models import Parameter

class PostmortemArticleCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the postmortem command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        parser.description = textwrap.dedent(
            """
            Create postmortems for articles that report on SE failures present in the database. If no arguments are provided, create postmortems for all
            SE failure articles that do not have a postmortem; otherwise, if --all is provided, create postmortems for all
            SE failure articles. If an article does not have a body, a postmortems will not be created for it.
            """
        )
        parser.add_argument(
            "--all",
            action="store_true",
            default=False,
            help="Create postmortems for all articles even if they already have a postmortem.",
        )
        parser.add_argument(
            "--key",
            type=str,
            default='None',
            help="Redo extraction for a specific postmortem key for all articles.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser, articles = None):
        """
        Run the postmortem creation process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        # Define a queryset of articles for postmortem creation
        queryset = (
            Article.objects.filter(
                describes_failure=True,
                #headline__icontains='Boeing'
            )
        )

        #Pre-process prompts:
        questions = {
        "title":            Parameter.get("title", "Provide a 10 word title for the software failure incident (return just the title)."),
        "summary":          Parameter.get("summary", "Summarize the software failure incident. Include when the failure occured, what system failed, the cause of failure, the impact of failure, the responsible entity, and the impacted entity. (answer in under 250 words)"),
        
        "time":             Parameter.get("time", "When (month and/or year) did the software failure incident happen? If necessary, calculate using article published date. ONLY return month and/or year."),
        "system":           Parameter.get("system", "What system failed in the software failure incident? (answer in under 10 words)"),
        "ResponsibleOrg":   Parameter.get("ResponsibleOrg", "Which entity(s) was responsible for causing the software failure? (answer in under 10 words)"),
        "ImpactedOrg":      Parameter.get("ImpactedOrg", "Which entity(s) was impacted by the software failure? (answer in under 10 words)"),
        }
        '''
        "SEcauses":     Parameter.get("SEcauses", "What were the software causes of the failure incident? (answer in under 100 words)"),
        "NSEcauses":    Parameter.get("NSEcauses", "What were the non-software causes of the failure incident? (answer in under 100 words)"),
        "impacts":      Parameter.get("impacts", "What happened due to the software failure incident? (answer in under 100 words)"),
        "mitigations":  Parameter.get("mitigations", "What could have prevented the software failure incident? (answer in under 100 words)"), 
        
        "phase":        Parameter.get("phase", "Was the software failure due to 'system design' (option 0) or 'operation' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "boundary":     Parameter.get("boundary", "Was the software failure due to faults from 'within the system' (option 0) or from 'outside the system' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "nature":       Parameter.get("nature", "Was the software failure due to 'human actions' (option 0) or 'non human actions' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "dimension":    Parameter.get("dimension", "Was the software failure due to 'hardware' (option 0) or 'software' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "objective":    Parameter.get("objective", "Was the software failure due to 'malicious' (option 0) or 'non-malicious' (option 1) faults or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "intent":       Parameter.get("intent", "Was the software failure due to 'deliberate' (option 0) or 'accidental' (option 1) fault or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "capability":   Parameter.get("capability", "Was the software failure 'accidental' (option 0) or due to 'development incompetence' (option 1) or 'both' (option 2) or 'neither' (option 3) or 'unknown' (option -1)?"),
        "duration":     Parameter.get("duration", "Was the software failure 'permanent' (option 0) or 'temporary' (option 1) or 'intermittent' (option 2) or 'unknown' (option -1)?"),
        "domain":       Parameter.get("domain", "What application domain is the system: 'automotive' (option 0) or 'critical infrastructure' (option 1) or 'healthcare' (option 2) or 'energy' (option 3) or 'transportation' (option 4) or 'infrastructure' (option 5) or 'aerospace' (option 6) or 'telecommunications' (option 7) or 'consumer device' (option 8) or 'unknown' (option -1)?"),
        "cps":          Parameter.get("cps", "Does the system contain software that controls physical components (cyber physical system) or is it an IoT system: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?"),
        "perception":   Parameter.get("perception", "Was the software failure due to 'sensors' (option 0) or 'actuators' (option 1) or 'processing unit' (option 2) or 'network communication' (option 3) or 'embedded software' (option 4) or 'unknown' (option -1)?"),
        "communication":Parameter.get("communication", "Was there a software failure at the communication level? If false, (option false). If true, then was the failure at the 'link level' (option 1) or 'connectivity level' (option 2) or 'unknown' (option -1)?"),
        "application":  Parameter.get("application", "Was there a software failure at the application level: 'true' (option true) or 'false' (option false) or 'unknown' (option -1)?"),
        "behaviour":    Parameter.get("behaviour", "Was the software failure due to a 'crash' (option 0) or 'omission' (option 1) or 'timing' (option 2) or 'value' (option 3) or 'Byzantine' fault (option 4) or 'unknown' (option -1)?")
        }
        '''

        #if args.key != 'None':
        #    questions = questions[args.key]

        

        # Create a mapping of questions to ChatGPT prompts
        questions_chat = {}
        for question_key in questions.keys():
            if "option" in questions[question_key]:
                questions_chat[question_key] = questions[question_key] + "\nRETURN ANSWER IN JSON FORMAT: {\"explanation\": \"explanation\", \"option\": \"option number\"}. Don't provide anything outside the format."
            #elif "word" or "words" in questions[question_key]:
            #    questions_chat[question_key] = questions[question_key]

        taxonomy_options = {
            "phase": {"0": "system design", "1": "operation", "2": "both", "3": "neither", "-1": "unknown"},
            "boundary": {"0": "within the system", "1": "outside the system", "2": "both", "3": "neither", "-1": "unknown"},
            "nature": {"0": "human actions", "1": "non human actions", "2": "both", "3": "neither", "-1": "unknown"},
            "dimension": {"0": "hardware", "1": "software", "2": "both", "3": "neither", "-1": "unknown"},
            "objective": {"0": "malicious", "1": "non-malicious", "2": "both", "3": "neither", "-1": "unknown"},
            "intent": {"0": "deliberate", "1": "accidental", "2": "both", "3": "neither", "-1": "unknown"},
            "capability": {"0": "accidental", "1": "development incompetence", "2": "both", "3": "neither", "-1": "unknown"},
            "duration": {"0": "permanent", "1": "temporary", "2": "intermittent", "3": "unknown"},
            "domain": {"0": "automotive", "1": "critical infrastructure", "2": "healthcare", "3": "energy", "4": "transportation", "5": "infrastructure", "6": "aerospace", "7": "telecommunications", "8": "consumer device", "-1": "unknown"},
            "cps": {"true": "true", "false": "false", "-1": "unknown"},
            "perception": {"0": "sensors", "1": "actuators", "2": "processing unit", "3": "network communication", "4": "embedded software", "-1": "unknown"},
            "communication": {"false": "False", "1": "link level", "2": "connectivity level", "-1": "unknown"},
            "application": {"true": "true", "false": "false", "-1": "unknown"},
            "behaviour": {"0": "crash", "1": "omission", "2": "timing", "3": "value", "4": "byzantine fault", "-1": "unknown"}
        }

        logging.info("\nCreating postmortems.")
        
        # Initialize ChatGPT model
        chatGPT = ChatGPT()
        inputs = {"model": "gpt-3.5-turbo", "temperature": 1}

        successful_failure_creations = 0
        for article in queryset:
            if article.body == "" or article.describes_failure is not True:
                logging.info("Article is empty or does not describe failure %s.", article)
                continue
            logging.info("Creating postmortem for article %s.", article)
            article.postmortem_from_article_ChatGPT(chatGPT, inputs, questions_chat, taxonomy_options, args.all, args.key)
            logging.info("Succesfully created postmortem for article %s.", article)
            successful_failure_creations += 1

        logging.info("Successfully created postmortems for %d articles.", successful_failure_creations)