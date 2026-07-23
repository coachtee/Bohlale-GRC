from django.urls import reverse_lazy

from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView

from .forms import RiskForm
from .models import Risk


class RiskListView(TenantListView):
    model = Risk
    template_name = "risks/list.html"
    context_object_name = "risks"

    def get_queryset(self):
        qs = super().get_queryset().select_related("owner")
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs


class RiskDetailView(TenantDetailView):
    model = Risk
    template_name = "risks/detail.html"
    context_object_name = "risk"


class RiskCreateView(TenantCreateView):
    model = Risk
    form_class = RiskForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Add risk", "cancel_url": reverse_lazy("risks:list")}

    def get_success_url(self):
        return reverse_lazy("risks:detail", args=[self.object.pk])


class RiskUpdateView(TenantUpdateView):
    model = Risk
    form_class = RiskForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit risk"}

    def get_success_url(self):
        return reverse_lazy("risks:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("risks:detail", args=[self.object.pk])
        return context


class RiskDeleteView(TenantDeleteView):
    model = Risk
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("risks:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("risks:detail", args=[self.object.pk])
        return context
