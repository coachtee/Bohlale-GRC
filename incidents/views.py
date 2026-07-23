from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from activity.utils import log_activity
from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView
from core.permissions import get_object_or_404_scoped, require_editor, require_organisation
from notifications.utils import notify
from tenancy.constants import APPROVER_ROLES
from tenancy.models import Membership

from .forms import ChangeEventForm, IncidentForm
from .models import ChangeEvent, Incident


class IncidentListView(TenantListView):
    model = Incident
    template_name = "incidents/list.html"
    context_object_name = "incidents"


class IncidentDetailView(TenantDetailView):
    model = Incident
    template_name = "incidents/detail.html"
    context_object_name = "incident"


class IncidentCreateView(TenantCreateView):
    model = Incident
    form_class = IncidentForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Report an incident", "cancel_url": reverse_lazy("incidents:list")}

    def form_valid(self, form):
        form.instance.discovered_by = self.request.user
        response = super().form_valid(form)
        link = reverse("incidents:detail", args=[self.object.pk])
        # APPROVER_ROLES (consultant, org_admin, executive) rather than
        # just admin roles: an incident with only a self-reporting
        # consultant and no separate org_admin must still reach someone
        # who can act on it — an Executive is a legitimate incident
        # decision-maker, and without this fallback such an org would
        # silently notify nobody at all.
        admins = Membership.objects.filter(
            organisation=self.request.organisation, is_active=True, role__in=APPROVER_ROLES
        ).exclude(user=self.request.user).select_related("user")
        for membership in admins:
            notify(
                self.request.organisation, membership.user,
                f"New {self.object.get_severity_display().lower()} severity incident reported: {self.object.title}",
                category="incident", link=link, send_email=True,
            )
        return response

    def get_success_url(self):
        return reverse_lazy("incidents:detail", args=[self.object.pk])


class IncidentUpdateView(TenantUpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit incident"}

    def get_success_url(self):
        return reverse_lazy("incidents:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("incidents:detail", args=[self.object.pk])
        return context


class IncidentDeleteView(TenantDeleteView):
    model = Incident
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("incidents:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("incidents:detail", args=[self.object.pk])
        return context


@require_organisation
def change_event_list(request):
    events = ChangeEvent.objects.filter(organisation=request.organisation).select_related("reported_by")
    return render(request, "incidents/change_event_list.html", {"events": events})


@require_editor
def change_event_create(request):
    if request.method == "POST":
        form = ChangeEventForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            event = form.save(commit=False)
            event.organisation = request.organisation
            event.reported_by = request.user
            event.save()
            log_activity(request, "reported", target=event, description=f"Change reported: {event.get_event_type_display()}")
            messages.success(request, "Change event recorded.")
            return redirect("incidents:change_event_detail", pk=event.pk)
    else:
        form = ChangeEventForm(organisation=request.organisation)
    return render(request, "incidents/change_event_form.html", {"form": form})


@require_organisation
def change_event_detail(request, pk):
    event = get_object_or_404_scoped(ChangeEvent.objects, request, pk=pk)
    return render(request, "incidents/change_event_detail.html", {"event": event})


@require_editor
def change_event_mark_reviewed(request, pk):
    event = get_object_or_404_scoped(ChangeEvent.objects, request, pk=pk)
    if request.method == "POST":
        event.status = "reviewed"
        event.review_notes = request.POST.get("review_notes", event.review_notes)
        event.save(update_fields=["status", "review_notes", "updated_at"])
        log_activity(request, "reviewed", target=event, description="Change event marked reviewed")
        messages.success(request, "Marked as reviewed.")
    return redirect("incidents:change_event_detail", pk=event.pk)
