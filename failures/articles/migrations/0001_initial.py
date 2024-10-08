# Generated by Django 4.1.3 on 2022-12-07 14:58

import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Failure",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="Name")),
                ("description", models.TextField(verbose_name="Description")),
                (
                    "started_at",
                    models.CharField(max_length=255, verbose_name="Started at"),
                ),
                ("ended_at", models.CharField(max_length=255, verbose_name="Ended at")),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Created at"),
                ),
                (
                    "manual_annotation",
                    models.BooleanField(
                        default=False, verbose_name="Manual Annotation"
                    ),
                ),
                ("display", models.BooleanField(default=False, verbose_name="Display")),
                ("industry", models.CharField(max_length=255, verbose_name="Industry")),
                (
                    "duration",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("TRANSIENT", "Transient"),
                            ("PERMANENT", "Permanent"),
                            ("INTERMITTENT", "Intermittent"),
                        ],
                        max_length=12,
                        verbose_name="Duration",
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        blank=True,
                        choices=[("INTERNAL", "Internal"), ("EXTERNAL", "External")],
                        max_length=8,
                        verbose_name="Location",
                    ),
                ),
                (
                    "semantics",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CRASH", "Crash"),
                            ("OMISSION", "Omission"),
                            ("TIMING", "Timing"),
                            ("VALUE", "Value"),
                            ("ARBITRARY", "Arbitrary"),
                        ],
                        max_length=9,
                        verbose_name="Semantics",
                    ),
                ),
                (
                    "behavior",
                    models.CharField(
                        blank=True,
                        choices=[("SOFT", "Soft"), ("HARD", "Hard")],
                        max_length=4,
                        verbose_name="Behavior",
                    ),
                ),
                (
                    "dimension",
                    models.CharField(
                        blank=True,
                        choices=[("SOFTWARE", "Software"), ("HARDWARE", "Hardware")],
                        max_length=8,
                        verbose_name="Dimension",
                    ),
                ),
            ],
            options={
                "verbose_name": "Failure",
                "verbose_name_plural": "Failures",
            },
        ),
        migrations.CreateModel(
            name="SearchQuery",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "keyword",
                    models.CharField(
                        help_text="Keyword to use for searching for news articles.",
                        max_length=255,
                        verbose_name="Keyword",
                    ),
                ),
                (
                    "start_year",
                    models.IntegerField(
                        blank=True,
                        help_text="News articles will be searched from this year onwards. This field is optional.",
                        null=True,
                        verbose_name="Start Year",
                    ),
                ),
                (
                    "end_year",
                    models.IntegerField(
                        blank=True,
                        help_text="News articles will be searched until this year. This field is optional.",
                        null=True,
                        verbose_name="End Year",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date and time when this search query was created.",
                        verbose_name="Created At",
                    ),
                ),
                (
                    "last_searched_at",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        help_text="Date and time when this search query was last searched.",
                        null=True,
                        verbose_name="Last Searched At",
                    ),
                ),
                (
                    "sources",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.URLField(max_length=255),
                        blank=True,
                        help_text="Sources to search for news articles, such as nytimes.com.",
                        null=True,
                        size=None,
                        verbose_name="Sources",
                    ),
                ),
            ],
            options={
                "verbose_name": "Search Query",
                "verbose_name_plural": "Search Queries",
            },
        ),
        migrations.CreateModel(
            name="FailureCause",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("description", models.TextField(verbose_name="Description")),
                (
                    "failure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="failure_causes",
                        related_query_name="failure_cause",
                        to="articles.failure",
                        verbose_name="Failure",
                    ),
                ),
            ],
            options={
                "verbose_name": "Failure Cause",
                "verbose_name_plural": "Failure Causes",
            },
        ),
        migrations.CreateModel(
            name="Article",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        help_text="Title of the article.",
                        max_length=510,
                        verbose_name="Title",
                    ),
                ),
                (
                    "url",
                    models.URLField(
                        help_text="URL of the article.",
                        max_length=510,
                        unique=True,
                        verbose_name="URL",
                    ),
                ),
                (
                    "published",
                    models.DateTimeField(
                        help_text="Date and time when the article was published.",
                        verbose_name="Published",
                    ),
                ),
                (
                    "source",
                    models.URLField(
                        help_text="URL of the source of the article, such as nytimes.com.",
                        verbose_name="Source",
                    ),
                ),
                (
                    "summary",
                    models.TextField(
                        blank=True,
                        help_text="Summary of the article generated by a summarizer model.",
                        verbose_name="Summary",
                    ),
                ),
                (
                    "body",
                    models.TextField(
                        blank=True,
                        help_text="Body of the article scraped from the URL.",
                        verbose_name="Body",
                    ),
                ),
                (
                    "embedding",
                    models.FileField(
                        help_text="NumPy array of the embedding of the article stored as a file.",
                        null=True,
                        upload_to="embeddings",
                        verbose_name="Embedding",
                    ),
                ),
                (
                    "scraped_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date and time when the article was scraped.",
                        verbose_name="Scraped at",
                    ),
                ),
                (
                    "failures",
                    models.ManyToManyField(
                        related_name="articles",
                        related_query_name="article",
                        to="articles.failure",
                        verbose_name="Failures",
                    ),
                ),
                (
                    "search_queries",
                    models.ManyToManyField(
                        related_name="articles",
                        related_query_name="article",
                        to="articles.searchquery",
                        verbose_name="Search Queries",
                    ),
                ),
            ],
            options={
                "verbose_name": "Article",
                "verbose_name_plural": "Articles",
            },
        ),
    ]
