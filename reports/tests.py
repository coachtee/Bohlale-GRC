from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from actions.models import CorrectiveAction
from audits.models import Audit
from controls.services import ensure_soa_entries
from documents.models import Document
from frameworks.models import Framework
from frameworks.services import adopt_framework, set_requirement_status
from reviews.services import create_review
from risks.models import Risk
from tenancy.models import Membership, Organisation

from .services import audit_readiness, executive_summary, gap_assessment_rows


class ReportServiceTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.framework = Framework.objects.get(code="ISO27001")
        adopt_framework(self.org, self.framework)

    def test_gap_assessment_lists_incomplete_requirements(self):
        rows = gap_assessment_rows(self.org, self.framework)
        self.assertEqual(len(rows), self.framework.requirements.count())
        requirement = self.framework.requirements.first()
        set_requirement_status(self.org, requirement, "complete")
        rows = gap_assessment_rows(self.org, self.framework)
        self.assertEqual(len(rows), self.framework.requirements.count() - 1)

    def test_audit_readiness_improves_as_data_is_added(self):
        baseline = audit_readiness(self.org, self.framework)
        self.assertEqual(baseline["overall"], 0)

        for requirement in self.framework.requirements.all():
            set_requirement_status(self.org, requirement, "complete")
        ensure_soa_entries(self.org, self.framework)
        Audit.objects.create(organisation=self.org, title="Internal audit", audit_type="internal", status="closed")
        create_review(self.org, meeting_date="2026-01-01", status="completed")

        improved = audit_readiness(self.org, self.framework)
        self.assertGreater(improved["overall"], baseline["overall"])

    def test_executive_summary_counts_open_actions(self):
        CorrectiveAction.objects.create(organisation=self.org, finding_description="x", status="open")
        CorrectiveAction.objects.create(organisation=self.org, finding_description="y", status="closed")
        summary = executive_summary(self.org)
        self.assertEqual(summary["open_actions"], 1)


class ReportViewTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")
        self.framework = Framework.objects.get(code="ISO27001")
        adopt_framework(self.org, self.framework)

    def test_hub_loads(self):
        response = self.client.get(reverse("reports:hub"))
        self.assertEqual(response.status_code, 200)

    def test_risk_register_excel_export(self):
        Risk.objects.create(organisation=self.org, title="Test risk", likelihood=3, impact=3)
        response = self.client.get(reverse("reports:risk_register"), {"format": "xlsx"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_readiness_report_renders(self):
        response = self.client.get(reverse("reports:readiness"))
        self.assertContains(response, "Overall Readiness")

    def test_policy_register_report_lists_documents(self):
        Document.objects.create(organisation=self.org, title="Info Sec Policy")
        response = self.client.get(reverse("reports:policy_register"))
        self.assertContains(response, "Info Sec Policy")


class ReportTenantIsolationTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        Risk.objects.create(organisation=self.org_b, title="Org B secret risk", likelihood=1, impact=1)
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_risk_register_report_excludes_other_org(self):
        response = self.client.get(reverse("reports:risk_register"))
        self.assertNotContains(response, "Org B secret risk")
