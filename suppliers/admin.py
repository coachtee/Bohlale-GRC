from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "name", "organisation", "criticality", "risk_rating", "status")
    list_filter = ("criticality", "risk_rating", "status", "organisation")
    search_fields = ("reference_code", "name")
