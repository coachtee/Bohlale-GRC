"""
Seeds the Framework Library: platform-global, built-in frameworks
(organisation=None) plus the FrameworkCategory sections that group them
in the UI, with "South African Compliance" pinned first (spec: SA-first
positioning).

IMPORTANT — copyright: this command writes only original, descriptive
guidance text authored for Bohlale GRC. It does NOT reproduce the
verbatim clause/control text of any copyrighted standard. Clause/domain
*titles* mirror the well-known public structure of these frameworks
(short factual headings, standard industry terminology — e.g. "Access
Control", "Leadership", the six NIST CSF Function names, the 18 CIS
Control names), which is how every compliance tool refers to them, but
the descriptions and guidance are original writing, not copied text.
POPIA and PAIA are South African legislation; their condition/structure
names are a matter of public record, and the guidance here is an
original plain-language summary, not a verbatim reproduction of either
Act — and is not legal advice. See BUILD_STATUS.md assumption #5.

Run automatically during deployment (see entrypoint.sh / DEPLOYMENT.md)
so a fresh install's Framework Library is never empty. Idempotent —
update_or_create throughout, safe to re-run at any time (e.g. after
editing the guidance text below).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from frameworks.models import (
    AssessmentQuestion,
    Domain,
    EvidenceExpectation,
    Framework,
    FrameworkCategory,
    Requirement,
)

# ---------------------------------------------------------------- Categories

CATEGORIES = [
    # (slug, name, description, order)
    (
        "south-african-compliance",
        "South African Compliance",
        "Local legal and governance obligations for organisations operating in South Africa — the default, first-class section of the library.",
        0,
    ),
    (
        "international-management-systems",
        "International Management Systems",
        "Globally recognised ISO management-system structures for security, privacy, continuity, quality and risk.",
        10,
    ),
    (
        "cybersecurity-frameworks",
        "Cybersecurity Frameworks",
        "Widely adopted cybersecurity control and maturity frameworks.",
        20,
    ),
]

# ---------------------------------------------------------------- Frameworks

ISO27001 = {
    "code": "ISO27001",
    "name": "ISO/IEC 27001 — Information Security Management",
    "version": "2022",
    "category": "international-management-systems",
    "icon": "shield-check",
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

ISO27701 = {
    "code": "ISO27701",
    "name": "ISO/IEC 27701 — Privacy Information Management",
    "version": "2019",
    "category": "international-management-systems",
    "icon": "eye",
    "description": (
        "A structural skeleton for a Privacy Information Management System (PIMS) — "
        "the privacy extension to an ISMS, for organisations acting as PII controllers "
        "and/or processors. Original guidance content only; consult the official "
        "published standard for authoritative requirement wording."
    ),
    "domains": [
        {"code": "1", "title": "PIMS Context & Roles", "requirements": [
            ("PIMS-1", "Determine controller/processor role",
             "Determine, and document, whether the organisation acts as a PII controller, a PII processor, or both, for each processing activity — obligations differ by role.")]},
        {"code": "2", "title": "Leadership & Planning for Privacy", "requirements": [
            ("PIMS-2", "Integrate privacy objectives into the management system",
             "Extend the ISMS's leadership commitment, policy and risk-planning processes to explicitly cover privacy objectives and PII-specific risk.")]},
        {"code": "3", "title": "Conditions for Collection & Processing", "requirements": [
            ("PIMS-3", "Establish and document a lawful basis",
             "Identify and record the lawful basis and purpose for each PII processing activity before collection begins.")]},
        {"code": "4", "title": "Privacy by Design & Default", "requirements": [
            ("PIMS-4", "Embed privacy into systems and processes from the outset",
             "Consider privacy risk and data minimisation at the design stage of new systems, products and processes, not as an afterthought.")]},
        {"code": "5", "title": "Obligations to PII Principals", "requirements": [
            ("PIMS-5", "Enable PII principal rights",
             "Provide PII principals (data subjects) with clear information about processing and a practical way to exercise access, correction and deletion rights.")]},
        {"code": "6", "title": "PII Sharing, Transfer & Third Parties", "requirements": [
            ("PIMS-6", "Control disclosure and transfer of PII",
             "Ensure any sharing, cross-border transfer or processor engagement involving PII is governed by an appropriate agreement and safeguards.")]},
    ],
}

POPIA = {
    "code": "POPIA",
    "name": "Protection of Personal Information Act (POPIA)",
    "version": "8 Conditions for Lawful Processing",
    "category": "south-african-compliance",
    "icon": "eye",
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

PAIA = {
    "code": "PAIA",
    "name": "Promotion of Access to Information Act (PAIA)",
    "version": "Manual & Access Request Structure",
    "category": "south-african-compliance",
    "icon": "document",
    "description": (
        "An original, plain-language compliance structure covering South Africa's "
        "Promotion of Access to Information Act — the right of access to records "
        "held by public and private bodies. This is compliance guidance, not legal "
        "advice — consult a qualified professional or the Information Regulator for "
        "authoritative interpretation."
    ),
    "domains": [
        {"code": "1", "title": "Section 51 Manual & Governance", "requirements": [
            ("PAIA-1", "Maintain a PAIA manual and accountable Information Officer",
             "Maintain and publish an up-to-date manual describing the records the organisation holds and how to request access to them, with a recorded, accountable Information Officer.")]},
        {"code": "2", "title": "Proactive Disclosure", "requirements": [
            ("PAIA-2", "Proactively publish available records",
             "Proactively publish categories of records that do not require a formal request, reducing the need for individual access requests.")]},
        {"code": "3", "title": "Request Handling", "requirements": [
            ("PAIA-3", "Handle access requests within statutory timeframes",
             "Maintain a documented process for receiving, logging and responding to access requests within the applicable statutory time limits, using the required forms.")]},
        {"code": "4", "title": "Grounds for Refusal", "requirements": [
            ("PAIA-4", "Apply refusal grounds lawfully",
             "Apply the mandatory and discretionary grounds for refusing a request consistently and lawfully, providing adequate written reasons to the requester.")]},
        {"code": "5", "title": "Fees & Access Formats", "requirements": [
            ("PAIA-5", "Charge only permitted fees",
             "Charge only the fees permitted for requests and access, and provide records in a reasonable format considering the requester's needs.")]},
        {"code": "6", "title": "Internal Appeals & Regulator Escalation", "requirements": [
            ("PAIA-6", "Provide an appeal and escalation path",
             "Provide a documented internal appeal process and inform requesters of their right to escalate to the Information Regulator or a court.")]},
    ],
}

ISO22301 = {
    "code": "ISO22301",
    "name": "ISO 22301 — Business Continuity Management",
    "version": "structure summary",
    "category": "international-management-systems",
    "icon": "clock",
    "description": (
        "A structural implementation skeleton for a Business Continuity Management "
        "System (BCMS), organised using the same high-level clause grouping as the "
        "internationally recognised standard. Original guidance content only — "
        "consult the official published standard for authoritative requirement wording."
    ),
    "domains": [
        {"code": "1", "title": "Context of the Organisation", "requirements": [
            ("BCMS-4", "Understand context and determine BCMS scope",
             "Determine internal/external issues and interested party requirements, and use them to define the BCMS's scope around the organisation's products and services.")]},
        {"code": "2", "title": "Leadership", "requirements": [
            ("BCMS-5", "Leadership and BC policy",
             "Top management demonstrates leadership and commitment, establishes a business continuity policy, and assigns roles and responsibilities.")]},
        {"code": "3", "title": "Planning", "requirements": [
            ("BCMS-6", "Actions to address risks and BC objectives",
             "Identify risks and opportunities relevant to continuity, set measurable BC objectives, and plan actions to achieve them.")]},
        {"code": "4", "title": "Support", "requirements": [
            ("BCMS-7", "Resources, competence and documented information",
             "Provide the resources needed for the BCMS, ensure competence and awareness, and maintain controlled documented information.")]},
        {"code": "5", "title": "Operation", "requirements": [
            ("BCMS-8.2", "Business impact analysis and risk assessment",
             "Analyse the impact of disruption over time and assess the risks that could cause a disruptive incident."),
            ("BCMS-8.3", "Business continuity strategies and solutions",
             "Select and implement strategies and solutions to protect prioritised activities and meet recovery time objectives."),
            ("BCMS-8.4", "Business continuity plans and procedures",
             "Document response and recovery plans and procedures, including roles, communications, and resource requirements."),
            ("BCMS-8.5", "Exercising and testing",
             "Exercise and test BC plans at planned intervals to confirm they are consistent with objectives and reveal gaps."),
        ]},
        {"code": "6", "title": "Performance Evaluation", "requirements": [
            ("BCMS-9", "Monitoring, internal audit and management review",
             "Monitor and measure BCMS performance, conduct internal audits, and have top management review the BCMS at planned intervals.")]},
        {"code": "7", "title": "Improvement", "requirements": [
            ("BCMS-10", "Nonconformity and continual improvement",
             "Address nonconformities identified through exercises, incidents or audits, and continually improve the BCMS.")]},
    ],
}

ISO9001 = {
    "code": "ISO9001",
    "name": "SABS ISO 9001 — Quality Management",
    "version": "structure summary",
    "category": "international-management-systems",
    "icon": "check",
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

ISO31000 = {
    "code": "ISO31000",
    "name": "ISO 31000 — Risk Management Guidelines",
    "version": "principles / framework / process structure",
    "category": "international-management-systems",
    "icon": "risk",
    "description": (
        "An original summary of the risk management guideline structure — "
        "Principles, Framework and Process — used here as an internal risk-maturity "
        "structure rather than a certifiable management system. Original guidance "
        "content only; consult the official published guideline for authoritative wording."
    ),
    "domains": [
        {"code": "1", "title": "Principles", "requirements": [
            ("RISK-P", "Apply sound risk management principles",
             "Manage risk in a way that is value-creating, integrated into governance, structured, inclusive of stakeholders, based on the best available information, and continually improved.")]},
        {"code": "2", "title": "Framework", "requirements": [
            ("RISK-F1", "Leadership and integration",
             "Top management demonstrates leadership and commitment, and integrates risk management into governance and all significant organisational activities."),
            ("RISK-F2", "Design, implementation and evaluation",
             "Design a risk management framework fit for the organisation's context, implement it, and evaluate and improve it over time."),
        ]},
        {"code": "3", "title": "Process", "requirements": [
            ("RISK-PR1", "Scope, context and criteria",
             "Define the scope, external and internal context, and risk criteria before assessing risk."),
            ("RISK-PR2", "Risk assessment",
             "Identify, analyse and evaluate risks against the defined criteria."),
            ("RISK-PR3", "Risk treatment",
             "Select and implement options to modify risk, and evaluate the effectiveness of the treatment applied."),
            ("RISK-PR4", "Monitoring, recording and communication",
             "Monitor and review risk and the framework's performance; record and report outcomes; communicate and consult with stakeholders throughout."),
        ]},
    ],
}

NIST_CSF = {
    "code": "NIST_CSF",
    "name": "NIST Cybersecurity Framework",
    "version": "2.0 — Functions structure",
    "category": "cybersecurity-frameworks",
    "icon": "shield-check",
    "description": (
        "An original structure organised around the six publicly known CSF 2.0 "
        "Functions (Govern, Identify, Protect, Detect, Respond, Recover). Original "
        "descriptive guidance only — this is not an official NIST publication and "
        "does not reproduce NIST's copyrighted text; consult the official published "
        "framework for authoritative wording."
    ),
    "domains": [
        {"code": "GV", "title": "Govern", "requirements": [
            ("NIST-GV", "Establish and monitor cybersecurity governance",
             "Establish and monitor the organisation's cybersecurity risk management strategy, roles, policy, oversight, and supply-chain risk expectations.")]},
        {"code": "ID", "title": "Identify", "requirements": [
            ("NIST-ID", "Understand assets, environment and risk",
             "Develop the organisational understanding needed to manage cybersecurity risk to systems, people, assets, data and capabilities.")]},
        {"code": "PR", "title": "Protect", "requirements": [
            ("NIST-PR", "Implement safeguards",
             "Implement appropriate safeguards — access control, awareness and training, data security, platform security — to manage and reduce cybersecurity risk.")]},
        {"code": "DE", "title": "Detect", "requirements": [
            ("NIST-DE", "Find and analyse anomalies",
             "Implement activities to find and analyse anomalies, indicators of compromise, and other potentially adverse events in a timely manner.")]},
        {"code": "RS", "title": "Respond", "requirements": [
            ("NIST-RS", "Respond to detected incidents",
             "Take action once a cybersecurity incident is detected, including incident management, analysis, mitigation and stakeholder communication.")]},
        {"code": "RC", "title": "Recover", "requirements": [
            ("NIST-RC", "Restore capabilities after an incident",
             "Restore assets and operations affected by a cybersecurity incident in a timely manner and communicate recovery progress to stakeholders.")]},
    ],
}

CIS_V8 = {
    "code": "CIS_V8",
    "name": "CIS Controls v8",
    "version": "18 Controls structure",
    "category": "cybersecurity-frameworks",
    "icon": "control",
    "description": (
        "An original structure listing the 18 publicly known CIS Controls v8 "
        "category titles with original descriptive guidance for each. Does not "
        "reproduce CIS's copyrighted safeguard text — consult the official "
        "published Controls for authoritative wording."
    ),
    "domains": [
        {"code": "1", "title": "Critical Security Controls", "requirements": [
            ("CIS-01", "Inventory and Control of Enterprise Assets",
             "Maintain an accurate inventory of all enterprise-connected devices so unmanaged or unauthorised assets can be found and addressed."),
            ("CIS-02", "Inventory and Control of Software Assets",
             "Maintain an inventory of authorised and unauthorised software to prevent unmanaged software from running unnoticed."),
            ("CIS-03", "Data Protection",
             "Identify, classify and protect data throughout its lifecycle based on its sensitivity."),
            ("CIS-04", "Secure Configuration of Enterprise Assets and Software",
             "Establish and maintain secure configurations to reduce the attack surface of assets and software."),
            ("CIS-05", "Account Management",
             "Manage the lifecycle of accounts — creation, use and timely deactivation — to prevent unauthorised access."),
            ("CIS-06", "Access Control Management",
             "Manage access to assets based on least privilege, using appropriate processes and tools."),
            ("CIS-07", "Continuous Vulnerability Management",
             "Continuously assess and track vulnerabilities so they can be remediated before exploitation."),
            ("CIS-08", "Audit Log Management",
             "Collect, review and retain audit logs to detect, understand and recover from an attack."),
            ("CIS-09", "Email and Web Browser Protections",
             "Improve protections and detections of threats delivered through email and web browsers."),
            ("CIS-10", "Malware Defenses",
             "Prevent or control the installation, spread and execution of malicious applications and code."),
            ("CIS-11", "Data Recovery",
             "Establish and maintain data recovery practices sufficient to restore in-scope assets after an incident."),
            ("CIS-12", "Network Infrastructure Management",
             "Establish, implement and manage network devices to prevent attackers exploiting vulnerable network services and access points."),
            ("CIS-13", "Network Monitoring and Defense",
             "Operate processes and tools to detect and respond to threats across the network."),
            ("CIS-14", "Security Awareness and Skills Training",
             "Establish a security awareness programme to influence workforce behaviour to be security-conscious."),
            ("CIS-15", "Service Provider Management",
             "Evaluate service providers that hold sensitive data or are responsible for critical platforms to ensure they protect that data appropriately."),
            ("CIS-16", "Application Software Security",
             "Manage the security lifecycle of in-house-developed, hosted or acquired software to prevent, detect and remediate weaknesses."),
            ("CIS-17", "Incident Response Management",
             "Establish a programme to prepare for, detect and respond quickly to an attack."),
            ("CIS-18", "Penetration Testing",
             "Test the effectiveness of controls by simulating an attacker's objectives and actions."),
        ]},
    ],
}

KING_IV = {
    "code": "KING_IV",
    "name": "King IV — Corporate Governance",
    "version": "Outcomes-based summary",
    "category": "south-african-compliance",
    "icon": "building",
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

ALL_FRAMEWORKS = [
    ISO27001, ISO27701, POPIA, PAIA, ISO22301, ISO9001, ISO31000, NIST_CSF, CIS_V8, KING_IV,
]


class Command(BaseCommand):
    help = "Seed the Framework Library: built-in frameworks (ISO 27001, ISO 27701, POPIA, PAIA, ISO 22301, ISO 9001, ISO 31000, NIST CSF, CIS Controls v8, King IV) and their categories."

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {}
        for slug, name, description, order in CATEGORIES:
            category, _ = FrameworkCategory.objects.update_or_create(
                slug=slug, defaults={"name": name, "description": description, "order": order}
            )
            categories[slug] = category

        for spec in ALL_FRAMEWORKS:
            framework, created = Framework.objects.update_or_create(
                organisation=None,
                code=spec["code"],
                defaults={
                    "name": spec["name"],
                    "version": spec["version"],
                    "description": spec["description"],
                    "category": categories[spec["category"]],
                    "icon": spec["icon"],
                    "status": "active",
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

        self.stdout.write(self.style.SUCCESS(f"Framework seeding complete — {len(ALL_FRAMEWORKS)} frameworks, {len(CATEGORIES)} categories."))
