import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from activity.utils import log_activity
from ai import service as ai_service
from core.permissions import can_administer, require_editor, require_organisation

from .forms import ExtractedDataEditForm, FrameworkImportForm, RequirementStatusForm
from .importer import extract_structure
from .models import Domain, Framework, FrameworkImport, Requirement, RequirementStatus
from .services import adopt_framework, framework_progress, set_requirement_status


def _visible_frameworks(request):
    return Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=request.organisation),
        is_published=True,
    )


@require_organisation
def framework_list(request):
    frameworks = _visible_frameworks(request).order_by("name")
    adopted_ids = set(
        request.organisation.framework_adoptions.values_list("framework_id", flat=True)
    )
    rows = [
        {"framework": fw, "adopted": fw.id in adopted_ids, "progress": framework_progress(request.organisation, fw)}
        for fw in frameworks
    ]
    return render(request, "frameworks/list.html", {"rows": rows})


@require_editor
def framework_adopt(request, pk):
    framework = get_object_or_404(_visible_frameworks(request), pk=pk)
    if request.method == "POST":
        adopt_framework(request.organisation, framework)
        log_activity(request, "adopted", target=framework, description=f"Adopted framework: {framework.name}")
        messages.success(request, f"{framework.name} added to your compliance frameworks.")
    return redirect("frameworks:detail", pk=framework.pk)


@require_organisation
def framework_detail(request, pk):
    framework = get_object_or_404(_visible_frameworks(request), pk=pk)
    domains = framework.domains.prefetch_related("requirements").all()
    statuses = {
        rs.requirement_id: rs
        for rs in RequirementStatus.objects.filter(organisation=request.organisation, requirement__framework=framework)
    }
    for domain in domains:
        for req in domain.requirements.all():
            req.current_status = statuses.get(req.id)
    is_adopted = request.organisation.framework_adoptions.filter(framework=framework).exists()
    return render(
        request,
        "frameworks/detail.html",
        {
            "framework": framework,
            "domains": domains,
            "is_adopted": is_adopted,
            "progress": framework_progress(request.organisation, framework),
        },
    )


@require_editor
def requirement_status_update(request, pk):
    requirement = get_object_or_404(Requirement.objects.filter(
        Q(framework__organisation__isnull=True) | Q(framework__organisation=request.organisation)
    ), pk=pk)
    if request.method == "POST":
        form = RequirementStatusForm(request.POST)
        if form.is_valid():
            set_requirement_status(
                request.organisation, requirement, form.cleaned_data["status"], form.cleaned_data["notes"]
            )
            log_activity(
                request, "updated", target=requirement,
                description=f"Requirement status updated: {requirement.ref_code} -> {form.cleaned_data['status']}",
            )
            messages.success(request, "Requirement status updated.")
    referer = request.META.get("HTTP_REFERER")
    if referer:
        return redirect(referer)
    return redirect("frameworks:detail", pk=requirement.framework_id)


# ---------------------------------------------------------------- Framework Studio

@require_organisation
def import_list(request):
    imports = FrameworkImport.objects.filter(organisation=request.organisation)
    return render(request, "frameworks/import_list.html", {"imports": imports})


@require_editor
def import_create(request):
    if request.method == "POST":
        form = FrameworkImportForm(request.POST, request.FILES)
        if form.is_valid():
            fw_import = form.save(commit=False)
            fw_import.organisation = request.organisation
            fw_import.created_by = request.user
            fw_import.save()
            log_activity(request, "created", target=fw_import, description="Framework import uploaded")
            return redirect("frameworks:import_analyse", pk=fw_import.pk)
    else:
        form = FrameworkImportForm()
    return render(request, "frameworks/import_form.html", {"form": form})


@require_editor
def import_analyse(request, pk):
    fw_import = get_object_or_404(FrameworkImport, pk=pk, organisation=request.organisation)
    text = fw_import.source_text
    if not text and fw_import.source_file:
        try:
            if fw_import.source_file.name.lower().endswith((".txt", ".csv")):
                text = fw_import.source_file.read().decode("utf-8", errors="ignore")
        except Exception:
            text = ""
    if not text:
        messages.warning(
            request,
            "Automatic text extraction is only available for pasted text or .txt/.csv uploads in this "
            "build. Please paste the framework text to continue.",
        )
        return redirect("frameworks:import_list")

    structure = extract_structure(text)
    generation = ai_service.generate(
        organisation=request.organisation,
        user=request.user,
        purpose="framework_extraction",
        user_prompt=text[:4000],
        context_reference=f"Framework Studio import: {fw_import.proposed_name or fw_import.pk}",
        related_object=fw_import,
    )
    fw_import.extracted_data = structure
    fw_import.status = "extracted"
    fw_import.notes = generation.output_text
    fw_import.save(update_fields=["extracted_data", "status", "notes"])
    log_activity(request, "analysed", target=fw_import, description="Framework import analysed and extracted")
    messages.success(request, "Draft structure extracted. Please review before publishing.")
    return redirect("frameworks:import_review", pk=fw_import.pk)


@require_editor
def import_review(request, pk):
    fw_import = get_object_or_404(FrameworkImport, pk=pk, organisation=request.organisation)
    if request.method == "POST":
        form = ExtractedDataEditForm(request.POST)
        if form.is_valid():
            try:
                fw_import.extracted_data = json.loads(form.cleaned_data["extracted_json"])
            except ValueError:
                messages.error(request, "That doesn't look like valid JSON — please check the structure.")
                return render(request, "frameworks/import_review.html", {"fw_import": fw_import, "form": form})
            fw_import.save(update_fields=["extracted_data"])
            messages.success(request, "Draft structure updated.")
            return redirect("frameworks:import_review", pk=fw_import.pk)
    else:
        form = ExtractedDataEditForm(initial={"extracted_json": json.dumps(fw_import.extracted_data, indent=2)})
    return render(request, "frameworks/import_review.html", {"fw_import": fw_import, "form": form})


@require_editor
def import_publish(request, pk):
    if not can_administer(request):
        raise PermissionDenied("Only organisation administrators can publish a framework.")
    fw_import = get_object_or_404(FrameworkImport, pk=pk, organisation=request.organisation)
    if request.method == "POST":
        name = fw_import.proposed_name or f"Custom framework {fw_import.pk.hex[:8]}"
        framework = Framework.objects.create(
            organisation=request.organisation,
            code=f"CUSTOM-{fw_import.pk.hex[:8].upper()}",
            name=name,
            source_type="imported",
            is_published=True,
            created_by=request.user,
        )
        for d_order, domain_data in enumerate(fw_import.extracted_data.get("domains", []), start=1):
            domain = Domain.objects.create(
                framework=framework, code=domain_data.get("code", str(d_order)),
                title=domain_data.get("title", f"Section {d_order}"), order=d_order,
            )
            for r_order, req_data in enumerate(domain_data.get("requirements", []), start=1):
                Requirement.objects.create(
                    framework=framework, domain=domain,
                    ref_code=req_data.get("ref_code", f"{domain.code}.{r_order}"),
                    title=req_data.get("title", "Untitled requirement"), order=r_order,
                )
        fw_import.status = "published"
        fw_import.resulting_framework = framework
        fw_import.reviewed_by = request.user
        fw_import.save(update_fields=["status", "resulting_framework", "reviewed_by"])
        adopt_framework(request.organisation, framework)
        log_activity(request, "published", target=framework, description=f"Framework published from import: {framework.name}")
        messages.success(request, f"{framework.name} has been published and added to your frameworks.")
        return redirect("frameworks:detail", pk=framework.pk)
    return redirect("frameworks:import_review", pk=fw_import.pk)
