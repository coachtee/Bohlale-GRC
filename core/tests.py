from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import User
from actions.models import CorrectiveAction
from documents.models import Document
from frameworks.models import Framework
from frameworks.services import adopt_framework
from journeys.services import start_journey
from risks.models import Risk
from tenancy.models import Membership, Organisation


class DashboardSmokeTests(TestCase):
    def setUp(self):
        call_command("seed_frameworks")
        call_command("seed_journey_templates")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(
            email="a@example.com", password="StrongPass123!", first_name="Thabiso"
        )
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_dashboard_renders_with_no_data(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Good")
        self.assertContains(response, "NIBS")

    def test_dashboard_renders_with_full_data(self):
        framework = Framework.objects.get(code="ISO27001")
        template = framework.journey_templates.get(goal_type="build_from_scratch")
        start_journey(self.org, template, self.user)
        adopt_framework(self.org, framework)
        Risk.objects.create(organisation=self.org, title="Phishing", likelihood=4, impact=5)
        Document.objects.create(organisation=self.org, title="Info Sec Policy", status="awaiting_approval")
        CorrectiveAction.objects.create(organisation=self.org, finding_description="Fix access reviews", status="open")

        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your Implementation Journey")
        # Risk Overview shows aggregate counts, not individual risk titles.
        self.assertContains(response, "1 High")
        self.assertContains(response, "Context of the Organisation")
        self.assertEqual(response.context["risk_overview"]["total"], 1)
        self.assertEqual(response.context["open_actions"]["total"], 1)

    def test_dashboard_redirects_without_organisation(self):
        User.objects.create_user(email="lonely@example.com", password="StrongPass123!")
        self.client.logout()
        self.client.login(email="lonely@example.com", password="StrongPass123!")
        response = self.client.get(reverse("core:dashboard"))
        self.assertRedirects(response, reverse("tenancy:organisation_list"))


class DashboardPerformanceTests(TestCase):
    """
    Locks in the N+1 fixes made during the production-readiness review
    (core/dashboard.py, frameworks/services.py::framework_progress,
    risks/models.py::Risk.get_matrix). Asserts the dashboard's query
    count does not grow with the number of adopted frameworks / pending
    approvals / risks — if it does, that's an N+1 regression even if
    every individual test still passes.
    """

    def setUp(self):
        call_command("seed_frameworks")
        self.org = Organisation.objects.create(name="NIBS")
        self.user = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.user, role="org_admin")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def _query_count_for_dashboard(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        return len(ctx.captured_queries)

    def test_query_count_does_not_grow_with_adopted_frameworks_or_risks(self):
        cache.clear()
        for framework in Framework.objects.all():
            adopt_framework(self.org, framework)
        for i in range(3):
            Risk.objects.create(organisation=self.org, title=f"Risk {i}", likelihood=3, impact=3)
        self._query_count_for_dashboard()  # warm-up: primes the risk-matrix cache
        small_count = self._query_count_for_dashboard()

        for i in range(3, 15):
            Risk.objects.create(organisation=self.org, title=f"Risk {i}", likelihood=3, impact=3)
        for i in range(5):
            doc = Document.objects.create(organisation=self.org, title=f"Policy {i}")
            from approvals.models import ApprovalRequest

            ApprovalRequest.objects.create(organisation=self.org, target=doc)
        large_count = self._query_count_for_dashboard()

        # Not strict equality: introducing pending approvals for the
        # first time costs one bounded, one-time ContentType lookup
        # (see _resolve_targets) — allow a small constant tolerance, but
        # 12 more risks and 5 more approvals must not multiply the query
        # count the way a true N+1 would (that would show up as +15/+20,
        # not +1/+2).
        self.assertLessEqual(
            large_count, small_count + 2,
            f"Dashboard query count grew from {small_count} to {large_count} as data volume "
            "grew — this indicates an N+1 query regression.",
        )


class DashboardTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        Risk.objects.create(organisation=self.org_b, title="Org B secret risk", likelihood=5, impact=5)
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_dashboard_never_shows_other_org_data(self):
        response = self.client.get(reverse("core:dashboard"))
        self.assertNotContains(response, "Org B secret risk")


class HealthCheckTests(TestCase):
    def test_health_check_confirms_db_connectivity_without_login(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class ReverseProxyHttpsTests(TestCase):
    """
    DEPLOYMENT.md's documented topology terminates TLS at Nginx and proxies
    to Gunicorn in plain HTTP over a Unix socket. Without SECURE_PROXY_SSL_HEADER,
    request.is_secure() is always False behind that proxy, which would make
    DJANGO_SECURE_SSL_REDIRECT=True redirect-loop forever once HTTPS is enabled
    (see config/settings.py and SECURITY_AUDIT.md).
    """

    def test_x_forwarded_proto_header_is_trusted_for_is_secure(self):
        self.assertEqual(settings.SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))
        request = RequestFactory().get("/", HTTP_X_FORWARDED_PROTO="https")
        self.assertTrue(request.is_secure())

    def test_without_the_header_request_is_not_treated_as_secure(self):
        request = RequestFactory().get("/")
        self.assertFalse(request.is_secure())


class RateLimitTests(TestCase):
    """Login brute-force protection (spec §45: "rate limiting where appropriate")."""

    def setUp(self):
        cache.clear()
        User.objects.create_user(email="a@example.com", password="StrongPass123!")

    def tearDown(self):
        cache.clear()

    def test_login_is_rate_limited_after_repeated_attempts(self):
        for _ in range(10):
            response = self.client.post(
                reverse("accounts:login"), {"username": "a@example.com", "password": "wrong"}
            )
            self.assertEqual(response.status_code, 200)
        blocked = self.client.post(
            reverse("accounts:login"), {"username": "a@example.com", "password": "wrong"}
        )
        self.assertEqual(blocked.status_code, 429)

    def test_successful_login_still_works_under_the_limit(self):
        response = self.client.post(
            reverse("accounts:login"), {"username": "a@example.com", "password": "StrongPass123!"}
        )
        self.assertEqual(response.status_code, 302)

    def test_page_reloads_do_not_count_against_the_login_limit(self):
        for _ in range(20):
            response = self.client.get(reverse("accounts:login"))
            self.assertEqual(response.status_code, 200)


class SeedNibsDemoTests(TestCase):
    """
    End-to-end integration coverage for the NIBS demonstration seed
    (spec §47): running this command exercises real service-layer code
    across nearly every app, so it doubles as a regression guard for
    the whole guided-implementation workflow.
    """

    def test_seed_command_runs_and_produces_expected_data(self):
        call_command("seed_nibs_demo")

        org = Organisation.objects.get(name__icontains="NIBS")
        self.assertTrue(org.is_demo)
        self.assertEqual(Membership.objects.filter(organisation=org).count(), 5)

        from journeys.models import OrganisationJourney

        journey = OrganisationJourney.objects.get(organisation=org)
        self.assertEqual(journey.progress_percent, 92)
        self.assertEqual(journey.current_step.title, "Check audit readiness")

        documents = Document.objects.filter(organisation=org)
        self.assertEqual(documents.count(), 2)
        self.assertTrue(all(d.status == "published" for d in documents))

        self.assertEqual(Risk.objects.filter(organisation=org).count(), 6)

        from actions.models import CorrectiveAction
        from audits.models import Audit
        from controls.models import Control
        from evidence.models import Evidence
        from reviews.models import ManagementReview

        self.assertEqual(Control.objects.filter(organisation=org).count(), 17)
        self.assertEqual(Evidence.objects.filter(organisation=org).count(), 4)
        self.assertTrue(Audit.objects.filter(organisation=org, status="closed").exists())
        self.assertTrue(ManagementReview.objects.filter(organisation=org, status="completed").exists())
        self.assertEqual(CorrectiveAction.objects.filter(organisation=org).count(), 2)

        from activity.models import AuditLog

        self.assertTrue(AuditLog.objects.filter(organisation=org).exists())

        iso27001 = Framework.objects.get(code="ISO27001")
        from frameworks.services import framework_progress

        self.assertGreaterEqual(framework_progress(org, iso27001), 90)

    def test_seed_command_is_idempotent(self):
        call_command("seed_nibs_demo")
        call_command("seed_nibs_demo")
        self.assertEqual(Organisation.objects.filter(name__icontains="NIBS").count(), 1)

    def test_demo_users_can_log_in_and_reach_dashboard(self):
        call_command("seed_nibs_demo")
        self.client.logout()
        logged_in = self.client.login(email="thabiso@bohlale-demo.example", password="NibsDemo2026!")
        self.assertTrue(logged_in)
        response = self.client.get(reverse("core:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Naleli Innovators Business School")
