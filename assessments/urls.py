from django.urls import path

from . import views

app_name = "assessments"

urlpatterns = [
    path("", views.assessment_list, name="list"),
    path("new/", views.assessment_create, name="create"),
    path("<uuid:pk>/", views.assessment_detail, name="detail"),
    path("results/<uuid:pk>/update/", views.assessment_result_update, name="result_update"),
]
