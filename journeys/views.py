from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from activity.utils import log_activity
from core.permissions import get_object_or_404_scoped, require_editor, require_organisation
from core.ratelimit import rate_limit
from frameworks.models import Framework
from knowledge.models import STATUS_AI_INFERENCE, STATUS_VERIFIED
from knowledge.services import set_item
from notifications.utils import notify

from .forms import InformationRequestForm, InformationResponseForm, InterviewAnswerForm, OnboardingGoalForm
from .models import GOAL_CHOICES, InformationRequest, InterviewExchange, InterviewSession, OrganisationJourney
from .services import get_or_build_template, mark_step_complete, mark_step_in_progress, stage_summary, start_journey

FRAMEWORK_HINT_BY_GOAL = {
    "popia_assessment": "POPIA",
}


# ------------------------------------------------------------------- Onboarding

@require_organisation
def onboarding_goal(request):
    if request.method == "POST":
        form = OnboardingGoalForm(request.POST)
        if form.is_valid():
            goal = form.cleaned_data["goal_type"]
            if goal == "import_custom_framework":
                return redirect("frameworks:import_create")
            if goal == "grc_baseline":
                messages.info(request, "Let's start by building your Organisation Knowledge Profile.")
                return redirect("knowledge:profile")
            hinted_code = FRAMEWORK_HINT_BY_GOAL.get(goal)
            if hinted_code:
                framework = Framework.objects.filter(code=hinted_code, organisation__isnull=True).first()
                if framework:
                    return redirect("journeys:onboarding_start", framework_id=framework.pk, goal_type=goal)
            request.session["onboarding_goal"] = goal
            return redirect("journeys:onboarding_framework")
    else:
        form = OnboardingGoalForm()
    return render(request, "journeys/onboarding_goal.html", {"form": form, "goals": GOAL_CHOICES})


@require_organisation
def onboarding_framework(request):
    goal = request.session.get("onboarding_goal", "build_from_scratch")
    frameworks = Framework.objects.filter(
        Q(organisation__isnull=True) | Q(organisation=request.organisation), is_published=True
    ).order_by("name")
    if request.method == "POST":
        framework_id = request.POST.get("framework_id")
        return redirect("journeys:onboarding_start", framework_id=framework_id, goal_type=goal)
    return render(request, "journeys/onboarding_framework.html", {"frameworks": frameworks, "goal": goal})


@require_editor
def onboarding_start(request, framework_id, goal_type):
    framework = get_object_or_404(
        Framework.objects.filter(Q(organisation__isnull=True) | Q(organisation=request.organisation)),
        pk=framework_id,
    )
    template = get_or_build_template(framework, goal_type)
    journey = start_journey(request.organisation, template, request.user)
    log_activity(request, "started", target=journey, description=f"Started guided journey: {template.name}")
    messages.success(request, f"Your guided journey — {template.name} — has started.")
    return redirect("journeys:journey_home")


# ------------------------------------------------------------------ Journey home

def _active_journey(request, journey_id=None):
    qs = OrganisationJourney.objects.filter(organisation=request.organisation).select_related("template", "current_step")
    if journey_id:
        return qs.filter(pk=journey_id).first()
    return qs.filter(status="in_progress").order_by("-started_at").first() or qs.order_by("-created_at").first()


@require_organisation
def journey_home(request):
    journeys = OrganisationJourney.objects.filter(organisation=request.organisation).select_related("template")
    journey_id = request.GET.get("journey")
    journey = _active_journey(request, journey_id)

    if journey is None:
        return render(request, "journeys/no_journey.html", {"goals": GOAL_CHOICES})

    stages = stage_summary(journey)
    step_id = request.GET.get("step")
    if step_id:
        focus_step = get_object_or_404(journey.template.steps, pk=step_id)
    else:
        focus_step = journey.current_step or journey.template.steps.first()

    progress = None
    if focus_step:
        progress = journey.step_progress.filter(step=focus_step).first()

    interview_session = None
    if focus_step:
        interview_session = InterviewSession.objects.filter(
            organisation=request.organisation, step=focus_step
        ).order_by("-created_at").first()

    info_requests = []
    if focus_step:
        info_requests = InformationRequest.objects.filter(organisation=request.organisation, step=focus_step)

    return render(
        request,
        "journeys/journey_home.html",
        {
            "journeys": journeys,
            "journey": journey,
            "stages": stages,
            "focus_step": focus_step,
            "progress": progress,
            "interview_session": interview_session,
            "info_requests": info_requests,
        },
    )


@require_editor
def step_mark_complete(request, step_id):
    journey = _active_journey(request, request.GET.get("journey"))
    step = get_object_or_404(journey.template.steps, pk=step_id)
    if request.method == "POST":
        mark_step_complete(journey, step, request.user)
        log_activity(request, "completed", target=step, description=f"Journey step completed: {step.title}")
        messages.success(request, f"'{step.title}' marked complete.")
    return redirect(f"{reverse('journeys:journey_home')}?journey={journey.pk}")


# ------------------------------------------------------------------- AI Interview

@require_editor
def interview_start(request, step_id):
    journey = _active_journey(request, request.GET.get("journey"))
    step = get_object_or_404(journey.template.steps, pk=step_id)
    session = InterviewSession.objects.filter(
        organisation=request.organisation, step=step, status="in_progress"
    ).first()
    if session is None:
        session = InterviewSession.objects.create(organisation=request.organisation, step=step, started_by=request.user)
        for i, question in enumerate(step.guidance_questions, start=1):
            InterviewExchange.objects.create(session=session, order=i, question_text=question)
        if not step.guidance_questions:
            InterviewExchange.objects.create(
                session=session, order=1, question_text=f"Tell me what you know about: {step.title}",
            )
    mark_step_in_progress(journey, step)
    return redirect("journeys:interview_session", session_id=session.pk)


@require_editor
def interview_session_view(request, session_id):
    session = get_object_or_404_scoped(InterviewSession.objects, request, pk=session_id)
    next_exchange = session.exchanges.filter(answer_text="").order_by("order").first()

    if request.method == "POST" and next_exchange is not None:
        form = InterviewAnswerForm(request.POST)
        if form.is_valid():
            next_exchange.answer_text = form.cleaned_data["answer_text"]
            next_exchange.answered_at = timezone.now()
            next_exchange.save()

            set_item(
                request.organisation,
                category="organisation_profile",
                label=next_exchange.question_text[:180],
                value=next_exchange.answer_text,
                status=STATUS_VERIFIED,
                source=f"Organisation Interview: {session.step.title}",
                user=request.user,
            )
            log_activity(request, "answered", target=session, description=f"Interview answer recorded for: {session.step.title}")
            next_exchange = session.exchanges.filter(answer_text="").order_by("order").first()
            if next_exchange is None:
                session.status = "completed"
                session.save(update_fields=["status"])
                messages.success(request, "All questions answered. The Knowledge Profile has been updated.")
            return redirect("journeys:interview_session", session_id=session.pk)
    else:
        form = InterviewAnswerForm() if next_exchange else None

    return render(
        request,
        "journeys/interview_session.html",
        {"session": session, "exchanges": session.exchanges.all(), "next_exchange": next_exchange, "form": form},
    )


# ------------------------------------------------------------- Information Requests

@require_organisation
def information_request_list(request):
    requests_qs = InformationRequest.objects.filter(organisation=request.organisation).select_related(
        "step", "assigned_to_user"
    )
    return render(request, "journeys/information_request_list.html", {"requests": requests_qs})


@require_editor
def information_request_create(request, step_id=None):
    step = None
    if step_id:
        journey = _active_journey(request, request.GET.get("journey"))
        step = get_object_or_404(journey.template.steps, pk=step_id) if journey else None
    if request.method == "POST":
        form = InformationRequestForm(request.POST, organisation=request.organisation)
        if form.is_valid():
            info_request = form.save(commit=False)
            info_request.organisation = request.organisation
            info_request.step = step
            info_request.requested_by = request.user
            info_request.save()
            if info_request.assigned_to_user:
                link = reverse("journeys:information_request_respond", args=[info_request.token])
                notify(
                    request.organisation, info_request.assigned_to_user,
                    f"You've been asked: {info_request.question_text[:100]}",
                    category="information_request", link=link, send_email=True,
                )
            elif info_request.assigned_email:
                from django.conf import settings
                from django.core.mail import send_mail

                link = request.build_absolute_uri(
                    reverse("journeys:information_request_respond", args=[info_request.token])
                )
                send_mail(
                    subject=f"{request.organisation.name} needs your input — Bohlale GRC",
                    message=f"{info_request.question_text}\n\nPlease respond here: {link}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[info_request.assigned_email],
                    fail_silently=True,
                )
            log_activity(request, "requested", target=info_request, description="Information requested")
            messages.success(request, "Information request sent.")
            return redirect("journeys:information_request_list")
    else:
        form = InformationRequestForm(organisation=request.organisation)
    return render(request, "journeys/information_request_form.html", {"form": form, "step": step})


@rate_limit("info_request_respond", limit=30, window_seconds=300)
def information_request_respond(request, token):
    """Public, token-authenticated response page — no login required,
    limited strictly to this one request (spec §12: secure limited-access
    questionnaires without full platform access)."""
    info_request = get_object_or_404(InformationRequest, token=token)
    if info_request.status == "answered":
        return render(request, "journeys/information_request_done.html", {"info_request": info_request})
    if request.method == "POST":
        form = InformationResponseForm(request.POST)
        if form.is_valid():
            info_request.response_text = form.cleaned_data["response_text"]
            info_request.status = "answered"
            info_request.responded_at = timezone.now()
            info_request.save()
            set_item(
                info_request.organisation,
                category=info_request.knowledge_category or "organisation_profile",
                label=info_request.knowledge_label or info_request.question_text[:180],
                value=info_request.response_text,
                status=STATUS_AI_INFERENCE,
                source=f"Information Request response from {info_request.assigned_role_label or info_request.assigned_email}",
            )
            log_activity(
                None, "responded", target=info_request, description="Information request answered",
                organisation=info_request.organisation,
            )
            return render(request, "journeys/information_request_done.html", {"info_request": info_request})
    else:
        form = InformationResponseForm()
    return render(request, "journeys/information_request_respond.html", {"info_request": info_request, "form": form})
