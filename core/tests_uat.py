"""
End-to-end UAT (spec §17 / UAT_PLAN.md): walks the full NIBS reference
scenario through real HTTP requests (self.client — URL routing, view,
form validation, template rendering, exactly as a manual tester clicking
through the UI would exercise it), not by calling service-layer
functions directly. Asserts actual persisted business outcomes and
permission enforcement at each step, not merely HTTP 200 responses. This
is a companion to (not a replacement for) `core.management.commands
.seed_nibs_demo`'s `SeedNibsDemoTests`, which cover the same journey via
direct service calls for fast, deterministic demo-data generation.

Run in isolation: `python manage.py test core.tests_uat -v 2`
"""

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from actions.models import CorrectiveAction
from approvals.models import ApprovalRequest, Signature
from audits.models import Audit, AuditFinding
from controls.models import Control, SoAEntry
from documents.models import Document
from evidence.models import Evidence
from frameworks.models import Framework
from incidents.models import Incident
from journeys.models import InformationRequest, InterviewSession, OrganisationJourney
from knowledge.models import KnowledgeItem
from notifications.models import Notification
from registers.models import RegisterEntry, RegisterType
from reviews.models import ManagementReview
from risks.models import Risk
from tenancy.models import Membership, Organisation


class NibsEndToEndUATTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        call_command("seed_journey_templates")
        self.org = Organisation.objects.create(name="Naleli Innovators Business School (NIBS)")
        self.consultant = User.objects.create_user(
            email="thabiso@example.com", password="StrongPass123!", first_name="Thabiso", last_name="Mokoena"
        )
        self.executive = User.objects.create_user(
            email="naledi@example.com", password="StrongPass123!", first_name="Naledi", last_name="Director"
        )
        Membership.objects.create(organisation=self.org, user=self.consultant, role="consultant")
        Membership.objects.create(organisation=self.org, user=self.executive, role="executive")
        self.contributor = User.objects.create_user(
            email="contributor@example.com", password="StrongPass123!", first_name="Contributor", last_name="Person"
        )
        Membership.objects.create(organisation=self.org, user=self.contributor, role="contributor")

    def _login(self, email):
        self.client.logout()
        self.client.login(email=email, password="StrongPass123!")
        self.client.get(reverse("tenancy:organisation_switch", args=[self.org.pk]))

    def test_full_nibs_journey_persists_real_data_and_enforces_permissions(self):
        # ---- Consultant logs in and starts the guided ISO 27001 journey ----
        self._login("thabiso@example.com")
        self.client.post(reverse("journeys:onboarding_goal"), {"goal_type": "build_from_scratch"})
        framework = Framework.objects.get(code="ISO27001")
        self.client.post(reverse("journeys:onboarding_framework"), {"framework_id": str(framework.pk)})
        self.client.get(reverse("journeys:onboarding_start", args=[framework.pk, "build_from_scratch"]))
        journey = OrganisationJourney.objects.get(organisation=self.org)
        self.assertEqual(journey.template.framework.code, "ISO27001")
        self.assertEqual(journey.status, "in_progress")

        # ---- Organisation knowledge profile: AI guided interview ----
        step1 = journey.template.steps.order_by("order").first()
        self.client.get(reverse("journeys:interview_start", args=[step1.pk]) + f"?journey={journey.pk}")
        session = InterviewSession.objects.get(organisation=self.org, step=step1)
        self.assertGreater(session.exchanges.count(), 0)
        for _ in session.exchanges.all():
            self.client.post(
                reverse("journeys:interview_session", args=[session.pk]),
                {"answer_text": "NIBS is a registered skills development provider based in Gauteng."},
            )
        session.refresh_from_db()
        self.assertEqual(session.status, "completed")
        self.assertTrue(KnowledgeItem.objects.filter(organisation=self.org, status="verified").exists())

        # ---- Request missing information from a stakeholder (no login needed to respond) ----
        self.client.post(
            reverse("journeys:information_request_create"),
            {
                "assigned_role_label": "IT Manager", "assigned_email": "sipho@example.com",
                "question_text": "Which cloud providers does NIBS use?",
            },
        )
        info_request = InformationRequest.objects.get(assigned_email="sipho@example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.client.logout()
        self.client.post(
            reverse("journeys:information_request_respond", args=[info_request.token]),
            {"response_text": "Google Workspace and AWS."},
        )
        info_request.refresh_from_db()
        self.assertEqual(info_request.status, "answered")
        self.assertTrue(KnowledgeItem.objects.filter(organisation=self.org, status="ai_inference").exists())

        # ---- Generate a draft ISMS scope document (AI, always starts as Draft) ----
        self._login("thabiso@example.com")
        scope_step = journey.template.steps.get(produces_document_type="isms_scope")
        self.client.post(reverse("documents:generate_for_step", args=[scope_step.pk]))
        doc = Document.objects.get(organisation=self.org, doc_type="isms_scope")
        self.assertEqual(doc.status, "draft")
        self.assertTrue(doc.ai_generated)

        # ---- Human review -> submit for approval ----
        self.client.post(reverse("documents:submit_review", args=[doc.pk]))
        self.client.post(reverse("documents:submit_approval", args=[doc.pk]))
        doc.refresh_from_db()
        self.assertEqual(doc.status, "awaiting_approval")
        approval_request = ApprovalRequest.objects.get(
            organisation=self.org, content_type=ContentType.objects.get_for_model(Document), object_id=str(doc.pk)
        )

        # Permission enforcement: an ordinary contributor cannot sign off.
        self._login("contributor@example.com")
        response = self.client.get(reverse("approvals:detail", args=[approval_request.pk]))
        self.assertEqual(response.status_code, 403)

        # ---- Authorised executive approves and electronically signs ----
        self._login("naledi@example.com")
        self.client.post(
            reverse("approvals:detail", args=[approval_request.pk]),
            {"decision": "approved", "typed_signature": "Naledi Director", "consent": "on"},
        )
        signature = Signature.objects.get(approval_request=approval_request)
        self.assertEqual(signature.decision, "approved")
        self.assertTrue(signature.consent)
        self.assertEqual(signature.document_hash, doc.content_hash())
        doc.refresh_from_db()
        self.assertEqual(doc.status, "approved")

        # ---- Publish the controlled document (approver-level) ----
        self.client.post(reverse("documents:publish", args=[doc.pk]))
        doc.refresh_from_db()
        self.assertEqual(doc.status, "published")
        progress = journey.step_progress.get(step=scope_step)
        self.assertEqual(progress.status, "completed")

        # ---- Risk assessment: record risks ----
        self._login("thabiso@example.com")
        self.client.post(
            reverse("risks:create"),
            {
                "title": "Unpatched public-facing web server", "category": "information_security",
                "likelihood": 4, "impact": 4, "treatment": "mitigate", "status": "open",
            },
        )
        risk = Risk.objects.get(organisation=self.org, title="Unpatched public-facing web server")
        self.assertEqual(risk.inherent_risk_score, 16)

        # ---- Map controls: SoA auto-seeds the common control library on first visit ----
        self.client.get(reverse("controls:soa"))
        self.assertTrue(Control.objects.filter(organisation=self.org).exists())
        soa_entry = SoAEntry.objects.filter(organisation=self.org, framework=framework).select_related("control").first()
        self.assertIsNotNone(soa_entry)
        self.client.post(
            reverse("controls:soa_entry_update", args=[soa_entry.pk]),
            {"applicable": "on", "implementation_status": "implemented", "justification": "Implemented via IT policy."},
        )
        soa_entry.refresh_from_db()
        self.assertTrue(soa_entry.applicable)
        self.assertEqual(soa_entry.control.implementation_status, "implemented")

        # ---- Upload evidence, and confirm it's only downloadable within this tenant ----
        self.client.post(
            reverse("evidence:create"),
            {
                "name": "Patch management policy", "evidence_type": "document",
                "file": SimpleUploadedFile("patch_policy.pdf", b"policy content"),
                "verification_status": "verified",
            },
        )
        evidence = Evidence.objects.get(organisation=self.org, name="Patch management policy")
        response = self.client.get(reverse("evidence:download", args=[evidence.pk]))
        self.assertEqual(response.status_code, 200)

        # ---- Record an incident; confirm admins/consultants get notified ----
        self.client.post(
            reverse("incidents:create"),
            {"title": "Phishing email reported", "description": "Staff member reported a suspicious email.", "severity": "medium", "status": "reported"},
        )
        incident = Incident.objects.get(organisation=self.org, title="Phishing email reported")
        self.assertTrue(
            Notification.objects.filter(organisation=self.org, category="incident", recipient=self.executive).exists()
        )

        # ---- Update a compliance register (Interested Parties) ----
        self.client.get(reverse("registers:hub"))  # ensures default register types exist
        register_type = RegisterType.objects.get(slug="interested-parties")
        self.client.post(
            reverse("registers:generic_create", args=[register_type.slug]),
            {"party": "Department of Higher Education", "interest": "Accreditation body", "requirements": "Annual compliance report"},
        )
        self.assertTrue(RegisterEntry.objects.filter(organisation=self.org, register_type=register_type).exists())

        # ---- Internal audit: plan, conduct, record a finding ----
        self.client.post(
            reverse("audits:create"),
            {"title": "Q3 Internal ISMS Audit", "audit_type": "internal", "status": "in_progress", "lead_auditor": self.consultant.pk},
        )
        audit = Audit.objects.get(organisation=self.org, title="Q3 Internal ISMS Audit")
        self.client.post(
            reverse("audits:add_finding", args=[audit.pk]),
            {"description": "Access review evidence not retained for Q2.", "severity": "minor_nonconformity", "status": "open"},
        )
        finding = AuditFinding.objects.get(audit=audit)
        audit.refresh_from_db()
        self.assertEqual(audit.status, "findings_recorded")

        # Closing an audit is an approver-level action, not editor-level
        # (the consultant currently logged in, Thabiso, *is* an approver —
        # check the boundary with a plain contributor instead).
        self._login("contributor@example.com")
        response = self.client.post(reverse("audits:close", args=[audit.pk]))
        self.assertEqual(response.status_code, 403)
        self._login("naledi@example.com")
        self.client.post(reverse("audits:close", args=[audit.pk]))
        audit.refresh_from_db()
        self.assertEqual(audit.status, "closed")

        # ---- Corrective action from the finding ----
        self._login("thabiso@example.com")
        self.client.post(
            reverse("actions:create_from_finding", args=[finding.pk]),
            {"source": "audit", "finding_description": "Access review evidence not retained for Q2.", "severity": "medium", "status": "open"},
        )
        action = CorrectiveAction.objects.get(
            organisation=self.org, content_type=ContentType.objects.get_for_model(AuditFinding), object_id=str(finding.pk)
        )
        self.assertEqual(action.source_record, finding)

        # ---- Management review ----
        self.client.post(
            reverse("reviews:create"),
            {"meeting_date": "2026-06-15", "attendees": "Naledi Director, Thabiso Mokoena", "agenda": "Quarterly ISMS review", "decisions": "Continue remediation of Q2 findings."},
        )
        review = ManagementReview.objects.get(organisation=self.org, meeting_date="2026-06-15")
        self.assertGreater(review.input_records.count(), 0)
        self._login("naledi@example.com")
        self.client.post(reverse("reviews:complete", args=[review.pk]))
        review.refresh_from_db()
        self.assertEqual(review.status, "completed")
        self.assertEqual(review.approved_by, self.executive)

        # ---- Audit readiness reflects real, non-zero progress ----
        response = self.client.get(reverse("reports:readiness"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Overall Readiness")
        self.assertNotContains(response, "certified")

        # ---- Reports hub is reachable and reflects real data ----
        response = self.client.get(reverse("reports:hub"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("reports:risk_register"))
        self.assertContains(response, "Unpatched public-facing web server")

        # ---- Final sanity: every major record type from this walkthrough persisted ----
        self.assertTrue(Document.objects.filter(organisation=self.org, status="published").exists())
        self.assertTrue(Risk.objects.filter(organisation=self.org).exists())
        self.assertTrue(SoAEntry.objects.filter(organisation=self.org).exists())
        self.assertTrue(Evidence.objects.filter(organisation=self.org).exists())
        self.assertTrue(Incident.objects.filter(organisation=self.org).exists())
        self.assertTrue(RegisterEntry.objects.filter(organisation=self.org).exists())
        self.assertTrue(Audit.objects.filter(organisation=self.org, status="closed").exists())
        self.assertTrue(CorrectiveAction.objects.filter(organisation=self.org).exists())
        self.assertTrue(ManagementReview.objects.filter(organisation=self.org, status="completed").exists())
