from django.contrib import admin

from .models import (
    AssessmentQuestion,
    Domain,
    EvidenceExpectation,
    Framework,
    FrameworkAdoption,
    FrameworkImport,
    Requirement,
    RequirementStatus,
)


class DomainInline(admin.TabularInline):
    model = Domain
    extra = 0


@admin.register(Framework)
class FrameworkAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "organisation", "source_type", "is_published")
    list_filter = ("source_type", "is_published")
    search_fields = ("name", "code")
    inlines = [DomainInline]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("title", "framework", "code", "order")
    list_filter = ("framework",)


@admin.register(Requirement)
class RequirementAdmin(admin.ModelAdmin):
    list_display = ("ref_code", "title", "framework", "domain")
    list_filter = ("framework",)
    search_fields = ("ref_code", "title")


admin.site.register(AssessmentQuestion)
admin.site.register(EvidenceExpectation)
admin.site.register(FrameworkAdoption)
admin.site.register(RequirementStatus)


@admin.register(FrameworkImport)
class FrameworkImportAdmin(admin.ModelAdmin):
    list_display = ("proposed_name", "organisation", "status", "created_at")
    list_filter = ("status",)
