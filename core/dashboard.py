"""
Assembles the data for the main organisation dashboard (spec §34).
Kept as a plain function (not baked into the view) so other places —
e.g. the executive summary report — could reuse pieces of the same
aggregation.
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from actions.models import STATUS_CLOSED as ACTION_CLOSED
from actions.models import CorrectiveAction
from activity.models import AuditLog
from approvals.models import ApprovalRequest
from documents.models import Document
from frameworks.models import Framework
from frameworks.services import framework_progress
from journeys.models import OrganisationJourney
from journeys.services import stage_summary
from risks.services import risk_overview


def _adopted_frameworks(organisation):
    return Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=organisation),
        adoptions__organisation=organisation,
    ).distinct()


def _primary_journey(organisation):
    # Prefer an in-progress journey (the common case — most visits are
    # mid-implementation); fall back to the most recently completed one
    # so a user who has actually finished their journey sees a
    # completion state rather than the dashboard reverting to looking
    # like nothing was ever started.
    base = OrganisationJourney.objects.filter(organisation=organisation).select_related(
        "template__framework", "current_step"
    )
    journey = base.filter(status="in_progress").order_by("-started_at").first()
    if journey is None:
        journey = base.filter(status="completed").order_by("-completed_at").first()
    return journey


def _open_actions_breakdown(organisation):
    today = timezone.now().date()
    week_end = today + timedelta(days=7)
    month_end = today + timedelta(days=30)
    open_actions = CorrectiveAction.objects.filter(organisation=organisation).exclude(status=ACTION_CLOSED)

    overdue = due_this_week = due_this_month = 0
    for action in open_actions:
        if not action.due_date:
            continue
        if action.due_date < today:
            overdue += 1
        elif action.due_date <= week_end:
            due_this_week += 1
        elif action.due_date <= month_end:
            due_this_month += 1

    return {
        "total": open_actions.count(),
        "overdue": overdue,
        "due_this_week": due_this_week,
        "due_this_month": due_this_month,
    }


def _resolve_targets(approvals):
    """
    ApprovalRequest.target is a GenericForeignKey, which Django's ORM
    cannot select_related — left alone, accessing `.target` on each of
    N approvals issues N extra queries. Since approvals are typically
    all against the same content type (Document), batch-fetch by
    content type instead: at most one extra query per distinct content
    type among the approvals actually being displayed, not one per row.
    """
    from django.contrib.contenttypes.models import ContentType

    ids_by_ct = {}
    for approval in approvals:
        ids_by_ct.setdefault(approval.content_type_id, set()).add(approval.object_id)
    resolved = {}
    for ct_id, object_ids in ids_by_ct.items():
        model_cls = ContentType.objects.get_for_id(ct_id).model_class()
        for obj in model_cls.objects.filter(pk__in=object_ids):
            resolved[(ct_id, str(obj.pk))] = obj
    return resolved


def _tasks_due_soon(request, limit=5):
    organisation = request.organisation
    tasks = []

    pending_approvals = list(
        ApprovalRequest.objects.filter(organisation=organisation, status="pending")
        .select_related("content_type")
        .order_by("-created_at")[:limit]
    )
    targets = _resolve_targets(pending_approvals)
    for approval in pending_approvals:
        target = targets.get((approval.content_type_id, str(approval.object_id)))
        tasks.append({
            "title": f"Review {target}" if target else "Review approval request",
            "meta": "Approval",
            "url": f"/approvals/{approval.pk}/",
            "action_label": "Review",
        })

    today = timezone.now().date()
    overdue_or_soon_actions = CorrectiveAction.objects.filter(
        organisation=organisation, due_date__isnull=False, due_date__lte=today + timedelta(days=14)
    ).exclude(status=ACTION_CLOSED)
    for action in overdue_or_soon_actions:
        tasks.append({
            "title": action.finding_description[:60],
            "meta": f"Due {'today' if action.due_date == today else action.due_date.strftime('%d %b %Y')}",
            "url": f"/actions/{action.pk}/",
            "action_label": "Start",
        })

    return tasks[:limit]


def _upcoming_reviews(organisation, limit=5):
    today = timezone.now().date()
    documents = (
        Document.objects.filter(organisation=organisation, next_review_date__isnull=False, next_review_date__gte=today)
        .order_by("next_review_date")[:limit]
    )
    reviews = []
    for document in documents:
        days = (document.next_review_date - today).days
        reviews.append({
            "title": document.title,
            "meta": f"Review due {document.next_review_date.strftime('%d %b %Y')}",
            "days_label": "Today" if days == 0 else f"In {days} day{'s' if days != 1 else ''}",
            "url": f"/documents/{document.pk}/",
        })
    return reviews


def _donut_style(pct, colour_var="var(--color-black)"):
    pct = max(0, min(100, pct))
    return f"background: conic-gradient({colour_var} 0% {pct}%, var(--color-grey-150) {pct}% 100%);"


def _risk_donut_style(counts):
    total = sum(counts.values()) or 1
    order = [("high", "var(--color-red)"), ("medium", "var(--color-amber)"),
             ("low", "var(--color-green)"), ("very_low", "var(--color-grey-400)")]
    stops = []
    cumulative = 0.0
    for key, colour in order:
        share = (counts.get(key, 0) / total) * 100
        start = cumulative
        cumulative += share
        stops.append(f"{colour} {start:.2f}% {cumulative:.2f}%")
    if not stops:
        return "background: var(--color-grey-150);"
    return f"background: conic-gradient({', '.join(stops)});"


def build_dashboard_context(request):
    organisation = request.organisation
    frameworks = _adopted_frameworks(organisation)
    compliance_overview = [
        {"framework": fw, "progress": framework_progress(organisation, fw)} for fw in frameworks
    ]

    journey = _primary_journey(organisation)
    journey_stages = stage_summary(journey) if journey else []
    org_risk_overview = risk_overview(organisation)

    context = {
        "organisation": organisation,
        "hour": timezone.localtime().hour,
        "compliance_overview": compliance_overview,
        "journey": journey,
        "journey_stages": journey_stages,
        "journey_donut_style": _donut_style(journey.progress_percent if journey else 0),
        "open_actions": _open_actions_breakdown(organisation),
        "risk_overview": org_risk_overview,
        "risk_donut_style": _risk_donut_style(org_risk_overview["counts"]),
        "tasks_due_soon": _tasks_due_soon(request),
        "upcoming_reviews": _upcoming_reviews(organisation),
        "recent_activity": AuditLog.objects.filter(organisation=organisation).select_related("actor")[:8],
    }
    return context
