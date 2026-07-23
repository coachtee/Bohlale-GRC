from django.urls import path

from . import views

app_name = "tenancy"

urlpatterns = [
    path("", views.organisation_list, name="organisation_list"),
    path("new/", views.organisation_create, name="organisation_create"),
    path("switch/<uuid:pk>/", views.organisation_switch, name="organisation_switch"),
    path("members/", views.member_list, name="member_list"),
    path("settings/", views.member_list, name="settings"),
    path("members/<uuid:pk>/role/", views.member_update_role, name="member_update_role"),
    path("members/<uuid:pk>/remove/", views.member_remove, name="member_remove"),
    path("members/invite/", views.invite_member, name="invite_member"),
    path("members/invite/<uuid:pk>/revoke/", views.revoke_invite, name="revoke_invite"),
    path("invite/<uuid:token>/accept/", views.accept_invite, name="accept_invite"),
]
