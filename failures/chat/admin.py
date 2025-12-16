from django.contrib import admin
from .models import ChainlitThread, ChainlitStep, ChainlitElement, ChainlitFeedback

@admin.register(ChainlitThread)
class ChainlitThreadAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "user")
    search_fields = ("name", "user__username")
    list_filter = ("created_at",)

@admin.register(ChainlitStep)
class ChainlitStepAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "thread", "created_at")
    search_fields = ("name", "input", "output")
    list_filter = ("type", "created_at")

@admin.register(ChainlitElement)
class ChainlitElementAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "thread")
    list_filter = ("type",)

@admin.register(ChainlitFeedback)
class ChainlitFeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "for_id", "value", "step")
    list_filter = ("value",)
