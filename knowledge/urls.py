from django.urls import path

from . import views

app_name = "knowledge"

urlpatterns = [
    path("", views.profile, name="profile"),
    path("new/", views.item_create, name="item_create"),
    path("<uuid:pk>/edit/", views.item_edit, name="item_edit"),
    path("<uuid:pk>/verify/", views.item_verify, name="item_verify"),
]
