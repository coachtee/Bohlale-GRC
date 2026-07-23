from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from activity.utils import log_activity
from core.permissions import get_object_or_404_scoped, require_approver, require_editor, require_organisation
from core.protected_media import serve_tenant_file

from .forms import InputRecordForm, ManagementReviewForm
from .models import ManagementReview, ManagementReviewInputRecord
from .services import create_review


@require_organisation
def review_list(request):
    reviews = ManagementReview.objects.filter(organisation=request.organisation)
    return render(request, "reviews/list.html", {"reviews": reviews})


@require_editor
def review_create(request):
    if request.method == "POST":
        form = ManagementReviewForm(request.POST, request.FILES, organisation=request.organisation)
        if form.is_valid():
            review = create_review(request.organisation, **form.cleaned_data)
            log_activity(request, "created", target=review, description=f"Management review scheduled: {review.meeting_date}")
            messages.success(request, "Management review created.")
            return redirect("reviews:detail", pk=review.pk)
    else:
        form = ManagementReviewForm(organisation=request.organisation)
    return render(request, "reviews/form.html", {"form": form})


@require_organisation
def review_detail(request, pk):
    review = get_object_or_404_scoped(ManagementReview.objects, request, pk=pk)
    return render(request, "reviews/detail.html", {"review": review, "inputs": review.input_records.all()})


@require_organisation
def review_download(request, pk):
    review = get_object_or_404_scoped(ManagementReview.objects, request, pk=pk)
    return serve_tenant_file(review, "attachment")


@require_editor
def input_record_update(request, pk):
    # ManagementReviewInputRecord has no organisation FK of its own —
    # it belongs to a review — so scope explicitly via the parent
    # review's organisation rather than get_object_or_404_scoped.
    record = get_object_or_404(ManagementReviewInputRecord, pk=pk, review__organisation=request.organisation)
    if request.method == "POST":
        form = InputRecordForm(request.POST)
        if form.is_valid():
            record.covered = form.cleaned_data["covered"]
            record.notes = form.cleaned_data["notes"]
            record.save(update_fields=["covered", "notes"])
            messages.success(request, "Updated.")
    return redirect("reviews:detail", pk=record.review_id)


@require_approver
def review_complete(request, pk):
    review = get_object_or_404_scoped(ManagementReview.objects, request, pk=pk)
    if request.method == "POST":
        review.status = "completed"
        review.approved_by = request.user
        review.save(update_fields=["status", "approved_by", "updated_at"])
        log_activity(request, "completed", target=review, description=f"Management review completed: {review}")
        messages.success(request, "Management review marked complete.")
    return redirect("reviews:detail", pk=review.pk)
