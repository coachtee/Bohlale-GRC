from django.contrib import admin

from .models import Document, DocumentVersion


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    readonly_fields = ("version_label", "status_at_snapshot", "changed_by", "change_reason", "document_hash", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "title", "organisation", "doc_type", "status", "version_label")
    list_filter = ("doc_type", "status", "organisation")
    search_fields = ("title", "reference_code")
    inlines = [DocumentVersionInline]
