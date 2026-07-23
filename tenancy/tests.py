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


class MemberManagementTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.admin = User.objects.create_user(email="admin@example.com", password="StrongPass123!")
        self.member = User.objects.create_user(email="member@example.com", password="StrongPass123!")
        self.admin_membership = Membership.objects.create(organisation=self.org, user=self.admin, role="org_admin")
        self.member_membership = Membership.objects.create(organisation=self.org, user=self.member, role="contributor")
        self.client.login(email="admin@example.com", password="StrongPass123!")

    def test_admin_can_change_member_role(self):
        response = self.client.post(
            reverse("tenancy:member_update_role", args=[self.member_membership.pk]), {"role": "risk_owner"}
        )
        self.assertEqual(response.status_code, 302)
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "risk_owner")

    def test_admin_can_remove_member(self):
        response = self.client.post(reverse("tenancy:member_remove", args=[self.member_membership.pk]))
        self.assertEqual(response.status_code, 302)
        self.member_membership.refresh_from_db()
        self.assertFalse(self.member_membership.is_active)

    def test_non_admin_cannot_change_roles(self):
        self.client.logout()
        self.client.login(email="member@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("tenancy:member_update_role", args=[self.admin_membership.pk]), {"role": "read_only"}
        )
        self.assertEqual(response.status_code, 403)

    def test_non_admin_cannot_remove_members(self):
        self.client.logout()
        self.client.login(email="member@example.com", password="StrongPass123!")
        response = self.client.post(reverse("tenancy:member_remove", args=[self.admin_membership.pk]))
        self.assertEqual(response.status_code, 403)

    def test_cannot_demote_the_last_admin(self):
        response = self.client.post(
            reverse("tenancy:member_update_role", args=[self.admin_membership.pk]), {"role": "contributor"}
        )
        self.assertEqual(response.status_code, 302)
        self.admin_membership.refresh_from_db()
        self.assertEqual(self.admin_membership.role, "org_admin")

    def test_cannot_remove_the_last_admin(self):
        response = self.client.post(reverse("tenancy:member_remove", args=[self.admin_membership.pk]))
        self.assertEqual(response.status_code, 302)
        self.admin_membership.refresh_from_db()
        self.assertTrue(self.admin_membership.is_active)

    def test_cannot_remove_own_membership(self):
        # Add a second admin first so the last-admin guard (tested
        # separately above) can't mask the self-removal guard.
        Membership.objects.create(
            organisation=self.org,
            user=User.objects.create_user(email="admin2@example.com", password="StrongPass123!"),
            role="org_admin",
        )
        response = self.client.post(reverse("tenancy:member_remove", args=[self.admin_membership.pk]))
        self.admin_membership.refresh_from_db()
        self.assertTrue(self.admin_membership.is_active)

    def test_removed_member_loses_access(self):
        self.client.post(reverse("tenancy:member_remove", args=[self.member_membership.pk]))
        self.client.logout()
        self.client.login(email="member@example.com", password="StrongPass123!")
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(response, reverse("tenancy:organisation_list"))


class MemberManagementTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.admin_a = User.objects.create_user(email="admin_a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.admin_a, role="org_admin")
        user_b = User.objects.create_user(email="user_b@example.com", password="StrongPass123!")
        self.membership_b = Membership.objects.create(organisation=self.org_b, user=user_b, role="contributor")
        self.client.login(email="admin_a@example.com", password="StrongPass123!")

    def test_org_a_admin_cannot_change_org_b_members_role(self):
        response = self.client.post(
            reverse("tenancy:member_update_role", args=[self.membership_b.pk]), {"role": "org_admin"}
        )
        self.assertEqual(response.status_code, 404)
        self.membership_b.refresh_from_db()
        self.assertEqual(self.membership_b.role, "contributor")

    def test_org_a_admin_cannot_remove_org_b_member(self):
        response = self.client.post(reverse("tenancy:member_remove", args=[self.membership_b.pk]))
        self.assertEqual(response.status_code, 404)
        self.membership_b.refresh_from_db()
        self.assertTrue(self.membership_b.is_active)
