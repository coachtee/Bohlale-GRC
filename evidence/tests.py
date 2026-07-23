import datetime

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from core.validators import validate_upload_file
from tenancy.models import Membership, Organisation

from .models import Evidence


class EvidenceModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_reference_code_assigned(self):
        evidence = Evidence.objects.create(organisation=self.org, name="Access review export")
        self.assertEqual(evidence.reference_code, "EVD-0001")

    def test_is_expired(self):
        evidence = Evidence.objects.create(
            organisation=self.org, name="Old cert", expiry_date=timezone.now().date() - datetime.timedelta(days=1)
        )
        self.assertTrue(evidence.is_expired)
        self.assertFalse(evidence.is_expiring_soon)

    def test_is_expiring_soon(self):
        evidence = Evidence.objects.create(
            organisation=self.org, name="Cert", expiry_date=timezone.now().date() + datetime.timedelta(days=10)
        )
        self.assertTrue(evidence.is_expiring_soon)
        self.assertFalse(evidence.is_expired)


class UploadValidatorTests(TestCase):
    def test_rejects_disallowed_extension(self):
        bad_file = SimpleUploadedFile("malware.exe", b"data")
        with self.assertRaises(ValidationError):
            validate_upload_file(bad_file)

    def test_accepts_allowed_extension(self):
        good_file = SimpleUploadedFile("evidence.pdf", b"data")
        validate_upload_file(good_file)  # should not raise

    def test_rejects_oversized_file(self):
        from django.test import override_settings

        with override_settings(MAX_UPLOAD_SIZE_MB=0):
            big_file = SimpleUploadedFile("evidence.pdf", b"x" * 1024)
            with self.assertRaises(ValidationError):
                validate_upload_file(big_file)


class EvidenceTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.evidence_b = Evidence.objects.create(organisation=self.org_b, name="Org B secret evidence")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_evidence(self):
        response = self.client.get(reverse("evidence:detail", args=[self.evidence_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_list_excludes_other_org(self):
        Evidence.objects.create(organisation=self.org_a, name="Org A evidence")
        response = self.client.get(reverse("evidence:list"))
        self.assertContains(response, "Org A evidence")
        self.assertNotContains(response, "Org B secret evidence")
