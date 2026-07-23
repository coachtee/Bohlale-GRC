from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from actions.models import CorrectiveAction
from audits.models import Audit
from controls.services import ensure_soa_entries
from core.permissions import require_organisation
from documents.models import Document
from frameworks.models import Framework
from incidents.models import Incident
from risks.models import Risk

from .exporters import excel_response
from .services import (
    audit_readiness,
    executive_summary,
    framework_compliance_rows,
    gap_assessment_rows,
)


def _adopted_frameworks(request):
    return Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=request.organisation),
        adoptions__organisation=request.organisation,
    ).distinct()


@require_organisation
def hub(request):
    reports = [
        {"name": "Executive Compliance Summary", "url": "reports:executive_summary"},
        {"name": "Gap Assessment Report", "url": "reports:gap_assessment"},
        {"name": "Risk Register", "url": "reports:risk_register"},
        {"name": "Risk Treatment Plan", "url": "reports:risk_treatment_plan"},
        {"name": "Statement of Applicability", "url": "controls:soa"},
        {"name": "Policy Register", "url": "reports:policy_register"},
        {"name": "Incident Register", "url": "reports:incident_register"},
        {"name": "Audit Report", "url": "reports:audit_report_list"},
        {"name": "Corrective Action Report", "url": "reports:corrective_action_report"},
        {"name": "Audit Readiness Report", "url": "reports:readiness"},
        {"name": "Framework Compliance Report", "url": "reports:framework_compliance"},
    ]
    return render(request, "reports/hub.html", {"reports": reports})


@require_organisation
def executive_summary_report(request):
    summary = executive_summary(request.organisation)
    return render(request, "reports/executive_summary.html", {"summary": summary})


@require_organisation
def readiness_report(request):
    frameworks = _adopted_frameworks(request)
    framework_id = request.GET.get("framework")
    framework = frameworks.filter(pk=framework_id).first() if framework_id else frameworks.first()
    if framework is None:
        return render(request, "reports/readiness_empty.html", {})
    ensure_soa_entries(request.organisation, framework)
    readiness = audit_readiness(request.organisation, framework)
    return render(
        request, "reports/readiness.html",
        {"frameworks": frameworks, "framework": framework, "readiness": readiness},
    )


@require_organisation
def gap_assessment_report(request):
    frameworks = _adopted_frameworks(request)
    framework_id = request.GET.get("framework")
    framework = frameworks.filter(pk=framework_id).first() if framework_id else frameworks.first()
    if framework is None:
        return render(request, "reports/gap_assessment_empty.html", {})
    rows = gap_assessment_rows(request.organisation, framework)
    return render(request, "reports/gap_assessment.html", {"frameworks": frameworks, "framework": framework, "rows": rows})


@require_organisation
def risk_register_report(request):
    risks = Risk.objects.filter(organisation=request.organisation).select_related("owner")
    if request.GET.get("format") == "xlsx":
        headers = ["ID", "Title", "Category", "Likelihood", "Impact", "Inherent Score", "Owner", "Treatment", "Status"]
        rows = [
            [r.reference_code, r.title, r.get_category_display(), r.likelihood, r.impact,
             r.inherent_risk_score, str(r.owner or ""), r.get_treatment_display(), r.get_status_display()]
            for r in risks
        ]
        return excel_response("risk_register.xlsx", headers, rows)
    return render(request, "reports/risk_register.html", {"risks": risks})


@require_organisation
def risk_treatment_plan_report(request):
    risks = Risk.objects.filter(organisation=request.organisation).exclude(treatment="accept").select_related("treatment_owner")
    if request.GET.get("format") == "xlsx":
        headers = ["ID", "Title", "Treatment", "Treatment Owner", "Treatment Plan", "Due Date", "Status"]
        rows = [
            [r.reference_code, r.title, r.get_treatment_display(), str(r.treatment_owner or ""),
             r.treatment_plan, str(r.due_date or ""), r.get_status_display()]
            for r in risks
        ]
        return excel_response("risk_treatment_plan.xlsx", headers, rows)
    return render(request, "reports/risk_treatment_plan.html", {"risks": risks})


@require_organisation
def policy_register_report(request):
    documents = Document.objects.filter(organisation=request.organisation).select_related("owner")
    if request.GET.get("format") == "xlsx":
        headers = ["Reference", "Title", "Type", "Version", "Owner", "Status", "Next Review"]
        rows = [
            [d.reference_code, d.title, d.get_doc_type_display(), d.version_label, str(d.owner or ""),
             d.get_status_display(), str(d.next_review_date or "")]
            for d in documents
        ]
        return excel_response("policy_register.xlsx", headers, rows)
    return render(request, "reports/policy_register.html", {"documents": documents})


@require_organisation
def incident_register_report(request):
    incidents = Incident.objects.filter(organisation=request.organisation)
    if request.GET.get("format") == "xlsx":
        headers = ["Reference", "Title", "Severity", "Status", "Discovered", "Personal Info Involved"]
        rows = [
            [i.reference_code, i.title, i.get_severity_display(), i.get_status_display(),
             str(i.discovered_at or ""), "Yes" if i.personal_info_involved else "No"]
            for i in incidents
        ]
        return excel_response("incident_register.xlsx", headers, rows)
    return render(request, "reports/incident_register.html", {"incidents": incidents})


@require_organisation
def corrective_action_report(request):
    actions = CorrectiveAction.objects.filter(organisation=request.organisation).select_related("owner")
    if request.GET.get("format") == "xlsx":
        headers = ["Reference", "Finding", "Source", "Owner", "Due Date", "Status"]
        rows = [
            [a.reference_code, a.finding_description, a.get_source_display(), str(a.owner or ""),
             str(a.due_date or ""), a.get_status_display()]
            for a in actions
        ]
        return excel_response("corrective_actions.xlsx", headers, rows)
    return render(request, "reports/corrective_action_report.html", {"actions": actions})


@require_organisation
def framework_compliance_report(request):
    rows = framework_compliance_rows(request.organisation)
    return render(request, "reports/framework_compliance.html", {"rows": rows})


@require_organisation
def audit_report_list(request):
    audits = Audit.objects.filter(organisation=request.organisation)
    return render(request, "reports/audit_report_list.html", {"audits": audits})


@require_organisation
def audit_report_detail(request, pk):
    audit = get_object_or_404(Audit, pk=pk, organisation=request.organisation)
    return render(request, "reports/audit_report_detail.html", {"audit": audit, "findings": audit.findings.all()})
