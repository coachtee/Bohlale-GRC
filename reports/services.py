"""
Report aggregation logic (spec §35). Reports are computed on the fly
from live data — no separate report-storage models — so they're always
current. Each function returns plain data structures the views render
either as a print-friendly HTML page (browser "Print to PDF") or an
Excel/CSV export (openpyxl / csv), per BUILD_STATUS.md Assumption 7.
"""

from django.db.models import Q
from django.utils import timezone

from actions.models import STATUS_CLOSED as ACTION_CLOSED
from actions.models import CorrectiveAction
from audits.models import Audit, AuditFinding
from controls.models import Control, SoAEntry
from controls.services import soa_coverage
from documents.models import STATUS_PUBLISHED, Document
from evidence.models import Evidence
from frameworks.models import Framework
from frameworks.services import framework_progress
from incidents.models import Incident
from reviews.models import ManagementReview
from risks.models import Risk
from risks.services import risk_overview


def _pct(numerator, denominator):
    if not denominator:
        return 0
    return round((numerator / denominator) * 100)


def evidence_coverage(organisation, framework):
    entries = list(
        SoAEntry.objects.filter(organisation=organisation, framework=framework, applicable=True)
        .values_list("control_id", flat=True)
    )
    total = len(entries)
    if total == 0:
        return 0
    # One query for which of these controls have any evidence, instead
    # of an `.exists()` query per SoA entry.
    controls_with_evidence = set(
        Control.objects.filter(pk__in=entries, evidence_items__isnull=False).values_list("pk", flat=True)
    )
    with_evidence = sum(1 for control_id in entries if control_id in controls_with_evidence)
    return _pct(with_evidence, total)


def risk_treatment_progress(organisation):
    risks = Risk.objects.filter(organisation=organisation)
    total = risks.count()
    treated = risks.exclude(status="open").count()
    return _pct(treated, total)


def document_approval_progress(organisation):
    docs = Document.objects.filter(organisation=organisation).exclude(status="archived")
    total = docs.count()
    published = docs.filter(status=STATUS_PUBLISHED).count()
    return _pct(published, total)


def internal_audit_completion(organisation):
    audits = Audit.objects.filter(organisation=organisation, audit_type="internal")
    total = audits.count()
    closed = audits.filter(status="closed").count()
    return _pct(closed, total)


def management_review_completion(organisation):
    reviews = ManagementReview.objects.filter(organisation=organisation)
    total = reviews.count()
    completed = reviews.filter(status="completed").count()
    return _pct(completed, total)


def corrective_action_progress(organisation):
    actions = CorrectiveAction.objects.filter(organisation=organisation)
    total = actions.count()
    closed = actions.filter(status=ACTION_CLOSED).count()
    return _pct(closed, total)


def open_major_gaps(organisation):
    return AuditFinding.objects.filter(
        organisation=organisation, severity="major_nonconformity"
    ).exclude(status="closed").count()


def audit_readiness(organisation, framework):
    """Audit Readiness (spec §33) — transparent, never claims
    certification; only ever says 'ready to begin certification audit
    preparation' or similar in the UI copy."""
    dimensions = {
        "Requirements": framework_progress(organisation, framework),
        "Controls": soa_coverage(organisation, framework),
        "Evidence": evidence_coverage(organisation, framework),
        "Risk Treatment": risk_treatment_progress(organisation),
        "Document Approval": document_approval_progress(organisation),
        "Internal Audit": internal_audit_completion(organisation),
        "Management Review": management_review_completion(organisation),
        "Corrective Actions": corrective_action_progress(organisation),
    }
    overall = round(sum(dimensions.values()) / len(dimensions)) if dimensions else 0
    return {
        "dimensions": dimensions,
        "open_major_gaps": open_major_gaps(organisation),
        "overall": overall,
    }


def executive_summary(organisation):
    adopted_frameworks = Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=organisation), adoptions__organisation=organisation
    ).distinct()
    framework_rows = [
        {"framework": fw, "progress": framework_progress(organisation, fw)} for fw in adopted_frameworks
    ]
    return {
        "frameworks": framework_rows,
        "risk_overview": risk_overview(organisation),
        "open_actions": CorrectiveAction.objects.filter(organisation=organisation).exclude(status=ACTION_CLOSED).count(),
        "overdue_actions": sum(1 for a in CorrectiveAction.objects.filter(organisation=organisation) if a.is_overdue),
        "documents_awaiting_approval": Document.objects.filter(organisation=organisation, status="awaiting_approval").count(),
        "documents_published": Document.objects.filter(organisation=organisation, status=STATUS_PUBLISHED).count(),
        "evidence_expiring_soon": sum(1 for e in Evidence.objects.filter(organisation=organisation) if e.is_expiring_soon),
        "open_incidents": Incident.objects.filter(organisation=organisation).exclude(status__in=["resolved", "closed"]).count(),
        "generated_at": timezone.now(),
    }


def gap_assessment_rows(organisation, framework):
    """Requirements not yet Complete for a framework — the Gap
    Assessment Report."""
    from frameworks.models import Requirement, RequirementStatus

    statuses = {
        rs.requirement_id: rs
        for rs in RequirementStatus.objects.filter(organisation=organisation, requirement__framework=framework)
    }
    rows = []
    for requirement in Requirement.objects.filter(framework=framework).select_related("domain"):
        status = statuses.get(requirement.id)
        if status is None or status.status not in ("complete", "not_applicable"):
            rows.append({"requirement": requirement, "status": status})
    return rows


def framework_compliance_rows(organisation):
    adopted = Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=organisation), adoptions__organisation=organisation
    ).distinct()
    return [{"framework": fw, "progress": framework_progress(organisation, fw)} for fw in adopted]
