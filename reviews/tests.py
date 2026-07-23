from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import REQUIRED_INPUTS, ManagementReview
from .services import create_review


class CreateReviewServiceTests(TestCase):
    def test_create_review_seeds_input_checklist(self):
        org = Organisation.objects.create(name="NIBS")
        review = create_review(org, meeting_date="2026-01-15")
        self.assertEqual(review.input_records.count(), len(REQUIRED_INPUTS))
        self.assertEqual(review.reference_code, "MR-0001")

    def test_inputs_covered_count(self):
        org = Organisation.objects.create(name="NIBS")
        review = create_review(org, meeting_date="2026-01-15")
        record = review.input_records.first()
        record.covered = True
        record.save()
        self.assertEqual(review.inputs_covered_count, 1)


class ReviewViewFlowTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_create_review_via_view(self):
        response = self.client.post(
            reverse("reviews:create"),
            {"meeting_date": "2026-02-01", "attendees": "CEO, ISMS Manager", "agenda": "Quarterly review", "decisions": ""},
        )
        self.assertEqual(response.status_code, 302)
        review = ManagementReview.objects.get(organisation=self.org)
        self.assertEqual(review.input_records.count(), len(REQUIRED_INPUTS))

    def test_mark_input_covered(self):
        review = create_review(self.org, meeting_date="2026-01-15")
        record = review.input_records.first()
        response = self.client.post(
            reverse("reviews:input_record_update", args=[record.pk]), {"covered": "on", "notes": "Reviewed"}
        )
        self.assertEqual(response.status_code, 302)
        record.refresh_from_db()
        self.assertTrue(record.covered)

    def test_complete_review(self):
        review = create_review(self.org, meeting_date="2026-01-15")
        response = self.client.post(reverse("reviews:complete", args=[review.pk]))
        self.assertEqual(response.status_code, 302)
        review.refresh_from_db()
        self.assertEqual(review.status, "completed")
        self.assertEqual(review.approved_by, self.user)

    def test_editor_cannot_complete_review(self):
        # Completing a management review sets approved_by (spec §32) —
        # an approval action requiring Approver-level roles, not any Editor.
        contributor = User.objects.create_user(email="contrib@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=contributor, role="compliance_manager")
        self.client.logout()
        self.client.login(email="contrib@example.com", password="StrongPass123!")
        review = create_review(self.org, meeting_date="2026-01-15")
        response = self.client.post(reverse("reviews:complete", args=[review.pk]))
        self.assertEqual(response.status_code, 403)
        review.refresh_from_db()
        self.assertNotEqual(review.status, "completed")

    def test_create_corrective_action_from_review(self):
        review = create_review(self.org, meeting_date="2026-01-15", decisions="Improve access reviews")
        response = self.client.post(
            reverse("actions:create_from_review", args=[review.pk]),
            {"source": "management_review", "finding_description": "Improve access reviews", "severity": "medium", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        from actions.models import CorrectiveAction

        action = CorrectiveAction.objects.get(organisation=self.org)
        self.assertEqual(action.source_record, review)


class ReviewTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.review_b = create_review(self.org_b, meeting_date="2026-01-01")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_review(self):
        response = self.client.get(reverse("reviews:detail", args=[self.review_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_a_cannot_download_org_b_review_attachment(self):
        self.review_b.attachment = SimpleUploadedFile("secret.pdf", b"org-b-confidential")
        self.review_b.save()
        response = self.client.get(reverse("reviews:download", args=[self.review_b.pk]))
        self.assertEqual(response.status_code, 404)
