from django.urls import path

from . import views

app_name = "frameworks"

urlpatterns = [
    path("", views.framework_list, name="list"),
    path("studio/", views.import_list, name="import_list"),
    path("studio/new/", views.import_create, name="import_create"),
    path("studio/<uuid:pk>/analyse/", views.import_analyse, name="import_analyse"),
    path("studio/<uuid:pk>/review/", views.import_review, name="import_review"),
    path("studio/<uuid:pk>/publish/", views.import_publish, name="import_publish"),
    path("<uuid:pk>/", views.framework_detail, name="detail"),
    path("<uuid:pk>/adopt/", views.framework_adopt, name="adopt"),
    path("requirements/<uuid:pk>/status/", views.requirement_status_update, name="requirement_status_update"),
]
