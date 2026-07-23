from django.contrib.contenttypes.models import ContentType


def _client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_activity(request, action, target=None, description="", organisation=None, metadata=None, actor=None):
    """
    Write one immutable audit trail entry.

    `request` may be a real HttpRequest (actor/organisation/IP are
    derived from it) or None for system/management-command actions, in
    which case pass `organisation` explicitly if applicable and,
    optionally, `actor` to attribute the entry to a specific user (e.g.
    from a management command seeding demo data) rather than "System".
    """
    from .models import AuditLog

    org = organisation
    ip = None
    if request is not None:
        actor = getattr(request, "user", None)
        if actor is not None and not actor.is_authenticated:
            actor = None
        org = org or getattr(request, "organisation", None)
        ip = _client_ip(request)

    content_type = None
    object_id = None
    if target is not None:
        content_type = ContentType.objects.get_for_model(target.__class__)
        object_id = str(target.pk)

    return AuditLog.objects.create(
        organisation=org,
        actor=actor,
        action=action,
        description=description[:500],
        content_type=content_type,
        object_id=object_id,
        ip_address=ip,
        metadata=metadata or {},
    )
