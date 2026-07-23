# User Acceptance Test Plan — NIBS Reference Scenario

This is the UAT plan for Bohlale GRC's primary reference journey (spec
§47): a consultant onboarding a fictional client organisation — Naleli
Innovators Business School (NIBS) — through a full ISO/IEC 27001
implementation, from organisation creation to audit readiness.

It exists in two forms, both covering the same steps:

1. **Automated**: `core/tests_uat.py::NibsEndToEndUATTests` — walks every
   step below through real HTTP requests (Django's test client — URL
   routing → view → form validation → template, exactly what a browser
   does), asserting actual persisted database state and permission
   enforcement at each step, not just HTTP 200 responses. Run it with
   `python manage.py test core.tests_uat -v 2`.
2. **Manual**: this checklist, for a human tester to follow in an actual
   browser against a running instance (`python manage.py runserver`, or
   a staging deployment) — see `UAT_RESULTS.md` for the results of the
   manual/visual pass performed during this review.

Fictional data only throughout — no real client, employee, or personal
information (per the product's data-safety rule).

## Personas used

| Persona | Email | Role | Purpose in this scenario |
|---|---|---|---|
| Thabiso Mokoena | thabiso@bohlale-demo.example | Consultant | Runs the engagement, does most data entry |
| Naledi Khumalo | naledi@nibs-demo.example | Executive | Approves/signs documents, closes audits, completes management review |
| Sipho Nkosi | sipho@nibs-demo.example | Contributor (IT Manager) | Responds to an information request; used to test permission boundaries |

(These match `seed_nibs_demo`'s fictional demo users, so a manual tester
can either run through the checklist on a fresh org or use
`python manage.py seed_nibs_demo` and inspect the result — see
`UAT_RESULTS.md` for which was used for each check.)

## Steps and expected outcomes

For each step: the action, the expected UI result, and — critically —
the expected **persisted business outcome**, since a page returning 200
is not the same as the workflow having actually worked.

1. **Consultant logs in** → `/accounts/login/` → redirected to
   `/dashboard/` (or `/organisations/` if no org yet). *Outcome*:
   session authenticated as the correct user.
2. **Creates NIBS** → Organisations → New Organisation → fill in name,
   type, industry, etc. → submit. *Outcome*: `Organisation` row created;
   a `Membership` with `role="org_admin"` (or `consultant`, if using an
   existing consultant account) links the creator to it; the new org
   becomes the active session organisation.
3. **Selects "Build a management system from scratch"** → **ISO/IEC
   27001** → guided onboarding wizard starts. *Outcome*: an
   `OrganisationJourney` is created against the ISO 27001
   "Build an ISMS from Scratch" template, `status="in_progress"`.
4. **Completes the AI guided interview** for the first step (Context of
   the Organisation) → answers each seeded question. *Outcome*: an
   `InterviewSession` reaches `status="completed"`; each answer becomes
   a `KnowledgeItem` with `status="verified"` (spec §10/§11).
5. **Requests missing information** from a stakeholder (e.g. "which
   cloud providers does NIBS use?", assigned to the IT Manager's email).
   *Outcome*: an `InformationRequest` is created with a unique token; an
   email is sent (console backend in dev) containing a link requiring no
   login. The recipient visits that link and answers — *outcome*: the
   request becomes `status="answered"`, and the answer becomes a
   `KnowledgeItem` with `status="ai_inference"` (pending human
   verification, not auto-trusted).
6. **Generates a draft ISMS Scope** via the guided journey step (AI
   Document Generation). *Outcome*: a `Document` with
   `doc_type="isms_scope"`, `status="draft"`, `ai_generated=True` is
   created — **never** anything past Draft, regardless of AI confidence
   (spec §13/§23 hard requirement).
7. **Human review**: consultant edits/reviews the draft, submits for
   review, then submits for approval. *Outcome*: `Document.status`
   progresses Draft → Under Review → Awaiting Approval; an
   `ApprovalRequest` is created; approver-role members are notified.
8. **A non-approver attempts to sign** (negative test). *Outcome*:
   **403 Forbidden** — only Executive/Approver, Org Admin or Consultant
   roles may reach the signing page.
9. **Executive approval + electronic sign-off**: Naledi opens the
   approval, types her full legal name exactly matching her profile
   name, ticks consent, submits. *Outcome*: a `Signature` record is
   created capturing typed name, consent, IP, timestamp, document
   version and content hash; `Document.status` becomes `approved`.
10. **Publish**: an approver publishes the approved document. *Outcome*:
    `Document.status` becomes `published`, `version_label` becomes the
    next whole version (e.g. `1.0`), `effective_date` is set, and the
    linked journey step is automatically marked complete.
11. **Risk assessment**: record a risk (e.g. "Unpatched public-facing web
    server", likelihood 4, impact 4). *Outcome*: a `Risk` row with
    `inherent_risk_score = likelihood × impact` (16).
12. **Map controls / Statement of Applicability**: visit the SoA page for
    the first time. *Outcome*: the common control library auto-seeds
    (`ensure_baseline_controls`), and one `SoAEntry` per control is
    created for the adopted framework. Mark a control applicable and
    implemented. *Outcome*: `SoAEntry.applicable=True`,
    `Control.implementation_status="implemented"` persisted.
13. **Upload evidence**: attach a file to demonstrate a control (e.g. a
    patch-management policy). *Outcome*: an `Evidence` row is created
    with the file stored under a per-organisation path; downloading it
    (as a member of the same org) succeeds; a different organisation's
    member gets **404**, not the file (spec §7/§45 — see
    `SECURITY_AUDIT.md`).
14. **Report an incident** (e.g. a phishing email). *Outcome*: an
    `Incident` row is created; org admins/consultants/executives are
    notified (spec §36 notification-trigger requirement).
15. **Update a compliance register** (e.g. add an Interested Party).
    *Outcome*: a `RegisterEntry` row is created against the correct
    `RegisterType`, with the answers stored in its JSON `data` field.
16. **Internal audit**: plan an audit, mark it in progress, record a
    finding. *Outcome*: an `Audit` row and a linked `AuditFinding` row
    are created; the audit's status auto-advances to
    `findings_recorded`.
17. **A contributor attempts to close the audit** (negative test).
    *Outcome*: **403 Forbidden** — closing is an approver-level sign-off
    action, not a routine edit.
18. **An approver closes the audit**. *Outcome*: `Audit.status` becomes
    `closed`.
19. **Corrective action from the finding**: create a corrective action
    linked to the audit finding. *Outcome*: a `CorrectiveAction` row is
    created with its `content_type`/`object_id` pointing at the
    originating `AuditFinding` (generic source linking, spec §31).
20. **Management review**: schedule a review meeting. *Outcome*: a
    `ManagementReview` is created with its required-inputs checklist
    auto-seeded (6 items mirroring ISO clause 9.3, spec §32). An
    approver marks it complete. *Outcome*: `status="completed"`,
    `approved_by` set to the approving user.
21. **Check audit readiness**. *Outcome*: the readiness report shows a
    real, non-zero, non-100% score reflecting the actual data entered
    above across all 8 dimensions (spec §33) — and the page must **never**
    use the word "certified" (the platform explicitly does not claim to
    grant certification).
22. **Generate reports**: visit the reports hub, the risk register
    report. *Outcome*: the exported/rendered content reflects the real
    risk just created (e.g. contains "Unpatched public-facing web
    server"), not placeholder or stale data.

## Out of scope for this plan

- Framework Studio (custom framework import) — covered by its own test
  suite (`frameworks/tests.py`), not re-walked here since it's an
  alternate entry point to the same downstream workflows (documents,
  controls, etc.) already exercised above.
- Assessments, assets, suppliers apps — covered by their own dedicated
  test suites; not part of the *primary* NIBS ISO 27001 narrative
  in spec §47, though they share the same tenant-isolation/RBAC
  patterns already verified everywhere else (`SECURITY_AUDIT.md`).
