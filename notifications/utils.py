import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("bohlale")


def notify(organisation, recipient, message, category="general", link="", send_email=False):
    """Create an in-app notification, optionally also emailing it."""
    from .models import Notification

    note = Notification.objects.create(
        organisation=organisation,
        recipient=recipient,
        category=category,
        message=message,
        link=link,
    )
    if send_email and recipient.email:
        try:
            send_mail(
                subject=f"Bohlale GRC — {message[:100]}",
                message=f"{message}\n\nOpen Bohlale GRC to review.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient.email],
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to send notification email to %s", recipient.email)
    return note
