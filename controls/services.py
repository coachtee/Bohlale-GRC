from frameworks.models import Framework, Requirement

from .models import Control, SoAEntry

# Common Control Library baseline (spec §19): original, generic control
# category names — not copied from any specific standard's control
# text — each mapped to one or more adopted frameworks' requirements so
# a single control can demonstrably satisfy multiple obligations at
# once. See BUILD_STATUS.md.
COMMON_CONTROLS = [
    ("Access Control", "Restrict access to information and systems based on business need and least privilege.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7")]),
    ("Asset Management", "Maintain an inventory of information assets and assign clear ownership.",
     [("ISO27001", "8.3")]),
    ("Cryptographic Controls", "Use encryption to protect the confidentiality and integrity of sensitive information.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7")]),
    ("Physical & Environmental Security", "Protect premises and equipment from unauthorised physical access and environmental threats.",
     [("ISO27001", "8.3")]),
    ("Operations Security", "Ensure correct and secure operation of information processing facilities.",
     [("ISO27001", "8.3")]),
    ("Communications Security", "Protect information in networks and during transmission.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7")]),
    ("Supplier Relationships", "Manage information security risks associated with suppliers and third parties.",
     [("ISO27001", "8.3")]),
    ("Incident Management", "Ensure a consistent approach to detecting, reporting and managing security incidents.",
     [("ISO27001", "8.3")]),
    ("Business Continuity", "Plan for the continuity of information security during a disruption.",
     [("ISO27001", "8.3")]),
    ("Compliance", "Avoid breaches of legal, statutory, regulatory or contractual obligations.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-1")]),
    ("HR Security", "Ensure employees understand and act on their information security responsibilities.",
     [("ISO27001", "8.3")]),
    ("Change Management", "Control changes to systems and processes that could affect security.",
     [("ISO27001", "8.3")]),
    ("Backup", "Maintain and test backup copies of information and systems.",
     [("ISO27001", "8.3")]),
    ("Logging & Monitoring", "Record events and monitor systems to detect anomalies and support investigations.",
     [("ISO27001", "8.3")]),
    ("Vulnerability Management", "Identify and remediate technical vulnerabilities in a timely manner.",
     [("ISO27001", "8.3")]),
    ("Network Security", "Protect information in networks from unauthorised access and disclosure.",
     [("ISO27001", "8.3")]),
    ("Data Protection & Privacy", "Protect personal information in line with applicable data protection law.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7")]),
]


def ensure_baseline_controls(organisation):
    """Seeds the common control library baseline for an organisation
    the first time it's needed (idempotent)."""
    if Control.objects.filter(organisation=organisation).exists():
        return
    for name, description, mappings in COMMON_CONTROLS:
        control = Control.objects.create(organisation=organisation, name=name, description=description)
        for framework_code, ref_code in mappings:
            requirement = Requirement.objects.filter(
                framework__code=framework_code, framework__organisation__isnull=True, ref_code=ref_code
            ).first()
            if requirement:
                control.framework_requirements.add(requirement)


def ensure_soa_entries(organisation, framework):
    """Ensures every control the org has is represented on the SoA for
    the given framework (defaulting to applicable=True)."""
    ensure_baseline_controls(organisation)
    existing_control_ids = set(
        SoAEntry.objects.filter(organisation=organisation, framework=framework).values_list("control_id", flat=True)
    )
    for control in Control.objects.filter(organisation=organisation):
        if control.id not in existing_control_ids:
            SoAEntry.objects.create(organisation=organisation, framework=framework, control=control)


def soa_coverage(organisation, framework):
    entries = SoAEntry.objects.filter(organisation=organisation, framework=framework)
    applicable = entries.filter(applicable=True)
    total = applicable.count()
    if total == 0:
        return 0
    implemented = applicable.filter(control__implementation_status="implemented").count()
    return round((implemented / total) * 100)
