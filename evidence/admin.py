from django.contrib import admin

from .models import Evidence


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "name", "organisation", "evidence_type", "verification_status", "expiry_date")
    list_filter = ("evidence_type", "verification_status", "organisation")
    search_fields = ("reference_code", "name")
