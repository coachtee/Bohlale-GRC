from django.contrib import admin

from .models import ApprovalRequest, Signature


class SignatureInline(admin.TabularInline):
    model = Signature
    extra = 0
    readonly_fields = [f.name for f in Signature._meta.fields]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ("organisation", "target", "status", "created_at")
    list_filter = ("status",)
    inlines = [SignatureInline]
