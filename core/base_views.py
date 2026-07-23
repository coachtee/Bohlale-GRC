"""
Reusable tenant-scoped, role-checked, audit-logged CRUD view bases.

Nearly every module in Bohlale GRC (risks, controls, assets, suppliers,
incidents, evidence, audits, actions, reviews, documents, ...) is a
register of TenantScopedModel records with the same shape: list, view,
create, edit, delete — always scoped to `request.organisation`, always
permission-checked, always audit-logged. Rather than repeat that
plumbing 15+ times, apps subclass these bases and only specify the
model/form/template.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from activity.utils import log_activity
from core.permissions import has_role
from tenancy.constants import EDITOR_ROLES


class OrganisationRequiredMixin(LoginRequiredMixin):
    """Ensures an active organisation is selected; 404s objects that
    belong to a different tenant instead of leaking existence via 403."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if getattr(request, "organisation", None) is None:
            from django.shortcuts import redirect

            return redirect("tenancy:organisation_list")
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(OrganisationRequiredMixin):
    allowed_roles = EDITOR_ROLES

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def check_role(self):
        if not has_role(self.request, self.allowed_roles):
            raise PermissionDenied("You do not have permission to perform this action.")


class TenantQuerysetMixin(OrganisationRequiredMixin):
    """Filters get_queryset() by the active organisation for every
    list/detail/update/delete view — the core tenant-isolation guarantee."""

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organisation=self.request.organisation)


class TenantListView(TenantQuerysetMixin, ListView):
    paginate_by = 25


class TenantDetailView(TenantQuerysetMixin, DetailView):
    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except Http404:
            raise Http404("Not found.")


class AuditedFormMixin:
    """Sets organisation + created_by-style fields, saves, and writes
    an activity log entry for create/update views."""

    audit_verb = "updated"

    def form_valid(self, form):
        is_create = self.object is None
        if hasattr(form.instance, "organisation_id"):
            form.instance.organisation = self.request.organisation
        response = super().form_valid(form)
        log_activity(
            self.request,
            action=self.audit_verb if not is_create else f"created",
            target=self.object,
            description=f"{self.object.__class__.__name__} {'created' if is_create else 'updated'}: {self.object}",
        )
        return response


class TenantCreateView(RoleRequiredMixin, TenantQuerysetMixin, AuditedFormMixin, CreateView):
    audit_verb = "created"

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def post(self, request, *args, **kwargs):
        self.check_role()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.check_role()
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.request.organisation
        return kwargs


class TenantUpdateView(RoleRequiredMixin, TenantQuerysetMixin, AuditedFormMixin, UpdateView):
    audit_verb = "updated"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.check_role()
        return super().post(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.check_role()
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organisation"] = self.request.organisation
        return kwargs


class TenantDeleteView(RoleRequiredMixin, TenantQuerysetMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.check_role()
        description = f"{self.object.__class__.__name__} deleted: {self.object}"
        target_repr = str(self.object)
        response = super().post(request, *args, **kwargs)
        log_activity(request, action="deleted", target=None, description=f"{description}")
        return response
