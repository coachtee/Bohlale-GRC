from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from core.ratelimit import rate_limit

from .forms import EmailAuthenticationForm, ProfileForm


@method_decorator(rate_limit("login", limit=10, window_seconds=300, methods=["POST"]), name="dispatch")
class BohlaleLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class BohlaleLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def export_my_data(request):
    """
    Self-service personal-information export (POPIA §23 "right of
    access" / technical readiness — see POPIA_READINESS.md). Covers the
    account-level personal information Bohlale GRC holds directly about
    this user. Organisation-level compliance records they authored
    (documents, risk entries, audit findings, etc.) remain part of the
    relevant organisation's own business/audit records and are exported
    separately by an organisation administrator via that organisation's
    reports — see POPIA_READINESS.md for why those aren't included here.
    """
    user = request.user
    memberships = [
        {
            "organisation": m.organisation.name,
            "role": m.get_role_display(),
            "is_active": m.is_active,
            "date_joined": m.date_joined.isoformat(),
        }
        for m in user.memberships.select_related("organisation")
    ]
    data = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "job_title": user.job_title,
        "phone_number": user.phone_number,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "organisation_memberships": memberships,
    }
    response = JsonResponse(data, json_dumps_params={"indent": 2})
    response["Content-Disposition"] = "attachment; filename=\"my-bohlale-grc-data.json\""
    return response


@login_required
def deactivate_account(request):
    """
    Self-service account deactivation. The account is deactivated
    (login blocked) rather than hard-deleted, because this user's id is
    referenced throughout every organisation they belong to as an
    immutable audit-trail actor, document owner/author/approver, risk
    owner, etc. — hard-deleting the row would corrupt that history for
    every organisation, not just remove this user's own data. See
    POPIA_READINESS.md for the documented purge/anonymisation procedure
    an organisation administrator or platform administrator can run when
    a full erasure is genuinely required (e.g. a completed POPIA
    deletion request).
    """
    if request.method == "POST":
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        logout(request)
        messages.info(request, "Your account has been deactivated and you have been logged out.")
        return redirect("accounts:login")
    return render(request, "accounts/deactivate_confirm.html")
