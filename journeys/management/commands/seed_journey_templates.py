"""
Seeds guided-implementation journey templates. Requires
`seed_frameworks` to have run first (journey steps link to
frameworks.Requirement for context).

The ISO 27001 "Build an ISMS from Scratch" template is hand-authored
with rich guidance to support the full NIBS demonstration workflow
(spec §47). POPIA / King IV / ISO 9001 get a lighter, auto-generated
template (one step per requirement) — documented as a v1 simplification
in BUILD_STATUS.md; they can be enriched the same way later without
any schema change.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from frameworks.models import Framework, Requirement
from journeys.models import JourneyStep, JourneyTemplate


def _req(framework, ref_code):
    return Requirement.objects.filter(framework=framework, ref_code=ref_code).first()


ISO_STEPS = [
    dict(
        order=1, phase="plan", stage_title="Context of the Organisation", stage_order=1,
        req="4.1", title="Understand your organisation",
        step_type="interview",
        description="Before anything else, Bohlale GRC needs to understand what your organisation actually does.",
        guidance_what="A clear picture of your organisation's purpose, activities, locations, people and key relationships.",
        guidance_why="Every later decision — scope, risks, controls — depends on this context being accurate.",
        guidance_who="Organisation Administrator or ISMS Manager, with input from the CEO/Director.",
        guidance_questions=[
            "What does the organisation do, and who are its customers/beneficiaries?",
            "Which locations, business units and departments should be considered?",
            "What are the organisation's key business processes?",
            "Does the organisation use any cloud providers or key technology suppliers?",
            "What personal information does the organisation process, and about whom?",
        ],
        guidance_existing_docs="Company profile, business plan, organograms, existing policies if any.",
        guidance_evidence="Organisational chart, register of business processes, list of locations.",
        completion_criteria="The Organisation Knowledge Profile has verified facts for organisation profile, locations, processes and key systems.",
    ),
    dict(
        order=2, phase="plan", stage_title="Context of the Organisation", stage_order=1,
        req="4.3", title="Define the ISMS scope",
        step_type="document", produces_document_type="isms_scope", requires_approval=True,
        description="Define and document the boundaries and applicability of your Information Security Management System.",
        guidance_what="A written ISMS Scope statement naming what's in scope (and explicitly what's excluded).",
        guidance_why="ISO 27001 requires a defined, documented scope before anything else can be certified or assessed against it.",
        guidance_who="ISMS Manager drafts; Executive/Approver signs off.",
        guidance_questions=[
            "Which locations should be included?",
            "Which business processes are included?",
            "Which information systems support these processes?",
            "Are any locations or business units excluded, and why?",
        ],
        guidance_existing_docs="Any prior scope statements, network diagrams, system inventories.",
        guidance_evidence="Approved ISMS Scope document, executive sign-off record.",
        completion_criteria="The ISMS Scope document is Published (approved and electronically signed).",
    ),
    dict(
        order=3, phase="plan", stage_title="Leadership", stage_order=2,
        req="5.1", title="Establish leadership commitment and roles",
        step_type="info",
        description="Top management commits to the ISMS and assigns information security roles and responsibilities.",
        guidance_what="Documented commitment from leadership, and assigned roles (ISMS Manager, Control Owners, Risk Owners).",
        guidance_why="Without visible leadership commitment and clear ownership, an ISMS stalls after the first audit.",
        guidance_who="CEO/Director, Organisation Administrator.",
        guidance_questions=["Who will own information security day-to-day?", "How will management demonstrate ongoing commitment?"],
        guidance_existing_docs="Organisational chart, terms of reference for any existing committees.",
        guidance_evidence="Meeting minutes recording leadership commitment, role assignment record.",
        completion_criteria="Key ISMS roles are assigned to named individuals in the platform.",
    ),
    dict(
        order=4, phase="plan", stage_title="Leadership", stage_order=2,
        req="5.2", title="Publish the Information Security Policy",
        step_type="document", produces_document_type="information_security_policy", requires_approval=True,
        description="Draft, review and publish the organisation's top-level Information Security Policy.",
        guidance_what="An approved Information Security Policy communicated to all staff.",
        guidance_why="This is the anchor policy that all other security procedures reference.",
        guidance_who="ISMS Manager drafts; Executive approves and signs.",
        guidance_questions=["What are the organisation's information security objectives?", "What existing rules or supplier requirements must the policy reflect?"],
        guidance_existing_docs="Any existing IT acceptable-use rules, supplier security requirements.",
        guidance_evidence="Published Information Security Policy, distribution/acknowledgement record.",
        completion_criteria="The Information Security Policy document is Published.",
    ),
    dict(
        order=5, phase="plan", stage_title="Planning", stage_order=3,
        req="6.2", title="Set information security objectives",
        step_type="info",
        description="Set measurable information security objectives aligned with the policy.",
        guidance_what="A short list of measurable objectives (e.g. reduce overdue access reviews to zero).",
        guidance_why="Objectives give the ISMS something concrete to be measured against at management review.",
        guidance_who="ISMS Manager, with executive sign-off.",
        guidance_questions=["What would 'good' look like in 12 months?"],
        guidance_existing_docs="Business plan / strategic objectives, if any.",
        guidance_evidence="Documented objectives with target dates and owners.",
        completion_criteria="At least one measurable objective is documented for the current period.",
    ),
    dict(
        order=6, phase="plan", stage_title="Planning", stage_order=3,
        req="6.1", title="Perform the risk assessment",
        step_type="risk_assessment",
        description="Identify information security risks and assess their likelihood and impact.",
        guidance_what="A populated risk register with inherent and residual risk ratings.",
        guidance_why="Risk assessment drives which controls are actually needed — it is the heart of ISO 27001.",
        guidance_who="ISMS Manager facilitates; risk owners across the business contribute.",
        guidance_questions=["What could go wrong with the information/systems in scope?", "How likely is it, and how bad would the impact be?", "What controls already reduce this risk?"],
        guidance_existing_docs="Any prior risk registers or incident history.",
        guidance_evidence="Completed risk register entries with ratings and treatment decisions.",
        completion_criteria="All in-scope information assets/processes have at least one assessed risk.",
    ),
    dict(
        order=7, phase="do", stage_title="Operation", stage_order=5,
        req="8.3", title="Select applicable controls and build the Statement of Applicability",
        step_type="controls",
        description="Decide which controls are applicable to treat the identified risks, and record the justification.",
        guidance_what="A completed Statement of Applicability (SoA): each control marked applicable/not applicable with justification.",
        guidance_why="The SoA is the master reference an auditor uses to understand your control decisions.",
        guidance_who="ISMS Manager and Control Owners.",
        guidance_questions=["Does this control address an identified risk?", "Is there a legal, regulatory or contractual reason it must apply?", "Who will own this control?"],
        guidance_existing_docs="Existing IT/security procedures that already implement a control.",
        guidance_evidence="SoA export, control implementation notes.",
        completion_criteria="Every control in the library has an applicability decision recorded.",
    ),
    dict(
        order=8, phase="do", stage_title="Support", stage_order=4,
        req="7.2", title="Provide resources, competence and awareness",
        step_type="info",
        description="Make sure the people operating the ISMS are competent, resourced and aware of their responsibilities.",
        guidance_what="Training/awareness records and evidence that control owners have what they need.",
        guidance_why="Controls fail in practice when the people responsible for them aren't trained or resourced.",
        guidance_who="HR/People Manager, Control Owners.",
        guidance_questions=["Has everyone with a security responsibility been trained?", "Is security awareness communicated to all staff?"],
        guidance_existing_docs="Training registers, induction materials.",
        guidance_evidence="Training attendance records, awareness communications.",
        completion_criteria="A training/awareness record exists covering the current period.",
    ),
    dict(
        order=9, phase="do", stage_title="Operation", stage_order=5,
        req="8.1", title="Collect implementation evidence",
        step_type="evidence",
        description="Gather evidence that controls are actually operating, not just documented.",
        guidance_what="Evidence attached to each implemented control (screenshots, logs, records, sign-offs).",
        guidance_why="Auditors — internal or external — look for evidence a control is operating, not just a policy stating it should.",
        guidance_who="Control Owners.",
        guidance_questions=["What would prove this control is actually happening?"],
        guidance_existing_docs="System exports, access review sign-offs, backup logs.",
        guidance_evidence="At least one piece of evidence per applicable control.",
        completion_criteria="Applicable controls each have supporting evidence attached.",
    ),
    dict(
        order=10, phase="check", stage_title="Performance Evaluation", stage_order=6,
        req="9.2", title="Conduct an internal audit",
        step_type="audit",
        description="Independently check that the ISMS conforms to requirements and is effectively implemented.",
        guidance_what="A completed internal audit with findings recorded.",
        guidance_why="Internal audit is a mandatory management-system requirement and the best rehearsal for a certification audit.",
        guidance_who="Internal Auditor (should be independent of the area being audited).",
        guidance_questions=["Is the ISMS being followed in practice, not just on paper?"],
        guidance_existing_docs="Prior audit reports, if any.",
        guidance_evidence="Audit plan, findings, evidence reviewed.",
        completion_criteria="At least one internal audit has been closed with findings recorded.",
    ),
    dict(
        order=11, phase="check", stage_title="Performance Evaluation", stage_order=6,
        req="9.3", title="Hold a management review",
        step_type="management_review",
        description="Top management formally reviews the ISMS's continuing suitability, adequacy and effectiveness.",
        guidance_what="A recorded management review meeting covering the required inputs (audit results, risk status, objectives, etc.).",
        guidance_why="This is where leadership actually steers the ISMS, and it's a mandatory requirement.",
        guidance_who="Top management, ISMS Manager.",
        guidance_questions=["Are we meeting our objectives?", "What needs to change?"],
        guidance_existing_docs="Prior review minutes, if any.",
        guidance_evidence="Management review minutes with decisions and actions.",
        completion_criteria="At least one management review is recorded for the current period.",
    ),
    dict(
        order=12, phase="act", stage_title="Improvement", stage_order=7,
        req="10.2", title="Track corrective actions",
        step_type="corrective_actions",
        description="Make sure findings from audits, incidents and reviews actually get fixed and verified.",
        guidance_what="An up-to-date corrective action register with owners and due dates.",
        guidance_why="An ISMS that never closes findings isn't improving — this is what 'continual improvement' looks like in practice.",
        guidance_who="Compliance Manager, relevant owners.",
        guidance_questions=["What's the root cause, not just the symptom?"],
        guidance_existing_docs="Audit findings, incident reports.",
        guidance_evidence="Closed corrective actions with verification evidence.",
        completion_criteria="No corrective action is overdue without a documented reason.",
    ),
    dict(
        order=13, phase="act", stage_title="Improvement", stage_order=7,
        req="10.1", title="Check audit readiness",
        step_type="audit_readiness",
        description="Get a transparent, honest picture of how ready the organisation is for a certification audit.",
        guidance_what="A readiness score across requirements, controls, evidence, risk treatment and open findings.",
        guidance_why="This tells you — and any consultant working with you — exactly what's left before a certification audit makes sense.",
        guidance_who="ISMS Manager, Organisation Administrator.",
        guidance_questions=["What's the single biggest gap right now?"],
        guidance_existing_docs="—",
        guidance_evidence="—",
        completion_criteria="Readiness has been reviewed and next actions agreed.",
    ),
]


class Command(BaseCommand):
    help = "Seed guided implementation journey templates (ISO 27001, POPIA, King IV, ISO 9001)."

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_iso27001()
        for code, goal in [("POPIA", "popia_assessment"), ("KING_IV", "implement_framework"), ("ISO9001", "implement_framework")]:
            self._seed_generic(code, goal)
        self.stdout.write(self.style.SUCCESS("Journey template seeding complete."))

    def _seed_iso27001(self):
        framework = Framework.objects.filter(code="ISO27001", organisation__isnull=True).first()
        if not framework:
            self.stdout.write(self.style.WARNING("ISO27001 framework not found — run seed_frameworks first."))
            return
        template, _ = JourneyTemplate.objects.update_or_create(
            framework=framework,
            goal_type="build_from_scratch",
            defaults={
                "name": "Build an ISMS from Scratch",
                "description": "A guided, step-by-step path to implementing an Information Security Management System aligned to ISO/IEC 27001, from scoping through to audit readiness.",
                "is_active": True,
            },
        )
        for step_spec in ISO_STEPS:
            spec = dict(step_spec)
            ref_code = spec.pop("req")
            requirement = _req(framework, ref_code)
            JourneyStep.objects.update_or_create(
                template=template, order=spec["order"],
                defaults={**spec, "requirement": requirement},
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded template: {template.name} ({len(ISO_STEPS)} steps)"))

    def _seed_generic(self, framework_code, goal_type):
        framework = Framework.objects.filter(code=framework_code, organisation__isnull=True).first()
        if not framework:
            return
        template, _ = JourneyTemplate.objects.update_or_create(
            framework=framework,
            goal_type=goal_type,
            defaults={
                "name": f"Implement {framework.name}",
                "description": f"A guided path through {framework.name}, one requirement at a time.",
                "is_active": True,
            },
        )
        order = 0
        for requirement in framework.requirements.select_related("domain").order_by("domain__order", "order"):
            order += 1
            JourneyStep.objects.update_or_create(
                template=template, order=order,
                defaults={
                    "requirement": requirement,
                    "phase": "plan",
                    "title": requirement.title,
                    "description": requirement.guidance,
                    "guidance_what": requirement.guidance,
                    "guidance_who": "Compliance Manager",
                    "step_type": "info",
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded template: {template.name} ({order} steps)"))
