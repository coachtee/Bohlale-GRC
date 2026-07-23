from django.urls import path

from . import views

app_name = "ai"

urlpatterns = [
    path("", views.generation_log, name="log"),
    path("<uuid:pk>/", views.generation_detail, name="detail"),
]
