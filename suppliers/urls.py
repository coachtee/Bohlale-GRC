from django.urls import path

from . import views

app_name = "suppliers"

urlpatterns = [
    path("", views.SupplierListView.as_view(), name="list"),
    path("new/", views.SupplierCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.SupplierDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.SupplierUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.SupplierDeleteView.as_view(), name="delete"),
]
