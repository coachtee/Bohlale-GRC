from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .middleware import SESSION_KEY
from .models import Membership, Organisation, OrganisationInvite


class OrganisationModelTests(TestCase):
    def test_slug_is_generated_and_unique(self):
        org1 = Organisation.objects.create(name="NIBS")
        org2 = Organisation.objects.create(name="NIBS")
        self.assertEqual(org1.slug, "nibs")
        self.assertNotEqual(org1.slug, org2.slug)

    def test_initials(self):
        org = Organisation.objects.create(name="Naleli Innovators Business School")
        self.assertEqual(org.initials, "NI")


class TenantIsolationTests(TestCase):
    """The core multi-tenancy guarantee: a user in Organisation A must
    never see Organisation B's data, even via a direct URL/PK guess."""

    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        self.user_b = User.objects.create_user(email="b@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        Membership.objects.create(organisation=self.org_b, user=self.user_b, role="org_admin")

    def test_middleware_auto_selects_sole_membership(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.wsgi_request.organisation, self.org_a)

    def test_user_cannot_switch_into_organisation_they_are_not_a_member_of(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(
            reverse("tenancy:organisation_switch", args=[self.org_b.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_member_list_only_shows_active_organisation_members(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("tenancy:member_list"))
        self.assertContains(response, "a@example.com")
        self.assertNotContains(response, "b@example.com")

    def test_organisation_list_only_shows_accessible_orgs(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("tenancy:organisation_list"))
        self.assertContains(response, "Org A")
        self.assertNotContains(response, "Org B")

    def test_superuser_can_access_any_organisation(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="StrongPass123!")
        self.client.login(email="admin@example.com", password="StrongPass123!")
        response = self.client.get(
            reverse("tenancy:organisation_switch", args=[self.org_b.pk]), follow=True
        )
        self.assertEqual(response.wsgi_request.session[SESSION_KEY], str(self.org_b.pk))


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Org A")
        self.admin_user = User.objects.create_user(email="admin@example.com", password="StrongPass123!")
        self.readonly_user = User.objects.create_user(email="ro@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.admin_user, role="org_admin")
        Membership.objects.create(organisation=self.org, user=self.readonly_user, role="read_only")

    def test_read_only_user_cannot_invite_members(self):
        self.client.login(email="ro@example.com", password="StrongPass123!")
        response = self.client.get(reverse("tenancy:invite_member"))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_invite_members(self):
        self.client.login(email="admin@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("tenancy:invite_member"), {"email": "new@example.com", "role": "contributor"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OrganisationInvite.objects.filter(email="new@example.com").exists())


class OrganisationOnboardingTests(TestCase):
    def test_creating_organisation_creates_org_admin_membership(self):
        user = User.objects.create_user(email="founder@example.com", password="StrongPass123!")
        self.client.login(email="founder@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("tenancy:organisation_create"),
            {
                "name": "NIBS",
                "organisation_type": "sdp",
                "industry": "Skills Development",
                "registration_number": "",
                "country": "South Africa",
                "province": "Gauteng",
                "website": "",
                "size": "11-50",
            },
        )
        org = Organisation.objects.get(name="NIBS")
        membership = Membership.objects.get(organisation=org, user=user)
        self.assertEqual(membership.role, "org_admin")
