from django.urls import reverse_lazy

from core.base_views import TenantCreateView, TenantDeleteView, TenantDetailView, TenantListView, TenantUpdateView

from .forms import SupplierForm
from .models import Supplier


class SupplierListView(TenantListView):
    model = Supplier
    template_name = "suppliers/list.html"
    context_object_name = "suppliers"


class SupplierDetailView(TenantDetailView):
    model = Supplier
    template_name = "suppliers/detail.html"
    context_object_name = "supplier"


class SupplierCreateView(TenantCreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Add supplier", "cancel_url": reverse_lazy("suppliers:list")}

    def get_success_url(self):
        return reverse_lazy("suppliers:detail", args=[self.object.pk])


class SupplierUpdateView(TenantUpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = "core/generic_form.html"
    extra_context = {"form_title": "Edit supplier"}

    def get_success_url(self):
        return reverse_lazy("suppliers:detail", args=[self.object.pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("suppliers:detail", args=[self.object.pk])
        return context


class SupplierDeleteView(TenantDeleteView):
    model = Supplier
    template_name = "core/generic_confirm_delete.html"
    success_url = reverse_lazy("suppliers:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = reverse_lazy("suppliers:detail", args=[self.object.pk])
        return context
