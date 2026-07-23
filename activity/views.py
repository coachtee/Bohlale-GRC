from django.shortcuts import render

from core.permissions import require_organisation
from .models import AuditLog


@require_organisation
def activity_feed(request):
    logs = AuditLog.objects.filter(organisation=request.organisation).select_related(
        "actor", "content_type"
    )[:200]
    return render(request, "activity/feed.html", {"logs": logs})
