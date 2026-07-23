from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from activity.utils import log_activity
from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView
from core.permissions import get_object_or_404_scoped, require_editor, require_organisation
from frameworks.models import Framework

from .forms import ControlForm, SoAEntryForm
from .models import Control, SoAEntry
from .services import ensure_soa_entries, soa_coverage


class ControlListView(TenantListView):
    model = Control
    template_name = "controls/list.html"
    context_object_name = "controls"

    def get_queryset(self):
        return super().get_queryset().select_related("owner").prefetch_related("framework_requirements__framework")


class ControlDetailView(TenantDetailView):
    model = Control
    template_name = "controls/detail.html"
    context_object_name = "control"


class ControlCreateView(TenantCreateView):
    model = Control
    form_class = ControlForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Add control", "cancel_url": reverse_lazy("controls:list")}

    def get_success_url(self):
        return reverse_lazy("controls:detail", args=[self.object.pk])


class ControlUpdateView(TenantUpdateView):
    model = Control
    form_class = ControlForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit control"}

    def get_success_url(self):
        return reverse_lazy("controls:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("controls:detail", args=[self.object.pk])
        return context


class ControlDeleteView(TenantDeleteView):
    model = Control
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("controls:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("controls:detail", args=[self.object.pk])
        return context


def _adopted_frameworks(request):
    return Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=request.organisation),
        adoptions__organisation=request.organisation,
    ).distinct()


@require_organisation
def soa_view(request):
    frameworks = _adopted_frameworks(request)
    framework_id = request.GET.get("framework")
    framework = frameworks.filter(pk=framework_id).first() if framework_id else frameworks.first()
    if framework is None:
        return render(request, "controls/soa_empty.html", {})

    ensure_soa_entries(request.organisation, framework)
    entries = SoAEntry.objects.filter(organisation=request.organisation, framework=framework).select_related(
        "control", "control__owner"
    )
    return render(
        request,
        "controls/soa.html",
        {
            "frameworks": frameworks,
            "framework": framework,
            "entries": entries,
            "coverage": soa_coverage(request.organisation, framework),
        },
    )


@require_editor
def soa_entry_update(request, pk):
    entry = get_object_or_404_scoped(SoAEntry.objects, request, pk=pk)
    if request.method == "POST":
        form = SoAEntryForm(request.POST)
        if form.is_valid():
            entry.applicable = form.cleaned_data["applicable"]
            entry.justification = form.cleaned_data["justification"]
            entry.save(update_fields=["applicable", "justification"])
            entry.control.implementation_status = form.cleaned_data["implementation_status"]
            entry.control.save(update_fields=["implementation_status", "updated_at"])
            log_activity(request, "updated", target=entry, description=f"SoA entry updated: {entry.control.name}")
            messages.success(request, f"'{entry.control.name}' updated.")
    return redirect(f"{reverse_lazy('controls:soa')}?framework={entry.framework_id}")


@require_organisation
def soa_export_csv(request):
    import csv

    frameworks = _adopted_frameworks(request)
    framework_id = request.GET.get("framework")
    framework = frameworks.filter(pk=framework_id).first() if framework_id else frameworks.first()
    if framework is None:
        return HttpResponse("No framework selected.", status=404)
    entries = SoAEntry.objects.filter(organisation=request.organisation, framework=framework).select_related("control")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="soa_{framework.code}.csv"'
    writer = csv.writer(response)
    writer.writerow(["Control", "Applicable", "Justification", "Implementation Status", "Owner"])
    for entry in entries:
        writer.writerow([
            entry.control.name, "Yes" if entry.applicable else "No", entry.justification,
            entry.control.get_implementation_status_display(), entry.control.owner or "",
        ])
    return response
