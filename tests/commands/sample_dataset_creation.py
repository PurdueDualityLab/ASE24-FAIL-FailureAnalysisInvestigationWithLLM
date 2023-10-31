import argparse
import logging
import textwrap
import pandas as pd
import csv
import random

from failures.articles.models import Article, SearchQuery, Incident
from datetime import datetime
from django.utils import timezone


class SampleDatasetCreationCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the generate article ids command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """
        # add description
        parser.description = textwrap.dedent(
            """
            Generates a random list of articles to use for testing. 
            The command will generate a list of article IDs then store the articles and respective incidents in 
            experiment_data_auto_incidents.csv, and experiment_data_auto_articles.csv. The command will also find articles that 
            describe software failures and are analyzeable and those that are not. 


            """
        )
        parser.add_argument(
            "--seed",
            type=int,  # Converts the values to integers
            help="The seed for randomly generating article IDs.",
        )
        parser.add_argument(
            "--countIncidents",
            type=int,  # Converts the values to integers
            help="Determines the number of article IDs to generate",
        )
        parser.add_argument(
            "--countANF",
            type=int,    # Converts the values to integers
            help="Determines the number IDs for articles classified as not reporting on software failure.",
        )
        parser.add_argument(
            "--countANA",
            type=int,    # Converts the values to integers
            help="Determines the number IDs for articles classified as reporting on software failure, but not analyzable.",
        )
        parser.add_argument(
            "--startYear",
            type=int,    # Converts the values to integers
            help="Start year for articles selected.",
        )
        parser.add_argument(
            "--endYear",
            type=int,    # Converts the values to integers
            help="End year for articles selected (Inclusive).",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        """
        Generates random list of article IDs given parameters and stores to to CSV files. 

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.

        """
        # Update publish dates
        self.__update_incident_publish_dates()
        logging.info("SampleDatasetCreationCommand: Incident published dates have been updated")

        # Set random seed
        if args.seed:
            random.seed(args.seed)

        # Define values for start and end years 
        start_year = args.startYear if args.startYear else 0
        end_year = args.endYear if args.endYear else datetime.now().year

        # Get DateTime for years
        start_date = timezone.make_aware(datetime(start_year, 1, 1))
        end_date = timezone.make_aware(datetime(end_year, 12, 31, 23, 59, 59))

        # Get incident ids
        incidents, incident_ids = self.__get_incident_ids(start_date, end_date, args)
        if incident_ids:
            logging.info("SampleDatasetCreationCommand: Incidents collected (seed = " + str(args.seed) + ")")
        else:
            logging.info("SampleDatasetCreationCommand: No incidents collected")

        # Get related articles
        incident_related_articles = Article.objects.filter(incident__id__in=incident_ids)
        incident_related_article_ids = list(incident_related_articles.values_list('id', flat=True))

        ## DELETE, THIS IS JUST FOR TESTING UNTIL DATABASE IS POPULATED ##
        # incident_related_article_ids = random.sample([x for x in range(10000)], 60)
        # incident_related_articles = Article.objects.filter(id__in=incident_related_article_ids)
        ## END DELETE ##

        # Download incidents to experiment_data_auto_incidents.csv
        auto_incidents_csv = "./tests/auto_evaluation/experiment_data_auto_incidents.csv"
        self.__download_incidents_to_csv(incidents, auto_incidents_csv)
        logging.info("SampleDatasetCreationCommand: Wrote " + str(len(incidents)) + " incidents to experiment_data_auto_incidents.csv")

        # Download articles to experiment_data_auto_articles.csv
        auto_articles_csv = "./tests/auto_evaluation/experiment_data_auto_articles.csv"
        self.__download_articles_to_csv(incident_related_articles, auto_articles_csv)
        logging.info("SampleDatasetCreationCommand: Wrote " + str(len(incident_related_articles)) + " incidents to experiment_data_auto_articles.csv")

        # Get random list of articles classified as non-failure reporting
        if not args.countANF:
            args.countANF = 20
        nf_articles = self.__get_articles_nf(start_date, end_date, args)

        # Get random list of articles classified as failure reporting but non analyzable
        if not args.countANA:
            args.countANA = 20
        na_articles = self.__get_articles_na(start_date, end_date, args)

        # Get aggregate articles
        combined_article_ids = set(incident_related_article_ids) | set(nf_articles) | set(na_articles)
        manual_articles = Article.objects.filter(id__in=combined_article_ids)

        # Download manual dataset to experiment_data_manual_articles.csv
        manual_articles_csv = "./tests/manual_evaluation/experiment_data_manual_articles.csv"
        self.__download_articles_to_csv(manual_articles, manual_articles_csv)
        logging.info("SampleDatasetCreationCommand: Wrote " + str(len(manual_articles)) + " incidents to experiment_data_manual_articles.csv")
        
        return 0

    def __update_incident_publish_dates(self):
        """
        Updates all incidents with published date of earliest article. 

        Args:
            None

        Returns:
            None
        """
        # Get all incidents with published date set as None
        incidents_with_none_date = Incident.objects.filter(published__isnull=True)

        for incident in incidents_with_none_date:
            # Get the associated articles for the incident
            articles_for_incident = Article.objects.filter(incident=incident)

            if articles_for_incident.exists():
                # Find the earliest published article among the associated articles
                earliest_article = articles_for_incident.order_by('published').first()

                # Set the published date of the incident to the earliest article's published date
                incident.published = earliest_article.published
                incident.save()

    def __get_incident_ids(self, start_date: datetime, end_date: datetime, args: argparse.Namespace):
        """
        Generates random list of incidents and their IDs given parameters . 

        Args:
            start_date (datetime): Start date for collecting incidents
            end_date (datetime): End date for collecting incidents
            args (argparse.Namespace): The parsed command-line arguments.

        Returns:
            random_incidents (queryset): set of random incidents from database
            random_incident_ids (list): list of random incident ids for random_incidents
        """
        # Query the incidents within the date range
        incidents_in_date_range = Incident.objects.filter(published__range=(start_date, end_date))
        incident_ids = list(incidents_in_date_range.values_list('id', flat=True))

        ## DELETE, THIS IS JUST FOR TESTING UNTIL DATABASE IS POPULATED ##
        # incident_ids = [x for x in range(10000)]
        ## END DELETE ##

        # Randomly select args.countIncidents from incident list
        numIncidents = args.countIncidents if args.countIncidents else 30
        numIncidents = min(len(incident_ids), numIncidents)
        random_incident_ids = random.sample(incident_ids, numIncidents)
        random_incidents = Incident.objects.filter(id__in=random_incident_ids)

        return (random_incidents, random_incident_ids)

    def __get_articles_nf(self, start_date: datetime, end_date: datetime, args: argparse.Namespace):
        """
        Get a random list of non-failure article IDs that fall within a date range.

        Args:
            start_date (datetime): Start date for collecting non-failure articles
            end_date (datetime): End date for collecting non-failure articles
            args (argparse.Namespace): The parsed command-line arguments.

        Returns:
            list: A list of random non-failure article IDs.
        """
        # Get article IDs that do not describe failures and fall within the date range
        non_failure_article_ids = list(Article.objects.filter(
            describes_failure=False,
            published__range=(start_date, end_date)
        ).values_list('id', flat=True))

        # If the count is greater than the number of non-failure articles, limit it to that number
        countANF = min(args.countANF, len(non_failure_article_ids))

        # Randomly select countANF article IDs from non-failure articles
        random_non_failure_article_ids = random.sample(non_failure_article_ids, countANF)

        return random_non_failure_article_ids

    def __get_articles_na(self, start_date: datetime, end_date: datetime, args: argparse.Namespace):
        """
        Get a random list of non-failure articles that are failure reporting but not analyzable
        and fall within a date range.

        Args:
            start_date (datetime): Start date for collecting non-failure articles
            end_date (datetime): End date for collecting non-failure articles
            args (argparse.Namespace): The parsed command-line arguments.

        Returns:
            list: A list of random non-failure article IDs.
        """
        # Get article IDs that are failure reporting (describes_failure=True),
        # but not analyzable (analyzable_failure=False) and fall within the date range
        non_failure_article_ids = list(Article.objects.filter(
            describes_failure=True,
            analyzable_failure=False,
            published__range=(start_date, end_date)
        ).values_list('id', flat=True))

        # If the count is greater than the number of non-failure articles, limit it to that number
        countANF = min(args.countANF, len(non_failure_article_ids))

        # Randomly select countANF article IDs from non-failure articles
        random_non_failure_article_ids = random.sample(non_failure_article_ids, countANF)

        return random_non_failure_article_ids

    def __download_incidents_to_csv(self, incidents, filename):
        """
        Download incidents to a CSV file.

        Args:
            incidents (QuerySet): QuerySet containing incidents.
            filename (str): Name of the CSV file to save.
        """
        with open(filename, 'w', newline='') as csvfile:
            incident_writer = csv.writer(csvfile)
            # Write the CSV header
            header = [
                "ID", "Published", "Title", "Summary", "System", "Time", "SEcauses",
                "NSEcauses", "Impacts", "Mitigations", "ResponsibleOrg", "ImpactedOrg",
                "Phase Option", "Boundary Option", "Nature Option", "Dimension Option",
                "Objective Option", "Intent Option", "Capability Option", "Duration Option",
                "Domain Option", "CPS Option", "Perception Option", "Communication Option",
                "Application Option", "Behaviour Option",
                "Phase Rationale", "Boundary Rationale", "Nature Rationale",
                "Dimension Rationale", "Objective Rationale", "Intent Rationale",
                "Capability Rationale", "Duration Rationale", "Domain Rationale",
                "CPS Rationale", "Perception Rationale", "Communication Rationale",
                "Application Rationale", "Behaviour Rationale",
                "Summary Embedding", "Time Embedding", "System Embedding",
                "ResponsibleOrg Embedding", "ImpactedOrg Embedding",
                "Software Causes Embedding", "Non-Software Causes Embedding",
                "Impacts Embedding", "Mitigations Embedding"
            ]
            incident_writer.writerow(header)

            # Write incident data to CSV
            for incident in incidents:
                data_row = [
                    incident.id, incident.published, incident.title, incident.summary,
                    incident.system, incident.time, incident.SEcauses, incident.NSEcauses,
                    incident.impacts, incident.mitigations, incident.ResponsibleOrg,
                    incident.ImpactedOrg, incident.phase_option, incident.boundary_option,
                    incident.nature_option, incident.dimension_option, incident.objective_option,
                    incident.intent_option, incident.capability_option, incident.duration_option,
                    incident.domain_option, incident.cps_option, incident.perception_option,
                    incident.communication_option, incident.application_option,
                    incident.behaviour_option, incident.phase_rationale, incident.boundary_rationale,
                    incident.nature_rationale, incident.dimension_rationale, incident.objective_rationale,
                    incident.intent_rationale, incident.capability_rationale, incident.duration_rationale,
                    incident.domain_rationale, incident.cps_rationale, incident.perception_rationale,
                    incident.communication_rationale, incident.application_rationale, incident.behaviour_rationale,
                    incident.summary_embedding, incident.time_embedding, incident.system_embedding,
                    incident.ResponsibleOrg_embedding, incident.ImpactedOrg_embedding,
                    incident.SEcauses_embedding, incident.NSEcauses_embedding, incident.impacts_embedding,
                    incident.mitigations_embedding
                ]
                incident_writer.writerow(data_row)

    
    def __download_articles_to_csv(self, articles, filename):
        """
        Download articles to a CSV file.

        Args:
            articles (QuerySet): QuerySet containing articles.
            filename (str): Name of the CSV file to save.
        """
        with open(filename, 'w', newline='') as csvfile:
            article_writer = csv.writer(csvfile)
            # Write the CSV header
            header = [
                "ID", "URL", "Published", "Source", "Article Summary", "Body",
                "Embedding", "Scraped At", "Scrape Successful", "Describes Failure",
                "Analyzable Failure", "Article Stored", "Similarity Score", "Headline",
                "Title", "Summary", "System", "Time", "SEcauses", "NSEcauses", "Impacts",
                "Mitigations", "ResponsibleOrg", "ImpactedOrg", "Phase Option", "Boundary Option",
                "Nature Option", "Dimension Option", "Objective Option", "Intent Option",
                "Capability Option", "Duration Option", "Domain Option", "CPS Option",
                "Perception Option", "Communication Option", "Application Option", "Behaviour Option",
                "Phase Rationale", "Boundary Rationale", "Nature Rationale", "Dimension Rationale",
                "Objective Rationale", "Intent Rationale", "Capability Rationale", "Duration Rationale",
                "Domain Rationale", "CPS Rationale", "Perception Rationale", "Communication Rationale",
                "Application Rationale", "Behaviour Rationale", "Summary Embedding", "Time Embedding",
                "System Embedding", "ResponsibleOrg Embedding", "ImpactedOrg Embedding",
                "Software Causes Embedding", "Non-Software Causes Embedding", "Impacts Embedding",
                "Mitigations Embedding"
            ]
            article_writer.writerow(header)

            # Write article data to CSV
            for article in articles:
                data_row = [
                    article.id, article.url, article.published, article.source, article.article_summary,
                    article.body, article.embedding, article.scraped_at, article.scrape_successful,
                    article.describes_failure, article.analyzable_failure, article.article_stored,
                    article.similarity_score, article.headline, article.title, article.summary,
                    article.system, article.time, article.SEcauses, article.NSEcauses, article.impacts,
                    article.mitigations, article.ResponsibleOrg, article.ImpactedOrg,
                    article.phase_option, article.boundary_option, article.nature_option,
                    article.dimension_option, article.objective_option, article.intent_option,
                    article.capability_option, article.duration_option, article.domain_option,
                    article.cps_option, article.perception_option, article.communication_option,
                    article.application_option, article.behaviour_option, article.phase_rationale,
                    article.boundary_rationale, article.nature_rationale, article.dimension_rationale,
                    article.objective_rationale, article.intent_rationale, article.capability_rationale,
                    article.duration_rationale, article.domain_rationale, article.cps_rationale,
                    article.perception_rationale, article.communication_rationale, article.application_rationale,
                    article.behaviour_rationale, article.summary_embedding, article.time_embedding,
                    article.system_embedding, article.ResponsibleOrg_embedding, article.ImpactedOrg_embedding,
                    article.SEcauses_embedding, article.NSEcauses_embedding, article.impacts_embedding,
                    article.mitigations_embedding
                ]
                article_writer.writerow(data_row)

