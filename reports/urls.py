from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.hub, name="hub"),
    path("executive-summary/", views.executive_summary_report, name="executive_summary"),
    path("readiness/", views.readiness_report, name="readiness"),
    path("gap-assessment/", views.gap_assessment_report, name="gap_assessment"),
    path("risk-register/", views.risk_register_report, name="risk_register"),
    path("risk-treatment-plan/", views.risk_treatment_plan_report, name="risk_treatment_plan"),
    path("policy-register/", views.policy_register_report, name="policy_register"),
    path("incident-register/", views.incident_register_report, name="incident_register"),
    path("corrective-actions/", views.corrective_action_report, name="corrective_action_report"),
    path("framework-compliance/", views.framework_compliance_report, name="framework_compliance"),
    path("audits/", views.audit_report_list, name="audit_report_list"),
    path("audits/<uuid:pk>/", views.audit_report_detail, name="audit_report_detail"),
]
