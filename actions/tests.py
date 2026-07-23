import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from audits.models import Audit, AuditFinding
from incidents.models import Incident
from tenancy.models import Membership, Organisation

from .models import CorrectiveAction


class CorrectiveActionModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_reference_code_assigned(self):
        action = CorrectiveAction.objects.create(organisation=self.org, finding_description="x")
        self.assertEqual(action.reference_code, "CA-0001")

    def test_is_overdue(self):
        action = CorrectiveAction.objects.create(
            organisation=self.org, finding_description="x",
            due_date=timezone.now().date() - datetime.timedelta(days=3),
        )
        self.assertTrue(action.is_overdue)

    def test_closed_action_never_overdue(self):
        action = CorrectiveAction.objects.create(
            organisation=self.org, finding_description="x",
            due_date=timezone.now().date() - datetime.timedelta(days=3), status="closed",
        )
        self.assertFalse(action.is_overdue)


class CreateFromSourceTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="compliance_manager")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_create_from_incident_links_source_record(self):
        incident = Incident.objects.create(organisation=self.org, title="Lost laptop", description="Laptop lost on train")
        response = self.client.post(
            reverse("actions:create_from_incident", args=[incident.pk]),
            {"source": "incident", "finding_description": "Laptop lost on train", "severity": "medium", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        action = CorrectiveAction.objects.get(organisation=self.org)
        self.assertEqual(action.source, "incident")
        self.assertEqual(action.source_record, incident)

    def test_create_from_audit_finding(self):
        audit = Audit.objects.create(organisation=self.org, title="Audit")
        finding = AuditFinding.objects.create(organisation=self.org, audit=audit, description="Gap found")
        response = self.client.post(
            reverse("actions:create_from_finding", args=[finding.pk]),
            {"source": "audit", "finding_description": "Gap found", "severity": "medium", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        action = CorrectiveAction.objects.get(organisation=self.org)
        self.assertEqual(action.source_record, finding)


class VerifyCloseTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")
        self.action = CorrectiveAction.objects.create(organisation=self.org, finding_description="x", status="verification")

    def test_verify_close_sets_closed_status_and_verifier(self):
        response = self.client.post(
            reverse("actions:verify_close", args=[self.action.pk]), {"verification_notes": "Confirmed fixed"}
        )
        self.assertEqual(response.status_code, 302)
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, "closed")
        self.assertEqual(self.action.verified_by, self.user)
        self.assertIsNotNone(self.action.closed_at)


class VerifyCloseRBACTests(TestCase):
    """Closing a corrective action is an independent-verification
    sign-off (spec §31) and requires an Approver-level role — an
    Editor-level role (e.g. compliance_manager, the action's own owner)
    must not be able to close it, either via the dedicated verify/close
    view or by bypassing it through the plain edit form."""

    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.editor = User.objects.create_user(email="editor@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.editor, role="compliance_manager")
        self.client.login(email="editor@example.com", password="StrongPass123!")
        self.action = CorrectiveAction.objects.create(organisation=self.org, finding_description="x", status="verification")

    def test_editor_cannot_verify_close(self):
        response = self.client.post(
            reverse("actions:verify_close", args=[self.action.pk]), {"verification_notes": "Confirmed fixed"}
        )
        self.assertEqual(response.status_code, 403)
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, "verification")

    def test_editor_cannot_close_via_plain_edit_form(self):
        response = self.client.post(
            reverse("actions:edit", args=[self.action.pk]),
            {"source": "other", "finding_description": "x", "status": "closed", "severity": "medium"},
        )
        self.assertEqual(response.status_code, 403)
        self.action.refresh_from_db()
        self.assertEqual(self.action.status, "verification")


class CorrectiveActionTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.action_b = CorrectiveAction.objects.create(organisation=self.org_b, finding_description="Org B secret finding")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_action(self):
        response = self.client.get(reverse("actions:detail", args=[self.action_b.pk]))
        self.assertEqual(response.status_code, 404)
