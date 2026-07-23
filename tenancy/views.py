from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from activity.utils import log_activity
from core.permissions import can_administer

from .forms import InviteMemberForm, OrganisationForm
from .middleware import set_active_organisation
from .models import Membership, Organisation, OrganisationInvite


@login_required
def organisation_list(request):
    """'My Organisations' — the consultant workspace / org picker."""
    orgs = request.accessible_organisations.order_by("name")
    memberships = {
        m.organisation_id: m
        for m in Membership.objects.filter(user=request.user, is_active=True)
    }
    rows = []
    for org in orgs:
        rows.append({"org": org, "membership": memberships.get(org.id)})
    return render(request, "tenancy/organisation_list.html", {"rows": rows})


@login_required
def organisation_create(request):
    if request.method == "POST":
        form = OrganisationForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save(commit=False)
            org.created_by = request.user
            org.save()
            Membership.objects.create(
                organisation=org,
                user=request.user,
                role="org_admin",
                date_joined=timezone.now(),
            )
            set_active_organisation(request, org)
            log_activity(
                request,
                action="created",
                target=org,
                description=f"Organisation created: {org.name}",
                organisation=org,
            )
            messages.success(request, f"{org.name} has been created.")
            return redirect("journeys:onboarding_goal")
    else:
        form = OrganisationForm()
    return render(request, "tenancy/organisation_form.html", {"form": form})


@login_required
def organisation_switch(request, pk):
    org = request.accessible_organisations.filter(pk=pk).first()
    if org is None:
        raise Http404("Organisation not found.")
    set_active_organisation(request, org)
    messages.info(request, f"Switched to {org.name}.")
    next_url = request.GET.get("next") or reverse("core:dashboard")
    return redirect(next_url)


@login_required
def member_list(request):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    members = Membership.objects.filter(
        organisation=request.organisation, is_active=True
    ).select_related("user").order_by("user__first_name")
    invites = OrganisationInvite.objects.filter(
        organisation=request.organisation, accepted=False
    )
    return render(
        request,
        "tenancy/member_list.html",
        {"members": members, "invites": invites, "can_manage": can_administer(request)},
    )


@login_required
def invite_member(request):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    if not can_administer(request):
        raise PermissionDenied("Only organisation administrators can invite members.")
    if request.method == "POST":
        form = InviteMemberForm(request.POST)
        if form.is_valid():
            invite = form.save(commit=False)
            invite.organisation = request.organisation
            invite.invited_by = request.user
            invite.save()
            log_activity(
                request,
                action="invited",
                target=invite,
                description=f"Invited {invite.email} as {invite.get_role_display()}",
            )
            messages.success(request, f"Invitation sent to {invite.email}.")
            return redirect("tenancy:member_list")
    else:
        form = InviteMemberForm()
    return render(request, "tenancy/invite_form.html", {"form": form})


@login_required
def revoke_invite(request, pk):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    if not can_administer(request):
        raise PermissionDenied("Only organisation administrators can manage invites.")
    invite = get_object_or_404(OrganisationInvite, pk=pk, organisation=request.organisation)
    if request.method == "POST":
        invite.delete()
        messages.info(request, f"Invitation to {invite.email} revoked.")
    return redirect("tenancy:member_list")


@login_required
def accept_invite(request, token):
    invite = get_object_or_404(OrganisationInvite, token=token, accepted=False)
    if request.user.email.lower() != invite.email.lower() and not request.user.is_superuser:
        messages.error(request, "This invitation was sent to a different email address.")
        return redirect("core:dashboard")
    membership, created = Membership.objects.get_or_create(
        organisation=invite.organisation,
        user=request.user,
        defaults={"role": invite.role, "invited_by": invite.invited_by},
    )
    invite.accepted = True
    invite.accepted_at = timezone.now()
    invite.save(update_fields=["accepted", "accepted_at"])
    set_active_organisation(request, invite.organisation)
    log_activity(
        request,
        action="joined",
        target=membership,
        description=f"{request.user} joined {invite.organisation} as {membership.get_role_display()}",
        organisation=invite.organisation,
    )
    messages.success(request, f"You have joined {invite.organisation.name}.")
    return redirect("core:dashboard")
