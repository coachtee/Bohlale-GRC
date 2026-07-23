from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification


@login_required
def notification_list(request):
    notes = Notification.objects.filter(recipient=request.user)
    if request.organisation is not None:
        notes = notes.filter(organisation=request.organisation)
    return render(request, "notifications/list.html", {"notifications": notes[:100]})


@login_required
def mark_read(request, pk):
    note = get_object_or_404(Notification, pk=pk, recipient=request.user)
    note.is_read = True
    note.save(update_fields=["is_read"])
    if note.link:
        return redirect(note.link)
    return redirect("notifications:list")


@login_required
def mark_all_read(request):
    qs = Notification.objects.filter(recipient=request.user, is_read=False)
    if request.organisation is not None:
        qs = qs.filter(organisation=request.organisation)
    qs.update(is_read=True)
    return redirect("notifications:list")
