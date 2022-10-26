from django.contrib import admin

from failures.articles.models import Annotation, Article, SearchQuery


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "published", "scraped_at")
    list_filter = ("scraped_at",)


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("keyword", "start_year", "end_year", "searched_at")
    list_filter = ("searched_at",)


admin.site.register(Annotation)
