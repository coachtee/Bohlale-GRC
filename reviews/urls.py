from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    path("", views.review_list, name="list"),
    path("new/", views.review_create, name="create"),
    path("<uuid:pk>/", views.review_detail, name="detail"),
    path("<uuid:pk>/download/", views.review_download, name="download"),
    path("<uuid:pk>/complete/", views.review_complete, name="complete"),
    path("inputs/<int:pk>/update/", views.input_record_update, name="input_record_update"),
]
