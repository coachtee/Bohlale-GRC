from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from frameworks.models import Framework
from frameworks.services import adopt_framework
from tenancy.models import Membership, Organisation

from .models import Control, SoAEntry
from .services import COMMON_CONTROLS, ensure_baseline_controls, ensure_soa_entries, soa_coverage


class BaselineControlSeedTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")

    def test_ensure_baseline_controls_creates_common_controls(self):
        ensure_baseline_controls(self.org)
        self.assertEqual(Control.objects.filter(organisation=self.org).count(), len(COMMON_CONTROLS))

    def test_ensure_baseline_controls_is_idempotent(self):
        ensure_baseline_controls(self.org)
        ensure_baseline_controls(self.org)
        self.assertEqual(Control.objects.filter(organisation=self.org).count(), len(COMMON_CONTROLS))

    def test_access_control_maps_to_multiple_frameworks(self):
        ensure_baseline_controls(self.org)
        access_control = Control.objects.get(organisation=self.org, name="Access Control")
        framework_codes = {req.framework.code for req in access_control.framework_requirements.all()}
        self.assertIn("ISO27001", framework_codes)
        self.assertIn("POPIA", framework_codes)


class SoATests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.framework = Framework.objects.get(code="ISO27001")
        adopt_framework(self.org, self.framework)

    def test_ensure_soa_entries_creates_one_per_control(self):
        ensure_soa_entries(self.org, self.framework)
        self.assertEqual(
            SoAEntry.objects.filter(organisation=self.org, framework=self.framework).count(),
            len(COMMON_CONTROLS),
        )

    def test_soa_coverage_zero_when_nothing_implemented(self):
        ensure_soa_entries(self.org, self.framework)
        self.assertEqual(soa_coverage(self.org, self.framework), 0)

    def test_soa_coverage_reflects_implemented_controls(self):
        ensure_soa_entries(self.org, self.framework)
        entries = list(SoAEntry.objects.filter(organisation=self.org, framework=self.framework))
        half = len(entries) // 2
        for entry in entries[:half]:
            entry.control.implementation_status = "implemented"
            entry.control.save()
        coverage = soa_coverage(self.org, self.framework)
        self.assertGreater(coverage, 0)
        self.assertLess(coverage, 100)

    def test_not_applicable_controls_excluded_from_denominator(self):
        ensure_soa_entries(self.org, self.framework)
        for entry in SoAEntry.objects.filter(organisation=self.org, framework=self.framework):
            entry.applicable = False
            entry.save()
        self.assertEqual(soa_coverage(self.org, self.framework), 0)


class SoAViewTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_soa_view_shows_empty_state_without_adopted_framework(self):
        response = self.client.get(reverse("controls:soa"))
        self.assertContains(response, "No adopted framework")

    def test_soa_view_auto_seeds_controls_once_framework_adopted(self):
        framework = Framework.objects.get(code="ISO27001")
        adopt_framework(self.org, framework)
        response = self.client.get(reverse("controls:soa"))
        self.assertContains(response, "Access Control")


class ControlTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.control_b = Control.objects.create(organisation=self.org_b, name="Org B secret control")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_control(self):
        response = self.client.get(reverse("controls:detail", args=[self.control_b.pk]))
        self.assertEqual(response.status_code, 404)


class ControlFormIDORTests(TestCase):
    def setUp(self):
        from frameworks.models import Requirement

        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a2@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="control_owner")
        framework_b = Framework.objects.create(name="Org B Private Framework", code="ORGB2", organisation=self.org_b)
        self.requirement_b = Requirement.objects.create(framework=framework_b, title="Org B secret requirement")
        self.client.login(email="a2@example.com", password="StrongPass123!")

    def test_form_queryset_excludes_other_orgs_private_requirement(self):
        from .forms import ControlForm

        form = ControlForm(organisation=self.org_a)
        self.assertNotIn(self.requirement_b, form.fields["framework_requirements"].queryset)

    def test_cannot_attach_other_orgs_private_requirement_via_post(self):
        self.client.post(
            reverse("controls:create"),
            {"name": "New control", "implementation_status": "not_implemented", "effectiveness": "not_assessed",
             "framework_requirements": [str(self.requirement_b.pk)]},
        )
        control = Control.objects.filter(name="New control").first()
        if control is not None:
            self.assertNotIn(self.requirement_b, control.framework_requirements.all())
