from django.utils import timezone

from ai import service as ai_service
from knowledge.services import verified_context_text

from .models import (
    STATUS_ARCHIVED,
    STATUS_AWAITING_APPROVAL,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNDER_REVIEW,
    Document,
)

STEP_DOC_TYPE_TO_PURPOSE = {
    "isms_scope": "isms_scope",
}


def submit_for_review(document, user):
    document.status = STATUS_UNDER_REVIEW
    document.snapshot_version(user, change_reason="Submitted for review")
    document.save(update_fields=["status", "updated_at"])
    return document


def submit_for_approval(document, user):
    from approvals.models import ApprovalRequest

    document.status = STATUS_AWAITING_APPROVAL
    document.snapshot_version(user, change_reason="Submitted for approval")
    document.save(update_fields=["status", "updated_at"])
    return ApprovalRequest.objects.create(
        organisation=document.organisation, target=document, requested_by=user
    )


def start_revision(document, user):
    """Editing a Published document opens a new revision cycle (spec
    §15): bump the minor version and drop back to Draft, keeping the
    published version intact in history."""
    try:
        major, minor = document.version_label.split(".")
        document.version_label = f"{major}.{int(minor) + 1}"
    except (ValueError, AttributeError):
        document.version_label = "1.1"
    document.status = STATUS_DRAFT
    document.save(update_fields=["status", "version_label", "updated_at"])
    return document


def _next_whole_version(version_label):
    try:
        major = int(float(version_label))
    except ValueError:
        major = 0
    return f"{major + 1}.0"


def publish(document, user):
    document.status = STATUS_PUBLISHED
    document.version_label = _next_whole_version(document.version_label)
    if not document.effective_date:
        document.effective_date = timezone.now().date()
    document.snapshot_version(user, change_reason="Published")
    document.save(update_fields=["status", "version_label", "effective_date", "updated_at"])
    if document.ai_generation_id:
        from ai.models import STATUS_APPROVED as AI_APPROVED
        from ai.models import STATUS_EDITED as AI_EDITED

        edited = document.content.strip() != document.ai_generation.output_text.strip()
        document.ai_generation.mark_reviewed(user, AI_EDITED if edited else AI_APPROVED)
    return document


def archive(document, user):
    """Archived is a terminal state (spec §14): a published document
    that is no longer in force but must be retained for audit history
    rather than deleted."""
    document.status = STATUS_ARCHIVED
    document.snapshot_version(user, change_reason="Archived")
    document.save(update_fields=["status", "updated_at"])
    return document


def generate_draft_for_step(organisation, step, user):
    """
    AI Document Generation (spec §13): gather verified organisational
    context, ask the AI service layer for a draft, and create a Draft
    controlled document from it. The draft is NEVER auto-approved —
    it is created in status=Draft and must go through
    review/approval/sign-off/publish like any other document.
    """
    context_text = verified_context_text(organisation)
    purpose = STEP_DOC_TYPE_TO_PURPOSE.get(step.produces_document_type, "document_draft")
    doc_type_label = dict(Document.doc_type.field.choices).get(step.produces_document_type, "document")
    prompt = (
        f"Draft a {doc_type_label} for the organisation, addressing: {step.description}\n\n"
        f"Verified organisational context:\n{context_text or '(no verified facts captured yet)'}"
    )
    generation = ai_service.generate(
        organisation=organisation,
        user=user,
        purpose=purpose,
        user_prompt=prompt,
        context_reference=f"Journey step: {step.title}; {len(context_text.splitlines())} verified knowledge facts used.",
    )
    doc_type = step.produces_document_type or "policy"
    doc_type_label = dict(Document.doc_type.field.choices).get(doc_type, "Document")
    document = Document.objects.create(
        organisation=organisation,
        title=f"{doc_type_label} — {organisation.name}",
        doc_type=doc_type,
        content=generation.output_text,
        owner=user,
        author=user,
        ai_generated=True,
        ai_generation=generation,
        journey_step=step,
        status=STATUS_DRAFT,
    )
    generation.related_object = document
    generation.save(update_fields=["content_type", "object_id"])
    document.snapshot_version(user, change_reason="AI-generated first draft")
    return document
