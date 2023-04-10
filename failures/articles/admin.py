from django.contrib import admin

from failures.articles.models import Article, Failure, SearchQuery


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published", "scraped_at", "describes_failure","describes_failure_confidence")
    list_filter = ("scraped_at",)


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = (
        "keyword",
        "start_year",
        "end_year",
        "created_at",
        "last_searched_at",
    )
    list_filter = ("created_at", "last_searched_at")


@admin.register(Failure)
class FailureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "system",
        "domain_option",
        "SEcauses",
        "phase_option",
        "behaviour_option",
    )
    list_filter = ("title",)
