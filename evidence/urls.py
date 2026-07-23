from django.urls import path

from . import views

app_name = "evidence"

urlpatterns = [
    path("", views.EvidenceListView.as_view(), name="list"),
    path("new/", views.EvidenceCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.EvidenceDetailView.as_view(), name="detail"),
    path("<uuid:pk>/download/", views.evidence_download, name="download"),
    path("<uuid:pk>/edit/", views.EvidenceUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.EvidenceDeleteView.as_view(), name="delete"),
]
