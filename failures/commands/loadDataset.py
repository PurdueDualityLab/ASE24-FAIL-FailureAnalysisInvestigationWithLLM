import argparse
import csv
import logging
import textwrap
from datetime import timezone as datetime_timezone
from pathlib import Path
from typing import Optional

from django.core.management.color import no_style
from django.db import connection, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from failures.articles.models import Article, Incident

class LoadDatasetCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for loading a local CSV dataset.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """

        parser.description = textwrap.dedent(
            """
            Load a bundled CSV dataset into the database. This is useful for local
            development when live article scraping is unavailable or unreliable.
            """
        )
        parser.add_argument(
            "--articles-csv",
            default="tests/fetched_data/Outdated/article_data.csv",
            help="Path to article CSV data.",
        )
        parser.add_argument(
            "--incidents-csv",
            default="tests/fetched_data/Outdated/incident_data.csv",
            help="Path to incident CSV data.",
        )
        parser.add_argument(
            "--relations-csv",
            default="tests/fetched_data/Outdated/articles2incidents.csv",
            help="Path to article-to-incident relation CSV data.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Load at most this many articles. Incidents are still loaded so relations can be resolved.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):
        logging.info("Loading local dataset.")

        articles_path = Path(args.articles_csv)
        incidents_path = Path(args.incidents_csv)
        relations_path = Path(args.relations_csv)

        for path in [articles_path, incidents_path, relations_path]:
            if not path.exists():
                parser.error(f"Dataset file does not exist: {path}")

        with transaction.atomic():
            incidents = self.load_incidents(incidents_path)
            articles = self.load_articles(articles_path, args.limit)
            linked = self.link_articles_to_incidents(relations_path, articles, incidents)
            self.reset_sequences()

        logging.info(
            "Dataset load complete: %d incidents, %d articles, %d article-incident links.",
            len(incidents),
            len(articles),
            linked,
        )
        print(
            f"Dataset load complete: {len(incidents)} incidents, "
            f"{len(articles)} articles, {linked} article-incident links."
        )

    def load_incidents(self, path: Path) -> dict[int, Incident]:
        field_map = {
            "Published": "published",
            "Title": "title",
            "Summary": "summary",
            "Time": "time",
            "System": "system",
            "ResponsibleOrg": "ResponsibleOrg",
            "ImpactedOrg": "ImpactedOrg",
            "SEcauses": "SEcauses",
            "NSEcauses": "NSEcauses",
            "Impacts": "impacts",
            "Preventions": "preventions",
            "Fixes": "fixes",
            "References": "references",
            "Recurring Option": "recurring_option",
            "Phase Option": "phase_option",
            "Boundary Option": "boundary_option",
            "Nature Option": "nature_option",
            "Dimension Option": "dimension_option",
            "Objective Option": "objective_option",
            "Intent Option": "intent_option",
            "Capability Option": "capability_option",
            "Duration Option": "duration_option",
            "Behaviour Option": "behaviour_option",
            "Domain Option": "domain_option",
            "Consequence Option": "consequence_option",
            "CPS Option": "cps_option",
            "Perception Option": "perception_option",
            "Communication Option": "communication_option",
            "Application Option": "application_option",
            "Recurring Rationale": "recurring_rationale",
            "Phase Rationale": "phase_rationale",
            "Boundary Rationale": "boundary_rationale",
            "Nature Rationale": "nature_rationale",
            "Dimension Rationale": "dimension_rationale",
            "Objective Rationale": "objective_rationale",
            "Intent Rationale": "intent_rationale",
            "Capability Rationale": "capability_rationale",
            "Duration Rationale": "duration_rationale",
            "Behaviour Rationale": "behaviour_rationale",
            "Domain Rationale": "domain_rationale",
            "Consequence Rationale": "consequence_rationale",
            "CPS Rationale": "cps_rationale",
            "Perception Rationale": "perception_rationale",
            "Communication Rationale": "communication_rationale",
            "Application Rationale": "application_rationale",
        }

        incidents = {}
        with path.open(newline="", encoding="utf-8") as csv_file:
            for row in csv.DictReader(csv_file):
                incident_id = self.parse_int(row.get("Incident ID"))
                if incident_id is None:
                    continue

                defaults = self.extract_defaults(row, field_map)
                defaults["complete_report"] = True
                incident, _ = Incident.objects.update_or_create(
                    id=incident_id,
                    defaults=defaults,
                )
                incidents[incident_id] = incident

        return incidents

            
    def load_articles(self, path: Path, limit: Optional[int]) -> dict[int, Article]:
        field_map = {
            "Published": "published",
            "URL": "url",
            "Source": "source",
            "Article Summary": "article_summary",
            "Body": "body",
            "Scrape Successful": "scrape_successful",
            "Describes Failure": "describes_failure",
            "Analyzable Failure": "analyzable_failure",
            "Article Stored": "article_stored",
            "Similarity Score": "similarity_score",
            "Headline": "headline",
            "Title": "title",
            "Summary": "summary",
            "System": "system",
            "Time": "time",
            "SEcauses": "SEcauses",
            "NSEcauses": "NSEcauses",
            "Impacts": "impacts",
            "Preventions": "preventions",
            "Fixes": "fixes",
            "ResponsibleOrg": "ResponsibleOrg",
            "ImpactedOrg": "ImpactedOrg",
            "References": "references",
            "Phase Option": "phase_option",
            "Boundary Option": "boundary_option",
            "Nature Option": "nature_option",
            "Dimension Option": "dimension_option",
            "Objective Option": "objective_option",
            "Intent Option": "intent_option",
            "Capability Option": "capability_option",
            "Duration Option": "duration_option",
            "Domain Option": "domain_option",
            "CPS Option": "cps_option",
            "Perception Option": "perception_option",
            "Communication Option": "communication_option",
            "Application Option": "application_option",
            "Behaviour Option": "behaviour_option",
            "Phase Rationale": "phase_rationale",
            "Boundary Rationale": "boundary_rationale",
            "Nature Rationale": "nature_rationale",
            "Dimension Rationale": "dimension_rationale",
            "Objective Rationale": "objective_rationale",
            "Intent Rationale": "intent_rationale",
            "Capability Rationale": "capability_rationale",
            "Duration Rationale": "duration_rationale",
            "Domain Rationale": "domain_rationale",
            "CPS Rationale": "cps_rationale",
            "Perception Rationale": "perception_rationale",
            "Communication Rationale": "communication_rationale",
            "Application Rationale": "application_rationale",
            "Behaviour Rationale": "behaviour_rationale",
        }

        articles = {}
        with path.open(newline="", encoding="utf-8") as csv_file:
            for index, row in enumerate(csv.DictReader(csv_file)):
                if limit is not None and index >= limit:
                    break

                article_id = self.parse_int(row.get("Article ID"))
                url = self.clean(row.get("URL"))
                if article_id is None or not url:
                    continue

                defaults = self.extract_defaults(row, field_map)
                defaults["url"] = url

                article = Article.objects.filter(id=article_id).first()
                if article is None:
                    article = Article.objects.filter(url=url).first()

                if article is None:
                    article = Article(id=article_id)

                for field, value in defaults.items():
                    setattr(article, field, value)
                article.save()
                articles[article_id] = article

        return articles

    def link_articles_to_incidents(
        self,
        path: Path,
        articles: dict[int, Article],
        incidents: dict[int, Incident],
    ) -> int:
        linked = 0
        with path.open(newline="", encoding="utf-8") as csv_file:
            for row in csv.DictReader(csv_file):
                article_id = self.parse_int(row.get("Article ID"))
                incident_id = self.parse_int(row.get("Incident ID"))
                article = articles.get(article_id)
                incident = incidents.get(incident_id)

                if article is None or incident is None:
                    continue

                article.incident = incident
                article.save(update_fields=["incident"])
                linked += 1

        return linked

    def reset_sequences(self):
        statements = connection.ops.sequence_reset_sql(no_style(), [Incident, Article])
        if not statements:
            return

        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)

    def extract_defaults(self, row: dict, field_map: dict[str, str]) -> dict:
        defaults = {}
        for csv_field, model_field in field_map.items():
            if csv_field not in row:
                continue
            defaults[model_field] = self.convert_value(model_field, row[csv_field])
        return defaults

    def convert_value(self, model_field: str, value: str):
        if model_field == "published":
            return self.parse_datetime(value)
        if model_field in {"scrape_successful", "describes_failure", "analyzable_failure", "article_stored"}:
            return self.parse_bool(value)
        if model_field == "similarity_score":
            return self.parse_float(value)
        return self.clean(value)

    def parse_datetime(self, value: str):
        value = self.clean(value)
        if not value:
            return None
        parsed = parse_datetime(value)
        if parsed is not None and timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, datetime_timezone.utc)
        return parsed

    def parse_bool(self, value: str):
        value = self.clean(value).lower()
        if value == "true":
            return True
        if value == "false":
            return False
        return None

    def parse_float(self, value: str):
        value = self.clean(value)
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def parse_int(self, value: str):
        value = self.clean(value)
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def clean(self, value) -> str:
        if value is None:
            return ""
        return str(value).strip()