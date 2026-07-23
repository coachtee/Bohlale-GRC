from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone

from activity.utils import log_activity
from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView
from core.permissions import get_object_or_404_scoped, require_approver, require_editor
from notifications.utils import notify

from .forms import AuditFindingForm, AuditForm
from .models import Audit


class AuditListView(TenantListView):
    model = Audit
    template_name = "audits/list.html"
    context_object_name = "audits"


class AuditDetailView(TenantDetailView):
    model = Audit
    template_name = "audits/detail.html"
    context_object_name = "audit"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["finding_form"] = AuditFindingForm(organisation=self.request.organisation)
        return context


class AuditCreateView(TenantCreateView):
    model = Audit
    form_class = AuditForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Plan an audit", "cancel_url": reverse_lazy("audits:list")}

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.lead_auditor and self.object.lead_auditor != self.request.user:
            when = f" on {self.object.scheduled_date:%d %b %Y}" if self.object.scheduled_date else ""
            notify(
                self.request.organisation, self.object.lead_auditor,
                f"You've been assigned as lead auditor for {self.object.title}{when}.",
                category="audit", link=reverse("audits:detail", args=[self.object.pk]), send_email=True,
            )
        return response

    def get_success_url(self):
        return reverse_lazy("audits:detail", args=[self.object.pk])


class AuditUpdateView(TenantUpdateView):
    model = Audit
    form_class = AuditForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit audit"}

    def get_success_url(self):
        return reverse_lazy("audits:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("audits:detail", args=[self.object.pk])
        return context


class AuditDeleteView(TenantDeleteView):
    model = Audit
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("audits:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("audits:detail", args=[self.object.pk])
        return context


@require_editor
def audit_add_finding(request, pk):
    audit = get_object_or_404_scoped(Audit.objects, request, pk=pk)
    if request.method == "POST":
        form = AuditFindingForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            finding = form.save(commit=False)
            finding.organisation = request.organisation
            finding.audit = audit
            finding.save()
            if audit.status == "in_progress":
                audit.status = "findings_recorded"
                audit.save(update_fields=["status", "updated_at"])
            log_activity(request, "created", target=finding, description=f"Finding recorded on {audit}")
            messages.success(request, "Finding recorded.")
    return redirect("audits:detail", pk=audit.pk)


@require_approver
def audit_close(request, pk):
    audit = get_object_or_404_scoped(Audit.objects, request, pk=pk)
    if request.method == "POST":
        audit.status = "closed"
        audit.closed_at = timezone.now()
        audit.save(update_fields=["status", "closed_at", "updated_at"])
        log_activity(request, "closed", target=audit, description=f"Audit closed: {audit.title}")
        messages.success(request, "Audit closed.")
    return redirect("audits:detail", pk=audit.pk)
