from .models import Assessment, AssessmentResult


def create_assessment_from_framework(organisation, framework, name, assessment_type, assessor, user=None):
    """Creates an Assessment pre-populated with one result row per
    requirement in the framework, ready for the assessor to rate."""
    assessment = Assessment.objects.create(
        organisation=organisation, framework=framework, name=name,
        assessment_type=assessment_type, assessor=assessor, status="in_progress",
    )
    for requirement in framework.requirements.all():
        AssessmentResult.objects.create(organisation=organisation, assessment=assessment, requirement=requirement)
    return assessment
