from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("", views.document_list, name="list"),
    path("new/", views.document_create, name="create"),
    path("generate/<uuid:step_id>/", views.generate_for_step, name="generate_for_step"),
    path("<uuid:pk>/", views.document_detail, name="detail"),
    path("<uuid:pk>/edit/", views.document_edit, name="edit"),
    path("<uuid:pk>/submit-review/", views.document_submit_review, name="submit_review"),
    path("<uuid:pk>/submit-approval/", views.document_submit_approval, name="submit_approval"),
    path("<uuid:pk>/publish/", views.document_publish, name="publish"),
]
