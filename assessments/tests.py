from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from frameworks.models import Framework
from tenancy.models import Membership, Organisation

from .models import Assessment, AssessmentResult
from .services import create_assessment_from_framework


class AssessmentServiceTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.framework = Framework.objects.get(code="ISO27001")

    def test_creating_assessment_seeds_one_result_per_requirement(self):
        assessment = create_assessment_from_framework(self.org, self.framework, "Initial Gap Assessment", "gap", None)
        self.assertEqual(assessment.results.count(), self.framework.requirements.count())
        self.assertEqual(assessment.reference_code, "ASMT-0001")

    def test_completion_percent_updates_as_results_rated(self):
        assessment = create_assessment_from_framework(self.org, self.framework, "Gap", "gap", None)
        self.assertEqual(assessment.completion_percent, 0)
        result = assessment.results.first()
        result.rating = "implemented"
        result.save()
        self.assertGreater(assessment.completion_percent, 0)


class AssessmentViewTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="compliance_manager")
        self.client.login(email="a@example.com", password="StrongPass123!")
        self.framework = Framework.objects.get(code="POPIA")

    def test_create_assessment_via_view(self):
        response = self.client.post(
            reverse("assessments:create"),
            {
                "name": "POPIA Gap Assessment", "assessment_type": "gap",
                "framework": str(self.framework.pk), "assessor": str(self.user.pk), "started_at": "2026-01-01",
            },
        )
        self.assertEqual(response.status_code, 302)
        assessment = Assessment.objects.get(name="POPIA Gap Assessment")
        self.assertEqual(assessment.results.count(), self.framework.requirements.count())

    def test_update_result_rating(self):
        assessment = create_assessment_from_framework(self.org, self.framework, "Gap", "gap", self.user)
        result = assessment.results.first()
        response = self.client.post(
            reverse("assessments:result_update", args=[result.pk]),
            {"rating": "implemented", "comments": "", "findings": "", "recommendations": "", "due_date": ""},
        )
        self.assertEqual(response.status_code, 302)
        result.refresh_from_db()
        self.assertEqual(result.rating, "implemented")


class AssessmentTenantIsolationTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        framework = Framework.objects.get(code="ISO27001")
        self.assessment_b = create_assessment_from_framework(self.org_b, framework, "Org B assessment", "gap", None)

    def test_org_a_cannot_view_org_b_assessment(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("assessments:detail", args=[self.assessment_b.pk]))
        self.assertEqual(response.status_code, 404)
