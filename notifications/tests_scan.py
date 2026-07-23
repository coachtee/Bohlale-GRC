import datetime

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from actions.models import CorrectiveAction
from audits.models import Audit
from documents.models import Document
from evidence.models import Evidence
from risks.models import Risk
from tenancy.models import Membership, Organisation

from .models import Notification


class ScanOverdueTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.owner = User.objects.create_user(email="owner@example.com", password="x")
        Membership.objects.create(organisation=self.org, user=self.owner, role="contributor")
        self.today = timezone.now().date()

    def test_overdue_action_notifies_owner(self):
        CorrectiveAction.objects.create(
            organisation=self.org, finding_description="Fix it", owner=self.owner,
            due_date=self.today - datetime.timedelta(days=2), status="open",
        )
        call_command("scan_overdue")
        self.assertTrue(Notification.objects.filter(recipient=self.owner, category="action_overdue").exists())

    def test_scan_is_idempotent_no_duplicate_unread_notifications(self):
        CorrectiveAction.objects.create(
            organisation=self.org, finding_description="Fix it", owner=self.owner,
            due_date=self.today - datetime.timedelta(days=2), status="open",
        )
        call_command("scan_overdue")
        call_command("scan_overdue")
        self.assertEqual(Notification.objects.filter(recipient=self.owner, category="action_overdue").count(), 1)

    def test_document_review_due_soon_notifies_owner(self):
        Document.objects.create(
            organisation=self.org, title="Policy", owner=self.owner,
            next_review_date=self.today + datetime.timedelta(days=5),
        )
        call_command("scan_overdue")
        self.assertTrue(Notification.objects.filter(recipient=self.owner, category="document_review").exists())

    def test_evidence_expiring_notifies_owner(self):
        Evidence.objects.create(
            organisation=self.org, name="Cert", owner=self.owner,
            expiry_date=self.today + datetime.timedelta(days=10),
        )
        call_command("scan_overdue")
        self.assertTrue(Notification.objects.filter(recipient=self.owner, category="evidence_expiry").exists())

    def test_overdue_risk_notifies_owner(self):
        Risk.objects.create(
            organisation=self.org, title="Unpatched server", likelihood=3, impact=3, owner=self.owner,
            due_date=self.today - datetime.timedelta(days=1), status="open",
        )
        call_command("scan_overdue")
        self.assertTrue(Notification.objects.filter(recipient=self.owner, category="risk_review").exists())

    def test_audit_due_soon_notifies_lead_auditor(self):
        Audit.objects.create(
            organisation=self.org, title="Q3 Internal Audit", lead_auditor=self.owner,
            scheduled_date=self.today + datetime.timedelta(days=3), status="planned",
        )
        call_command("scan_overdue")
        self.assertTrue(Notification.objects.filter(recipient=self.owner, category="audit_date").exists())

    def test_no_owner_falls_back_to_org_admins(self):
        admin = User.objects.create_user(email="admin@example.com", password="x")
        Membership.objects.create(organisation=self.org, user=admin, role="org_admin")
        CorrectiveAction.objects.create(
            organisation=self.org, finding_description="Fix it", owner=None,
            due_date=self.today - datetime.timedelta(days=2), status="open",
        )
        call_command("scan_overdue")
        self.assertTrue(Notification.objects.filter(recipient=admin, category="action_overdue").exists())
