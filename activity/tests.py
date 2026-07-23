from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import AuditLog
from .utils import log_activity


class LogActivityTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Org A")
        self.user = User.objects.create_user(email="a@example.com", password="x")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")

    def test_log_activity_from_request(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = self.user
        request.organisation = self.org

        log = log_activity(request, action="created", target=self.org, description="Org created")
        self.assertEqual(AuditLog.objects.count(), 1)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.organisation, self.org)
        self.assertEqual(log.target, self.org)

    def test_log_activity_without_request(self):
        log = log_activity(None, action="seeded", description="Demo data seeded", organisation=self.org)
        self.assertIsNone(log.actor)
        self.assertEqual(log.organisation, self.org)

    def test_audit_log_is_read_only_in_admin(self):
        from django.contrib import admin as django_admin

        model_admin = django_admin.site._registry[AuditLog]
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None))
        self.assertFalse(model_admin.has_delete_permission(None))


class ActivityFeedTenantIsolationTests(TestCase):
    """A GRC platform's audit trail is itself sensitive (spec §9/§45) —
    Org A must never see Org B's activity feed entries."""

    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        log_activity(None, action="created", description="Org B secret action", organisation=self.org_b)
        log_activity(None, action="created", description="Org A visible action", organisation=self.org_a)
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_activity_feed_excludes_other_organisations(self):
        response = self.client.get(reverse("activity:feed"))
        self.assertContains(response, "Org A visible action")
        self.assertNotContains(response, "Org B secret action")
