import datetime
import logging
import time
from typing import Optional

import feedparser
from django.db import models
from django.utils.translation import gettext_lazy as _
from newsplease import NewsPlease

from failures.networks.models import Summarizer, ZeroShotClassifier


class SearchQuery(models.Model):
    keyword = models.CharField(_("Keyword"), max_length=255)

    start_year = models.IntegerField(_("Start Year"), null=True)

    end_year = models.IntegerField(_("End Year"), null=True)

    searched_at = models.DateTimeField(_("Searched at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Search Query")
        verbose_name_plural = _("Search Queries")

    def __str__(self):
        return f"{self.keyword}"


class Article(models.Model):
    failures = models.ManyToManyField(
        "Failure",
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Failures"),
    )

    search_queries = models.ManyToManyField(
        SearchQuery,
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Search Queries"),
    )

    title = models.CharField(_("Title"), max_length=510)

    # Marking url as unique=True because we don't want to store the same article twice
    url = models.URLField(_("URL"), unique=True, max_length=510)

    published = models.DateTimeField(_("Published"))

    source = models.URLField(_("Source"))

    summary = models.TextField(_("Summary"), blank=True)

    body = models.TextField(_("Body"), blank=True)

    embedding = models.FileField(_("Embedding"), upload_to="embeddings", null=True)

    scraped_at = models.DateTimeField(_("Scraped at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.title

    def has_manual_annotation(self) -> bool:
        return self.failures.filter(manual_annotation=True).exists()

    @classmethod
    def create_from_google_news_rss_feed(
        cls,
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        sources: Optional[list[str]] = None,
    ):
        url = cls.format_google_news_rss_url(keyword, start_year, end_year, sources)
        feed = feedparser.parse(url)
        search_query = SearchQuery.objects.create(
            keyword=keyword, start_year=start_year, end_year=end_year
        )
        logging.info(f"Created search query: {search_query}")
        for entry in feed.entries:
            # TODO: reduce queries here
            if not cls.objects.filter(url=entry.link).exists():
                article = cls.objects.create(
                    title=entry["title"],
                    url=entry["link"],
                    # example: Mon, 24 Oct 2022 11:00:00 GMT
                    published=datetime.datetime.strptime(
                        entry["published"], "%a, %d %b %Y %H:%M:%S %Z"
                    ),
                    source=entry["source"]["href"],
                )
                logging.info(f"Created article: {article}")
            else:
                article = cls.objects.get(url=entry.link)
            logging.info(f"Adding search query to article: {search_query} - {article}")
            article.search_queries.add(search_query)

    # TODO: should this method be on SearchQuery?
    @staticmethod
    def format_google_news_rss_url(
        keyword: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        sources: Optional[list[str]] = None,
    ) -> str:
        keyword = keyword.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={keyword}"
        if start_year:
            url += f"%20after%3A{start_year}-01-01"
        if end_year:
            url += f"%20before%3A{end_year}-01-01"
        for i, source in enumerate(sources):
            if i > 0:
                url += "%20OR"
            url += f"%20site%3Ahttps%3A%2F%2F{source}"
        url += "&hl=en-US&gl=US&ceid=US%3Aen"
        return url

    def scrape_body(self):
        try:
            article = NewsPlease.from_url(self.url)
        except Exception as e:
            logging.error(f"Failed to scrape article: {self.url} - {e}")
            return
        if article.maintext is None:
            logging.error(f"Failed to scrape article: {self.url} - No text found")
            return
        self.body = article.maintext
        self.save()
        logging.info(f"Scraped body for {self.url}")

    def summarize_body(self, summarizer: Summarizer):
        self.summary: str = summarizer.run(self.body)
        self.save()


class Failure(models.Model):
    class Duration(models.TextChoices):
        TRANSIENT = "TRANSIENT", _("Transient")
        PERMANENT = "PERMANENT", _("Permanent")
        INTERMITTENT = "INTERMITTENT", _("Intermittent")

    class Location(models.TextChoices):
        INTERNAL = "INTERNAL", _("Internal")
        EXTERNAL = "EXTERNAL", _("External")

    class Semantics(models.TextChoices):
        CRASH = "CRASH", _("Crash")
        OMISSION = "OMISSION", _("Omission")
        TIMING = "TIMING", _("Timing")
        VALUE = "VALUE", _("Value")
        ARBITRARY = "ARBITRARY", _("Arbitrary")

    class Behavior(models.TextChoices):
        SOFT = "SOFT", _("Soft")
        HARD = "HARD", _("Hard")

    class Dimension(models.TextChoices):
        SOFTWARE = "SOFTWARE", _("Software")
        HARDWARE = "HARDWARE", _("Hardware")

    name = models.CharField(_("Name"), max_length=255)

    description = models.TextField(_("Description"))

    started_at = models.DateTimeField(_("Started at"))

    # ended_at may not apply to all failures, so marking it as null=True
    ended_at = models.DateTimeField(_("Ended at"), null=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    # manual_annotation=False means that the failure was automatically detected
    manual_annotation = models.BooleanField(_("Manual Annotation"), default=False)

    # display means that this failure should be displayed in the UI, because it has been merged with other failures
    display = models.BooleanField(_("Display"), default=False)

    industry = models.CharField(_("Industry"), max_length=255)

    duration = models.CharField(
        _("Duration"),
        max_length=12,
        choices=Duration.choices,
    )

    location = models.CharField(
        _("Location"),
        max_length=8,
        choices=Location.choices,
    )

    semantics = models.CharField(
        _("Semantics"),
        max_length=9,
        choices=Semantics.choices,
    )

    behavior = models.CharField(
        _("Behavior"),
        max_length=4,
        choices=Behavior.choices,
    )

    dimension = models.CharField(
        _("Dimension"),
        max_length=8,
        choices=Dimension.choices,
    )

    class Meta:
        verbose_name = _("Failure")
        verbose_name_plural = _("Failures")

    def __str__(self):
        return self.name

    @classmethod
    def create_automated_from_article(
        cls, article: Article, classifier: ZeroShotClassifier
    ):
        for field in ("duration", "location", "semantics", "behavior", "dimension"):
            labels = [choice[0].lower() for choice in getattr(cls, field).choices]
            result = classifier.run(article.summary, labels)
            scores = result["scores"]
            predicted_label = result["labels"][scores.index(max(scores))]
            setattr(article, field, predicted_label.upper())
        article.save()
