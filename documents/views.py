from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from activity.utils import log_activity
from core.permissions import can_approve, get_object_or_404_scoped, require_editor, require_organisation
from notifications.utils import notify
from tenancy.constants import APPROVER_ROLES
from tenancy.models import Membership

from .forms import DocumentContentForm, DocumentForm
from .models import STATUS_APPROVED, STATUS_DRAFT, STATUS_PUBLISHED, Document
from .services import generate_draft_for_step, publish, start_revision, submit_for_approval, submit_for_review


@require_organisation
def document_list(request):
    documents = Document.objects.filter(organisation=request.organisation).select_related("owner")
    status_filter = request.GET.get("status")
    if status_filter:
        documents = documents.filter(status=status_filter)
    return render(request, "documents/list.html", {"documents": documents, "status_filter": status_filter})


@require_editor
def document_create(request):
    if request.method == "POST":
        form = DocumentForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            document = form.save(commit=False)
            document.organisation = request.organisation
            document.author = request.user
            if not document.owner_id:
                document.owner = request.user
            document.save()
            form.save_m2m()
            document.snapshot_version(request.user, change_reason="Initial draft")
            log_activity(request, "created", target=document, description=f"Document created: {document.title}")
            messages.success(request, "Document created as a draft.")
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentForm(organisation=request.organisation)
    return render(request, "documents/form.html", {"form": form})


def _pending_approval_request(document):
    from approvals.models import ApprovalRequest

    content_type = ContentType.objects.get_for_model(Document)
    return ApprovalRequest.objects.filter(
        content_type=content_type, object_id=str(document.pk), status="pending"
    ).first()


@require_organisation
def document_detail(request, pk):
    document = get_object_or_404_scoped(Document.objects, request, pk=pk)
    versions = document.versions.all()[:20]
    can_sign = can_approve(request)
    pending_approval = _pending_approval_request(document)
    return render(
        request,
        "documents/detail.html",
        {"document": document, "versions": versions, "can_sign": can_sign, "pending_approval": pending_approval},
    )


@require_editor
def document_edit(request, pk):
    document = get_object_or_404_scoped(Document.objects, request, pk=pk)
    if document.status == STATUS_PUBLISHED:
        start_revision(document, request.user)
        messages.info(
            request,
            f"Editing a published document — this opens revision {document.version_label} as a new draft.",
        )
    if request.method == "POST":
        form = DocumentContentForm(request.POST)
        if form.is_valid():
            document.content = form.cleaned_data["content"]
            document.save(update_fields=["content", "updated_at"])
            document.snapshot_version(request.user, change_reason=form.cleaned_data["change_reason"] or "Content updated")
            log_activity(request, "updated", target=document, description=f"Document content updated: {document.title}")
            messages.success(request, "Document updated.")
            return redirect("documents:detail", pk=document.pk)
    else:
        form = DocumentContentForm(initial={"content": document.content})
    return render(request, "documents/edit.html", {"form": form, "document": document})


@require_editor
def document_submit_review(request, pk):
    document = get_object_or_404_scoped(Document.objects, request, pk=pk)
    if request.method == "POST" and document.status == STATUS_DRAFT:
        submit_for_review(document, request.user)
        log_activity(request, "submitted", target=document, description=f"Submitted for review: {document.title}")
        messages.success(request, "Document submitted for review.")
    return redirect("documents:detail", pk=document.pk)


@require_editor
def document_submit_approval(request, pk):
    document = get_object_or_404_scoped(Document.objects, request, pk=pk)
    if request.method == "POST" and document.status in (STATUS_DRAFT, "under_review"):
        approval_request = submit_for_approval(document, request.user)
        approver_memberships = Membership.objects.filter(
            organisation=request.organisation, role__in=APPROVER_ROLES, is_active=True
        ).select_related("user")
        for membership in approver_memberships:
            notify(
                request.organisation, membership.user,
                f"'{document.title}' is awaiting your approval.",
                category="approval", link=f"/approvals/{approval_request.pk}/", send_email=True,
            )
        log_activity(request, "submitted", target=document, description=f"Submitted for approval: {document.title}")
        messages.success(request, "Document submitted for approval. Approvers have been notified.")
    return redirect("documents:detail", pk=document.pk)


@require_editor
def document_publish(request, pk):
    document = get_object_or_404_scoped(Document.objects, request, pk=pk)
    if not can_approve(request):
        raise PermissionDenied("Only an Executive/Approver, Organisation Administrator or Consultant may publish.")
    if request.method == "POST" and document.status == STATUS_APPROVED:
        publish(document, request.user)
        if document.journey_step:
            from journeys.models import OrganisationJourney
            from journeys.services import mark_step_complete

            journey = OrganisationJourney.objects.filter(
                organisation=request.organisation, template_id=document.journey_step.template_id
            ).first()
            if journey:
                mark_step_complete(journey, document.journey_step, request.user)
        log_activity(request, "published", target=document, description=f"Published: {document.title} v{document.version_label}")
        messages.success(request, f"'{document.title}' has been published as v{document.version_label}.")
    return redirect("documents:detail", pk=document.pk)


@require_editor
def generate_for_step(request, step_id):
    from journeys.models import JourneyStep

    step = get_object_or_404(JourneyStep, pk=step_id)
    document = generate_draft_for_step(request.organisation, step, request.user)
    log_activity(request, "generated", target=document, description=f"AI draft generated for step: {step.title}")
    messages.success(request, "A first draft has been generated. Please review it carefully before submitting for approval.")
    return redirect("documents:detail", pk=document.pk)
