from .models import RegisterType

DEFAULT_REGISTER_TYPES = [
    {
        "slug": "interested-parties",
        "name": "Interested Parties Register",
        "description": "Parties relevant to the management system and their needs/expectations.",
        "icon": "org",
        "field_schema": [
            {"name": "party", "label": "Interested Party", "type": "text", "required": True},
            {"name": "category", "label": "Category", "type": "select",
             "choices": ["Internal", "External", "Regulatory", "Customer", "Supplier"]},
            {"name": "expectation", "label": "Needs & Expectations", "type": "textarea"},
        ],
    },
    {
        "slug": "legal-regulatory",
        "name": "Legal & Regulatory Register",
        "description": "Legal, statutory, regulatory and contractual obligations the organisation must meet.",
        "icon": "framework",
        "field_schema": [
            {"name": "obligation", "label": "Obligation", "type": "text", "required": True},
            {"name": "source", "label": "Source", "type": "text"},
            {"name": "applicability", "label": "Applicability", "type": "textarea"},
            {"name": "compliance_status", "label": "Compliance Status", "type": "select",
             "choices": ["Compliant", "Partially Compliant", "Non-Compliant", "Under Review"]},
        ],
    },
    {
        "slug": "processing-activities",
        "name": "Processing Activities Register",
        "description": "Personal information processing activities (POPIA record of processing).",
        "icon": "shield-check",
        "field_schema": [
            {"name": "activity", "label": "Processing Activity", "type": "text", "required": True},
            {"name": "purpose", "label": "Purpose", "type": "textarea"},
            {"name": "personal_info_categories", "label": "Personal Information Categories", "type": "textarea"},
            {"name": "legal_basis", "label": "Legal Basis", "type": "text"},
            {"name": "retention", "label": "Retention Period", "type": "text"},
        ],
    },
    {
        "slug": "training",
        "name": "Training Register",
        "description": "Security and compliance training/awareness records.",
        "icon": "user",
        "field_schema": [
            {"name": "topic", "label": "Training Topic", "type": "text", "required": True},
            {"name": "audience", "label": "Audience", "type": "text"},
            {"name": "date_completed", "label": "Date Completed", "type": "date"},
            {"name": "status", "label": "Status", "type": "select", "choices": ["Planned", "Completed", "Overdue"]},
        ],
    },
]


def ensure_default_register_types():
    for spec in DEFAULT_REGISTER_TYPES:
        RegisterType.objects.update_or_create(
            slug=spec["slug"],
            defaults={
                "name": spec["name"], "description": spec["description"],
                "icon": spec["icon"], "field_schema": spec["field_schema"],
            },
        )


def register_hub_summary(organisation):
    """Counts across every register — dedicated apps plus the generic
    engine — for the Compliance/Registers hub page."""
    from actions.models import CorrectiveAction
    from assets.models import Asset
    from audits.models import AuditFinding
    from incidents.models import Incident
    from risks.models import Risk
    from suppliers.models import Supplier

    ensure_default_register_types()

    dedicated = [
        {"name": "Risk Register", "count": Risk.objects.filter(organisation=organisation).count(), "url": "risks:list", "icon": "risk"},
        {"name": "Asset Register", "count": Asset.objects.filter(organisation=organisation).count(), "url": "assets:list", "icon": "asset"},
        {"name": "Supplier Register", "count": Supplier.objects.filter(organisation=organisation).count(), "url": "suppliers:list", "icon": "supplier"},
        {"name": "Incident Register", "count": Incident.objects.filter(organisation=organisation).count(), "url": "incidents:list", "icon": "incident"},
        {"name": "Data Breach Register", "count": Incident.objects.filter(organisation=organisation, personal_info_involved=True).count(), "url": "incidents:list", "icon": "incident"},
        {"name": "Corrective Action Register", "count": CorrectiveAction.objects.filter(organisation=organisation).count(), "url": "actions:list", "icon": "action"},
        {"name": "Audit Findings Register", "count": AuditFinding.objects.filter(organisation=organisation).count(), "url": "audits:list", "icon": "audit"},
    ]

    generic = []
    for register_type in RegisterType.objects.all():
        generic.append({
            "name": register_type.name,
            "count": register_type.entries.filter(organisation=organisation).count(),
            "url": ("registers:generic_list", register_type.slug),
            "icon": register_type.icon,
        })

    return {"dedicated": dedicated, "generic": generic}
