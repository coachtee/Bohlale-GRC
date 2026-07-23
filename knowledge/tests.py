from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import KnowledgeItem
from .services import profile_completeness, set_item, verified_context_text


class KnowledgeServiceTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_set_item_upserts(self):
        set_item(self.org, "organisation_profile", "Legal name", "NIBS (Pty) Ltd")
        set_item(self.org, "organisation_profile", "Legal name", "NIBS (Pty) Ltd Updated")
        self.assertEqual(KnowledgeItem.objects.filter(organisation=self.org).count(), 1)
        item = KnowledgeItem.objects.get(organisation=self.org)
        self.assertEqual(item.value, "NIBS (Pty) Ltd Updated")

    def test_profile_completeness(self):
        set_item(self.org, "organisation_profile", "A", "x", status="verified")
        set_item(self.org, "organisation_profile", "B", "", status="missing")
        self.assertEqual(profile_completeness(self.org), 50)

    def test_verified_context_excludes_ai_inference(self):
        set_item(self.org, "organisation_profile", "Verified fact", "Confirmed", status="verified")
        set_item(self.org, "organisation_profile", "Guess", "Maybe", status="ai_inference")
        text = verified_context_text(self.org)
        self.assertIn("Confirmed", text)
        self.assertNotIn("Maybe", text)


class KnowledgeTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        set_item(self.org_a, "organisation_profile", "Org A fact", "secret A")
        set_item(self.org_b, "organisation_profile", "Org B fact", "secret B")

    def test_profile_view_only_shows_active_org_items(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("knowledge:profile"))
        self.assertContains(response, "Org A fact")
        self.assertNotContains(response, "Org B fact")
