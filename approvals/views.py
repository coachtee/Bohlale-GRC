from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.utils import timezone

from activity.utils import log_activity
from core.permissions import can_approve, get_object_or_404_scoped, require_organisation
from notifications.utils import notify

from .forms import SignatureForm
from .models import REQUEST_APPROVED, REQUEST_REJECTED, ApprovalRequest, Signature


def _client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    return xff.split(",")[0].strip() if xff else request.META.get("REMOTE_ADDR")


@require_organisation
def approval_list(request):
    requests_qs = ApprovalRequest.objects.filter(organisation=request.organisation).select_related(
        "requested_by", "content_type"
    )
    return render(request, "approvals/list.html", {"requests": requests_qs})


@require_organisation
def approval_detail(request, pk):
    approval_request = get_object_or_404_scoped(ApprovalRequest.objects, request, pk=pk)
    document = approval_request.target
    form = None

    if approval_request.status == "pending":
        if not can_approve(request):
            raise PermissionDenied(
                "Only an Executive/Approver, Organisation Administrator or Consultant may sign this off."
            )
        if request.method == "POST":
            form = SignatureForm(request.POST, expected_name=request.user.get_full_name() or request.user.email)
            if form.is_valid():
                decision = form.cleaned_data["decision"]
                role_label = request.membership.get_role_display() if request.membership else "Platform Administrator"
                signature = Signature.objects.create(
                    approval_request=approval_request,
                    approver=request.user,
                    role=role_label,
                    decision=decision,
                    typed_signature=form.cleaned_data["typed_signature"],
                    consent=form.cleaned_data["consent"],
                    document_version=getattr(document, "version_label", ""),
                    document_hash=document.content_hash() if hasattr(document, "content_hash") else "",
                    ip_address=_client_ip(request),
                )
                approval_request.status = REQUEST_APPROVED if decision == "approved" else REQUEST_REJECTED
                approval_request.decided_at = timezone.now()
                approval_request.save(update_fields=["status", "decided_at"])

                if hasattr(document, "status"):
                    if decision == "approved":
                        document.status = "approved"
                        document.approver = request.user
                        document.approval_date = timezone.now().date()
                        document.save(update_fields=["status", "approver", "approval_date", "updated_at"])
                    else:
                        document.status = "draft"
                        document.save(update_fields=["status", "updated_at"])
                        if document.author:
                            notify(
                                request.organisation, document.author,
                                f"'{document}' was not approved and has been returned to draft.",
                                category="approval",
                            )

                log_activity(
                    request, decision, target=signature,
                    description=f"{decision.title()}: {document} (electronically signed by {signature.typed_signature})",
                )
                messages.success(request, f"Your decision ({decision}) has been recorded and electronically signed.")
                return redirect("documents:detail", pk=document.pk)
        else:
            form = SignatureForm(expected_name=request.user.get_full_name() or request.user.email)

    return render(
        request,
        "approvals/detail.html",
        {"approval_request": approval_request, "document": document, "form": form},
    )
