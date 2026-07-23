from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .importer import extract_structure
from .models import Framework, RequirementStatus
from .services import adopt_framework, framework_progress, set_requirement_status


class SeedFrameworksTests(TestCase):
    def test_seed_creates_global_frameworks(self):
        call_command("seed_frameworks")
        self.assertTrue(Framework.objects.filter(code="ISO27001", organisation__isnull=True).exists())
        self.assertTrue(Framework.objects.filter(code="POPIA", organisation__isnull=True).exists())
        iso = Framework.objects.get(code="ISO27001")
        self.assertEqual(iso.domains.count(), 7)

    def test_seed_is_idempotent(self):
        call_command("seed_frameworks")
        call_command("seed_frameworks")
        self.assertEqual(Framework.objects.filter(code="ISO27001").count(), 1)


class ExtractStructureTests(TestCase):
    def test_extracts_numbered_headings(self):
        text = "4 Context of the Organisation\n4.1 Understanding the organisation\n4.2 Interested parties\n5 Leadership\n5.1 Leadership and commitment\n"
        result = extract_structure(text)
        self.assertEqual(len(result["domains"]), 2)
        self.assertEqual(result["domains"][0]["code"], "4")
        self.assertEqual(len(result["domains"][0]["requirements"]), 2)

    def test_falls_back_to_general_domain(self):
        result = extract_structure("just some plain text with no headings")
        self.assertEqual(result["domains"][0]["title"], "General")


class FrameworkProgressTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.framework = Framework.objects.get(code="ISO27001")

    def test_progress_zero_before_any_status(self):
        self.assertEqual(framework_progress(self.org, self.framework), 0)

    def test_progress_increases_with_completed_requirements(self):
        requirements = list(self.framework.requirements.all())
        total = len(requirements)
        for req in requirements[: total // 2]:
            set_requirement_status(self.org, req, "complete")
        progress = framework_progress(self.org, self.framework)
        self.assertGreater(progress, 0)
        self.assertLess(progress, 100)

    def test_not_applicable_excluded_from_denominator(self):
        requirements = list(self.framework.requirements.all())
        for req in requirements:
            set_requirement_status(self.org, req, "not_applicable")
        self.assertEqual(framework_progress(self.org, self.framework), 0)


class FrameworkTenantIsolationTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.custom_b = Framework.objects.create(
            organisation=self.org_b, code="CUSTOM1", name="Org B Private Framework", source_type="custom"
        )

    def test_org_a_cannot_see_org_b_custom_framework(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("frameworks:list"))
        self.assertNotContains(response, "Org B Private Framework")

    def test_org_a_cannot_open_org_b_custom_framework_by_url(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("frameworks:detail", args=[self.custom_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_global_framework_visible_to_all(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("frameworks:list"))
        self.assertContains(response, "ISO/IEC 27001")


class FrameworkAdoptionTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_adopt_framework_view(self):
        framework = Framework.objects.get(code="ISO27001")
        response = self.client.post(reverse("frameworks:adopt", args=[framework.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.org.framework_adoptions.filter(framework=framework).exists())
