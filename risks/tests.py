from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tenancy.models import Membership, Organisation

from .models import Risk, RiskMatrixConfig
from .services import risk_overview


class RiskModelTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_inherent_score_computed_on_save(self):
        risk = Risk.objects.create(organisation=self.org, title="Phishing", likelihood=4, impact=5)
        self.assertEqual(risk.inherent_risk_score, 20)

    def test_reference_code_sequential(self):
        r1 = Risk.objects.create(organisation=self.org, title="A", likelihood=1, impact=1)
        r2 = Risk.objects.create(organisation=self.org, title="B", likelihood=1, impact=1)
        self.assertEqual(r1.reference_code, "RISK-0001")
        self.assertEqual(r2.reference_code, "RISK-0002")

    def test_residual_score_none_until_both_set(self):
        risk = Risk.objects.create(organisation=self.org, title="A", likelihood=4, impact=4, residual_likelihood=2)
        self.assertIsNone(risk.residual_risk_score)
        risk.residual_impact = 2
        risk.save()
        self.assertEqual(risk.residual_risk_score, 4)

    def test_default_matrix_bands(self):
        matrix = RiskMatrixConfig.objects.create(organisation=self.org)
        self.assertEqual(matrix.band_for_score(2)[0], "very_low")
        self.assertEqual(matrix.band_for_score(8)[0], "low")
        self.assertEqual(matrix.band_for_score(12)[0], "medium")
        self.assertEqual(matrix.band_for_score(20)[0], "high")


class RiskOverviewServiceTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")

    def test_overview_counts_by_band(self):
        Risk.objects.create(organisation=self.org, title="High1", likelihood=5, impact=5)  # 25 -> high
        Risk.objects.create(organisation=self.org, title="Low1", likelihood=3, impact=2)  # 6 -> low
        Risk.objects.create(organisation=self.org, title="Closed", likelihood=5, impact=5, status="closed")
        overview = risk_overview(self.org)
        self.assertEqual(overview["counts"]["high"], 1)
        self.assertEqual(overview["counts"]["low"], 1)
        self.assertEqual(overview["total"], 2)  # closed risk excluded


class RiskViewTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="org_admin")
        self.risk_b = Risk.objects.create(organisation=self.org_b, title="Org B secret risk", likelihood=3, impact=3)
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_list_excludes_other_org(self):
        Risk.objects.create(organisation=self.org_a, title="Org A risk", likelihood=3, impact=3)
        response = self.client.get(reverse("risks:list"))
        self.assertContains(response, "Org A risk")
        self.assertNotContains(response, "Org B secret risk")

    def test_detail_404s_for_other_org(self):
        response = self.client.get(reverse("risks:detail", args=[self.risk_b.pk]))
        self.assertEqual(response.status_code, 404)


class RiskCrudPermissionTests(TestCase):
    def setUp(self):
        self.org = Organisation.objects.create(name="NIBS")
        self.editor = User.objects.create_user(email="e@example.com", password="StrongPass123!")
        self.readonly = User.objects.create_user(email="r@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org, user=self.editor, role="risk_owner")
        Membership.objects.create(organisation=self.org, user=self.readonly, role="read_only")

    def test_editor_can_create_risk(self):
        self.client.login(email="e@example.com", password="StrongPass123!")
        response = self.client.post(
            reverse("risks:create"),
            {"title": "New risk", "category": "operational", "likelihood": 3, "impact": 3, "treatment": "mitigate", "status": "open"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Risk.objects.filter(title="New risk").exists())

    def test_read_only_cannot_create_risk(self):
        self.client.login(email="r@example.com", password="StrongPass123!")
        response = self.client.get(reverse("risks:create"))
        self.assertEqual(response.status_code, 403)


class RiskFormIDORTests(TestCase):
    """A risk must not be linkable to another organisation's private
    custom-framework requirements just by posting that requirement's pk
    (spec §5: tenant isolation)."""

    def setUp(self):
        from frameworks.models import Framework, Requirement

        self.org_a = Organisation.objects.create(name="Org A")
        self.org_b = Organisation.objects.create(name="Org B")
        self.user_a = User.objects.create_user(email="a@example.com", password="StrongPass123!")
        Membership.objects.create(organisation=self.org_a, user=self.user_a, role="risk_owner")
        framework_b = Framework.objects.create(name="Org B Private Framework", code="ORGB", organisation=self.org_b)
        self.requirement_b = Requirement.objects.create(framework=framework_b, title="Org B secret requirement")
        self.client.login(email="a@example.com", password="StrongPass123!")

    def test_form_queryset_excludes_other_orgs_private_requirement(self):
        from .forms import RiskForm

        form = RiskForm(organisation=self.org_a)
        self.assertNotIn(self.requirement_b, form.fields["related_requirements"].queryset)

    def test_cannot_attach_other_orgs_private_requirement_via_post(self):
        self.client.post(
            reverse("risks:create"),
            {
                "title": "New risk", "category": "operational", "likelihood": 3, "impact": 3,
                "treatment": "mitigate", "status": "open", "related_requirements": [str(self.requirement_b.pk)],
            },
        )
        risk = Risk.objects.filter(title="New risk").first()
        # The form rejects the cross-tenant requirement pk as an invalid
        # choice, so the risk either isn't created at all, or is created
        # without the other org's requirement attached — never with it.
        if risk is not None:
            self.assertNotIn(self.requirement_b, risk.related_requirements.all())
