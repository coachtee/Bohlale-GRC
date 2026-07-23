from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from risks.models import Risk
from tenancy.models import Membership, Organisation

from .models import RegisterEntry, RegisterType
from .services import DEFAULT_REGISTER_TYPES, ensure_default_register_types, register_hub_summary


class RegisterTypeSeedTests(TestCase):
    def test_ensure_default_register_types_creates_four(self):
        ensure_default_register_types()
        self.assertEqual(RegisterType.objects.count(), len(DEFAULT_REGISTER_TYPES))

    def test_idempotent(self):
        ensure_default_register_types()
        ensure_default_register_types()
        self.assertEqual(RegisterType.objects.count(), len(DEFAULT_REGISTER_TYPES))


class HubSummaryTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_hub_summary_counts_dedicated_and_generic(self):
        Risk.objects.create(organisation=self.org, title="Test risk", likelihood=1, impact=1)
        summary = register_hub_summary(self.org)
        risk_row = next(r for r in summary["dedicated"] if r["name"] == "Risk Register")
        self.assertEqual(risk_row["count"], 1)
        self.assertEqual(len(summary["generic"]), len(DEFAULT_REGISTER_TYPES))


class GenericRegisterViewTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")
        ensure_default_register_types()
        self.register_type = RegisterType.objects.get(slug="interested-parties")

    def test_create_entry(self):
        response = self.client.post(
            reverse("registers:generic_create", args=[self.register_type.slug]),
            {"party": "Information Regulator", "category": "Regulatory", "expectation": "POPIA compliance"},
        )
        self.assertEqual(response.status_code, 302)
        entry = RegisterEntry.objects.get(organisation=self.org, register_type=self.register_type)
        self.assertEqual(entry.data["party"], "Information Regulator")

    def test_list_view_renders_entry_values(self):
        RegisterEntry.objects.create(
            organisation=self.org, register_type=self.register_type,
            data={"party": "SETA", "category": "Regulatory", "expectation": "Accreditation"},
        )
        response = self.client.get(reverse("registers:generic_list", args=[self.register_type.slug]))
        self.assertContains(response, "SETA")


class RegisterTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        ensure_default_register_types()
        self.register_type = RegisterType.objects.get(slug="training")
        self.entry_b = RegisterEntry.objects.create(
            organisation=self.org_b, register_type=self.register_type, data={"topic": "Org B secret training"}
        )
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_list_excludes_other_org_entries(self):
        response = self.client.get(reverse("registers:generic_list", args=[self.register_type.slug]))
        self.assertNotContains(response, "Org B secret training")

    def test_cannot_edit_other_org_entry(self):
        response = self.client.get(reverse("registers:generic_edit", args=[self.register_type.slug, self.entry_b.pk]))
        self.assertEqual(response.status_code, 404)
