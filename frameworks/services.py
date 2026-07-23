from .models import REQ_COMPLETE, REQ_NOT_APPLICABLE, FrameworkAdoption, Requirement, RequirementStatus


def adopt_framework(organisation, framework):
    adoption, _ = FrameworkAdoption.objects.get_or_create(organisation=organisation, framework=framework)
    return adoption


def framework_progress(organisation, framework):
    requirements = Requirement.objects.filter(framework=framework)
    total = requirements.count()
    if total == 0:
        return 0
    statuses = {
        rs.requirement_id: rs.status
        for rs in RequirementStatus.objects.filter(organisation=organisation, requirement__framework=framework)
    }
    applicable_total = 0
    done = 0
    for req in requirements:
        status = statuses.get(req.id)
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
