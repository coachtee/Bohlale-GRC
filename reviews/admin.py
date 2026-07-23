from django.contrib import admin

from .models import ManagementReview, ManagementReviewInputRecord


class InputRecordInline(admin.TabularInline):
    model = ManagementReviewInputRecord
    extra = 0


@admin.register(ManagementReview)
class ManagementReviewAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "organisation", "meeting_date", "status")
    list_filter = ("status", "organisation")
    inlines = [InputRecordInline]
