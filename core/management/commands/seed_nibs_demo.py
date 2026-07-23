"""
Seeds the NIBS demonstration tenant and walks it through the full
end-to-end scenario described in spec §47:

Create Organisation -> Build an ISMS -> ISO/IEC 27001 -> Organisation
Interview -> Request Missing Information -> Knowledge Profile ->
Generate Draft ISMS Scope -> Human Review -> Approval -> Electronic
Sign-Off -> Controlled Document -> Continue Guided Implementation ->
Policies -> Risk Assessment -> Controls -> Statement of Applicability
-> Evidence -> Internal Audit -> Management Review -> Corrective
Actions -> Audit Readiness.

Every record created here is fictional demonstration data (spec §15) —
no real client, employee or operational information. Re-running this
command is safe: it is idempotent on the organisation name/slug and
will not create a second demo tenant.

This command exercises the SAME service-layer functions the real UI
calls (journeys.services, documents.services, frameworks.services,
etc.) rather than re-implementing the workflow — so seeding this data
is itself a form of integration coverage for the real business logic.
"""

import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from actions.models import CorrectiveAction
from approvals.models import REQUEST_APPROVED, ApprovalRequest, Signature
from audits.models import Audit, AuditFinding
from controls.models import Control, SoAEntry
from controls.services import ensure_baseline_controls, ensure_soa_entries
from documents.services import generate_draft_for_step, publish, submit_for_approval, submit_for_review
from evidence.models import Evidence
from frameworks.models import Framework
from frameworks.services import adopt_framework, set_requirement_status
from activity.utils import log_activity
from assets.models import Asset
from incidents.models import ChangeEvent, Incident
from journeys.models import InformationRequest, InterviewExchange, InterviewSession
from journeys.services import mark_step_complete, start_journey
from knowledge.models import STATUS_AI_INFERENCE, STATUS_VERIFIED
from knowledge.services import set_item
from registers.models import RegisterEntry, RegisterType
from registers.services import ensure_default_register_types
from reviews.services import create_review
from risks.models import Risk
from suppliers.models import Supplier
from tenancy.models import Membership, Organisation

User = get_user_model()

DEMO_PASSWORD = "NibsDemo2026!"


class Command(BaseCommand):
    help = "Seed the fictional NIBS demonstration tenant and walk it through the full ISO 27001 journey (spec §47)."

    def handle(self, *args, **options):
        call_command("seed_frameworks", verbosity=0)
        call_command("seed_journey_templates", verbosity=0)
        ensure_default_register_types()

        org, created = Organisation.objects.get_or_create(
            name="Naleli Innovators Business School (NIBS)",
            defaults=dict(
                organisation_type="sdp",
                industry="Skills Development & Training",
                registration_number="2016/000000/07",
                country="South Africa",
                province="Gauteng",
                size="11-50",
                is_demo=True,
            ),
        )
        if not created:
            self.stdout.write(self.style.WARNING(f"'{org.name}' already exists — skipping re-seed."))
            self._print_credentials(org)
            return

        users = self._create_users(org)
        log_activity(
            None, "created", target=org, organisation=org, actor=users["thabiso"],
            description=f"Organisation created: {org.name}",
        )
        self._build_knowledge_profile(org, users)
        self._information_request(org, users)

        journey = self._start_journey(org, users)
        steps = {s.order: s for s in journey.template.steps.all()}

        self._step_understand_org(journey, steps[1], users)
        self._step_isms_scope(org, journey, steps[2], users)
        self._step_leadership(journey, steps[3], users)
        self._step_policy(org, journey, steps[4], users)
        self._step_objectives(journey, steps[5], users)
        self._step_risk_assessment(org, journey, steps[6], users)
        self._step_controls_soa(org, journey, steps[7], users)
        self._step_support(org, journey, steps[8], users)
        self._step_evidence(org, journey, steps[9], users)
        self._step_internal_audit(org, journey, steps[10], users)
        self._step_management_review(org, journey, steps[11], users)
        self._step_corrective_actions(org, journey, steps[12], users)
        # Step 13 (Audit Readiness) is deliberately left as the current
        # step — a first-time viewer lands on "what's next" rather than
        # a fully completed journey, matching the product's own
        # 'what should I do next' principle (spec §46).

        self._adopt_secondary_frameworks(org)
        self._incident_and_change_event(org, users)
        self._assets_and_suppliers(org, users)

        self.stdout.write(self.style.SUCCESS(f"NIBS demonstration tenant seeded: {org.name}"))
        self._print_credentials(org)

    # ------------------------------------------------------------ setup

    def _create_users(self, org):
        people = [
            ("thabiso@bohlale-demo.example", "Thabiso", "Mokoena", "GRC Consultant", "consultant"),
            ("naledi@nibs-demo.example", "Naledi", "Khumalo", "Chief Executive Officer", "executive"),
            ("sipho@nibs-demo.example", "Sipho", "Nkosi", "IT Manager", "contributor"),
            ("nokuthula@nibs-demo.example", "Nokuthula", "Dlamini", "HR Manager", "contributor"),
            ("lerato@nibs-demo.example", "Lerato", "Mahlangu", "Information Officer", "compliance_manager"),
        ]
        users = {}
        for email, first, last, job_title, role in people:
            user, was_created = User.objects.get_or_create(
                email=email, defaults=dict(first_name=first, last_name=last, job_title=job_title)
            )
            if was_created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            Membership.objects.get_or_create(organisation=org, user=user, defaults={"role": role})
            users[email.split("@")[0]] = user
        return users

    def _print_credentials(self, org):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo login (all fictional users share one password):"))
        self.stdout.write(f"  Password: {DEMO_PASSWORD}")
        self.stdout.write("  thabiso@bohlale-demo.example   — GRC Consultant (org_admin-equivalent)")
        self.stdout.write("  naledi@nibs-demo.example       — CEO / Executive Approver")
        self.stdout.write("  sipho@nibs-demo.example        — IT Manager")
        self.stdout.write("  nokuthula@nibs-demo.example    — HR Manager")
        self.stdout.write("  lerato@nibs-demo.example       — Information Officer / Compliance Manager")
        self.stdout.write(f"  Organisation: {org.name}")

    def _build_knowledge_profile(self, org, users):
        facts = [
            ("organisation_profile", "Legal name", "Naleli Innovators Business School (Pty) Ltd"),
            ("organisation_profile", "Sector", "Private skills development provider (accredited training)"),
            ("business_activities", "Primary activity",
             "Accredited business administration, leadership and digital-skills training for corporate and "
             "public-sector clients across South Africa."),
            ("locations", "Head office", "Johannesburg, Gauteng, South Africa — single site, hybrid staff."),
            ("departments", "Key departments", "Programme Delivery, Learner Support, IT, HR, Finance."),
            ("systems", "Learning Management System", "Cloud-hosted SaaS LMS used to deliver and track accredited training."),
            ("systems", "Productivity suite", "Google Workspace for staff email, documents and collaboration."),
            ("suppliers", "Key technology suppliers", "LMS SaaS provider; Google Workspace; local IT support contractor."),
            ("personal_information", "Categories processed",
             "Learner personal information (ID numbers, contact details, results), staff HR records, client contact details."),
            ("regulatory_requirements", "Key obligations", "POPIA; SETA accreditation and reporting requirements."),
        ]
        for category, label, value in facts:
            set_item(org, category, label, value, status=STATUS_VERIFIED, source="Organisation Interview", user=users["thabiso"])

    def _information_request(self, org, users):
        request = InformationRequest.objects.create(
            organisation=org,
            requested_by=users["thabiso"],
            assigned_to_user=users["sipho"],
            assigned_role_label="IT Manager",
            question_text="Which cloud providers and information systems support the LMS and learner records?",
            knowledge_category="systems",
            knowledge_label="Cloud infrastructure",
        )
        request.status = "answered"
        request.response_text = (
            "The LMS is hosted with our SaaS provider on their African region infrastructure; learner records "
            "sync nightly to a backup store managed by the same provider. Staff productivity runs on Google "
            "Workspace."
        )
        request.responded_at = timezone.now()
        request.save()
        set_item(
            org, "systems", "Cloud infrastructure", request.response_text,
            status=STATUS_AI_INFERENCE, source="Information Request response from IT Manager",
        )

    # ---------------------------------------------------------- journey

    def _start_journey(self, org, users):
        framework = Framework.objects.get(code="ISO27001")
        template = framework.journey_templates.get(goal_type="build_from_scratch")
        journey = start_journey(org, template, users["thabiso"])
        log_activity(
            None, "started", target=journey, organisation=org, actor=users["thabiso"],
            description=f"Started guided journey: {template.name}",
        )
        return journey

    # Some ISO 27001 clauses are genuinely covered by a broader guided
    # step even though the journey only links one "primary" requirement
    # per step (spec §8 steps are coarser than the standard's granular
    # clause list). Mapping these sibling clauses avoids the demo
    # looking artificially incomplete on the Compliance Overview
    # (framework-wide requirement completion) while the guided journey
    # itself shows 12/13 steps done.
    SIBLING_REQUIREMENTS = {
        1: ["4.2"],                        # Understand your organisation -> Interested Parties
        2: ["4.4"],                        # ISMS Scope -> the ISMS itself (clause 4.4)
        3: ["5.3"],                        # Leadership & roles -> Organisational roles
        6: ["8.2"],                        # Risk assessment -> ongoing risk assessment
        8: ["7.1", "7.3", "7.4", "7.5"],   # Support -> resources/awareness/communication/docs
        11: ["9.1"],                       # Management review -> monitoring, measurement, analysis
    }

    def _complete_requirement(self, org, step, status="complete"):
        if step.requirement_id:
            set_requirement_status(org, step.requirement, status)
        framework = step.template.framework
        if status == "complete" and framework:
            for ref_code in self.SIBLING_REQUIREMENTS.get(step.order, []):
                requirement = framework.requirements.filter(ref_code=ref_code).first()
                if requirement:
                    set_requirement_status(org, requirement, status)

    def _step_understand_org(self, journey, step, users):
        session = InterviewSession.objects.create(organisation=journey.organisation, step=step, started_by=users["thabiso"], status="completed")
        answers = [
            "NIBS is a private skills development provider delivering accredited business, leadership and "
            "digital-skills training to corporate and public-sector learners.",
            "Only the Johannesburg head office; all staff and systems are included, no other sites.",
            "Programme delivery, learner registration and assessment, and client/SETA reporting.",
            "Yes — the LMS is a SaaS product hosted by our cloud LMS provider; Google Workspace is used for productivity.",
            "The LMS SaaS provider and Google Workspace are the two key technology suppliers.",
        ]
        for i, question in enumerate(step.guidance_questions, start=1):
            InterviewExchange.objects.create(
                session=session, order=i, question_text=question,
                answer_text=answers[(i - 1) % len(answers)], answered_at=timezone.now(),
            )
        self._complete_requirement(journey.organisation, step)
        mark_step_complete(journey, step, users["thabiso"], notes="Organisation interview completed.")

    def _approve_and_publish(self, document, journey, requested_by, approver):
        submit_for_review(document, requested_by)
        approval_request = submit_for_approval(document, requested_by)
        Signature.objects.create(
            approval_request=approval_request,
            approver=approver,
            role="Executive / Approver",
            decision="approved",
            typed_signature=approver.get_full_name(),
            consent=True,
            document_version=document.version_label,
            document_hash=document.content_hash(),
            ip_address="127.0.0.1",
        )
        approval_request.status = REQUEST_APPROVED
        approval_request.decided_at = timezone.now()
        approval_request.save(update_fields=["status", "decided_at"])
        log_activity(
            None, "approved", target=document, organisation=document.organisation, actor=approver,
            description=f"Approved and electronically signed: {document.title}",
        )

        document.status = "approved"
        document.approver = approver
        document.approval_date = timezone.now().date()
        document.save(update_fields=["status", "approver", "approval_date", "updated_at"])

        publish(document, requested_by)
        log_activity(
            None, "published", target=document, organisation=document.organisation, actor=requested_by,
            description=f"Published: {document.title} v{document.version_label}",
        )
        if document.journey_step:
            self._complete_requirement(document.organisation, document.journey_step)
            mark_step_complete(journey, document.journey_step, requested_by, notes="Published and communicated.")
        return document

    def _step_isms_scope(self, org, journey, step, users):
        document = generate_draft_for_step(org, step, users["thabiso"])
        log_activity(
            None, "generated", target=document, organisation=org, actor=users["thabiso"],
            description=f"AI generated {document.get_doc_type_display()} draft (v{document.version_label})",
        )
        document.content = (
            document.content
            + "\n\nScope confirmed by the ISMS Manager: covers the Johannesburg head office, the LMS platform, "
            "Google Workspace, and all learner and staff personal information processed by NIBS. Excludes "
            "personal devices not enrolled in mobile device management."
        )
        document.next_review_date = timezone.now().date() + datetime.timedelta(days=365)
        document.save()
        self._approve_and_publish(document, journey, users["thabiso"], users["naledi"])

    def _step_leadership(self, journey, step, users):
        self._complete_requirement(journey.organisation, step)
        mark_step_complete(journey, step, users["naledi"], notes="CEO confirmed ISMS Manager and Control Owner appointments.")

    def _step_policy(self, org, journey, step, users):
        document = generate_draft_for_step(org, step, users["thabiso"])
        log_activity(
            None, "generated", target=document, organisation=org, actor=users["thabiso"],
            description=f"AI generated {document.get_doc_type_display()} draft (v{document.version_label})",
        )
        document.next_review_date = timezone.now().date() + datetime.timedelta(days=365)
        document.save()
        self._approve_and_publish(document, journey, users["thabiso"], users["naledi"])

    def _step_objectives(self, journey, step, users):
        self._complete_requirement(journey.organisation, step)
        mark_step_complete(
            journey, step, users["thabiso"],
            notes="Objective set: zero overdue access reviews and 100% security awareness training completion by year end.",
        )

    def _step_risk_assessment(self, org, journey, step, users):
        risks = [
            dict(title="Phishing compromise of staff email", category="information_security", threat="Targeted phishing email",
                 vulnerability="Limited security awareness training", likelihood=4, impact=4, treatment="mitigate"),
            dict(title="Unauthorised access to learner records", category="information_security", threat="Weak access controls on LMS",
                 vulnerability="Shared LMS admin credentials", likelihood=3, impact=5, treatment="mitigate"),
            dict(title="Loss of LMS availability during peak enrolment", category="operational", threat="SaaS provider outage",
                 vulnerability="No documented business continuity plan", likelihood=2, impact=4, treatment="mitigate"),
            dict(title="POPIA non-compliance in learner data handling", category="compliance", threat="Regulatory investigation",
                 vulnerability="No documented processing register", likelihood=3, impact=4, treatment="mitigate"),
            dict(title="Key IT staff departure", category="people", threat="Sole IT administrator resigns",
                 vulnerability="No documented handover procedures", likelihood=2, impact=3, treatment="accept"),
            dict(title="Cloud LMS supplier data breach", category="third_party", threat="Supplier security incident",
                 vulnerability="No supplier security assessment on file", likelihood=2, impact=5, treatment="transfer"),
        ]
        for spec in risks:
            residual_likelihood = max(1, spec["likelihood"] - 2)
            residual_impact = max(1, spec["impact"] - 1)
            Risk.objects.create(
                organisation=org,
                title=spec["title"], category=spec["category"], threat=spec["threat"],
                vulnerability=spec["vulnerability"], likelihood=spec["likelihood"], impact=spec["impact"],
                residual_likelihood=residual_likelihood, residual_impact=residual_impact,
                owner=users["sipho"], treatment=spec["treatment"], treatment_owner=users["sipho"],
                treatment_plan="Mitigating controls implemented and tracked via the control library and SoA.",
                due_date=timezone.now().date() + datetime.timedelta(days=60),
                status="in_treatment",
            )
        log_activity(
            None, "updated", organisation=org, actor=users["thabiso"],
            description=f"Risk Register updated: {len(risks)} risks identified and rated",
        )
        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["thabiso"], notes="Initial risk assessment completed for in-scope assets and processes.")

    def _step_controls_soa(self, org, journey, step, users):
        ensure_baseline_controls(org)
        framework = Framework.objects.get(code="ISO27001")
        ensure_soa_entries(org, framework)

        implemented = {"Access Control", "Cryptographic Controls", "Incident Management", "Backup",
                       "Logging & Monitoring", "HR Security", "Data Protection & Privacy"}
        partial = {"Business Continuity", "Vulnerability Management", "Supplier Relationships"}
        for control in Control.objects.filter(organisation=org):
            if control.name in implemented:
                control.implementation_status = "implemented"
                control.effectiveness = "effective"
            elif control.name in partial:
                control.implementation_status = "partially_implemented"
                control.effectiveness = "partially_effective"
            else:
                control.implementation_status = "not_implemented"
                control.effectiveness = "not_tested"
            control.owner = users["sipho"]
            control.implementation_notes = "Reviewed during ISO 27001 implementation project."
            control.save()

        for entry in SoAEntry.objects.filter(organisation=org, framework=framework):
            entry.applicable = True
            entry.justification = "Applicable — addresses risks identified in the risk assessment."
            entry.save()

        log_activity(
            None, "updated", organisation=org, actor=users["sipho"],
            description="Statement of Applicability updated: control implementation status recorded",
        )
        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["thabiso"], notes="Statement of Applicability completed for all controls.")

    def _step_support(self, org, journey, step, users):
        register_type = RegisterType.objects.filter(slug="training").first()
        if register_type:
            RegisterEntry.objects.create(
                organisation=org, register_type=register_type, created_by=users["nokuthula"],
                data={
                    "topic": "Information Security Awareness", "audience": "All staff",
                    "date_completed": str(timezone.now().date() - datetime.timedelta(days=20)),
                    "status": "Completed",
                },
            )
        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["nokuthula"], notes="Security awareness training delivered to all staff.")

    def _step_evidence(self, org, journey, step, users):
        controls = {c.name: c for c in Control.objects.filter(organisation=org)}
        evidence_specs = [
            ("Access review export — Q1 2026", "log_export", ["Access Control"]),
            ("Backup job success logs — March 2026", "log_export", ["Backup"]),
            ("Security awareness training attendance register", "record", ["HR Security"]),
            ("MFA configuration screenshot — Google Workspace", "screenshot", ["Access Control", "Cryptographic Controls"]),
        ]
        for name, evidence_type, control_names in evidence_specs:
            evidence = Evidence.objects.create(
                organisation=org, name=name, evidence_type=evidence_type,
                owner=users["sipho"], uploaded_by=users["nokuthula"] if "training" in name.lower() else users["sipho"],
                verification_status="verified",
                notes="Collected during ISO 27001 implementation evidence-gathering.",
            )
            for control_name in control_names:
                control = controls.get(control_name)
                if control:
                    evidence.related_controls.add(control)
            log_activity(
                None, "uploaded", target=evidence, organisation=org, actor=evidence.uploaded_by,
                description=f"Evidence uploaded: {evidence.name}",
            )
        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["sipho"], notes="Initial evidence collected for implemented controls.")

    def _step_internal_audit(self, org, journey, step, users):
        framework = Framework.objects.get(code="ISO27001")
        audit = Audit.objects.create(
            organisation=org, title="ISO 27001 Internal Audit — 2026 Cycle 1", audit_type="internal",
            framework=framework, scope="Full ISMS scope per the approved ISMS Scope document.",
            lead_auditor=users["lerato"],
            scheduled_date=timezone.now().date() - datetime.timedelta(days=10),
            start_date=timezone.now().date() - datetime.timedelta(days=7),
            end_date=timezone.now().date() - datetime.timedelta(days=5),
            status="findings_recorded",
        )
        finding_minor = AuditFinding.objects.create(
            organisation=org, audit=audit,
            description="Access reviews are performed but not consistently documented with sign-off.",
            severity="minor_nonconformity", status="open",
        )
        AuditFinding.objects.create(
            organisation=org, audit=audit,
            description="Backup restoration has not yet been tested end-to-end.",
            severity="observation", status="open",
        )
        audit.status = "closed"
        audit.closed_at = timezone.now()
        audit.save(update_fields=["status", "closed_at", "updated_at"])
        log_activity(
            None, "closed", target=audit, organisation=org, actor=users["lerato"],
            description=f"Internal audit closed: {audit.title} (2 findings)",
        )

        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["lerato"], notes="Internal audit closed; two findings raised.")
        return finding_minor

    def _step_management_review(self, org, journey, step, users):
        framework = Framework.objects.get(code="ISO27001")
        review = create_review(
            org, framework=framework,
            meeting_date=timezone.now().date() - datetime.timedelta(days=2),
            attendees="Naledi Khumalo (CEO), Thabiso Mokoena (GRC Consultant), Sipho Nkosi (IT Manager), "
                       "Lerato Mahlangu (Information Officer)",
            agenda="Quarterly ISMS management review: risk status, audit results, objectives, improvement opportunities.",
            decisions="Approved continued investment in security awareness training; agreed to close open "
                      "corrective actions within 30 days; approved budget for a supplier security assessment.",
            status="draft",
        )
        for record in review.input_records.all():
            record.covered = True
            record.notes = "Reviewed with management team."
            record.save()
        review.status = "completed"
        review.approved_by = users["naledi"]
        review.save(update_fields=["status", "approved_by", "updated_at"])
        log_activity(
            None, "completed", target=review, organisation=org, actor=users["naledi"],
            description=f"Management review completed: {review.reference_code}",
        )

        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["naledi"], notes="Management review completed and minuted.")

    def _step_corrective_actions(self, org, journey, step, users):
        from django.contrib.contenttypes.models import ContentType

        finding = AuditFinding.objects.filter(organisation=org, severity="minor_nonconformity").first()
        action1 = CorrectiveAction.objects.create(
            organisation=org, source="audit",
            content_type=ContentType.objects.get_for_model(AuditFinding) if finding else None,
            object_id=str(finding.pk) if finding else None,
            finding_description="Access reviews are performed but not consistently documented with sign-off.",
            severity="medium", root_cause="No standard access-review template with sign-off requirement.",
            action_description="Introduce a standard quarterly access-review template requiring manager sign-off.",
            owner=users["sipho"], due_date=timezone.now().date() + datetime.timedelta(days=30), status="in_progress",
        )
        CorrectiveAction.objects.create(
            organisation=org, source="other",
            finding_description="Backup restoration has not yet been tested end-to-end.",
            severity="low", root_cause="No scheduled restoration test.",
            action_description="Schedule and document a full backup restoration test.",
            owner=users["sipho"],
            due_date=timezone.now().date() - datetime.timedelta(days=3),
            status="closed", verified_by=users["lerato"],
            verification_notes="Restoration test completed successfully; logs attached as evidence.",
            closed_at=timezone.now(),
        )
        log_activity(
            None, "created", target=action1, organisation=org, actor=users["thabiso"],
            description="Corrective action logged from internal audit finding",
        )
        self._complete_requirement(org, step)
        mark_step_complete(journey, step, users["thabiso"], notes="Corrective actions logged and tracked to closure.")

    # ---------------------------------------------------- extra flavour

    def _adopt_secondary_frameworks(self, org):
        for code, complete_count in [("POPIA", 4), ("KING_IV", 1), ("ISO9001", 1)]:
            framework = Framework.objects.filter(code=code, organisation__isnull=True).first()
            if not framework:
                continue
            adopt_framework(org, framework)
            requirements = list(framework.requirements.all()[:complete_count])
            for requirement in requirements:
                set_requirement_status(org, requirement, "complete")

    def _incident_and_change_event(self, org, users):
        incident = Incident.objects.create(
            organisation=org, title="Staff laptop left on public transport",
            description="An IT staff laptop was left on a minibus taxi after hours. The device was "
                        "full-disk encrypted and remotely wiped as a precaution.",
            occurred_at=timezone.now() - datetime.timedelta(days=15),
            discovered_at=timezone.now() - datetime.timedelta(days=15),
            discovered_by=users["sipho"], systems_affected="Staff laptop (encrypted)",
            information_affected="No learner data stored locally on the device.",
            personal_info_involved=False, severity="low",
            immediate_actions="Device remotely wiped; password reset for the affected staff account.",
            status="resolved",
        )
        log_activity(
            None, "reported", target=incident, organisation=org, actor=users["sipho"],
            description=f"Incident reported: {incident.title}",
        )
        ChangeEvent.objects.create(
            organisation=org, event_type="new_supplier",
            description="Engaged a new cloud backup provider for offsite backup storage.",
            reported_by=users["sipho"], status="reviewed",
            review_notes="Added to the Supplier Register and Risk Register; reviewed by IT Manager.",
        )

    def _assets_and_suppliers(self, org, users):
        Asset.objects.create(
            organisation=org, name="Learning Management System", asset_type="application",
            owner=users["sipho"], classification="confidential", location="Cloud (SaaS)",
            related_process="Programme delivery and learner assessment", status="active",
        )
        Asset.objects.create(
            organisation=org, name="Google Workspace tenant", asset_type="application",
            owner=users["sipho"], classification="internal", location="Cloud (SaaS)",
            related_process="Staff collaboration and email", status="active",
        )
        Supplier.objects.create(
            organisation=org, name="CloudLearn Hosting (Pty) Ltd", service="LMS SaaS hosting",
            owner=users["sipho"], criticality="high", data_access=True, personal_info_access=True,
            risk_rating="medium", assessment_notes="Annual security questionnaire on file.",
            review_date=timezone.now().date() + datetime.timedelta(days=180),
        )
