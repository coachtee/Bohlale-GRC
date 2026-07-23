from .models import Membership, Organisation

SESSION_KEY = "active_organisation_id"


class TenantMiddleware:
    """
    Resolves the active organisation (tenant) for the request.

    Sets:
      request.organisation — the active Organisation, or None.
      request.membership   — the user's Membership in that organisation
                              (role, etc.), or None for platform admins
                              who are not themselves members.
      request.accessible_organisations — queryset of orgs this user may
                              switch into (their memberships; all orgs
                              for platform admins).

    Tenant isolation is enforced downstream by every view/queryset
    filtering on request.organisation — this middleware only ever
    narrows access to organisations the user is actually authorised
    for, it never widens it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.organisation = None
        request.membership = None
        request.accessible_organisations = Organisation.objects.none()

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            if user.is_superuser:
                accessible = Organisation.objects.filter(is_active=True)
            else:
                accessible = Organisation.objects.filter(
                    memberships__user=user, memberships__is_active=True, is_active=True
                ).distinct()
            request.accessible_organisations = accessible

            active_id = request.session.get(SESSION_KEY)
            org = None
            if active_id:
                org = accessible.filter(pk=active_id).first()
            if org is None and accessible.count() == 1:
                org = accessible.first()
            if org is not None:
                request.organisation = org
                request.session[SESSION_KEY] = str(org.pk)
                request.membership = Membership.objects.filter(
                    organisation=org, user=user
                ).first()

        return self.get_response(request)


def set_active_organisation(request, organisation):
    request.session[SESSION_KEY] = str(organisation.pk)
