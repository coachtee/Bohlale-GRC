from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import Asset


class AssetModelTests(TestCase):
    def test_reference_code_assigned(self):
        org = Organisation.objects.create(name="NIBS")
        asset = Asset.objects.create(organisation=org, name="LMS Server", asset_type="system")
        self.assertEqual(asset.reference_code, "AST-0001")


class AssetTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.asset_b = Asset.objects.create(organisation=self.org_b, name="Org B secret asset")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_asset(self):
        response = self.client.get(reverse("assets:detail", args=[self.asset_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_list_excludes_other_org(self):
        Asset.objects.create(organisation=self.org_a, name="Org A asset")
        response = self.client.get(reverse("assets:list"))
        self.assertContains(response, "Org A asset")
        self.assertNotContains(response, "Org B secret asset")

    def test_create_asset_via_view(self):
        response = self.client.post(
            reverse("assets:create"),
            {"name": "New laptop fleet", "asset_type": "hardware", "classification": "internal", "status": "active"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Asset.objects.filter(name="New laptop fleet", organisation=self.org_a).exists())
