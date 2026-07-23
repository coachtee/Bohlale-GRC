from django.urls import path

from . import views

app_name = "approvals"

urlpatterns = [
    path("", views.approval_list, name="list"),
    path("<uuid:pk>/", views.approval_detail, name="detail"),
]
