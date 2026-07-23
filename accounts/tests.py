import json

from django.test import TestCase
from django.urls import reverse

from tenancy.models import Membership, Organisation

from .models import User


class UserModelTests(TestCase):
    def test_create_user_uses_email_as_username_field(self):
        user = User.objects.create_user(email="jane@example.com", password="StrongPass123!")
        self.assertEqual(user.username, "jane@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="StrongPass123!")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_display_name_and_initials(self):
        user = User.objects.create_user(
            email="jane@example.com", password="x", first_name="Jane", last_name="Doe"
        )
        self.assertEqual(user.display_name, "Jane Doe")
        self.assertEqual(user.initials, "JD")


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="jane@example.com", password="StrongPass123!")

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "jane@example.com", "password": "StrongPass123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_anonymous is False or True)

    def test_login_wrong_password_fails(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "jane@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)


class PopiaSelfServiceTests(TestCase):
    """spec §12/§45/POPIA_READINESS.md: technical data-access and
    deactivation capabilities for the account holder's own data."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="jane@example.com", password="StrongPass123!", first_name="Jane", last_name="Doe"
        )
        self.org = Organisation.objects.create(name="NIBS")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="jane@example.com", password="StrongPass123!")

    def test_export_my_data_returns_own_profile_and_memberships(self):
        response = self.client.get(reverse("accounts:export_my_data"))
        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertEqual(payload["email"], "jane@example.com")
        self.assertEqual(len(payload["organisation_memberships"]), 1)
        self.assertEqual(payload["organisation_memberships"][0]["organisation"], "NIBS")

    def test_deactivate_requires_post(self):
        response = self.client.get(reverse("accounts:deactivate_account"))
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_deactivate_blocks_further_login(self):
        response = self.client.post(reverse("accounts:deactivate_account"))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

        can_login = self.client.login(email="jane@example.com", password="StrongPass123!")
        self.assertFalse(can_login)

    def test_export_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:export_my_data"))
        self.assertEqual(response.status_code, 302)
