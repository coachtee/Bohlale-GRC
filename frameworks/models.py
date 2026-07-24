import uuid

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel
from core.validators import validate_upload_file

SOURCE_BUILT_IN = "built_in"
SOURCE_CUSTOM = "custom"
SOURCE_IMPORTED = "imported"

SOURCE_TYPE_CHOICES = [
    (SOURCE_BUILT_IN, "Built-in"),
    (SOURCE_CUSTOM, "Custom"),
    (SOURCE_IMPORTED, "Imported"),
]

STATUS_ACTIVE = "active"
STATUS_DRAFT = "draft"
STATUS_RETIRED = "retired"

FRAMEWORK_STATUS_CHOICES = [
    (STATUS_ACTIVE, "Active"),
    (STATUS_DRAFT, "Draft"),
    (STATUS_RETIRED, "Retired"),
]


class FrameworkCategory(models.Model):
    """
    A first-class grouping section for the Framework Library (e.g.
    "South African Compliance", "International Management Systems",
    "Cybersecurity Frameworks"). Plain data, not a Python enum/choices
    list, so new categories can be added by a future session (or an
    admin) without a code change — only `order` controls where a
    category's section appears in the library, letting a specific
    category (South African Compliance) be pinned first.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=60, unique=True)
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=300, blank=True)
    order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Framework categories"

    def __str__(self):
        return self.name


class Framework(TimeStampedModel):
    """
    A framework-agnostic definition (spec §17): Framework -> Domains ->
    Requirements -> (Controls, live in the `controls` app) ->
    Assessment Questions -> Evidence Expectations.

    `organisation = None` marks a platform-global, built-in framework
    (e.g. the ISO 27001 structural skeleton, POPIA, King IV, ISO 9001)
    available to every tenant. `organisation` set marks a tenant's own
    custom/imported framework, visible only to that tenant. Built-in
    frameworks never reproduce copyrighted standard text — see
    frameworks/management/commands/seed_frameworks.py and
    BUILD_STATUS.md assumption #5.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation",
        on_delete=models.CASCADE,
        related_name="custom_frameworks",
        null=True,
        blank=True,
    )
    code = models.CharField(max_length=255)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        FrameworkCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="frameworks",
    )
    icon = models.CharField(
        max_length=255, blank=True, default="framework",
        help_text="Icon key from core.templatetags.icons — see the icon set there.",
    )
    status = models.CharField(max_length=20, choices=FRAMEWORK_STATUS_CHOICES, default=STATUS_ACTIVE)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPE_CHOICES, default=SOURCE_CUSTOM)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "code"], name="unique_framework_code_per_scope"
            )
        ]

    def __str__(self):
        return f"{self.name} {self.version}".strip()

    @property
    def is_global(self):
        return self.organisation_id is None


class Domain(TimeStampedModel):
    """A section/clause/domain within a framework (e.g. 'Leadership',
    or Annex-style control category 'Access control')."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name="domains")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", null=True, blank=True
    )
    code = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "code"]

    def __str__(self):
        return f"{self.code} {self.title}".strip()


class Requirement(TimeStampedModel):
    """One assessable requirement within a domain."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name="requirements")
    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="requirements", null=True, blank=True
    )
    ref_code = models.CharField(max_length=255, blank=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    guidance = models.TextField(
        blank=True, help_text="Plain-language explanation of what this requirement means in practice."
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["domain__order", "order", "ref_code"]

    def __str__(self):
        return f"{self.ref_code} {self.title}".strip()


class AssessmentQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name="assessment_questions")
    text = models.CharField(max_length=500)
    help_text = models.CharField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text


class EvidenceExpectation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name="evidence_expectations")
    description = models.CharField(max_length=300)
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return self.description


class FrameworkAdoption(TimeStampedModel):
    """Marks that an organisation is actively implementing/tracking a
    given framework — drives the dashboard Compliance Overview."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation", on_delete=models.CASCADE, related_name="framework_adoptions"
    )
    framework = models.ForeignKey(Framework, on_delete=models.CASCADE, related_name="adoptions")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organisation", "framework"], name="unique_adoption_per_org")
        ]

    def __str__(self):
        return f"{self.organisation} — {self.framework}"


REQ_NOT_STARTED = "not_started"
REQ_IN_PROGRESS = "in_progress"
REQ_COMPLETE = "complete"
REQ_NOT_APPLICABLE = "not_applicable"

REQUIREMENT_STATUS_CHOICES = [
    (REQ_NOT_STARTED, "Not Started"),
    (REQ_IN_PROGRESS, "In Progress"),
    (REQ_COMPLETE, "Complete"),
    (REQ_NOT_APPLICABLE, "Not Applicable"),
]


class RequirementStatus(TimeStampedModel):
    """Per-organisation implementation status against one Requirement.
    Feeds the Compliance Overview progress bars, the Gap Assessment
    report, and the 'Requirements Completion' Audit Readiness dimension."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation", on_delete=models.CASCADE, related_name="requirement_statuses"
    )
    requirement = models.ForeignKey(Requirement, on_delete=models.CASCADE, related_name="statuses")
    status = models.CharField(max_length=20, choices=REQUIREMENT_STATUS_CHOICES, default=REQ_NOT_STARTED)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "requirement"], name="unique_requirement_status_per_org"
            )
        ]

    def __str__(self):
        return f"{self.requirement} — {self.get_status_display()}"


IMPORT_STATUS_CHOICES = [
    ("uploaded", "Uploaded"),
    ("analysing", "Analysing"),
    ("extracted", "Extracted — Awaiting Review"),
    ("approved", "Approved"),
    ("published", "Published"),
    ("rejected", "Rejected"),
]


def framework_import_upload_path(instance, filename):
    return f"framework_imports/{instance.organisation_id}/{filename}"


class FrameworkImport(TimeStampedModel):
    """
    Framework Studio (spec §18): Upload -> Analyse -> Extract -> Review
    -> Correct -> Approve -> Publish. `extracted_data` holds the
    AI-drafted structure (domains/requirements) pending human review;
    nothing here is written into a live Framework until approved and
    published.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        "tenancy.Organisation", on_delete=models.CASCADE, related_name="framework_imports"
    )
    source_file = models.FileField(
        upload_to=framework_import_upload_path, blank=True, null=True, validators=[validate_upload_file]
    )
    source_text = models.TextField(
        blank=True, help_text="Pasted source text, used when no file is uploaded."
    )
    proposed_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=IMPORT_STATUS_CHOICES, default="uploaded")
    extracted_data = models.JSONField(default=dict, blank=True)
    resulting_framework = models.ForeignKey(
        Framework, on_delete=models.SET_NULL, null=True, blank=True, related_name="import_source"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="framework_imports"
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="framework_imports_reviewed",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.proposed_name or f"Import #{str(self.id)[:8]}"
