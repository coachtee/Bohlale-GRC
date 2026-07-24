from django.urls import path

from . import views

app_name = "frameworks"

urlpatterns = [
    path("", views.framework_list, name="list"),
    path("new/", views.framework_create, name="create"),
    path("studio/", views.import_list, name="import_list"),
    path("studio/new/", views.import_create, name="import_create"),
    path("studio/<uuid:pk>/analyse/", views.import_analyse, name="import_analyse"),
    path("studio/<uuid:pk>/review/", views.import_review, name="import_review"),
    path("studio/<uuid:pk>/publish/", views.import_publish, name="import_publish"),
    path("<uuid:pk>/", views.framework_detail, name="detail"),
    path("<uuid:pk>/adopt/", views.framework_adopt, name="adopt"),
    path("<uuid:pk>/domains/new/", views.domain_create, name="domain_create"),
    path("<uuid:pk>/domains/<uuid:domain_pk>/requirements/new/", views.requirement_create, name="requirement_create"),
    path("<uuid:pk>/ciso-assist/", views.ciso_assist, name="ciso_assist"),
    path("requirements/<uuid:pk>/status/", views.requirement_status_update, name="requirement_status_update"),
]
