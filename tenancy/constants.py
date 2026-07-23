"""
Role definitions for Bohlale GRC's role-based access control (RBAC).

Roles are held per-Membership (a user can have different roles in
different organisations) — see tenancy.models.Membership. The one
exception is Platform Administrator, which is modelled as Django's
`is_superuser`/`is_staff` since it is not scoped to any one tenant.
"""

CONSULTANT = "consultant"
ORG_ADMIN = "org_admin"
EXECUTIVE = "executive"
COMPLIANCE_MANAGER = "compliance_manager"
ISMS_MANAGER = "isms_manager"
CONTROL_OWNER = "control_owner"
RISK_OWNER = "risk_owner"
DOCUMENT_OWNER = "document_owner"
INTERNAL_AUDITOR = "internal_auditor"
CONTRIBUTOR = "contributor"
EXTERNAL_REVIEWER = "external_reviewer"
READ_ONLY = "read_only"

ROLE_CHOICES = [
    (CONSULTANT, "Consultant"),
    (ORG_ADMIN, "Organisation Administrator"),
    (EXECUTIVE, "Executive / Approver"),
    (COMPLIANCE_MANAGER, "Compliance Manager"),
    (ISMS_MANAGER, "ISMS Manager"),
    (CONTROL_OWNER, "Control Owner"),
    (RISK_OWNER, "Risk Owner"),
    (DOCUMENT_OWNER, "Document Owner"),
    (INTERNAL_AUDITOR, "Internal Auditor"),
    (CONTRIBUTOR, "Contributor"),
    (EXTERNAL_REVIEWER, "External Reviewer"),
    (READ_ONLY, "Read-Only User"),
]

# Roles that can administer the organisation (users, settings, all records).
ADMIN_ROLES = {CONSULTANT, ORG_ADMIN}

# Roles that can approve/sign documents, sign off risk treatments, etc.
APPROVER_ROLES = {CONSULTANT, ORG_ADMIN, EXECUTIVE}

# Roles that can create/edit day-to-day records (documents, risks, controls...).
EDITOR_ROLES = {
    CONSULTANT,
    ORG_ADMIN,
    EXECUTIVE,
    COMPLIANCE_MANAGER,
    ISMS_MANAGER,
    CONTROL_OWNER,
    RISK_OWNER,
    DOCUMENT_OWNER,
    INTERNAL_AUDITOR,
    CONTRIBUTOR,
}

# Roles that can only view, not edit.
VIEW_ONLY_ROLES = {EXTERNAL_REVIEWER, READ_ONLY}

ORGANISATION_TYPE_CHOICES = [
    ("sme", "Small / Medium Enterprise"),
    ("npo", "Non-Profit Organisation"),
    ("ngo", "Non-Governmental Organisation"),
    ("sdp", "Skills Development Provider"),
    ("public_sector", "Public Sector Entity"),
    ("consultancy", "Consultancy / Practitioner"),
    ("other", "Other"),
]
