from django.urls import path

from . import views

app_name = "audits"

urlpatterns = [
    path("", views.AuditListView.as_view(), name="list"),
    path("new/", views.AuditCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.AuditDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.AuditUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/delete/", views.AuditDeleteView.as_view(), name="delete"),
    path("<uuid:pk>/findings/add/", views.audit_add_finding, name="add_finding"),
    path("<uuid:pk>/close/", views.audit_close, name="close"),
]
