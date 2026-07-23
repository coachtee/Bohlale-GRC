from django.contrib import admin

from .models import AIGeneration


@admin.register(AIGeneration)
class AIGenerationAdmin(admin.ModelAdmin):
    list_display = ("purpose", "organisation", "provider", "model", "review_status", "created_at")
    list_filter = ("purpose", "provider", "review_status")
    readonly_fields = [f.name for f in AIGeneration._meta.fields if f.name != "review_status"]
