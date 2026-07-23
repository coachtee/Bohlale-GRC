"""
Seeds the platform-global, built-in frameworks (organisation=None):
ISO/IEC 27001 (ISMS implementation structure), POPIA, King IV and
SABS ISO 9001.

IMPORTANT — copyright: this command writes only original, descriptive
guidance text authored for Bohlale GRC. It does NOT reproduce the
verbatim clause text of any copyrighted standard. Clause/domain
*titles* mirror the well-known public structure of these frameworks
(short factual headings, standard industry terminology), which is how
every compliance tool refers to them, but the descriptions and
guidance are original writing, not copied text. POPIA is South African
legislation; its condition names are a matter of public record, and
the guidance here is an original plain-language summary, not a
verbatim reproduction of the Act — and is not legal advice.
See BUILD_STATUS.md assumption #5.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from frameworks.models import AssessmentQuestion, Domain, EvidenceExpectation, Framework, Requirement

ISO27001 = {
    "code": "ISO27001",
    "name": "ISO/IEC 27001 — Information Security Management",
    "version": "2022 structure",
    "description": (
        "A structural implementation skeleton for an Information Security Management "
        "System (ISMS), organised using the same Plan-Do-Check-Act clause grouping as "
        "the internationally recognised standard. Original guidance content only — "
        "does not reproduce the standard's copyrighted text. Consult the official "
        "published standard for the authoritative requirement wording."
    ),
    "domains": [
        {
            "code": "1", "title": "Context of the Organisation",
            "requirements": [
                ("4.1", "Understanding the organisation and its context",
                 "Identify internal and external issues relevant to your organisation's purpose that affect its ability to achieve the intended outcome(s) of the ISMS."),
                ("4.2", "Understanding the needs and expectations of interested parties",
                 "Identify the parties relevant to information security (regulators, customers, employees, suppliers) and their relevant requirements."),
                ("4.3", "Determining the scope of the ISMS",
                 "Define and document the boundaries and applicability of the ISMS, considering the issues, interested party requirements, and interfaces/dependencies with other organisations."),
                ("4.4", "Information security management system",
                 "Establish, implement, maintain and continually improve the ISMS, including its processes and their interactions."),
            ],
        },
        {
            "code": "2", "title": "Leadership",
            "requirements": [
                ("5.1", "Leadership and commitment",
                 "Top management demonstrates leadership and commitment to the ISMS by ensuring policy and objectives are established and resources are available."),
                ("5.2", "Policy",
                 "Establish an information security policy appropriate to the organisation's purpose, with objectives and a commitment to continual improvement."),
                ("5.3", "Organisational roles, responsibilities and authorities",
                 "Assign and communicate responsibilities and authorities for roles relevant to information security."),
            ],
        },
        {
            "code": "3", "title": "Planning",
            "requirements": [
                ("6.1", "Actions to address risks and opportunities",
                 "Plan a repeatable information security risk assessment and risk treatment process, and determine controls necessary to implement the treatment plan."),
                ("6.2", "Information security objectives and planning to achieve them",
                 "Establish measurable information security objectives at relevant functions and levels, with plans to achieve them."),
            ],
        },
        {
            "code": "4", "title": "Support",
            "requirements": [
                ("7.1", "Resources", "Determine and provide the resources needed for the ISMS."),
                ("7.2", "Competence", "Ensure people doing work affecting information security performance are competent."),
                ("7.3", "Awareness", "Ensure staff are aware of the information security policy and their contribution to it."),
                ("7.4", "Communication", "Determine internal and external communications relevant to the ISMS."),
                ("7.5", "Documented information", "Maintain documented information required by the ISMS in a controlled manner."),
            ],
        },
        {
            "code": "5", "title": "Operation",
            "requirements": [
                ("8.1", "Operational planning and control", "Plan, implement and control the processes needed to meet information security requirements."),
                ("8.2", "Information security risk assessment", "Perform information security risk assessments at planned intervals or on significant change."),
                ("8.3", "Information security risk treatment", "Implement the risk treatment plan and retain documented evidence of the results."),
            ],
        },
        {
            "code": "6", "title": "Performance Evaluation",
            "requirements": [
                ("9.1", "Monitoring, measurement, analysis and evaluation", "Determine what needs monitoring/measuring, methods, timing and who analyses results."),
                ("9.2", "Internal audit", "Conduct internal audits at planned intervals to check the ISMS conforms to requirements and is effectively implemented."),
                ("9.3", "Management review", "Top management reviews the ISMS at planned intervals to ensure continuing suitability, adequacy and effectiveness."),
            ],
        },
        {
            "code": "7", "title": "Improvement",
            "requirements": [
                ("10.1", "Continual improvement", "Continually improve the suitability, adequacy and effectiveness of the ISMS."),
                ("10.2", "Nonconformity and corrective action", "React to nonconformities, evaluate the need for corrective action, and implement it."),
            ],
        },
    ],
}

POPIA = {
    "code": "POPIA",
    "name": "Protection of Personal Information Act (POPIA)",
    "version": "8 Conditions for Lawful Processing",
    "description": (
        "An original, plain-language compliance structure covering South Africa's "
        "Protection of Personal Information Act, organised around its eight publicly "
        "known conditions for lawful processing. This is compliance guidance, not "
        "legal advice — consult a qualified professional or the Information Regulator "
        "for authoritative interpretation."
    ),
    "domains": [
        {"code": "1", "title": "Accountability", "requirements": [
            ("POPIA-1", "Accountability for processing", "Determine who is responsible for ensuring personal information processing complies with POPIA (typically the Information Officer).")]},
        {"code": "2", "title": "Processing Limitation", "requirements": [
            ("POPIA-2", "Lawful and minimal processing", "Process personal information lawfully, and only to the minimum extent needed for the stated purpose, with the data subject's consent or another lawful basis.")]},
        {"code": "3", "title": "Purpose Specification", "requirements": [
            ("POPIA-3", "Collect for a specific, defined purpose", "Collect personal information for a specific, explicitly defined and lawful purpose related to a function of the organisation.")]},
        {"code": "4", "title": "Further Processing Limitation", "requirements": [
            ("POPIA-4", "Compatible further processing", "Ensure any further processing of personal information is compatible with the original purpose of collection.")]},
        {"code": "5", "title": "Information Quality", "requirements": [
            ("POPIA-5", "Keep information accurate and up to date", "Take reasonably practicable steps to ensure personal information is complete, accurate and not misleading.")]},
        {"code": "6", "title": "Openness", "requirements": [
            ("POPIA-6", "Notify data subjects of collection", "Maintain documentation of processing operations and notify data subjects of what is collected and why.")]},
        {"code": "7", "title": "Security Safeguards", "requirements": [
            ("POPIA-7", "Secure personal information appropriately", "Implement appropriate, reasonable technical and organisational measures to prevent loss, damage or unauthorised access, and have a data breach response process."),
        ]},
        {"code": "8", "title": "Data Subject Participation", "requirements": [
            ("POPIA-8", "Enable data subject rights", "Enable data subjects to establish what personal information is held about them and to request correction or deletion where appropriate.")]},
    ],
}

KING_IV = {
    "code": "KING_IV",
    "name": "King IV — Corporate Governance",
    "version": "Outcomes-based summary",
    "description": (
        "An original, high-level governance structure summarising the outcomes-based "
        "approach associated with South African corporate governance good practice. "
        "Not a reproduction of the King IV Report; use for internal governance "
        "self-assessment only."
    ),
    "domains": [
        {"code": "1", "title": "Ethical Culture", "requirements": [
            ("KING-1", "Leadership sets an ethical tone", "The governing body should lead ethically and effectively, setting the tone for the organisation's culture.")]},
        {"code": "2", "title": "Good Performance", "requirements": [
            ("KING-2", "Strategy, performance and value creation are governed", "Governance structures should direct strategy and monitor performance against agreed objectives.")]},
        {"code": "3", "title": "Effective Control", "requirements": [
            ("KING-3", "Risk and technology governance", "The organisation should govern risk, and information and technology, in a way that supports strategy and objectives.")]},
        {"code": "4", "title": "Legitimacy", "requirements": [
            ("KING-4", "Stakeholder-inclusive governance", "The organisation should be a responsible corporate citizen and engage with stakeholders in a mutually beneficial way.")]},
    ],
}

ISO9001 = {
    "code": "ISO9001",
    "name": "SABS ISO 9001 — Quality Management",
    "version": "Structure summary",
    "description": (
        "A structural implementation skeleton for a Quality Management System (QMS), "
        "organised using the same high-level clause grouping as the internationally "
        "recognised standard. Original guidance content only — consult the official "
        "published standard for authoritative requirement wording."
    ),
    "domains": [
        {"code": "1", "title": "Context of the Organisation", "requirements": [
            ("QMS-4", "Understand context and interested parties", "Determine internal/external issues and interested party requirements relevant to the QMS.")]},
        {"code": "2", "title": "Leadership", "requirements": [
            ("QMS-5", "Leadership and quality policy", "Top management demonstrates leadership and establishes a quality policy and objectives.")]},
        {"code": "3", "title": "Planning", "requirements": [
            ("QMS-6", "Actions to address risks and opportunities", "Plan actions to address risks/opportunities and quality objectives.")]},
        {"code": "4", "title": "Support", "requirements": [
            ("QMS-7", "Resources, competence and documented information", "Provide resources, ensure competence, and maintain documented information for the QMS.")]},
        {"code": "5", "title": "Operation", "requirements": [
            ("QMS-8", "Operational planning and control", "Plan and control the processes needed to meet requirements for the provision of products and services.")]},
        {"code": "6", "title": "Performance Evaluation", "requirements": [
            ("QMS-9", "Monitoring, internal audit and management review", "Monitor, measure, audit and review the QMS at planned intervals.")]},
        {"code": "7", "title": "Improvement", "requirements": [
            ("QMS-10", "Nonconformity and continual improvement", "Address nonconformities and continually improve the suitability and effectiveness of the QMS.")]},
    ],
}

ALL_FRAMEWORKS = [ISO27001, POPIA, KING_IV, ISO9001]


class Command(BaseCommand):
    help = "Seed platform-global built-in frameworks (ISO 27001, POPIA, King IV, ISO 9001)."

    @transaction.atomic
    def handle(self, *args, **options):
        for spec in ALL_FRAMEWORKS:
            framework, created = Framework.objects.update_or_create(
                organisation=None,
                code=spec["code"],
                defaults={
                    "name": spec["name"],
                    "version": spec["version"],
                    "description": spec["description"],
                    "source_type": "built_in",
                    "is_published": True,
                },
            )
            for d_order, domain_spec in enumerate(spec["domains"], start=1):
                domain, _ = Domain.objects.update_or_create(
                    framework=framework,
                    code=domain_spec["code"],
                    defaults={"title": domain_spec["title"], "order": d_order},
                )
                for r_order, (ref_code, title, guidance) in enumerate(domain_spec["requirements"], start=1):
                    requirement, _ = Requirement.objects.update_or_create(
                        framework=framework,
                        ref_code=ref_code,
                        defaults={
                            "domain": domain,
                            "title": title,
                            "guidance": guidance,
                            "order": r_order,
                        },
                    )
                    AssessmentQuestion.objects.get_or_create(
                        requirement=requirement,
                        text=f"Has the organisation addressed: {title}?",
                        defaults={"order": 1},
                    )
                    EvidenceExpectation.objects.get_or_create(
                        requirement=requirement,
                        description=f"Documented evidence demonstrating '{title}' is in place",
                        defaults={"is_required": True},
                    )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} framework: {framework.name}"))

        self.stdout.write(self.style.SUCCESS("Framework seeding complete."))
