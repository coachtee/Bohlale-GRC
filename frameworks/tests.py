import re

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ai.models import AIGeneration
from tenancy.models import Membership, Organisation

from .importer import extract_structure
from .models import Framework, FrameworkCategory, RequirementStatus
from .services import adopt_framework, framework_progress, set_requirement_status

BUILT_IN_FRAMEWORK_CODES = [
    "ISO27001", "ISO27701", "POPIA", "PAIA", "ISO22301", "ISO9001", "ISO31000", "NIST_CSF", "CIS_V8", "KING_IV",
]


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

    def test_seed_creates_all_nine_required_frameworks_plus_king_iv(self):
        call_command("seed_frameworks")
        for code in BUILT_IN_FRAMEWORK_CODES:
            self.assertTrue(
                Framework.objects.filter(code=code, organisation__isnull=True).exists(), f"missing framework {code}"
            )
        self.assertEqual(Framework.objects.filter(organisation__isnull=True).count(), len(BUILT_IN_FRAMEWORK_CODES))

    def test_seed_creates_south_african_compliance_category_first(self):
        call_command("seed_frameworks")
        categories = list(FrameworkCategory.objects.order_by("order"))
        self.assertEqual(categories[0].slug, "south-african-compliance")
        for code in ["POPIA", "PAIA", "KING_IV"]:
            fw = Framework.objects.get(code=code)
            self.assertEqual(fw.category.slug, "south-african-compliance")

    def test_every_built_in_framework_has_domains_and_requirements(self):
        call_command("seed_frameworks")
        for code in BUILT_IN_FRAMEWORK_CODES:
            fw = Framework.objects.get(code=code)
            self.assertGreater(fw.domains.count(), 0, f"{code} has no domains")
            self.assertGreater(fw.requirements.count(), 0, f"{code} has no requirements")
            self.assertTrue(fw.icon)
            self.assertEqual(fw.status, "active")

    def test_no_copyrighted_verbatim_iso_clause_text(self):
        # Guardrail, not a legal determination: the seeded guidance text
        # must be original prose, not the standard's own clause wording
        # (spot-check a distinctive phrase from the real ISO 27001 text
        # that this codebase must never reproduce verbatim).
        call_command("seed_frameworks")
        all_text = " ".join(
            Framework.objects.filter(organisation__isnull=True).values_list("description", flat=True)
        )
        self.assertNotIn("This document was prepared by Technical Committee", all_text)


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


class FrameworkLibraryViewTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_library_page_renders_with_south_african_section_first(self):
        response = self.client.get(reverse("frameworks:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "South African Compliance")
        self.assertContains(response, "POPIA")
        self.assertContains(response, "CIS Controls v8")
        # South African Compliance is order=0, so its section heading
        # should appear before the international-standards section.
        content = response.content.decode()
        self.assertLess(content.index("South African Compliance"), content.index("International Management Systems"))

    def test_empty_state_shown_when_no_custom_frameworks(self):
        response = self.client.get(reverse("frameworks:list"))
        self.assertContains(response, "No custom or imported frameworks yet.")
        self.assertContains(response, "Create Framework Manually")

    def test_framework_detail_page_renders(self):
        framework = Framework.objects.get(code="ISO27001")
        response = self.client.get(reverse("frameworks:detail", args=[framework.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Model CISO Assistant")


class FrameworkCreateManuallyTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_create_framework_manually(self):
        response = self.client.post(
            reverse("frameworks:create"),
            {"name": "Client Code of Conduct", "version": "2026", "description": "A custom internal standard.", "category": ""},
        )
        self.assertEqual(response.status_code, 302)
        framework = Framework.objects.get(name="Client Code of Conduct")
        self.assertEqual(framework.organisation, self.org_a)
        self.assertEqual(framework.source_type, "custom")

    def test_add_domain_and_requirement_to_own_custom_framework(self):
        framework = Framework.objects.create(organisation=self.org_a, code="CUSTOM-X", name="My Framework", source_type="custom")
        self.client.post(reverse("frameworks:domain_create", args=[framework.pk]), {"title": "Access", "code": "1"})
        domain = framework.domains.get(title="Access")
        self.client.post(
            reverse("frameworks:requirement_create", args=[framework.pk, domain.pk]),
            {"ref_code": "1.1", "title": "Restrict admin access", "guidance": "Limit admin accounts."},
        )
        self.assertTrue(domain.requirements.filter(title="Restrict admin access").exists())

    def test_detail_page_has_no_duplicate_form_field_ids_across_multiple_domains(self):
        # Regression test: the add-domain form and every per-domain
        # add-requirement form share field names (title/code/ref_code),
        # so without a unique auto_id per form instance the rendered
        # page would contain duplicate `id="..."` attributes and broken
        # <label for="..."> associations once a framework has 2+ domains.
        framework = Framework.objects.create(organisation=self.org_a, code="CUSTOM-DUP", name="Dup Test", source_type="custom")
        for i in range(3):
            self.client.post(reverse("frameworks:domain_create", args=[framework.pk]), {"title": f"Domain {i}", "code": str(i)})

        response = self.client.get(reverse("frameworks:detail", args=[framework.pk]))
        html = response.content.decode()
        ids = re.findall(r'\bid="([^"]+)"', html)
        duplicates = {i for i in ids if ids.count(i) > 1}
        self.assertEqual(duplicates, set(), f"duplicate id attributes found: {duplicates}")

    def test_cannot_add_domain_to_another_orgs_framework(self):
        framework_b = Framework.objects.create(organisation=self.org_b, code="CUSTOM-B", name="Org B Framework", source_type="custom")
        response = self.client.post(reverse("frameworks:domain_create", args=[framework_b.pk]), {"title": "Hack"})
        self.assertEqual(response.status_code, 404)

    def test_cannot_add_domain_to_a_built_in_framework(self):
        framework = Framework.objects.get(code="ISO27001")
        response = self.client.post(reverse("frameworks:domain_create", args=[framework.pk]), {"title": "Hack"})
        self.assertEqual(response.status_code, 404)


class CisoAssistTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")
        self.framework = Framework.objects.get(code="ISO27001")

    def test_explain_control_creates_ai_generation(self):
        response = self.client.post(
            reverse("frameworks:ciso_assist", args=[self.framework.pk]),
            {"action": "explain_control", "requirement_id": ""},
        )
        self.assertEqual(response.status_code, 302)
        generation = AIGeneration.objects.filter(organisation=self.org, purpose="control_explanation").first()
        self.assertIsNotNone(generation)
        self.assertEqual(generation.related_object, self.framework)

    def test_suggest_evidence_for_specific_requirement(self):
        requirement = self.framework.requirements.first()
        response = self.client.post(
            reverse("frameworks:ciso_assist", args=[self.framework.pk]),
            {"action": "suggest_evidence", "requirement_id": str(requirement.pk)},
        )
        self.assertEqual(response.status_code, 302)
        generation = AIGeneration.objects.filter(organisation=self.org, purpose="evidence_suggestion").first()
        self.assertIsNotNone(generation)
        self.assertIn(requirement.ref_code, generation.context_reference)

    def test_draft_guidance_purpose(self):
        response = self.client.post(
            reverse("frameworks:ciso_assist", args=[self.framework.pk]),
            {"action": "draft_guidance", "requirement_id": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AIGeneration.objects.filter(organisation=self.org, purpose="framework_guidance").exists())

    def test_generation_is_tenant_scoped(self):
        other_org = Organisation.objects.create(name="Other Org")
        other_user = User.objects.create_user(email="b@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=other_org, user=other_user, role="org_admin")

        self.client.post(reverse("frameworks:ciso_assist", args=[self.framework.pk]), {"action": "explain_control"})

        self.client.logout()
        self.client.login(email="b@example.com", password="StrongPass123!")
        response = self.client.get(reverse("frameworks:detail", args=[self.framework.pk]))
        self.assertEqual(AIGeneration.objects.filter(organisation=other_org).count(), 0)
        self.assertEqual(response.status_code, 200)
