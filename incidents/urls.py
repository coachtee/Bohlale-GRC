from django.urls import path

from . import views

app_name = "incidents"

urlpatterns = [
    path("", views.IncidentListView.as_view(), name="list"),
    path("new/", views.IncidentCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.IncidentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.IncidentUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.IncidentDeleteView.as_view(), name="delete"),
    path("changes/", views.change_event_list, name="change_event_list"),
    path("changes/new/", views.change_event_create, name="change_event_create"),
    path("changes/<uuid:pk>/", views.change_event_detail, name="change_event_detail"),
    path("changes/<uuid:pk>/reviewed/", views.change_event_mark_reviewed, name="change_event_mark_reviewed"),
]
