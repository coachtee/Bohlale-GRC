from collections import OrderedDict

from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone

from activity.utils import log_activity
from core.permissions import get_object_or_404_scoped, require_editor, require_organisation

from .forms import KnowledgeItemForm
from .models import CATEGORY_CHOICES, KnowledgeItem
from .services import profile_completeness


@require_organisation
def profile(request):
    items = KnowledgeItem.objects.filter(organisation=request.organisation)
    grouped = OrderedDict((key, {"label": label, "items": []}) for key, label in CATEGORY_CHOICES)
    for item in items:
        grouped[item.category]["items"].append(item)
    completeness = profile_completeness(request.organisation)
    return render(
        request,
        "knowledge/profile.html",
        {"grouped": grouped, "completeness": completeness},
    )


@require_editor
def item_create(request):
    if request.method == "POST":
        form = KnowledgeItemForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            item = form.save(commit=False)
            item.organisation = request.organisation
            if item.status == "verified":
                item.verified_by = request.user
                item.verified_at = timezone.now()
            item.save()
            log_activity(request, "created", target=item, description=f"Knowledge item added: {item.label}")
            messages.success(request, "Knowledge item saved.")
            return redirect("knowledge:profile")
    else:
        form = KnowledgeItemForm(organisation=request.organisation)
    return render(request, "knowledge/item_form.html", {"form": form})


@require_editor
def item_edit(request, pk):
    item = get_object_or_404_scoped(KnowledgeItem.objects, request, pk=pk)
    if request.method == "POST":
        form = KnowledgeItemForm(request.POST, instance=item, organisation=request.organisation)
        if form.is_valid():
            item = form.save(commit=False)
            if item.status == "verified" and not item.verified_by:
                item.verified_by = request.user
                item.verified_at = timezone.now()
            item.save()
            log_activity(request, "updated", target=item, description=f"Knowledge item updated: {item.label}")
            messages.success(request, "Knowledge item updated.")
            return redirect("knowledge:profile")
    else:
        form = KnowledgeItemForm(instance=item, organisation=request.organisation)
    return render(request, "knowledge/item_form.html", {"form": form, "item": item})


@require_editor
def item_verify(request, pk):
    item = get_object_or_404_scoped(KnowledgeItem.objects, request, pk=pk)
    if request.method == "POST":
        item.mark_verified(request.user)
        log_activity(request, "verified", target=item, description=f"Knowledge item verified: {item.label}")
        messages.success(request, f"'{item.label}' marked as verified.")
    return redirect("knowledge:profile")
