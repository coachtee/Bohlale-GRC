def notification_counts(request):
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated or getattr(request, "organisation", None) is None:
        return {"unread_notification_count": 0, "recent_notifications": []}
    from .models import Notification

    qs = Notification.objects.filter(recipient=user, organisation=request.organisation)
    return {
        "unread_notification_count": qs.filter(is_read=False).count(),
        "recent_notifications": qs[:8],
    }
