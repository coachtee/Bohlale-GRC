import uuid

from django.conf import settings
from django.db import models

from core.models import TenantScopedModel, TimeStampedModel

GOAL_CHOICES = [
    ("build_from_scratch", "Build a management system from scratch"),
    ("gap_assessment", "Conduct a gap assessment"),
    ("improve_existing", "Improve an existing management system"),
    ("audit_prep", "Prepare for an internal audit"),
    ("certification_prep", "Prepare for certification"),
    ("popia_assessment", "Assess POPIA compliance"),
    ("grc_baseline", "Conduct a GRC baseline assessment"),
    ("implement_framework", "Implement a selected framework"),
    ("import_custom_framework", "Import a custom framework"),
]

PHASE_PLAN = "plan"
PHASE_DO = "do"
PHASE_CHECK = "check"
PHASE_ACT = "act"

PHASE_CHOICES = [
    (PHASE_PLAN, "Plan"),
    (PHASE_DO, "Do"),
    (PHASE_CHECK, "Check"),
    (PHASE_ACT, "Act"),
]

STEP_TYPE_INFO = "info"
STEP_TYPE_INTERVIEW = "interview"
STEP_TYPE_DOCUMENT = "document"
STEP_TYPE_RISK = "risk_assessment"
STEP_TYPE_CONTROLS = "controls"
STEP_TYPE_EVIDENCE = "evidence"
STEP_TYPE_AUDIT = "audit"
STEP_TYPE_REVIEW = "management_review"
STEP_TYPE_ACTIONS = "corrective_actions"
STEP_TYPE_READINESS = "audit_readiness"

STEP_TYPE_CHOICES = [
    (STEP_TYPE_INFO, "Information / Acknowledgement"),
    (STEP_TYPE_INTERVIEW, "AI Guided Interview"),
    (STEP_TYPE_DOCUMENT, "Produces a Controlled Document"),
    (STEP_TYPE_RISK, "Risk Assessment"),
    (STEP_TYPE_CONTROLS, "Control Selection / SoA"),
    (STEP_TYPE_EVIDENCE, "Evidence Collection"),
    (STEP_TYPE_AUDIT, "Internal Audit"),
    (STEP_TYPE_REVIEW, "Management Review"),
    (STEP_TYPE_ACTIONS, "Corrective Actions"),
    (STEP_TYPE_READINESS, "Audit Readiness"),
]


class JourneyTemplate(TimeStampedModel):
    """A reusable guided-implementation journey definition — e.g.
    'Build an ISMS from Scratch' for ISO 27001. Platform-defined
    (not tenant-scoped); an organisation's own progress against a
    template lives in OrganisationJourney/StepProgress."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(
        "frameworks.Framework", on_delete=models.CASCADE, related_name="journey_templates", null=True, blank=True
    )
    goal_type = models.CharField(max_length=40, choices=GOAL_CHOICES)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class JourneyStep(models.Model):
    """
    One step of the guided implementation engine (spec §8). Answers,
    for the user: what is required, why, what to do, who's involved,
    what questions to ask, what documents/evidence might already
    exist, what to create, who approves it, and what's next (the
    'what's next' is simply the following step in `order`).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(JourneyTemplate, on_delete=models.CASCADE, related_name="steps")
    requirement = models.ForeignKey(
        "frameworks.Requirement", on_delete=models.SET_NULL, null=True, blank=True, related_name="journey_steps"
    )
    phase = models.CharField(max_length=10, choices=PHASE_CHOICES, default=PHASE_PLAN)
    order = models.PositiveIntegerField(default=0)
    stage_title = models.CharField(
        max_length=100, blank=True,
        help_text="Groups steps for the implementation stepper (e.g. 'Context of the Organisation'). "
                   "Falls back to the linked requirement's domain title if blank.",
    )
    stage_order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    guidance_what = models.TextField(blank=True, verbose_name="What is required?")
    guidance_why = models.TextField(blank=True, verbose_name="Why is it required?")
    guidance_who = models.CharField(max_length=300, blank=True, verbose_name="Who should be involved?")
    guidance_questions = models.JSONField(default=list, blank=True, verbose_name="What questions should I ask?")
    guidance_existing_docs = models.TextField(blank=True, verbose_name="What documents might already exist?")
    guidance_evidence = models.TextField(blank=True, verbose_name="What evidence should I look for?")
    completion_criteria = models.TextField(blank=True)

    step_type = models.CharField(max_length=30, choices=STEP_TYPE_CHOICES, default=STEP_TYPE_INFO)
    produces_document_type = models.CharField(max_length=40, blank=True)
    requires_approval = models.BooleanField(default=False)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.title}"

    @property
    def resolved_stage_title(self):
        if self.stage_title:
            return self.stage_title
        if self.requirement and self.requirement.domain:
            return self.requirement.domain.title
        return self.get_phase_display()

    @property
    def resolved_stage_order(self):
        if self.stage_order:
            return self.stage_order
        if self.requirement and self.requirement.domain:
            return self.requirement.domain.order
        return 0


JOURNEY_NOT_STARTED = "not_started"
JOURNEY_IN_PROGRESS = "in_progress"
JOURNEY_COMPLETED = "completed"

JOURNEY_STATUS_CHOICES = [
    (JOURNEY_NOT_STARTED, "Not Started"),
    (JOURNEY_IN_PROGRESS, "In Progress"),
    (JOURNEY_COMPLETED, "Completed"),
]


class OrganisationJourney(TenantScopedModel):
    """
    An organisation's instance of implementing a JourneyTemplate — this
    is the 'Project / Management System' referenced in spec §5 (see
    BUILD_STATUS.md assumption #2: no separate `projects` app).
    """

    template = models.ForeignKey(JourneyTemplate, on_delete=models.PROTECT, related_name="organisation_journeys")
    status = models.CharField(max_length=20, choices=JOURNEY_STATUS_CHOICES, default=JOURNEY_NOT_STARTED)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_step = models.ForeignKey(
        JourneyStep, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    def __str__(self):
        return f"{self.organisation} — {self.template.name}"

    @property
    def progress_percent(self):
        total = self.step_progress.count()
        if total == 0:
            return 0
        done = self.step_progress.filter(status="completed").count()
        return round((done / total) * 100)


STEP_NOT_STARTED = "not_started"
STEP_IN_PROGRESS = "in_progress"
STEP_COMPLETED = "completed"
STEP_SKIPPED = "skipped"

STEP_PROGRESS_STATUS_CHOICES = [
    (STEP_NOT_STARTED, "Not Started"),
    (STEP_IN_PROGRESS, "In Progress"),
    (STEP_COMPLETED, "Completed"),
    (STEP_SKIPPED, "Skipped"),
]


class StepProgress(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation_journey = models.ForeignKey(
        OrganisationJourney, on_delete=models.CASCADE, related_name="step_progress"
    )
    step = models.ForeignKey(JourneyStep, on_delete=models.CASCADE, related_name="progress_entries")
    status = models.CharField(max_length=20, choices=STEP_PROGRESS_STATUS_CHOICES, default=STEP_NOT_STARTED)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["step__order"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation_journey", "step"], name="unique_progress_per_step"
            )
        ]

    def __str__(self):
        return f"{self.step} — {self.status}"


# --------------------------------------------------------------- AI Interview

INTERVIEW_IN_PROGRESS = "in_progress"
INTERVIEW_COMPLETED = "completed"

INTERVIEW_STATUS_CHOICES = [
    (INTERVIEW_IN_PROGRESS, "In Progress"),
    (INTERVIEW_COMPLETED, "Completed"),
]


class InterviewSession(TenantScopedModel):
    """An AI Guided Interview session (spec §11) tied to a journey
    step. Answers are written back to the Organisation Knowledge
    Profile as VERIFIED facts (a human directly typed them)."""

    step = models.ForeignKey(JourneyStep, on_delete=models.CASCADE, related_name="interview_sessions")
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=INTERVIEW_STATUS_CHOICES, default=INTERVIEW_IN_PROGRESS)

    def __str__(self):
        return f"Interview: {self.step.title} ({self.organisation})"


class InterviewExchange(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name="exchanges")
    order = models.PositiveIntegerField(default=0)
    question_text = models.CharField(max_length=500)
    knowledge_category = models.CharField(max_length=40, blank=True)
    knowledge_label = models.CharField(max_length=200, blank=True)
    answer_text = models.TextField(blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order"]


# ---------------------------------------------------------- Information Requests

REQUEST_PENDING = "pending"
REQUEST_ANSWERED = "answered"
REQUEST_CANCELLED = "cancelled"

REQUEST_STATUS_CHOICES = [
    (REQUEST_PENDING, "Pending"),
    (REQUEST_ANSWERED, "Answered"),
    (REQUEST_CANCELLED, "Cancelled"),
]


class InformationRequest(TenantScopedModel):
    """The Information Request Engine (spec §12): the practitioner
    assigns a targeted question to a stakeholder — an existing member,
    or an external recipient who answers via a secure, single-purpose
    token link without needing full platform access."""

    step = models.ForeignKey(
        JourneyStep, on_delete=models.SET_NULL, null=True, blank=True, related_name="information_requests"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="information_requests_made"
    )
    assigned_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="information_requests_assigned",
    )
    assigned_role_label = models.CharField(max_length=100, blank=True, help_text="e.g. CEO, IT Manager, Information Officer")
    assigned_email = models.EmailField(blank=True, help_text="Used when the recipient is external / has no platform account.")
    question_text = models.TextField()
    knowledge_category = models.CharField(max_length=40, blank=True)
    knowledge_label = models.CharField(max_length=200, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default=REQUEST_PENDING)
    response_text = models.TextField(blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Request: {self.assigned_role_label or self.assigned_email} — {self.question_text[:60]}"
