from django.contrib import admin

from .models import ChangeEvent, Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "title", "organisation", "severity", "status")
    list_filter = ("severity", "status", "organisation")
    search_fields = ("reference_code", "title")


@admin.register(ChangeEvent)
class ChangeEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "organisation", "status", "created_at")
    list_filter = ("event_type", "status")
