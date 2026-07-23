from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from actions.models import CorrectiveAction
from documents.models import Document
from frameworks.models import Framework
from frameworks.services import adopt_framework
from journeys.services import start_journey
from risks.models import Risk
from tenancy.models import Membership, Organisation


class DashboardSmokeTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        call_command("seed_journey_templates")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(
            email="a@example.com", password="StrongPass123!", first_name="Thabiso"
        )
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_dashboard_renders_with_no_data(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good")
        self.assertContains(response, "NIBS")

    def test_dashboard_renders_with_full_data(self):
        framework = Framework.objects.get(code="ISO27001")
        template = framework.journey_templates.get(goal_type="build_from_scratch")
        start_journey(self.org, template, self.user)
        adopt_framework(self.org, framework)
        Risk.objects.create(organisation=self.org, title="Phishing", likelihood=4, impact=5)
        Document.objects.create(organisation=self.org, title="Info Sec Policy", status="awaiting_approval")
        CorrectiveAction.objects.create(organisation=self.org, finding_description="Fix access reviews", status="open")

        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Implementation Journey")
        # Risk Overview shows aggregate counts, not individual risk titles.
        self.assertContains(response, "1 High")
        self.assertContains(response, "Context of the Organisation")
        self.assertEqual(response.context["risk_overview"]["total"], 1)
        self.assertEqual(response.context["open_actions"]["total"], 1)

    def test_dashboard_redirects_without_organisation(self):
        User.objects.create_user(email="lonely@example.com", password="StrongPass123!")
        self.client.logout()
        self.client.login(email="lonely@example.com", password="StrongPass123!")
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(response, reverse("tenancy:organisation_list"))


class DashboardTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        Risk.objects.create(organisation=self.org_b, title="Org B secret risk", likelihood=5, impact=5)
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_dashboard_never_shows_other_org_data(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertNotContains(response, "Org B secret risk")
