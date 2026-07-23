import uuid

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core.models import TenantScopedModel, TimeStampedModel


class RegisterType(TimeStampedModel):
    """
    Defines a configurable register (spec §27) — e.g. Interested
    Parties Register, Legal & Regulatory Register, Processing
    Activities Register, Training Register — that isn't already a
    dedicated app (Risk/Asset/Supplier/Incident/Corrective Action/
    Audit Findings are first-class apps; everything else runs through
    this generic engine so new registers can be added without a
    schema migration).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=30, default="register")
    field_schema = models.JSONField(
        default=list,
        help_text='List of {"name","label","type": "text|textarea|date|select", "choices": [...]}',
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RegisterEntry(TenantScopedModel):
    register_type = models.ForeignKey(RegisterType, on_delete=models.CASCADE, related_name="entries")
    data = models.JSONField(default=dict, blank=True, encoder=DjangoJSONEncoder)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Register entries"

    def __str__(self):
        first_field = self.register_type.field_schema[0]["name"] if self.register_type.field_schema else None
        return str(self.data.get(first_field, self.pk)) if first_field else str(self.pk)
