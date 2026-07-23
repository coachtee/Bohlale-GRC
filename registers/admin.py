from django.contrib import admin

from .models import RegisterEntry, RegisterType


@admin.register(RegisterType)
class RegisterTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")


@admin.register(RegisterEntry)
class RegisterEntryAdmin(admin.ModelAdmin):
    list_display = ("register_type", "organisation", "created_at")
    list_filter = ("register_type", "organisation")
