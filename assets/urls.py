from django.urls import path

from . import views

app_name = "assets"

urlpatterns = [
    path("", views.AssetListView.as_view(), name="list"),
    path("new/", views.AssetCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.AssetDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.AssetUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.AssetDeleteView.as_view(), name="delete"),
]
