from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

TYPE_CHOICES = [
    ("gap", "Gap Assessment"),
    ("baseline", "Baseline Assessment"),
    ("maturity", "Maturity Assessment"),
    ("compliance", "Compliance Assessment"),
    ("readiness", "Readiness Assessment"),
    ("internal_control", "Internal Control Assessment"),
    ("custom", "Custom Assessment"),
]

STATUS_CHOICES = [
    ("not_started", "Not Started"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
]

RATING_CHOICES = [
    ("not_assessed", "Not Assessed"),
    ("not_implemented", "Not Implemented"),
    ("partially_implemented", "Partially Implemented"),
    ("implemented", "Implemented"),
    ("effective", "Effective"),
    ("not_applicable", "Not Applicable"),
]

RATING_SCORE = {
    "not_assessed": 0, "not_implemented": 0, "partially_implemented": 1, "implemented": 2, "effective": 2,
}


class Assessment(ReferenceCodeMixin, TenantScopedModel):
    REFERENCE_PREFIX = "ASMT"

    framework = models.ForeignKey(
        "frameworks.Framework", on_delete=models.SET_NULL, null=True, blank=True, related_name="assessments"
    )
    name = models.CharField(max_length=200)
    assessment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="gap")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="not_started")
    assessor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assessments_led"
    )
    started_at = models.DateField(null=True, blank=True)
    completed_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference_code} {self.name}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)

    @property
    def completion_percent(self):
        total = self.results.count()
        if total == 0:
            return 0
        done = self.results.exclude(rating="not_assessed").count()
        return round((done / total) * 100)


class AssessmentResult(TenantScopedModel):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="results")
    requirement = models.ForeignKey(
        "frameworks.Requirement", on_delete=models.CASCADE, null=True, blank=True, related_name="assessment_results"
    )
    control = models.ForeignKey(
        "controls.Control", on_delete=models.CASCADE, null=True, blank=True, related_name="assessment_results"
    )
    rating = models.CharField(max_length=30, choices=RATING_CHOICES, default="not_assessed")
    comments = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    evidence = models.ManyToManyField("evidence.Evidence", blank=True, related_name="assessment_results")
    responsible_person = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["requirement__domain__order", "requirement__order"]

    def __str__(self):
        target = self.requirement or self.control
        return f"{target} — {self.get_rating_display()}"
