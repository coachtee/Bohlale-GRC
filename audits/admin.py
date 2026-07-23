from django.contrib import admin

from .models import Audit, AuditFinding


class AuditFindingInline(admin.TabularInline):
    model = AuditFinding
    extra = 0


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "title", "organisation", "audit_type", "status")
    list_filter = ("audit_type", "status", "organisation")
    search_fields = ("reference_code", "title")
    inlines = [AuditFindingInline]
