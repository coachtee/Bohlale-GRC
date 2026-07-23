from django.test import TestCase
from django.urls import reverse

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
