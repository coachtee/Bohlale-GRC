from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from activity.utils import log_activity
from core.permissions import get_object_or_404_scoped, require_editor, require_organisation

from .forms import AssessmentCreateForm, AssessmentResultForm
from .models import Assessment, AssessmentResult
from .services import create_assessment_from_framework


@require_organisation
def assessment_list(request):
    assessments = Assessment.objects.filter(organisation=request.organisation).select_related("framework", "assessor")
    return render(request, "assessments/list.html", {"assessments": assessments})


@require_editor
def assessment_create(request):
    if request.method == "POST":
        form = AssessmentCreateForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            data = form.cleaned_data
            assessment = create_assessment_from_framework(
                request.organisation, data["framework"], data["name"], data["assessment_type"], data["assessor"]
            )
            assessment.started_at = data["started_at"]
            assessment.save(update_fields=["started_at"])
            log_activity(request, "created", target=assessment, description=f"Assessment started: {assessment.name}")
            messages.success(request, f"'{assessment.name}' created with {assessment.results.count()} requirements to assess.")
            return redirect("assessments:detail", pk=assessment.pk)
    else:
        form = AssessmentCreateForm(organisation=request.organisation)
    return render(request, "assessments/form.html", {"form": form})


@require_organisation
def assessment_detail(request, pk):
    assessment = get_object_or_404_scoped(Assessment.objects, request, pk=pk)
    results = assessment.results.select_related("requirement__domain", "control").all()
    return render(
        request,
        "assessments/detail.html",
        {"assessment": assessment, "results": results, "completion": assessment.completion_percent},
    )


@require_editor
def assessment_result_update(request, pk):
    result = get_object_or_404_scoped(AssessmentResult.objects, request, pk=pk)
    if request.method == "POST":
        form = AssessmentResultForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            log_activity(request, "updated", target=result, description=f"Assessment result updated: {result}")
            messages.success(request, "Result updated.")
    return redirect(reverse("assessments:detail", args=[result.assessment_id]))
