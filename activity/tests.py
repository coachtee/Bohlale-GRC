from django.test import RequestFactory, TestCase

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
