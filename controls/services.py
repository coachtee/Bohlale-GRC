from frameworks.models import Framework, Requirement

from .models import Control, SoAEntry

# Common Control Library baseline (spec §19): original, generic control
# category names — not copied from any specific standard's control
# text — each mapped to requirements across as many adopted frameworks
# as it genuinely satisfies, so a single control can demonstrably
# satisfy multiple obligations at once (e.g. one "Access Control"
# control mapping to ISO 27001, POPIA, ISO 27701 and CIS Controls v8
# simultaneously). See BUILD_STATUS.md and frameworks/management/
# commands/seed_frameworks.py for the framework codes/ref codes used
# below.
COMMON_CONTROLS = [
    ("Access Control", "Restrict access to information and systems based on business need and least privilege.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7"), ("ISO27701", "PIMS-6"), ("NIST_CSF", "NIST-PR"), ("CIS_V8", "CIS-06")]),
    ("Asset Management", "Maintain an inventory of information assets and assign clear ownership.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-01"), ("CIS_V8", "CIS-02")]),
    ("Cryptographic Controls", "Use encryption to protect the confidentiality and integrity of sensitive information.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7"), ("ISO27701", "PIMS-6"), ("CIS_V8", "CIS-03")]),
    ("Physical & Environmental Security", "Protect premises and equipment from unauthorised physical access and environmental threats.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-01")]),
    ("Operations Security", "Ensure correct and secure operation of information processing facilities.",
     [("ISO27001", "8.3"), ("ISO9001", "QMS-8")]),
    ("Communications Security", "Protect information in networks and during transmission.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7"), ("CIS_V8", "CIS-12"), ("CIS_V8", "CIS-13")]),
    ("Supplier Relationships", "Manage information security risks associated with suppliers and third parties.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-15"), ("ISO27701", "PIMS-6")]),
    ("Incident Management", "Ensure a consistent approach to detecting, reporting and managing security incidents.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-17"), ("NIST_CSF", "NIST-RS")]),
    ("Business Continuity", "Plan for the continuity of information security during a disruption.",
     [("ISO27001", "8.3"), ("ISO22301", "BCMS-8.3"), ("ISO22301", "BCMS-8.4"), ("NIST_CSF", "NIST-RC")]),
    ("Compliance", "Avoid breaches of legal, statutory, regulatory or contractual obligations.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-1"), ("PAIA", "PAIA-1"), ("KING_IV", "KING-3"), ("NIST_CSF", "NIST-GV")]),
    ("HR Security", "Ensure employees understand and act on their information security responsibilities.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-14")]),
    ("Change Management", "Control changes to systems and processes that could affect security.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-04")]),
    ("Backup", "Maintain and test backup copies of information and systems.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-11"), ("ISO22301", "BCMS-8.3")]),
    ("Logging & Monitoring", "Record events and monitor systems to detect anomalies and support investigations.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-08"), ("CIS_V8", "CIS-13"), ("NIST_CSF", "NIST-DE")]),
    ("Vulnerability Management", "Identify and remediate technical vulnerabilities in a timely manner.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-07"), ("NIST_CSF", "NIST-ID")]),
    ("Network Security", "Protect information in networks from unauthorised access and disclosure.",
     [("ISO27001", "8.3"), ("CIS_V8", "CIS-12"), ("CIS_V8", "CIS-09")]),
    ("Data Protection & Privacy", "Protect personal information in line with applicable data protection law.",
     [("ISO27001", "8.3"), ("POPIA", "POPIA-7"), ("ISO27701", "PIMS-3"), ("ISO27701", "PIMS-5"), ("CIS_V8", "CIS-03")]),
    ("Risk Management", "Identify, assess and treat risks to the organisation's objectives on an ongoing basis.",
     [("ISO27001", "6.1"), ("ISO31000", "RISK-PR2"), ("ISO31000", "RISK-PR3"), ("KING_IV", "KING-3")]),
    ("Records & Information Governance", "Maintain accurate, controlled records and a documented process for handling access requests.",
     [("PAIA", "PAIA-1"), ("PAIA", "PAIA-3"), ("ISO9001", "QMS-7"), ("ISO27001", "7.5")]),
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


def related_frameworks_via_controls(organisation, framework):
    """
    Other frameworks that share at least one of this org's controls
    with `framework` — the concrete, queryable expression of
    cross-framework control mapping (e.g. ISO 27001 <-> POPIA <-> PAIA
    sharing a "Data Protection & Privacy" control), derived live from
    Control.framework_requirements rather than a separate mapping table.
    Returns a list of (Framework, shared_control_count) tuples, most
    controls shared first.
    """
    controls = Control.objects.filter(
        organisation=organisation, framework_requirements__framework=framework
    ).distinct().prefetch_related("framework_requirements__framework")

    counts = {}
    for control in controls:
        other_frameworks = {
            req.framework for req in control.framework_requirements.all() if req.framework_id != framework.id
        }
        for other in other_frameworks:
            counts[other] = counts.get(other, 0) + 1

    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0].name))
