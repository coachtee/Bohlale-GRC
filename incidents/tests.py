from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification
from tenancy.models import Membership, Organisation

from .models import ChangeEvent, Incident


class IncidentModelTests(TestCase):
    def test_reference_code_assigned(self):
        org = Organisation.objects.create(name="NIBS")
        incident = Incident.objects.create(organisation=org, title="Phishing email reported", description="x")
        self.assertEqual(incident.reference_code, "INC-0001")


class ChangeEventSuggestionTests(TestCase):
    def test_new_supplier_suggests_supplier_and_risk_register(self):
        org = Organisation.objects.create(name="NIBS")
        event = ChangeEvent.objects.create(organisation=org, event_type="new_supplier", description="Added CloudCo")
        labels = [label for label, _ in event.suggestions]
        self.assertIn("Supplier Register", labels)
        self.assertIn("Risk Register", labels)


class IncidentReportFlowTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="contributor")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_report_incident_sets_discovered_by(self):
        response = self.client.post(
            reverse("incidents:create"),
            {
                "title": "Lost laptop", "description": "Laptop left on a train.",
                "severity": "medium", "status": "reported", "personal_info_involved": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        incident = Incident.objects.get(title="Lost laptop")
        self.assertEqual(incident.discovered_by, self.user)

    def test_reporting_incident_notifies_org_admins(self):
        admin = User.objects.create_user(email="admin@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=admin, role="org_admin")
        response = self.client.post(
            reverse("incidents:create"),
            {
                "title": "Suspicious login", "description": "Multiple failed attempts.",
                "severity": "high", "status": "reported",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notification.objects.filter(recipient=admin, category="incident").exists())

    def test_change_event_mark_reviewed(self):
        event = ChangeEvent.objects.create(organisation=self.org, event_type="new_system", reported_by=self.user)
        response = self.client.post(
            reverse("incidents:change_event_mark_reviewed", args=[event.pk]), {"review_notes": "Added to asset register"}
        )
        self.assertEqual(response.status_code, 302)
        event.refresh_from_db()
        self.assertEqual(event.status, "reviewed")


class IncidentTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.incident_b = Incident.objects.create(organisation=self.org_b, title="Org B secret incident", description="x")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_incident(self):
        response = self.client.get(reverse("incidents:detail", args=[self.incident_b.pk]))
        self.assertEqual(response.status_code, 404)
