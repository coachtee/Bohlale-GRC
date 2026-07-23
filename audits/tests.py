from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification
from tenancy.models import Membership, Organisation

from .models import Audit, AuditFinding


class AuditModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_reference_code_assigned(self):
        audit = Audit.objects.create(organisation=self.org, title="Annual ISMS Internal Audit")
        self.assertEqual(audit.reference_code, "AUD-0001")

    def test_open_major_findings_count(self):
        audit = Audit.objects.create(organisation=self.org, title="Audit")
        AuditFinding.objects.create(organisation=self.org, audit=audit, description="x", severity="major_nonconformity")
        AuditFinding.objects.create(
            organisation=self.org, audit=audit, description="y", severity="major_nonconformity", status="closed"
        )
        self.assertEqual(audit.open_major_findings_count, 1)


class AuditFlowTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="internal_auditor")
        self.client.login(email="a@example.com", password="StrongPass123!")
        self.audit = Audit.objects.create(organisation=self.org, title="Audit", status="in_progress")

    def test_add_finding_moves_status_to_findings_recorded(self):
        response = self.client.post(
            reverse("audits:add_finding", args=[self.audit.pk]),
            {"description": "Access reviews not evidenced", "severity": "minor_nonconformity", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "findings_recorded")
        self.assertEqual(self.audit.findings.count(), 1)

    def test_close_audit(self):
        response = self.client.post(reverse("audits:close", args=[self.audit.pk]))
        self.assertEqual(response.status_code, 302)
        self.audit.refresh_from_db()
        self.assertEqual(self.audit.status, "closed")
        self.assertIsNotNone(self.audit.closed_at)

    def test_assigning_lead_auditor_on_create_notifies_them(self):
        auditor = User.objects.create_user(email="auditor@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=auditor, role="internal_auditor")
        response = self.client.post(
            reverse("audits:create"),
            {"title": "Q3 Internal Audit", "audit_type": "internal", "status": "planned", "lead_auditor": auditor.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(recipient=auditor, category="audit").exists())


class AuditTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.audit_b = Audit.objects.create(organisation=self.org_b, title="Org B secret audit")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_audit(self):
        response = self.client.get(reverse("audits:detail", args=[self.audit_b.pk]))
        self.assertEqual(response.status_code, 404)
