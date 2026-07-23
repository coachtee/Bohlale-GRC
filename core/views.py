from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def dashboard(request):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    from core.dashboard import build_dashboard_context

    context = build_dashboard_context(request)
    return render(request, "core/dashboard.html", context)


@login_required
def home(request):
    return redirect("core:dashboard")


def health(request):
    from django.http import JsonResponse

    return JsonResponse({"status": "ok"})
