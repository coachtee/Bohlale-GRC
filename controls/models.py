from django.conf import settings
from django.db import models

from core.models import ReferenceCodeMixin, TenantScopedModel

IMPLEMENTATION_STATUS_CHOICES = [
    ("not_implemented", "Not Implemented"),
    ("partially_implemented", "Partially Implemented"),
    ("implemented", "Implemented"),
    ("not_applicable", "Not Applicable"),
]

EFFECTIVENESS_CHOICES = [
    ("not_tested", "Not Tested"),
    ("not_effective", "Not Effective"),
    ("partially_effective", "Partially Effective"),
    ("effective", "Effective"),
]


class Control(ReferenceCodeMixin, TenantScopedModel):
    """
    A control the organisation implements. Controls are not owned by a
    single framework — the same control can satisfy several framework
    requirements at once (spec §19's Common Control Library concept),
    represented here by `framework_requirements` mapping to
    frameworks.Requirement across any adopted framework.
    """

    REFERENCE_PREFIX = "CTRL"

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="controls_owned"
    )
    implementation_status = models.CharField(max_length=30, choices=IMPLEMENTATION_STATUS_CHOICES, default="not_implemented")
    effectiveness = models.CharField(max_length=30, choices=EFFECTIVENESS_CHOICES, default="not_tested")
    implementation_notes = models.TextField(blank=True)

    framework_requirements = models.ManyToManyField("frameworks.Requirement", blank=True, related_name="controls")
    risks = models.ManyToManyField("risks.Risk", blank=True, related_name="controls")
    policies = models.ManyToManyField("documents.Document", blank=True, related_name="controls")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.reference_code} {self.name}"

    def save(self, *args, **kwargs):
        self.assign_reference_code()
        super().save(*args, **kwargs)


class ControlTest(TenantScopedModel):
    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="tests")
    tested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    test_date = models.DateField()
    result = models.CharField(
        max_length=20, choices=[("pass", "Pass"), ("fail", "Fail"), ("partial", "Partial")]
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.control} — {self.get_result_display()} ({self.test_date})"


class SoAEntry(TenantScopedModel):
    """
    One line of the Statement of Applicability (spec §24) for a given
    framework: is this control applicable, why, what's the
    implementation status, who owns it, which risks does it treat.
    """

    framework = models.ForeignKey("frameworks.Framework", on_delete=models.CASCADE, related_name="soa_entries")
    control = models.ForeignKey(Control, on_delete=models.CASCADE, related_name="soa_entries")
    applicable = models.BooleanField(default=True)
    justification = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organisation", "framework", "control"], name="unique_soa_entry")
        ]
        ordering = ["control__name"]

    def __str__(self):
        return f"SoA: {self.control.name} ({self.framework.code})"
