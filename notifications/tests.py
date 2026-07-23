from django.core import mail
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import Notification
from .utils import notify


class NotifyUtilTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Org A")
        self.user = User.objects.create_user(email="a@example.com", password="x")

    def test_notify_creates_in_app_notification(self):
        notify(self.org, self.user, "Test message", category="general")
        self.assertEqual(Notification.objects.count(), 1)

    def test_notify_can_send_email(self):
        notify(self.org, self.user, "Overdue action", category="action_overdue", send_email=True)
        self.assertEqual(len(mail.outbox), 1)


class NotificationViewTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Org A")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_user_only_sees_own_notifications(self):
        other = User.objects.create_user(email="b@example.com", password="x")
        notify(self.org, self.user, "Mine", category="general")
        notify(self.org, other, "Not mine", category="general")
        response = self.client.get(reverse("notifications:list"))
        self.assertContains(response, "Mine")
        self.assertNotContains(response, "Not mine")

    def test_mark_all_read(self):
        notify(self.org, self.user, "Mine", category="general")
        self.client.get(reverse("notifications:mark_all_read"))
        self.assertFalse(Notification.objects.filter(recipient=self.user, is_read=False).exists())
