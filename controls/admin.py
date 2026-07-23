from django.contrib import admin

from .models import Control, ControlTest, SoAEntry


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "name", "organisation", "implementation_status", "effectiveness")
    list_filter = ("implementation_status", "effectiveness", "organisation")
    search_fields = ("reference_code", "name")


admin.site.register(ControlTest)


@admin.register(SoAEntry)
class SoAEntryAdmin(admin.ModelAdmin):
    list_display = ("control", "framework", "organisation", "applicable")
    list_filter = ("applicable", "framework")
