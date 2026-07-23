from django.urls import path

from . import views

app_name = "registers"

urlpatterns = [
    path("", views.hub, name="hub"),
    path("<slug:slug>/", views.generic_list, name="generic_list"),
    path("<slug:slug>/new/", views.generic_create, name="generic_create"),
    path("<slug:slug>/<uuid:pk>/edit/", views.generic_edit, name="generic_edit"),
    path("<slug:slug>/<uuid:pk>/delete/", views.generic_delete, name="generic_delete"),
]
