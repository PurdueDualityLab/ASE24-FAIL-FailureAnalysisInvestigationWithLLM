from django.contrib import admin

from failures.articles.models import Article, Failure, SearchQuery

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

@admin.register(Article)
class ArticleAdmin(ImportExportModelAdmin):
    list_display = (
        "headline",
        "title",
        "describes_failure",
        "published",
        "source",
        "summary",
        "system",
        "organization",
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
        "published",
        "title",
        "summary",
    )
    list_filter = ("title",)