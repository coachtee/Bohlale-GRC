"""
Scheduled overdue/due-soon scan (spec §36). Intended to run from cron
(see DEPLOYMENT.md) — no Celery/Redis required, per spec §39. Creates
in-app (+ optional email) notifications for: overdue corrective
actions, documents due/overdue for review, evidence expiring soon,
risks past their treatment due date, and upcoming/overdue audit dates.
Deduplicates against already-unread notifications for the same object
so re-running this daily doesn't spam recipients.
"""

import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from actions.models import STATUS_CLOSED, CorrectiveAction
from audits.models import Audit
from documents.models import STATUS_ARCHIVED, Document
from evidence.models import Evidence
from notifications.models import Notification
from notifications.utils import notify
from risks.models import Risk
from tenancy.models import Membership


def _admins_for(organisation):
    return [
        m.user
        for m in Membership.objects.filter(
            organisation=organisation, is_active=True, role__in=["org_admin", "consultant"]
        ).select_related("user")
    ]


def _already_notified(recipient, link):
    return Notification.objects.filter(recipient=recipient, link=link, is_read=False).exists()


class Command(BaseCommand):
    help = "Scan for overdue actions, document reviews, evidence expiry and risk reviews, and notify."

    def handle(self, *args, **options):
        created = 0
        created += self._scan_actions()
        created += self._scan_documents()
        created += self._scan_evidence()
        created += self._scan_risks()
        created += self._scan_audits()
        self.stdout.write(self.style.SUCCESS(f"Created {created} notification(s)."))

    def _notify_owner_or_admins(self, organisation, owner, message, category, link):
        recipients = [owner] if owner else _admins_for(organisation)
        sent = 0
        for recipient in recipients:
            if recipient and not _already_notified(recipient, link):
                notify(organisation, recipient, message, category=category, link=link, send_email=True)
                sent += 1
        return sent

    def _scan_actions(self):
        today = timezone.now().date()
        count = 0
        for action in CorrectiveAction.objects.filter(due_date__lt=today).exclude(status=STATUS_CLOSED):
            link = f"/actions/{action.pk}/"
            count += self._notify_owner_or_admins(
                action.organisation, action.owner,
                f"Corrective action overdue: {action.finding_description[:80]}",
                "action_overdue", link,
            )
        return count

    def _scan_documents(self):
        today = timezone.now().date()
        count = 0
        for document in Document.objects.filter(next_review_date__isnull=False).exclude(status=STATUS_ARCHIVED):
            if document.next_review_date > today and not document.is_review_due_soon:
                continue
            link = f"/documents/{document.pk}/"
            verb = "overdue for review" if document.next_review_date < today else "due for review soon"
            count += self._notify_owner_or_admins(
                document.organisation, document.owner,
                f"'{document.title}' is {verb} ({document.next_review_date}).",
                "document_review", link,
            )
        return count

    def _scan_evidence(self):
        count = 0
        for evidence in Evidence.objects.filter(expiry_date__isnull=False):
            if not (evidence.is_expired or evidence.is_expiring_soon):
                continue
            link = f"/evidence/{evidence.pk}/"
            verb = "has expired" if evidence.is_expired else "is expiring soon"
            count += self._notify_owner_or_admins(
                evidence.organisation, evidence.owner,
                f"Evidence '{evidence.name}' {verb} ({evidence.expiry_date}).",
                "evidence_expiry", link,
            )
        return count

    def _scan_risks(self):
        today = timezone.now().date()
        count = 0
        for risk in Risk.objects.filter(due_date__lt=today).exclude(status__in=["closed", "accepted"]):
            link = f"/risks/{risk.pk}/"
            count += self._notify_owner_or_admins(
                risk.organisation, risk.owner,
                f"Risk treatment overdue: {risk.title}",
                "risk_review", link,
            )
        return count

    def _scan_audits(self):
        today = timezone.now().date()
        soon = today + datetime.timedelta(days=7)
        count = 0
        for audit in Audit.objects.filter(
            scheduled_date__isnull=False, scheduled_date__lte=soon, status="planned"
        ):
            link = f"/audits/{audit.pk}/"
            verb = "is overdue to begin" if audit.scheduled_date < today else "is coming up soon"
            count += self._notify_owner_or_admins(
                audit.organisation, audit.lead_auditor,
                f"Audit '{audit.title}' {verb} ({audit.scheduled_date}).",
                "audit_date", link,
            )
        return count
