import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import Supplier


class SupplierModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_reference_code_assigned(self):
        supplier = Supplier.objects.create(organisation=self.org, name="CloudCo")
        self.assertEqual(supplier.reference_code, "SUP-0001")

    def test_is_review_overdue(self):
        supplier = Supplier.objects.create(
            organisation=self.org, name="CloudCo", review_date=timezone.now().date() - datetime.timedelta(days=5)
        )
        self.assertTrue(supplier.is_review_overdue)


class SupplierTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.supplier_b = Supplier.objects.create(organisation=self.org_b, name="Org B secret supplier")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_supplier(self):
        response = self.client.get(reverse("suppliers:detail", args=[self.supplier_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_create_supplier_via_view(self):
        response = self.client.post(
            reverse("suppliers:create"),
            {
                "name": "New Cloud Supplier", "service": "Hosting", "criticality": "high",
                "risk_rating": "medium", "status": "active",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Supplier.objects.filter(name="New Cloud Supplier", organisation=self.org_a).exists())
