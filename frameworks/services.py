from .models import REQ_COMPLETE, REQ_NOT_APPLICABLE, FrameworkAdoption, Requirement, RequirementStatus


def adopt_framework(organisation, framework):
    adoption, _ = FrameworkAdoption.objects.get_or_create(organisation=organisation, framework=framework)
    return adoption


def framework_progress(organisation, framework):
    # 2 queries total (was 3: a .count(), a status fetch, then a second
    # full re-evaluation of `requirements` in the for-loop) — called once
    # per adopted framework on every dashboard load and in reports, so
    # this adds up under multiple adoptions.
    requirement_ids = list(Requirement.objects.filter(framework=framework).values_list("id", flat=True))
    total = len(requirement_ids)
    if total == 0:
        return 0
    statuses = dict(
        RequirementStatus.objects.filter(
            organisation=organisation, requirement_id__in=requirement_ids
        ).values_list("requirement_id", "status")
    )
    applicable_total = 0
    done = 0
    for req_id in requirement_ids:
        status = statuses.get(req_id)
        if status == REQ_NOT_APPLICABLE:
            continue
        applicable_total += 1
        if status == REQ_COMPLETE:
            done += 1
    if applicable_total == 0:
        return 0
    return round((done / applicable_total) * 100)


def set_requirement_status(organisation, requirement, status, notes=""):
    obj, _ = RequirementStatus.objects.update_or_create(
        organisation=organisation, requirement=requirement, defaults={"status": status, "notes": notes}
    )
    return obj
