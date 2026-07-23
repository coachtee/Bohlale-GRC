from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from . import service
from .models import STATUS_APPROVED, STATUS_PENDING, AIGeneration
from .providers.mock import MockProvider
from .providers.openai_compatible import OpenAICompatibleProvider


class MockProviderTests(TestCase):
    def test_isms_scope_purpose_produces_draft_marker(self):
        provider = MockProvider()
        output = provider.complete(
            system_prompt="sys", user_prompt="NIBS is a skills development provider.",
            purpose="isms_scope",
        )
        self.assertIn("DRAFT", output.upper())
        self.assertIn("NIBS", output)

    def test_unknown_purpose_falls_back_to_general(self):
        provider = MockProvider()
        output = provider.complete(system_prompt="sys", user_prompt="hello", purpose="something_new")
        self.assertIn("hello", output)


class OpenAICompatibleProviderFailureTests(TestCase):
    """The system must remain functional (never crash a request) when
    a configured real AI provider is unreachable (spec §10: "graceful
    behaviour when the provider is unavailable")."""

    def test_network_failure_returns_placeholder_instead_of_raising(self):
        provider = OpenAICompatibleProvider(base_url="https://unreachable.invalid", api_key="x", model="m")
        with patch("ai.providers.openai_compatible.requests.post", side_effect=ConnectionError("boom")):
            output = provider.complete(system_prompt="sys", user_prompt="hello", purpose="general")
        self.assertIn("unavailable", output.lower())

    def test_non_200_response_returns_placeholder_instead_of_raising(self):
        import requests

        provider = OpenAICompatibleProvider(base_url="https://api.example.invalid", api_key="x", model="m")

        class _BadResponse:
            def raise_for_status(self):
                raise requests.HTTPError("500 server error")

        with patch("ai.providers.openai_compatible.requests.post", return_value=_BadResponse()):
            output = provider.complete(system_prompt="sys", user_prompt="hello", purpose="general")
        self.assertIn("unavailable", output.lower())


@override_settings(AI_PROVIDER="mock")
class AIServiceTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")

    def test_generate_creates_ai_generation_record(self):
        generation = service.generate(
            organisation=self.org,
            user=self.user,
            purpose="isms_scope",
            user_prompt="Test context",
            context_reference="Knowledge profile: 3 verified facts",
        )
        self.assertEqual(AIGeneration.objects.count(), 1)
        self.assertEqual(generation.organisation, self.org)
        self.assertEqual(generation.requested_by, self.user)
        self.assertEqual(generation.review_status, STATUS_PENDING)
        self.assertEqual(generation.provider, "mock")

    def test_mark_reviewed(self):
        generation = service.generate(
            organisation=self.org, user=self.user, purpose="isms_scope", user_prompt="x"
        )
        generation.mark_reviewed(self.user, STATUS_APPROVED)
        generation.refresh_from_db()
        self.assertEqual(generation.review_status, STATUS_APPROVED)
        self.assertEqual(generation.reviewed_by, self.user)
        self.assertIsNotNone(generation.reviewed_at)


class AIGenerationLogTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        service.generate(organisation=self.org_a, user=self.user_a, purpose="isms_scope", user_prompt="A secret")
        service.generate(organisation=self.org_b, user=self.user_a, purpose="isms_scope", user_prompt="B secret")

    def test_log_only_shows_active_org_generations(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("ai:log"))
        self.assertEqual(response.status_code, 200)
        gens = response.context["generations"]
        self.assertEqual(len(gens), 1)
        self.assertEqual(gens[0].organisation, self.org_a)
