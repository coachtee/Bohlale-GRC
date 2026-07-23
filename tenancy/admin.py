from django.contrib import admin

from .models import Membership, Organisation, OrganisationInvite


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 0


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ("name", "organisation_type", "is_demo", "is_active", "created_at")
    list_filter = ("organisation_type", "is_demo", "is_active")
    search_fields = ("name", "registration_number")
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organisation", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__email", "organisation__name")


@admin.register(OrganisationInvite)
class OrganisationInviteAdmin(admin.ModelAdmin):
    list_display = ("email", "organisation", "role", "accepted", "created_at")
    list_filter = ("role", "accepted")
