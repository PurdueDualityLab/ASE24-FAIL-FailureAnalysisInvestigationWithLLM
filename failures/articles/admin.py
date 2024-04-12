from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse

from failures.articles.models import Article, Incident, SearchQuery, Article_Ko, Incident_Ko

from import_export.admin import ImportExportModelAdmin


'''
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "headline",
        "title",
        "published",
        "source",
        "describes_failure",
        "summary",
        "system",
        "time",
        "SEcauses",
        "NSEcauses",
        "impacts",
        "mitigations",
        "phase_option",
        "boundary_option",
        "nature_option",
        "dimension_option",
        "objective_option",
        "intent_option",
        "capability_option",
        "duration_option",
        "domain_option",
        "cps_option",
        "perception_option",
        "communication_option",
        "application_option",
        "behaviour_option",
        "phase_rationale",
        "boundary_rationale",
        "nature_rationale",
        "dimension_rationale",
        "objective_rationale",
        "intent_rationale",
        "capability_rationale",
        "duration_rationale",
        "domain_rationale",
        "cps_rationale",
        "perception_rationale",
        "communication_rationale",
        "application_rationale",
        "behaviour_rationale",
    )
    list_filter = ("describes_failure",)

'''

@admin.register(Article_Ko)
class Article_KoAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "headline",
        "body",
    )
    search_fields = ["id"]

@admin.register(Article)
class ArticleAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "experiment",
        "headline",
        "title",
        "scrape_successful",
        "describes_failure",
        "analyzable_failure",
        "published",
        "source",
        "summary",
        #"summary_embedding",
        "system",
        "ResponsibleOrg",
        "ImpactedOrg",
        "time",
        "SEcauses",
        "NSEcauses",
        "impacts",
        "preventions",
        "fixes",
        "phase_option",
        "boundary_option",
        "nature_option",
        "dimension_option",
        "objective_option",
        "intent_option",
        "capability_option",
        "duration_option",
        "domain_option",
        "cps_option",
        "perception_option",
        "communication_option",
        "application_option",
        "behaviour_option",
        "phase_rationale",
        "boundary_rationale",
        "nature_rationale",
        "dimension_rationale",
        "objective_rationale",
        "intent_rationale",
        "capability_rationale",
        "duration_rationale",
        "domain_rationale",
        "cps_rationale",
        "perception_rationale",
        "communication_rationale",
        "application_rationale",
        "behaviour_rationale",
    )
    search_fields = ["id"]
    
'''
class ArticleInline(admin.TabularInline):
    model = Article

#@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    inlines = [
        ArticleInline,
    ]

admin.site.register(Incident, IncidentAdmin)
'''

@admin.register(Incident)
class IncidentAdmin(ImportExportModelAdmin):
    list_display = (
        "id",
        "experiment",
        "title",
        "summary",
        #"summary_embedding",
        "system",
        "ResponsibleOrg",
        "ImpactedOrg",
        "time",
        "SEcauses",
        "NSEcauses",
        "impacts",
        "preventions",
        "fixes",
        "references",
        "phase_option",
        "boundary_option",
        "nature_option",
        "dimension_option",
        "objective_option",
        "intent_option",
        "capability_option",
        "duration_option",
        "domain_option",
        "consequence_option",
        "cps_option",
        "perception_option",
        "communication_option",
        "application_option",
        "behaviour_option",
        "phase_rationale",
        "boundary_rationale",
        "nature_rationale",
        "dimension_rationale",
        "objective_rationale",
        "intent_rationale",
        "capability_rationale",
        "duration_rationale",
        "domain_rationale",
        "consequence_rationale",
        "cps_rationale",
        "perception_rationale",
        "communication_rationale",
        "application_rationale",
        "behaviour_rationale",
        "get_articles",
    )
    search_fields = ["title"]

    '''
    def get_articles(self, obj):
        articles = obj.articles.all()

        return ", ".join([article.headline for article in articles])

    get_articles.short_description = "Source Articles"
    '''

    
    def article_admin_url(self, article_id):
        # Construct the URL to the article change page in the admin
        return reverse("admin:articles_article_change", args=[article_id])

    def get_articles(self, obj):
        articles = obj.articles.all()
        articles_links = [
            format_html('<a href="{}">{}</a>', self.article_admin_url(article.id), article.headline)
            for article in articles
        ]

        return format_html(", ".join(articles_links))
    
    get_articles.short_description = "Source Articles"
    

    

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = (
        "keyword",
        "start_year",
        "start_month",
        "end_year",
        "end_month",
        "sources",
        "created_at",
        "last_searched_at",
    )
    list_filter = ("created_at", "last_searched_at")


'''
@admin.register(Failure)
class FailureAdmin(admin.ModelAdmin):
    list_display = (
        "published",
        "title",
        "summary",
    )
    list_filter = ("title",)
'''