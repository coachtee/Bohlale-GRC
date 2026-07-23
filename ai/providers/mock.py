"""
Deterministic, offline AI provider. Requires no API key, so the whole
product — including the NIBS demonstration journey — works without any
external AI dependency. Produces original, template-based drafting
text (never copies from any external corpus) that is always framed as
a draft requiring human review, per spec §13/§23.
"""

import textwrap

from .base import AIProvider


def _wrap(text):
    return "\n".join(
        line for para in text.strip().split("\n") for line in textwrap.wrap(para, 100) or [""]
    )


class MockProvider(AIProvider):
    name = "mock"

    def complete(self, *, system_prompt, user_prompt, purpose="general", max_tokens=1200):
        handler = getattr(self, f"_handle_{purpose}", self._handle_general)
        return handler(user_prompt)

    # -- purpose-specific templated generation -----------------------

    def _handle_interview_question(self, prompt):
        return (
            "Thanks — based on what you've told me so far, here is the next question:\n\n"
            "Could you confirm the specific locations, business units and information "
            "systems that should be included in scope, and note anything that should "
            "explicitly be excluded and why?"
        )

    def _handle_isms_scope(self, prompt):
        return _wrap(f"""
ISMS SCOPE (AI-GENERATED DRAFT — REQUIRES HUMAN REVIEW)

1. Purpose
This Information Security Management System (ISMS) scope defines the boundaries
and applicability of the organisation's ISMS in accordance with the organisation's
context, interested party requirements, and the information covered by the
knowledge profile below.

2. Organisational context considered
{prompt}

3. Proposed scope statement
The ISMS covers the people, processes, information systems and locations involved
in delivering the organisation's core business activities, including the
information assets, applications and third-party/supplier relationships that
support those activities, as captured in the Organisation Knowledge Profile.

4. Proposed exclusions
Any business units, locations or systems not confirmed as verified facts in the
Organisation Knowledge Profile are provisionally excluded from this draft scope
and should be reviewed before approval.

5. Next step
This is a first draft only. Please review, correct any inaccuracies, confirm
exclusions, and route for executive approval and electronic sign-off before this
becomes a controlled document.
""")

    def _handle_document_draft(self, prompt):
        return _wrap(f"""
DRAFT DOCUMENT (AI-GENERATED — REQUIRES HUMAN REVIEW BEFORE APPROVAL)

Context used for this draft:
{prompt}

Purpose
This document has been drafted using the organisation's verified knowledge
profile and the applicable framework requirements. It sets out the intended
policy/procedure position for review by the document owner.

Scope
Applies to all people, systems and processes described in the organisational
context above, unless a narrower scope is agreed during review.

Policy / Procedure statement
The organisation is committed to managing this area in a manner consistent with
its stated objectives, applicable legal and regulatory requirements, and the
expectations of its interested parties. Specific commitments, responsibilities
and procedural steps should be reviewed and refined by the document owner prior
to approval.

Roles and responsibilities
The document owner is responsible for maintaining this document. Specific role
assignments should be confirmed during review.

Review
This document should be reviewed at least annually or after a significant
organisational change.

-- End of AI-generated draft. Edit as needed, then submit for approval. --
""")

    def _handle_gap_explanation(self, prompt):
        return _wrap(f"""
Gap summary (AI-generated — for guidance only):
{prompt}

This requirement does not yet appear to be fully addressed. Consider: confirming
whether a policy or procedure already exists informally; identifying the
responsible owner; and determining what evidence would demonstrate this
requirement is met. Human review is required before recording a final
assessment rating.
""")

    def _handle_evidence_suggestion(self, prompt):
        return _wrap(f"""
Possible evidence to look for, based on the context provided:
{prompt}

- A relevant approved policy or procedure document
- Records/logs demonstrating the control operating (e.g. access reviews, training
  records, meeting minutes)
- Screenshots or exports from the relevant system configuration
- Correspondence or sign-off confirming the activity took place

Please confirm which of these actually exist before attaching them as evidence.
""")

    def _handle_executive_summary(self, prompt):
        return _wrap(f"""
Executive Compliance Summary (AI-generated draft):
{prompt}

Overall, implementation is progressing. Priority areas for executive attention
are any open high-severity risks, overdue corrective actions, and any documents
awaiting approval. Please review the underlying registers before circulating
this summary externally.
""")

    def _handle_framework_extraction(self, prompt):
        return _wrap(f"""
Draft framework structure extracted from the uploaded content (REQUIRES REVIEW):
{prompt}

A domain/requirement structure has been inferred from the document layout
(headings and numbering). Please review each extracted requirement carefully,
correct any inaccuracies, and only publish the framework once you are satisfied
it correctly reflects the source document and that you hold the necessary rights
to use its content within your organisation.
""")

    def _handle_general(self, prompt):
        return _wrap(f"AI draft response (demo mode) based on:\n{prompt}")
