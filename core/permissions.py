"""
Role-based permission helpers shared across every app.

`request.organisation` and `request.membership` are set by
`tenancy.middleware.TenantMiddleware` for every authenticated request
where the user has selected/has access to an active organisation.
Platform administrators (Django superusers) bypass membership-role
checks entirely, per spec section 6.
"""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import redirect

from tenancy.constants import ADMIN_ROLES, APPROVER_ROLES, EDITOR_ROLES


def is_platform_admin(user):
    return user.is_authenticated and user.is_superuser


def has_role(request, allowed_roles):
    """True if the current user may act in the given role set on
    request.organisation (platform admins always pass)."""
    if is_platform_admin(request.user):
        return True
    membership = getattr(request, "membership", None)
    if membership is None:
        return False
    return membership.role in allowed_roles


def can_administer(request):
    return has_role(request, ADMIN_ROLES)


def can_approve(request):
    return has_role(request, APPROVER_ROLES)


def can_edit(request):
    return has_role(request, EDITOR_ROLES)


def require_organisation(view_func):
    """Ensure the request has an active organisation before proceeding."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if getattr(request, "organisation", None) is None:
            return redirect("tenancy:organisation_list")
        return view_func(request, *args, **kwargs)

    return _wrapped


def require_role(allowed_roles):
    """View decorator: 403 unless the user holds one of allowed_roles
    in the active organisation (or is a platform admin)."""

    def decorator(view_func):
        @wraps(view_func)
        @require_organisation
        def _wrapped(request, *args, **kwargs):
            if not has_role(request, allowed_roles):
                raise PermissionDenied("You do not have permission to perform this action.")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def require_editor(view_func):
    return require_role(EDITOR_ROLES)(view_func)


def require_admin(view_func):
    return require_role(ADMIN_ROLES)(view_func)


def require_approver(view_func):
    return require_role(APPROVER_ROLES)(view_func)


def get_object_or_404_scoped(queryset, request, **kwargs):
    """
    Fetch an object from a tenant-scoped queryset, filtered defensively
    by request.organisation, raising 404 (not 403) if it does not exist
    within the current tenant — this avoids confirming to an
    unauthorised tenant that a record with that ID exists elsewhere.
    """
    try:
        return queryset.filter(organisation=request.organisation).get(**kwargs)
    except queryset.model.DoesNotExist:
        raise Http404("Not found.")
