from django.utils import timezone

from .models import STATUS_AI_INFERENCE, STATUS_MISSING, STATUS_VERIFIED, KnowledgeItem


def set_item(organisation, category, label, value, status=STATUS_VERIFIED, source="", user=None):
    """Create or update one Knowledge Profile fact (upsert by
    organisation+category+label)."""
    item, _ = KnowledgeItem.objects.update_or_create(
        organisation=organisation,
        category=category,
        label=label,
        defaults={
            "value": value,
            "status": status,
            "source": source,
            "verified_by": user if status == STATUS_VERIFIED else None,
            "verified_at": timezone.now() if status == STATUS_VERIFIED else None,
        },
    )
    return item


def profile_completeness(organisation):
    qs = KnowledgeItem.objects.filter(organisation=organisation)
    total = qs.count()
    if total == 0:
        return 0
    verified = qs.filter(status=STATUS_VERIFIED).count()
    return round((verified / total) * 100)


def verified_context_text(organisation, limit=60):
    """
    Assemble a plain-text summary of VERIFIED knowledge facts for this
    organisation, for use as AI prompt context. Never includes
    AI-inference-only facts as if they were confirmed, and never pulls
    data from any other tenant (queryset is always filtered by
    `organisation`) — see spec §38 (AI must respect tenant boundaries
    and prioritise verified facts).
    """
    items = KnowledgeItem.objects.filter(
        organisation=organisation, status=STATUS_VERIFIED
    ).exclude(value="")[:limit]
    lines = [f"- {item.get_category_display()} / {item.label}: {item.value}" for item in items]
    return "\n".join(lines)


def missing_items(organisation, category=None):
    qs = KnowledgeItem.objects.filter(organisation=organisation, status=STATUS_MISSING)
    if category:
        qs = qs.filter(category=category)
    return qs
