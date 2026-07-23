from django.contrib import admin

from .models import Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "name", "organisation", "asset_type", "classification", "status")
    list_filter = ("asset_type", "classification", "status", "organisation")
    search_fields = ("reference_code", "name")
