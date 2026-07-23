from django.shortcuts import render

from core.permissions import get_object_or_404_scoped, require_organisation

from .models import AIGeneration


@require_organisation
def generation_log(request):
    generations = AIGeneration.objects.filter(organisation=request.organisation).select_related(
        "requested_by", "reviewed_by"
    )[:200]
    return render(request, "ai/log.html", {"generations": generations})


@require_organisation
def generation_detail(request, pk):
    generation = get_object_or_404_scoped(AIGeneration.objects, request, pk=pk)
    return render(request, "ai/detail.html", {"generation": generation})
