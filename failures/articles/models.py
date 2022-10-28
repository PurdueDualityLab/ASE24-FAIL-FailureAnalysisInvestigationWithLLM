import datetime
from typing import Optional

import feedparser
import newsplease
from django.db import models
from django.utils.translation import gettext_lazy as _

from failures.networks.models import ZeroShotClassifier


class SearchQuery(models.Model):
    keyword = models.CharField(_("Keyword"), max_length=255)

    start_year = models.IntegerField(_("Start Year"), null=True)

    end_year = models.IntegerField(_("End Year"), null=True)

    searched_at = models.DateTimeField(_("Searched at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Search Query")
        verbose_name_plural = _("Search Queries")

    def __str__(self):
        return self.keyword


class Article(models.Model):
    failure = models.ForeignKey(
        "failures.Failure",
        on_delete=models.CASCADE,
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Failure"),
        null=True,
    )

    search_query = models.ManyToManyField(
        SearchQuery,
        related_name="articles",
        related_query_name="article",
        verbose_name=_("Search Query"),
    )

    title = models.CharField(_("Title"), max_length=255)

    # Marking url as unique=True because we don't want to store the same article twice
    url = models.URLField(_("URL"), unique=True)

    published = models.DateTimeField(_("Published"))

    source = models.URLField(_("Source"))

    summary = models.TextField(_("Summary"), blank=True)

    body = models.TextField(_("Body"), blank=True)

    scraped_at = models.DateTimeField(_("Scraped at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Article")
        verbose_name_plural = _("Articles")

    def __str__(self):
        return self.title

    def has_manual_annotation(self) -> bool:
        if self.failure is not None:
            self.failure: Failure
            return self.failure.manual_annotation
        return False

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
            else:
                article = cls.objects.get(url=entry.link)
            article.search_query.add(search_query)

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
        article = newsplease.NewsPlease.from_url(self.url)
        self.body = article.text
        self.save()

    def summarize_body(self, summarizer):
        self.summary = summarizer(self.body)
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

    description = models.TextField(_("Description"), blank=True)

    started_at = models.DateTimeField(_("Started at"))

    # ended_at may not apply to all failures, so marking it as null=True
    ended_at = models.DateTimeField(_("Ended at"), null=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    manual_annotation = models.BooleanField(_("Manual Annotation"), default=False)

    automated_annotation = models.BooleanField(_("Automated Annotation"), default=False)

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
            result = classifier.classify(article.summary, labels)
            scores = result["scores"]
            predicted_label = result["labels"][scores.index(max(scores))]
            setattr(article, field, predicted_label.upper())
        article.save()
