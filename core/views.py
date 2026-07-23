from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard(request):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    from core.dashboard import build_dashboard_context

    context = build_dashboard_context(request)
    hour = context.get("hour", 12)
    if hour < 12:
        context["daypart"] = "morning"
    elif hour < 18:
        context["daypart"] = "afternoon"
    else:
        context["daypart"] = "evening"
    return render(request, "core/dashboard.html", context)


@login_required
def home(request):
    return redirect("core:dashboard")


def health(request):
    """
    Public, unauthenticated health check for uptime monitoring (free-tier
    services like UptimeRobot/healthchecks.io, or a load balancer) — see
    DEPLOYMENT.md's Monitoring section. Actually checks database
    connectivity rather than just confirming the process is alive, since
    "Gunicorn responds" and "the app actually works" are different
    questions — a DB outage is the most common real-world case this
    should catch.
    """
    from django.db import connection
    from django.http import JsonResponse

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:
        return JsonResponse({"status": "error", "detail": str(exc)}, status=503)
    return JsonResponse({"status": "ok"})
