from django.contrib import admin

from .models import (
    InformationRequest,
    InterviewExchange,
    InterviewSession,
    JourneyStep,
    JourneyTemplate,
    OrganisationJourney,
    StepProgress,
)


class JourneyStepInline(admin.TabularInline):
    model = JourneyStep
    extra = 0


@admin.register(JourneyTemplate)
class JourneyTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "framework", "goal_type", "is_active")
    inlines = [JourneyStepInline]


@admin.register(OrganisationJourney)
class OrganisationJourneyAdmin(admin.ModelAdmin):
    list_display = ("organisation", "template", "status", "progress_percent")


admin.site.register(JourneyStep)
admin.site.register(StepProgress)
admin.site.register(InterviewSession)
admin.site.register(InterviewExchange)
admin.site.register(InformationRequest)
