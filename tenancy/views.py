from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from activity.utils import log_activity
from core.permissions import can_administer

from .constants import ADMIN_ROLES, ROLE_CHOICES
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
        {"members": members, "invites": invites, "can_manage": can_administer(request), "role_choices": ROLE_CHOICES},
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


def _active_admin_count(organisation, exclude_membership_id=None):
    qs = Membership.objects.filter(organisation=organisation, is_active=True, role__in=ADMIN_ROLES)
    if exclude_membership_id:
        qs = qs.exclude(pk=exclude_membership_id)
    return qs.count()


@login_required
def member_update_role(request, pk):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    if not can_administer(request):
        raise PermissionDenied("Only organisation administrators can change member roles.")
    membership = get_object_or_404(Membership, pk=pk, organisation=request.organisation)
    if request.method == "POST":
        new_role = request.POST.get("role")
        if new_role not in dict(ROLE_CHOICES):
            messages.error(request, "Unknown role.")
            return redirect("tenancy:member_list")
        if membership.role in ADMIN_ROLES and new_role not in ADMIN_ROLES and _active_admin_count(request.organisation, exclude_membership_id=membership.pk) == 0:
            messages.error(request, "Cannot change this member's role — they are the organisation's last administrator.")
            return redirect("tenancy:member_list")
        old_role = membership.get_role_display()
        membership.role = new_role
        membership.save(update_fields=["role", "updated_at"])
        log_activity(
            request, action="role_changed", target=membership,
            description=f"{membership.user}'s role changed from {old_role} to {membership.get_role_display()}",
        )
        messages.success(request, f"{membership.user}'s role updated to {membership.get_role_display()}.")
    return redirect("tenancy:member_list")


@login_required
def member_remove(request, pk):
    if request.organisation is None:
        return redirect("tenancy:organisation_list")
    if not can_administer(request):
        raise PermissionDenied("Only organisation administrators can remove members.")
    membership = get_object_or_404(Membership, pk=pk, organisation=request.organisation)
    if request.method == "POST":
        if membership.role in ADMIN_ROLES and _active_admin_count(request.organisation, exclude_membership_id=membership.pk) == 0:
            messages.error(request, "Cannot remove this member — they are the organisation's last administrator.")
            return redirect("tenancy:member_list")
        if membership.user_id == request.user.id:
            messages.error(request, "You cannot remove your own membership.")
            return redirect("tenancy:member_list")
        # Soft-deactivate rather than delete: preserves the immutable
        # audit trail and every historical owner/actor FK pointing at
        # this membership's user (spec §6/§45).
        membership.is_active = False
        membership.save(update_fields=["is_active", "updated_at"])
        log_activity(
            request, action="removed", target=membership,
            description=f"{membership.user} removed from {request.organisation.name}",
        )
        messages.success(request, f"{membership.user} has been removed from this organisation.")
    return redirect("tenancy:member_list")


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
