from django.urls import path

from . import views

app_name = "risks"

urlpatterns = [
    path("", views.RiskListView.as_view(), name="list"),
    path("new/", views.RiskCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.RiskDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.RiskUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.RiskDeleteView.as_view(), name="delete"),
]
