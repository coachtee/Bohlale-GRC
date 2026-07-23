from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone

from activity.utils import log_activity
from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView
from core.permissions import can_approve, get_object_or_404_scoped, require_approver, require_editor

from .forms import CorrectiveActionForm
from .models import STATUS_CLOSED, CorrectiveAction


class CorrectiveActionListView(TenantListView):
    model = CorrectiveAction
    template_name = "actions/list.html"
    context_object_name = "actions"

    def get_queryset(self):
        return super().get_queryset().select_related("owner")


class CorrectiveActionDetailView(TenantDetailView):
    model = CorrectiveAction
    template_name = "actions/detail.html"
    context_object_name = "action"


class CorrectiveActionCreateView(TenantCreateView):
    model = CorrectiveAction
    form_class = CorrectiveActionForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Create corrective action", "cancel_url": reverse_lazy("actions:list")}

    def get_success_url(self):
        return reverse_lazy("actions:detail", args=[self.object.pk])


class CorrectiveActionUpdateView(TenantUpdateView):
    model = CorrectiveAction
    form_class = CorrectiveActionForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit corrective action"}

    def get_success_url(self):
        return reverse_lazy("actions:detail", args=[self.object.pk])

    def form_valid(self, form):
        closing_now = form.instance.status == STATUS_CLOSED and not form.instance.closed_at
        if closing_now:
            # Closing a corrective action is an independent-verification
            # sign-off (spec §31), not a routine edit — require Approver
            # level even though the plain edit form is otherwise open to
            # any Editor-level role. Use the dedicated `action_verify_close`
            # view for the normal closure flow; this only guards against
            # bypassing it via this form.
            if not can_approve(self.request):
                raise PermissionDenied(
                    "Only an Executive/Approver, Organisation Administrator or Consultant may close a corrective action."
                )
            form.instance.closed_at = timezone.now()
            form.instance.verified_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("actions:detail", args=[self.object.pk])
        return context


class CorrectiveActionDeleteView(TenantDeleteView):
    model = CorrectiveAction
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("actions:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("actions:detail", args=[self.object.pk])
        return context


def _create_from_source(request, source, model_cls, pk, description_attr="description"):
    record = get_object_or_404_scoped(model_cls.objects, request, pk=pk)
    if request.method == "POST":
        form = CorrectiveActionForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            action = form.save(commit=False)
            action.organisation = request.organisation
            action.source = source
            action.content_type = ContentType.objects.get_for_model(model_cls)
            action.object_id = str(record.pk)
            action.save()
            log_activity(request, "created", target=action, description=f"Corrective action created from {source}")
            messages.success(request, "Corrective action created.")
            return redirect("actions:detail", pk=action.pk)
    else:
        initial = {"source": source, "finding_description": getattr(record, description_attr, str(record))}
        form = CorrectiveActionForm(organisation=request.organisation, initial=initial)
    return render(
        request, "core/generic_form.html",
        {"form": form, "form_title": "Create corrective action", "cancel_url": reverse_lazy("actions:list")},
    )


@require_editor
def create_from_incident(request, pk):
    from incidents.models import Incident

    return _create_from_source(request, "incident", Incident, pk, description_attr="description")


@require_editor
def create_from_finding(request, pk):
    from audits.models import AuditFinding

    return _create_from_source(request, "audit", AuditFinding, pk, description_attr="description")


@require_editor
def create_from_review(request, pk):
    from reviews.models import ManagementReview

    return _create_from_source(request, "management_review", ManagementReview, pk, description_attr="decisions")


@require_approver
def action_verify_close(request, pk):
    action = get_object_or_404_scoped(CorrectiveAction.objects, request, pk=pk)
    if request.method == "POST":
        action.status = STATUS_CLOSED
        action.verified_by = request.user
        action.verification_notes = request.POST.get("verification_notes", action.verification_notes)
        action.closed_at = timezone.now()
        action.save(update_fields=["status", "verified_by", "verification_notes", "closed_at", "updated_at"])
        log_activity(request, "closed", target=action, description=f"Corrective action verified and closed: {action}")
        messages.success(request, "Corrective action verified and closed.")
    return redirect("actions:detail", pk=action.pk)
