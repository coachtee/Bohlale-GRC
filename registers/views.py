from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from activity.utils import log_activity
from core.permissions import get_object_or_404_scoped, require_editor, require_organisation

from .forms import build_register_form
from .models import RegisterEntry, RegisterType
from .services import ensure_default_register_types, register_hub_summary


@require_organisation
def hub(request):
    summary = register_hub_summary(request.organisation)
    return render(request, "registers/hub.html", summary)


@require_organisation
def generic_list(request, slug):
    ensure_default_register_types()
    register_type = get_object_or_404(RegisterType, slug=slug)
    entries = RegisterEntry.objects.filter(organisation=request.organisation, register_type=register_type)
    return render(request, "registers/generic_list.html", {"register_type": register_type, "entries": entries})


@require_editor
def generic_create(request, slug):
    register_type = get_object_or_404(RegisterType, slug=slug)
    if request.method == "POST":
        form = build_register_form(register_type, data=request.POST)
        if form.is_valid():
            entry = RegisterEntry.objects.create(
                organisation=request.organisation, register_type=register_type,
                data=form.cleaned_data, created_by=request.user,
            )
            log_activity(request, "created", target=entry, description=f"{register_type.name} entry added")
            messages.success(request, "Entry added.")
            return redirect("registers:generic_list", slug=slug)
    else:
        form = build_register_form(register_type)
    return render(request, "registers/generic_form.html", {"form": form, "register_type": register_type})


@require_editor
def generic_edit(request, slug, pk):
    register_type = get_object_or_404(RegisterType, slug=slug)
    entry = get_object_or_404_scoped(RegisterEntry.objects, request, pk=pk)
    if request.method == "POST":
        form = build_register_form(register_type, data=request.POST)
        if form.is_valid():
            entry.data = form.cleaned_data
            entry.save(update_fields=["data", "updated_at"])
            log_activity(request, "updated", target=entry, description=f"{register_type.name} entry updated")
            messages.success(request, "Entry updated.")
            return redirect("registers:generic_list", slug=slug)
    else:
        form = build_register_form(register_type, initial=entry.data)
    return render(request, "registers/generic_form.html", {"form": form, "register_type": register_type, "entry": entry})


@require_editor
def generic_delete(request, slug, pk):
    register_type = get_object_or_404(RegisterType, slug=slug)
    entry = get_object_or_404_scoped(RegisterEntry.objects, request, pk=pk)
    if request.method == "POST":
        entry.delete()
        messages.info(request, "Entry deleted.")
        return redirect("registers:generic_list", slug=slug)
    cancel_url = reverse("registers:generic_list", args=[slug])
    return render(request, "core/generic_confirm_delete.html", {"object": entry, "cancel_url": cancel_url})
