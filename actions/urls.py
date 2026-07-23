from django.urls import path

from . import views

app_name = "actions"

urlpatterns = [
    path("", views.CorrectiveActionListView.as_view(), name="list"),
    path("new/", views.CorrectiveActionCreateView.as_view(), name="create"),
    path("from-incident/<uuid:pk>/", views.create_from_incident, name="create_from_incident"),
    path("from-finding/<uuid:pk>/", views.create_from_finding, name="create_from_finding"),
    path("from-review/<uuid:pk>/", views.create_from_review, name="create_from_review"),
    path("<uuid:pk>/", views.CorrectiveActionDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.CorrectiveActionUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.CorrectiveActionDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/verify-close/", views.action_verify_close, name="verify_close"),
]
