from django.contrib import admin

from .models import KnowledgeItem


@admin.register(KnowledgeItem)
class KnowledgeItemAdmin(admin.ModelAdmin):
    list_display = ("label", "organisation", "category", "status", "updated_at")
    list_filter = ("category", "status", "organisation")
    search_fields = ("label", "value")
