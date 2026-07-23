from django.contrib import admin

from .models import CorrectiveAction


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "organisation", "source", "severity", "status", "due_date")
    list_filter = ("source", "severity", "status", "organisation")
    search_fields = ("reference_code", "finding_description")
