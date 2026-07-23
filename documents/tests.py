from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from ai.models import STATUS_APPROVED as AI_APPROVED
from ai.models import STATUS_PENDING as AI_PENDING
from journeys.models import OrganisationJourney
from journeys.services import start_journey
from knowledge.services import set_item
from tenancy.models import Membership, Organisation

from .models import Document
from .services import generate_draft_for_step, publish, start_revision, submit_for_approval, submit_for_review


class DocumentModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_reference_code_auto_assigned_and_sequential(self):
        doc1 = Document.objects.create(organisation=self.org, title="Policy A")
        doc2 = Document.objects.create(organisation=self.org, title="Policy B")
        self.assertEqual(doc1.reference_code, "DOC-0001")
        self.assertEqual(doc2.reference_code, "DOC-0002")

    def test_content_hash_changes_with_content(self):
        doc = Document.objects.create(organisation=self.org, title="Policy A", content="v1")
        hash1 = doc.content_hash()
        doc.content = "v2"
        self.assertNotEqual(hash1, doc.content_hash())


class DocumentLifecycleServiceTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="x")
        self.document = Document.objects.create(organisation=self.org, title="Info Sec Policy", content="Draft text")

    def test_submit_for_review_snapshots_version(self):
        submit_for_review(self.document, self.user)
        self.assertEqual(self.document.status, "under_review")
        self.assertEqual(self.document.versions.count(), 1)

    def test_submit_for_approval_creates_approval_request(self):
        approval_request = submit_for_approval(self.document, self.user)
        self.assertEqual(self.document.status, "awaiting_approval")
        self.assertEqual(approval_request.target, self.document)

    def test_publish_bumps_to_next_whole_version_and_sets_effective_date(self):
        self.document.status = "approved"
        self.document.save()
        publish(self.document, self.user)
        self.assertEqual(self.document.status, "published")
        self.assertEqual(self.document.version_label, "1.0")
        self.assertIsNotNone(self.document.effective_date)

    def test_start_revision_bumps_minor_version_and_returns_to_draft(self):
        self.document.status = "published"
        self.document.version_label = "1.0"
        self.document.save()
        start_revision(self.document, self.user)
        self.assertEqual(self.document.version_label, "1.1")
        self.assertEqual(self.document.status, "draft")


class AIDraftGovernanceTests(TestCase):
    """Verifies spec §13/§23: AI-generated content must never
    automatically become an approved/published controlled document."""

    def setUp(self):
        call_command("seed_frameworks")
        call_command("seed_journey_templates")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        from frameworks.models import Framework

        framework = Framework.objects.get(code="ISO27001")
        template = framework.journey_templates.get(goal_type="build_from_scratch")
        self.journey = start_journey(self.org, template, self.user)
        self.scope_step = template.steps.get(produces_document_type="isms_scope")
        set_item(self.org, "organisation_profile", "Type", "Skills Development Provider", status="verified")

    def test_generated_draft_starts_as_draft_status_not_published(self):
        document = generate_draft_for_step(self.org, self.scope_step, self.user)
        self.assertEqual(document.status, "draft")
        self.assertTrue(document.ai_generated)
        self.assertEqual(document.ai_generation.review_status, AI_PENDING)

    def test_generated_draft_uses_verified_knowledge_context(self):
        document = generate_draft_for_step(self.org, self.scope_step, self.user)
        self.assertIn("Skills Development Provider", document.content)

    def test_full_review_approve_publish_marks_ai_generation_approved(self):
        document = generate_draft_for_step(self.org, self.scope_step, self.user)
        submit_for_review(document, self.user)
        submit_for_approval(document, self.user)
        document.status = "approved"
        document.save()
        publish(document, self.user)
        document.ai_generation.refresh_from_db()
        self.assertIn(document.ai_generation.review_status, ["approved", "edited"])

    def test_publishing_isms_scope_completes_journey_step(self):
        document = generate_draft_for_step(self.org, self.scope_step, self.user)
        document.status = "approved"
        document.save()
        self.client.login(email="a@example.com", password="StrongPass123!")
        self.client.get(reverse("core:dashboard"))  # resolves active org via middleware
        response = self.client.post(reverse("documents:publish", args=[document.pk]))
        self.assertEqual(response.status_code, 302)
        progress = self.journey.step_progress.get(step=self.scope_step)
        self.assertEqual(progress.status, "completed")


class DocumentTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.doc_b = Document.objects.create(organisation=self.org_b, title="Org B secret policy")

    def test_org_a_cannot_view_org_b_document(self):
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("documents:detail", args=[self.doc_b.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_a_document_list_excludes_org_b(self):
        Document.objects.create(organisation=self.org_a, title="Org A policy")
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("documents:list"))
        self.assertContains(response, "Org A policy")
        self.assertNotContains(response, "Org B secret policy")

    def test_org_a_cannot_download_org_b_document_attachment(self):
        self.doc_b.attachment = SimpleUploadedFile("secret.pdf", b"org-b-confidential")
        self.doc_b.save()
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("documents:download", args=[self.doc_b.pk]))
        self.assertEqual(response.status_code, 404)


class DocumentDownloadTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="Org A")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.document = Document.objects.create(
            organisation=self.org, title="Policy", attachment=SimpleUploadedFile("policy.pdf", b"policy-bytes")
        )
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_same_org_member_can_download(self):
        response = self.client.get(reverse("documents:download", args=[self.document.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response.streaming_content), b"policy-bytes")


class DocumentFormIDORTests(TestCase):
    def setUp(self):
        from frameworks.models import Framework

        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.framework_b = Framework.objects.create(name="Org B Private Framework", code="ORGB", organisation=self.org_b)

    def test_form_queryset_excludes_other_orgs_private_framework(self):
        from .forms import DocumentForm

        form = DocumentForm(organisation=self.org_a)
        self.assertNotIn(self.framework_b, form.fields["related_frameworks"].queryset)
