from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from documents.models import Document
from documents.services import submit_for_approval, submit_for_review
from tenancy.models import Membership, Organisation

from .models import ApprovalRequest, Signature


class ElectronicSignOffTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.executive = User.objects.create_user(
            email="exec@example.com", password="StrongPass123!", first_name="Jane", last_name="Director"
        )
        self.contributor = User.objects.create_user(email="c@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.executive, role="executive")
        Membership.objects.create(organisation=self.org, user=self.contributor, role="contributor")

        self.document = Document.objects.create(organisation=self.org, title="Information Security Policy", content="Policy text")
        submit_for_review(self.document, self.contributor)
        self.approval_request = submit_for_approval(self.document, self.contributor)

    def test_contributor_cannot_access_signing_page(self):
        self.client.login(email="c@example.com", password="StrongPass123!")
        response = self.client.get(reverse("approvals:detail", args=[self.approval_request.pk]))
        self.assertEqual(response.status_code, 403)

    def test_typed_signature_must_match_full_name(self):
        self.client.login(email="exec@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("approvals:detail", args=[self.approval_request.pk]),
            {"decision": "approved", "typed_signature": "Someone Else", "consent": "on"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Signature.objects.count(), 0)

    def test_approving_signs_and_publishes_workflow_state(self):
        self.client.login(email="exec@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("approvals:detail", args=[self.approval_request.pk]),
            {"decision": "approved", "typed_signature": "Jane Director", "consent": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, "approved")
        self.assertEqual(self.document.approver, self.executive)

        signature = Signature.objects.get()
        self.assertEqual(signature.decision, "approved")
        self.assertTrue(signature.consent)
        self.assertEqual(signature.document_hash, self.document.content_hash())
        self.assertIsNotNone(signature.ip_address)

        self.approval_request.refresh_from_db()
        self.assertEqual(self.approval_request.status, "approved")

    def test_rejecting_returns_document_to_draft(self):
        self.client.login(email="exec@example.com", password="StrongPass123!")
        self.client.post(
            reverse("approvals:detail", args=[self.approval_request.pk]),
            {"decision": "rejected", "typed_signature": "Jane Director", "consent": "on"},
        )
        self.document.refresh_from_db()
        self.assertEqual(self.document.status, "draft")

    def test_consent_is_required(self):
        self.client.login(email="exec@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("approvals:detail", args=[self.approval_request.pk]),
            {"decision": "approved", "typed_signature": "Jane Director"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Signature.objects.count(), 0)


class ApprovalTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="executive")

        doc_b = Document.objects.create(organisation=self.org_b, title="Org B policy")
        self.request_b = ApprovalRequest.objects.create(organisation=self.org_b, target=doc_b)

    def test_org_a_cannot_view_org_b_approval_request(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("approvals:detail", args=[self.request_b.pk]))
        self.assertEqual(response.status_code, 404)
