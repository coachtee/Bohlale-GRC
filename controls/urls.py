from django.urls import path

from . import views

app_name = "controls"

urlpatterns = [
    path("", views.ControlListView.as_view(), name="list"),
    path("new/", views.ControlCreateView.as_view(), name="create"),
    path("soa/", views.soa_view, name="soa"),
    path("soa/export.csv", views.soa_export_csv, name="soa_export_csv"),
    path("soa/<uuid:pk>/update/", views.soa_entry_update, name="soa_entry_update"),
    path("<uuid:pk>/", views.ControlDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.ControlUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.ControlDeleteView.as_view(), name="delete"),
]
