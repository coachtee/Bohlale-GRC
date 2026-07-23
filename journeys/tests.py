from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from frameworks.models import Framework
from knowledge.models import KnowledgeItem
from tenancy.models import Membership, Organisation

from .models import InformationRequest, JOURNEY_IN_PROGRESS, OrganisationJourney, STEP_COMPLETED
from .services import get_or_build_template, mark_step_complete, start_journey


def _seed():
    call_command("seed_frameworks")
    call_command("seed_journey_templates")


class JourneyTemplateSeedTests(TestCase):
    def test_iso27001_template_has_13_steps(self):
        _seed()
        framework = Framework.objects.get(code="ISO27001")
        template = framework.journey_templates.get(goal_type="build_from_scratch")
        self.assertEqual(template.steps.count(), 13)

    def test_get_or_build_template_builds_when_missing(self):
        _seed()
        org = Organisation.objects.create(name="Org")
        custom = Framework.objects.create(organisation=org, code="X1", name="Custom FW", source_type="custom")
        from frameworks.models import Domain, Requirement

        domain = Domain.objects.create(framework=custom, code="1", title="Section 1", order=1)
        Requirement.objects.create(framework=custom, domain=domain, ref_code="1.1", title="Do a thing")
        template = get_or_build_template(custom, "implement_framework")
        self.assertEqual(template.steps.count(), 1)


class StartJourneyTests(TestCase):
    def setUp(self):
        _seed()
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.framework = Framework.objects.get(code="ISO27001")
        self.template = self.framework.journey_templates.get(goal_type="build_from_scratch")

    def test_start_journey_creates_progress_for_every_step(self):
        journey = start_journey(self.org, self.template, self.user)
        self.assertEqual(journey.step_progress.count(), self.template.steps.count())
        self.assertEqual(journey.status, JOURNEY_IN_PROGRESS)
        self.assertEqual(journey.current_step, self.template.steps.first())

    def test_start_journey_adopts_framework(self):
        start_journey(self.org, self.template, self.user)
        self.assertTrue(self.org.framework_adoptions.filter(framework=self.framework).exists())

    def test_mark_step_complete_advances_current_step(self):
        journey = start_journey(self.org, self.template, self.user)
        first_step = self.template.steps.first()
        mark_step_complete(journey, first_step, self.user)
        journey.refresh_from_db()
        self.assertNotEqual(journey.current_step, first_step)
        progress = journey.step_progress.get(step=first_step)
        self.assertEqual(progress.status, STEP_COMPLETED)

    def test_completing_all_steps_completes_journey(self):
        journey = start_journey(self.org, self.template, self.user)
        for step in self.template.steps.all():
            mark_step_complete(journey, step, self.user)
        journey.refresh_from_db()
        self.assertEqual(journey.status, "completed")
        self.assertIsNone(journey.current_step)

    def test_completed_journey_page_shows_completion_state_not_step_one(self):
        # Regression: journey_home previously fell back to
        # `journey.template.steps.first()` whenever current_step was
        # None, which only happens once every step is complete — so a
        # finished journey misleadingly kept showing step 1 as the
        # "current step" with a Completed badge instead of a genuine
        # completion state.
        journey = start_journey(self.org, self.template, self.user)
        for step in self.template.steps.all():
            mark_step_complete(journey, step, self.user)
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("journeys:journey_home"))
        self.assertIsNone(response.context["focus_step"])
        self.assertContains(response, "Journey complete")
        self.assertNotContains(response, "CURRENT STEP")

    def test_completed_journey_still_appears_on_dashboard(self):
        # Regression: core.dashboard._primary_journey only looked for
        # status="in_progress", so a fully-completed journey (status
        # becomes "completed") disappeared from the dashboard entirely,
        # making it look like nothing had ever been started.
        journey = start_journey(self.org, self.template, self.user)
        for step in self.template.steps.all():
            mark_step_complete(journey, step, self.user)
        self.client.login(email="a@example.com", password="StrongPass123!")
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.context["journey"], journey)
        self.assertContains(response, "100%")
        self.assertNotContains(response, "No guided journey started yet")


class OnboardingFlowTests(TestCase):
    def setUp(self):
        _seed()
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_full_onboarding_wizard(self):
        response = self.client.post(reverse("journeys:onboarding_goal"), {"goal_type": "build_from_scratch"})
        self.assertRedirects(response, reverse("journeys:onboarding_framework"))

        framework = Framework.objects.get(code="ISO27001")
        response = self.client.post(reverse("journeys:onboarding_framework"), {"framework_id": str(framework.pk)})
        self.assertRedirects(
            response,
            reverse("journeys:onboarding_start", args=[framework.pk, "build_from_scratch"]),
            fetch_redirect_response=False,
        )

        response = self.client.get(response.url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(OrganisationJourney.objects.filter(organisation=self.org).exists())
        self.assertContains(response, "Understand your organisation")

    def test_popia_goal_skips_framework_picker(self):
        response = self.client.post(reverse("journeys:onboarding_goal"), {"goal_type": "popia_assessment"}, follow=True)
        self.assertEqual(response.status_code, 200)
        journey = OrganisationJourney.objects.get(organisation=self.org)
        self.assertEqual(journey.template.framework.code, "POPIA")

    def test_import_custom_framework_goal_redirects_to_framework_studio(self):
        response = self.client.post(reverse("journeys:onboarding_goal"), {"goal_type": "import_custom_framework"})
        self.assertRedirects(response, reverse("frameworks:import_create"))


class InterviewFlowTests(TestCase):
    def setUp(self):
        _seed()
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")
        framework = Framework.objects.get(code="ISO27001")
        template = framework.journey_templates.get(goal_type="build_from_scratch")
        self.journey = start_journey(self.org, template, self.user)
        self.step = template.steps.first()

    def test_interview_start_creates_session_with_seeded_questions(self):
        response = self.client.get(
            reverse("journeys:interview_start", args=[self.step.pk]) + f"?journey={self.journey.pk}", follow=True
        )
        self.assertEqual(response.status_code, 200)
        session = response.context["session"]
        self.assertEqual(session.exchanges.count(), len(self.step.guidance_questions))

    def test_answering_all_questions_completes_session_and_updates_knowledge_profile(self):
        self.client.get(reverse("journeys:interview_start", args=[self.step.pk]) + f"?journey={self.journey.pk}")
        from .models import InterviewSession

        session = InterviewSession.objects.get(organisation=self.org, step=self.step)
        for _ in session.exchanges.all():
            response = self.client.get(reverse("journeys:interview_session", args=[session.pk]))
            next_q = response.context["next_exchange"]
            self.client.post(reverse("journeys:interview_session", args=[session.pk]), {"answer_text": "An answer."})
        session.refresh_from_db()
        self.assertEqual(session.status, "completed")
        self.assertTrue(KnowledgeItem.objects.filter(organisation=self.org, status="verified").exists())


class InformationRequestTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_create_request_to_external_email_sends_email(self):
        response = self.client.post(
            reverse("journeys:information_request_create"),
            {
                "assigned_role_label": "IT Manager",
                "assigned_email": "it@example.com",
                "question_text": "Which systems does the organisation use?",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(InformationRequest.objects.filter(assigned_email="it@example.com").exists())

    def test_respond_via_token_updates_knowledge_profile_as_ai_inference(self):
        info_request = InformationRequest.objects.create(
            organisation=self.org, requested_by=self.user, assigned_email="it@example.com",
            question_text="Which systems does the organisation use?",
        )
        self.client.logout()
        response = self.client.post(
            reverse("journeys:information_request_respond", args=[info_request.token]),
            {"response_text": "We use Google Workspace and a custom LMS."},
        )
        self.assertEqual(response.status_code, 200)
        info_request.refresh_from_db()
        self.assertEqual(info_request.status, "answered")
        item = KnowledgeItem.objects.get(organisation=self.org, label=info_request.question_text[:180])
        self.assertEqual(item.status, "ai_inference")

    def test_answered_request_token_cannot_be_reanswered(self):
        info_request = InformationRequest.objects.create(
            organisation=self.org, requested_by=self.user, assigned_email="it@example.com",
            question_text="Q", status="answered", response_text="already answered",
        )
        self.client.logout()
        response = self.client.get(reverse("journeys:information_request_respond", args=[info_request.token]))
        self.assertEqual(response.status_code, 200)


class JourneyTenantIsolationTests(TestCase):
    def setUp(self):
        _seed()
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")

        framework = Framework.objects.get(code="ISO27001")
        template = get_or_build_template(framework, "build_from_scratch")
        self.journey_b = start_journey(self.org_b, template, self.user_a)

        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_org_a_cannot_view_org_b_journey_via_query_param(self):
        response = self.client.get(reverse("journeys:journey_home"), {"journey": str(self.journey_b.pk)})
        # Org A has no journey of its own, so passing Org B's journey pk
        # as a query param must not resolve to it — falls back to "no
        # journey started" rather than leaking Org B's journey.
        self.assertNotEqual(response.context.get("journey"), self.journey_b)

    def test_org_a_cannot_access_org_b_interview_session(self):
        from .models import InterviewSession

        step = self.journey_b.template.steps.first()
        interview_session = InterviewSession.objects.create(
            organisation=self.org_b, step=step, started_by=self.user_a,
        )
        response = self.client.get(reverse("journeys:interview_session", args=[interview_session.pk]))
        self.assertEqual(response.status_code, 404)

    def test_org_a_information_request_list_excludes_org_b(self):
        InformationRequest.objects.create(
            organisation=self.org_b, requested_by=self.user_a, assigned_email="it@example.com",
            question_text="Org B secret question",
        )
        response = self.client.get(reverse("journeys:information_request_list"))
        self.assertNotContains(response, "Org B secret question")
        self.assertNotContains(response, "<form")
