from django.contrib import admin

from .models import Assessment, AssessmentResult


class AssessmentResultInline(admin.TabularInline):
    model = AssessmentResult
    extra = 0


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "name", "organisation", "assessment_type", "status")
    list_filter = ("assessment_type", "status", "organisation")
    inlines = [AssessmentResultInline]
