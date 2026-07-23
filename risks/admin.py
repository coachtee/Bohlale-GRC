from django.contrib import admin

from .models import Risk, RiskMatrixConfig


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "title", "organisation", "category", "inherent_risk_score", "status")
    list_filter = ("category", "status", "treatment", "organisation")
    search_fields = ("reference_code", "title")


admin.site.register(RiskMatrixConfig)
