import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from core.models import TimeStampedModel
from core.validators import validate_upload_file
from .constants import ORGANISATION_TYPE_CHOICES, ROLE_CHOICES


class Organisation(TimeStampedModel):
    """A tenant. All tenant-scoped data hangs off this model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    organisation_type = models.CharField(
        max_length=20, choices=ORGANISATION_TYPE_CHOICES, default="sme"
    )
    industry = models.CharField(max_length=150, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="South Africa")
    province = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="org_logos/", blank=True, null=True, validators=[validate_upload_file])
    size = models.CharField(
        max_length=30,
        choices=[
            ("1-10", "1–10 employees"),
            ("11-50", "11–50 employees"),
            ("51-200", "51–200 employees"),
            ("201-500", "201–500 employees"),
            ("500+", "500+ employees"),
        ],
        default="1-10",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organisations_created",
    )
    is_demo = models.BooleanField(
        default=False,
        help_text="Marks fictional demonstration tenants (e.g. NIBS).",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)[:200] or "organisation"
            slug = base_slug
            i = 1
            while Organisation.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                i += 1
                slug = f"{base_slug}-{i}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def initials(self):
        parts = [p[0] for p in self.name.split() if p][:2]
        return "".join(parts).upper() or "OR"


class Membership(TimeStampedModel):
    """A user's role within one organisation. A user may hold different
    memberships (and therefore different roles) across organisations —
    this is how one person can be a Consultant on several client
    tenants and, separately, an Org Admin of their own organisation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="contributor")
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships_invited",
    )
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("organisation", "user")]
        ordering = ["organisation__name"]

    def __str__(self):
        return f"{self.user} — {self.organisation} ({self.get_role_display()})"


class OrganisationInvite(TimeStampedModel):
    """An email invitation to join an organisation with a given role.
    Also doubles as the mechanism for the Information Request Engine's
    'external limited-access' recipients (spec §12) via `limited_access`."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="invites"
    )
    email = models.EmailField()
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default="contributor")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Invite: {self.email} → {self.organisation} ({self.get_role_display()})"
