import json
import uuid

from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from activity.utils import log_activity
from ai import service as ai_service
from ai.models import AIGeneration
from core.permissions import can_administer, require_editor, require_organisation

from .forms import (
    DomainQuickForm,
    ExtractedDataEditForm,
    FrameworkForm,
    FrameworkImportForm,
    RequirementQuickForm,
    RequirementStatusForm,
)
from .importer import extract_structure
from .models import Domain, Framework, FrameworkImport, Requirement, RequirementStatus
from .services import adopt_framework, framework_progress, set_requirement_status


def _visible_frameworks(request):
    return Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=request.organisation),
        is_published=True,
    )


def _framework_row(request, adopted_ids, fw):
    return {"framework": fw, "adopted": fw.id in adopted_ids, "progress": framework_progress(request.organisation, fw)}


def _ciso_generations_for(organisation, framework):
    """Recent Model CISO Assistant output for this framework, most
    recent first — shown inline on the framework detail page."""
    content_type = ContentType.objects.get_for_model(Framework)
    return AIGeneration.objects.filter(
        organisation=organisation, content_type=content_type, object_id=str(framework.id)
    ).select_related("requested_by").order_by("-created_at")[:5]


@require_organisation
def framework_list(request):
    adopted_ids = set(
        request.organisation.framework_adoptions.values_list("framework_id", flat=True)
    )

    builtin = (
        _visible_frameworks(request)
        .filter(organisation__isnull=True)
        .select_related("category")
        .order_by("category__order", "category__name", "name")
    )
    category_sections = []
    seen_categories = {}
    for fw in builtin:
        key = fw.category_id
        if key not in seen_categories:
            seen_categories[key] = {"category": fw.category, "rows": []}
            category_sections.append(seen_categories[key])
        seen_categories[key]["rows"].append(_framework_row(request, adopted_ids, fw))

    custom = (
        _visible_frameworks(request).filter(organisation=request.organisation).order_by("name")
    )
    custom_rows = [_framework_row(request, adopted_ids, fw) for fw in custom]

    return render(
        request,
        "frameworks/list.html",
        {
            "category_sections": category_sections,
            "custom_rows": custom_rows,
            "has_any_builtin": builtin.exists(),
        },
    )


@require_editor
def framework_create(request):
    if request.method == "POST":
        form = FrameworkForm(request.POST)
        if form.is_valid():
            framework = form.save(commit=False)
            framework.organisation = request.organisation
            framework.source_type = "custom"
            framework.is_published = True
            framework.code = f"CUSTOM-{uuid.uuid4().hex[:8].upper()}"
            framework.created_by = request.user
            framework.save()
            log_activity(request, "created", target=framework, description=f"Framework created: {framework.name}")
            messages.success(
                request, f"{framework.name} has been created. Add domains and requirements below to build it out."
            )
            return redirect("frameworks:detail", pk=framework.pk)
    else:
        form = FrameworkForm()
    return render(
        request, "core/generic_form.html",
        {"form": form, "form_title": "Create Framework Manually", "cancel_url": "/frameworks/"},
    )


def _own_framework_or_404(request, pk):
    """Org-owned custom/imported frameworks only — never a built-in
    (organisation is null) or another tenant's framework. 404, not 403,
    per the project's tenant-isolation convention."""
    return get_object_or_404(Framework, pk=pk, organisation=request.organisation)


@require_editor
def domain_create(request, pk):
    framework = _own_framework_or_404(request, pk)
    if request.method == "POST":
        form = DomainQuickForm(request.POST)
        if form.is_valid():
            order = framework.domains.count() + 1
            Domain.objects.create(
                framework=framework,
                code=form.cleaned_data["code"] or str(order),
                title=form.cleaned_data["title"],
                order=order,
            )
            log_activity(request, "updated", target=framework, description=f"Domain added to {framework.name}")
            messages.success(request, "Domain added.")
        else:
            messages.error(request, "Please provide a domain title.")
    return redirect("frameworks:detail", pk=framework.pk)


@require_editor
def requirement_create(request, pk, domain_pk):
    framework = _own_framework_or_404(request, pk)
    domain = get_object_or_404(Domain, pk=domain_pk, framework=framework)
    if request.method == "POST":
        form = RequirementQuickForm(request.POST)
        if form.is_valid():
            order = domain.requirements.count() + 1
            Requirement.objects.create(
                framework=framework,
                domain=domain,
                ref_code=form.cleaned_data["ref_code"] or f"{domain.code}.{order}",
                title=form.cleaned_data["title"],
                guidance=form.cleaned_data["guidance"],
                order=order,
            )
            log_activity(request, "updated", target=framework, description=f"Requirement added to {framework.name}")
            messages.success(request, "Requirement added.")
        else:
            messages.error(request, "Please provide a requirement title.")
    return redirect("frameworks:detail", pk=framework.pk)


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
    from controls.services import related_frameworks_via_controls

    framework = get_object_or_404(_visible_frameworks(request), pk=pk)
    domains = framework.domains.prefetch_related("requirements").all()
    statuses = {
        rs.requirement_id: rs
        for rs in RequirementStatus.objects.filter(organisation=request.organisation, requirement__framework=framework)
    }
    can_edit_structure = framework.organisation_id == request.organisation.id
    for domain in domains:
        for req in domain.requirements.all():
            req.current_status = statuses.get(req.id)
        if can_edit_structure:
            # Each domain gets its own quick-add-requirement form instance
            # with a unique auto_id, so its rendered <input id="..."> /
            # <label for="..."> pairs don't collide with every other
            # domain's form (or the page's single add-domain form) when
            # several forms with the same field names share one page.
            domain.requirement_form = RequirementQuickForm(auto_id=f"id_req_{domain.pk.hex}_%s")
    is_adopted = request.organisation.framework_adoptions.filter(framework=framework).exists()
    return render(
        request,
        "frameworks/detail.html",
        {
            "framework": framework,
            "domains": domains,
            "is_adopted": is_adopted,
            "progress": framework_progress(request.organisation, framework),
            "can_edit_structure": can_edit_structure,
            "domain_form": DomainQuickForm(auto_id="id_domainform_%s"),
            "related_frameworks": related_frameworks_via_controls(request.organisation, framework) if is_adopted else [],
            "ciso_generations": _ciso_generations_for(request.organisation, framework),
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


# ---------------------------------------------------------------- Model CISO Assistant

CISO_PURPOSE_BY_ACTION = {
    "explain_control": "control_explanation",
    "suggest_evidence": "evidence_suggestion",
    "draft_guidance": "framework_guidance",
}

CISO_ACTION_LABELS = {
    "explain_control": "a control explanation",
    "suggest_evidence": "an evidence suggestion",
    "draft_guidance": "implementation guidance",
}


@require_editor
def ciso_assist(request, pk):
    """
    Model CISO Assistant panel (framework detail page): explain a
    control, suggest evidence, or draft implementation guidance for the
    selected framework — optionally focused on one requirement. Goes
    through the same ai.service.generate() governance path as every
    other AI feature (AIGeneration record, human-review framing,
    tenant-scoped context only).
    """
    framework = get_object_or_404(_visible_frameworks(request), pk=pk)
    if request.method != "POST":
        return redirect("frameworks:detail", pk=framework.pk)

    action = request.POST.get("action")
    purpose = CISO_PURPOSE_BY_ACTION.get(action)
    if purpose is None:
        messages.error(request, "Unrecognised Model CISO Assistant action.")
        return redirect("frameworks:detail", pk=framework.pk)

    from controls.models import Control

    requirement = Requirement.objects.filter(
        pk=request.POST.get("requirement_id") or None, framework=framework
    ).first()

    if requirement:
        context_reference = f"{framework.name} — {requirement.ref_code} {requirement.title}"
        prompt_lines = [
            f"Framework: {framework.name} ({framework.version})",
            f"Requirement: {requirement.ref_code} — {requirement.title}",
        ]
        if requirement.guidance:
            prompt_lines.append(f"Guidance: {requirement.guidance}")
        mapped_controls = Control.objects.filter(organisation=request.organisation, framework_requirements=requirement)
        if mapped_controls:
            prompt_lines.append("Organisation's mapped control(s): " + ", ".join(c.name for c in mapped_controls))
    else:
        context_reference = framework.name
        prompt_lines = [
            f"Framework: {framework.name} ({framework.version})",
            f"Description: {framework.description}",
        ]

    ai_service.generate(
        organisation=request.organisation,
        user=request.user,
        purpose=purpose,
        user_prompt="\n".join(prompt_lines),
        context_reference=context_reference,
        related_object=framework,
    )
    log_activity(
        request, "created", target=framework,
        description=f"Model CISO Assistant drafted {CISO_ACTION_LABELS.get(action, action)} for {framework.name}",
    )
    messages.success(request, "Model CISO Assistant has drafted a response below — review before relying on it.")
    return redirect("frameworks:detail", pk=framework.pk)
