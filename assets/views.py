from django.urls import reverse_lazy

from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView

from .forms import AssetForm
from .models import Asset


class AssetListView(TenantListView):
    model = Asset
    template_name = "assets/list.html"
    context_object_name = "assets"


class AssetDetailView(TenantDetailView):
    model = Asset
    template_name = "assets/detail.html"
    context_object_name = "asset"


class AssetCreateView(TenantCreateView):
    model = Asset
    form_class = AssetForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Add asset", "cancel_url": reverse_lazy("assets:list")}

    def get_success_url(self):
        return reverse_lazy("assets:detail", args=[self.object.pk])


class AssetUpdateView(TenantUpdateView):
    model = Asset
    form_class = AssetForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit asset"}

    def get_success_url(self):
        return reverse_lazy("assets:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("assets:detail", args=[self.object.pk])
        return context


class AssetDeleteView(TenantDeleteView):
    model = Asset
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("assets:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("assets:detail", args=[self.object.pk])
        return context
