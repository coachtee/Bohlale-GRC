from django.urls import reverse_lazy

from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView
from core.permissions import get_object_or_404_scoped, require_organisation
from core.protected_media import serve_tenant_file

from .forms import EvidenceForm
from .models import Evidence


@require_organisation
def evidence_download(request, pk):
    evidence = get_object_or_404_scoped(Evidence.objects, request, pk=pk)
    return serve_tenant_file(evidence, "file")


class EvidenceListView(TenantListView):
    model = Evidence
    template_name = "evidence/list.html"
    context_object_name = "evidence_items"


class EvidenceDetailView(TenantDetailView):
    model = Evidence
    template_name = "evidence/detail.html"
    context_object_name = "evidence"


class EvidenceCreateView(TenantCreateView):
    model = Evidence
    form_class = EvidenceForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Upload evidence", "cancel_url": reverse_lazy("evidence:list")}

    def get_success_url(self):
        return reverse_lazy("evidence:detail", args=[self.object.pk])

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)


class EvidenceUpdateView(TenantUpdateView):
    model = Evidence
    form_class = EvidenceForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit evidence"}

    def get_success_url(self):
        return reverse_lazy("evidence:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("evidence:detail", args=[self.object.pk])
        return context


class EvidenceDeleteView(TenantDeleteView):
    model = Evidence
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("evidence:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("evidence:detail", args=[self.object.pk])
        return context
