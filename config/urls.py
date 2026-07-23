"""
URL configuration for the Bohlale GRC project.

Each business module owns its own `urls.py` (namespaced by app_label)
and is included here under a URL prefix that matches the primary
sidebar navigation (see templates/core/_sidebar.html).
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("organisations/", include("tenancy.urls")),
    path("activity/", include("activity.urls")),
    path("notifications/", include("notifications.urls")),
    path("knowledge/", include("knowledge.urls")),
    path("ai/", include("ai.urls")),
    path("frameworks/", include("frameworks.urls")),
    path("journey/", include("journeys.urls")),
    path("documents/", include("documents.urls")),
    path("approvals/", include("approvals.urls")),
    path("risks/", include("risks.urls")),
    path("controls/", include("controls.urls")),
    path("evidence/", include("evidence.urls")),
    path("assessments/", include("assessments.urls")),
    path("assets/", include("assets.urls")),
    path("suppliers/", include("suppliers.urls")),
    path("incidents/", include("incidents.urls")),
    path("registers/", include("registers.urls")),
    path("audits/", include("audits.urls")),
    path("actions/", include("actions.urls")),
    path("reviews/", include("reviews.urls")),
    path("reports/", include("reports.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "core.error_views.error_403"
handler404 = "core.error_views.error_404"
handler500 = "core.error_views.error_500"
