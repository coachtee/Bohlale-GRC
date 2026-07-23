from collections import OrderedDict

from django.utils import timezone

from frameworks.services import adopt_framework

from .models import (
    JOURNEY_COMPLETED,
    JOURNEY_IN_PROGRESS,
    STEP_COMPLETED,
    JourneyStep,
    JourneyTemplate,
    OrganisationJourney,
    StepProgress,
)


def get_or_build_template(framework, goal_type):
    """
    Finds a pre-seeded template for this framework+goal. If none
    exists (e.g. a freshly imported custom framework with no
    hand-authored journey), builds a simple one automatically — one
    step per requirement — so onboarding always works, even for
    frameworks nobody has written guided content for yet.
    """
    template = (
        JourneyTemplate.objects.filter(framework=framework, goal_type=goal_type, is_active=True).first()
        or JourneyTemplate.objects.filter(framework=framework, is_active=True).first()
    )
    if template is not None:
        return template

    template = JourneyTemplate.objects.create(
        framework=framework,
        goal_type=goal_type,
        name=f"Implement {framework.name}",
        description=f"An automatically generated guided path through {framework.name}.",
    )
    order = 0
    for requirement in framework.requirements.select_related("domain").order_by("domain__order", "order"):
        order += 1
        JourneyStep.objects.create(
            template=template,
            requirement=requirement,
            order=order,
            title=requirement.title,
            description=requirement.guidance,
            guidance_what=requirement.guidance,
            guidance_who="Compliance Manager",
            step_type="info",
        )
    if order == 0:
        JourneyStep.objects.create(
            template=template, order=1, title=f"Review {framework.name}",
            description="Review this framework's requirements and record your implementation status.",
            step_type="info",
        )
    return template


def start_journey(organisation, template, user=None):
    journey, created = OrganisationJourney.objects.get_or_create(
        organisation=organisation,
        template=template,
        defaults={"status": JOURNEY_IN_PROGRESS, "started_at": timezone.now()},
    )
    if not created and journey.status == "not_started":
        journey.status = JOURNEY_IN_PROGRESS
        journey.started_at = timezone.now()
        journey.save(update_fields=["status", "started_at"])

    for step in template.steps.all():
        StepProgress.objects.get_or_create(organisation_journey=journey, step=step)

    if template.framework_id:
        adopt_framework(organisation, template.framework)

    recalculate_current_step(journey)
    return journey


def recalculate_current_step(journey):
    next_progress = (
        journey.step_progress.exclude(status=STEP_COMPLETED).order_by("step__order").first()
    )
    journey.current_step = next_progress.step if next_progress else None
    if next_progress is None:
        journey.status = JOURNEY_COMPLETED
        journey.completed_at = journey.completed_at or timezone.now()
    journey.save(update_fields=["current_step", "status", "completed_at"])
    return journey


def mark_step_complete(journey, step, user, notes=""):
    progress, _ = StepProgress.objects.get_or_create(organisation_journey=journey, step=step)
    progress.status = STEP_COMPLETED
    progress.completed_by = user
    progress.completed_at = timezone.now()
    if notes:
        progress.notes = notes
    progress.save()
    recalculate_current_step(journey)
    return progress


def mark_step_in_progress(journey, step):
    progress, _ = StepProgress.objects.get_or_create(organisation_journey=journey, step=step)
    if progress.status == "not_started":
        progress.status = "in_progress"
        progress.save(update_fields=["status", "updated_at"])
    return progress


def stage_summary(journey):
    """Groups steps by resolved stage for the implementation stepper."""
    steps = list(journey.template.steps.select_related("requirement__domain"))
    progress_by_step = {p.step_id: p for p in journey.step_progress.all()}

    stages = OrderedDict()
    for step in steps:
        key = (step.resolved_stage_order, step.resolved_stage_title)
        stages.setdefault(key, []).append(step)

    result = []
    reached_current = False
    for (order, title), stage_steps in sorted(stages.items(), key=lambda kv: kv[0][0]):
        statuses = [progress_by_step.get(s.id).status if progress_by_step.get(s.id) else "not_started" for s in stage_steps]
        if all(s == STEP_COMPLETED for s in statuses):
            stage_status = "done"
        elif not reached_current and any(s != STEP_COMPLETED for s in statuses):
            stage_status = "current"
            reached_current = True
        else:
            stage_status = "upcoming"
        result.append({"order": order, "title": title, "status": stage_status, "steps": stage_steps})
    return result
