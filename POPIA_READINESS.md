# POPIA / Privacy Technical Readiness

This document is a **product-level privacy review** of Bohlale GRC for
operators deploying it as a South African SaaS platform. It covers what
the software does and does not do.

**This document is not legal advice, and using this software does not by
itself make an organisation POPIA-compliant.** POPIA compliance is an
organisational and legal undertaking — appointing an Information Officer,
running a PAIA manual, signing operator/processor agreements, defining
retention schedules, and training staff are decisions the deploying
organisation must make, not something a codebase can decide on its
behalf. This document separates what is a **technical capability** (built
into the software) from what remains an **organisational/legal decision**
(the deploying organisation's responsibility).

## 1. Personal information the platform processes

| Category | Where | Notes |
|---|---|---|
| User account data | `accounts.User` | Name, email, job title, phone number — the platform's own users (staff/consultants), not data subjects of the tenant organisations' own compliance activity. |
| Organisation profile | `tenancy.Organisation` | Business data, not personal information, except where a sole proprietor's own details are used as the org profile. |
| Membership/role data | `tenancy.Membership` | Links a User to an Organisation with a role. |
| Audit trail | `activity.AuditLog` | Actor (User), action, timestamp — necessarily retains who-did-what for compliance/audit-integrity purposes; this is itself a POPIA-relevant justification (accountability, security safeguards) for retaining certain personal data past a "delete on request" ideal. |
| Uploaded documents/evidence | `documents.Document.attachment`, `evidence.Evidence.file`, `reviews.ManagementReview.attachment` | May contain personal information if a tenant uploads a document that includes it (e.g. an HR policy naming individuals, or evidence containing a screenshot with names). This is **tenant-supplied content** — Bohlale GRC does not control what a tenant uploads, so operators must ensure tenants understand this is their own POPIA responsibility for what they upload. |
| Incident records | `incidents.Incident` | `personal_info_involved` boolean and free-text fields may describe a data-subject-relevant incident (e.g. a POPIA-notifiable breach) — this is the intended purpose of the field, per spec §25. |
| Knowledge profile | `knowledge.KnowledgeItem` | Free-text organisational facts; a tenant could enter personal information here (e.g. a named Information Officer) as part of describing their organisation. |
| AI processing | `ai.AIGeneration` | Prompts sent to an AI provider are built server-side from the target organisation's own verified Knowledge Profile facts (see `ai/service.py` docstring) — never another tenant's data. If `AI_PROVIDER=openai_compatible` is configured against a real, possibly overseas, endpoint, any personal information present in the prompt (e.g. a name mentioned in a Knowledge Profile fact) leaves the platform's own infrastructure. With the default `AI_PROVIDER=mock`, nothing leaves the server at all. |
| Notifications | `notifications.Notification` | References the recipient user and a message; low sensitivity. |

## 2. Technical capabilities implemented

- **Access**: `accounts:export_my_data` — any logged-in user can download
  a JSON export of their own account-level personal information (name,
  email, job title, phone, membership/role history) at any time, no
  approval needed. This satisfies the account-holder's own "right of
  access" to what Bohlale GRC itself holds about them directly.
  Organisation-level compliance records they authored (documents they
  wrote, risks they own, findings they raised) are **not** included in
  this export, because those records are the organisation's own business
  and audit records, not solely the individual's personal information —
  an organisation administrator exports those via that organisation's
  Reports section instead (already implemented, tenant-scoped).
- **Correction**: `accounts:profile` — every user can edit their own
  name, job title and phone number directly at any time (existing
  feature).
- **Deactivation**: `accounts:deactivate_account` — a user can
  self-service deactivate their own account (blocks login immediately).
  This is intentionally a **deactivation**, not a hard delete — see
  §3 below for why, and for the documented purge procedure.
- **Tenant isolation**: every tenant-scoped record carries an
  `organisation` FK and is enforced by `TenantMiddleware` plus
  view-level scoping (see `SECURITY_AUDIT.md`) — one organisation's
  personal/compliance data is never visible to another organisation.
  This is a POPIA "security safeguards" control (condition 7).
- **Secure file handling**: uploaded files (which may contain personal
  information) are served only through tenant-and-RBAC-checked download
  views, never a public URL — see `core/protected_media.py` and
  `SECURITY_AUDIT.md`.
- **Audit logging**: `activity.AuditLog` provides an immutable record of
  who did what and when — supports POPIA's accountability and security
  safeguard conditions, and is itself a defensible reason to retain
  certain actor references even after a user requests account
  deactivation (see §3).
- **Backups**: `BACKUP_RESTORE.md` documents encrypted-at-rest-capable,
  access-controlled backup storage guidance — relevant to POPIA's
  "security safeguards" condition for data at rest.

## 3. Deletion / erasure — deactivation vs. hard delete

Bohlale GRC deliberately implements **soft deactivation** rather than an
automatic one-click hard delete for user accounts, because:

- A user's `id` is referenced as an immutable actor in `activity.AuditLog`
  entries across every organisation they've ever been a member of.
  Hard-deleting the row (or `on_delete=CASCADE`ing it away) would corrupt
  the audit trail's completeness for *every* one of those organisations —
  a much bigger integrity problem than the deletion request itself.
- The same applies to `owner`/`author`/`approver`/`verified_by` foreign
  keys across documents, risks, controls, evidence, audits, findings,
  corrective actions and management reviews (mostly `on_delete=SET_NULL`
  or `PROTECT`-equivalent by design, so deleting the row either nulls out
  audit-relevant attribution or is blocked entirely).

**When a genuine erasure request must be honoured** (e.g. a completed
POPIA deletion request that has been through the deploying
organisation's own assessment — not every deactivation is a POPIA
erasure request), the documented operational procedure is:

1. Deactivate the account first (`accounts:deactivate_account`, or a
   platform administrator can do the same via Django admin).
2. Have a platform administrator anonymise the personally-identifying
   fields (`first_name`, `last_name`, `email`, `phone_number`,
   `job_title`) on the `accounts.User` row via the Django shell/admin,
   replacing them with a non-identifying placeholder (e.g.
   `deleted-user-<id>@bohlalegrc.example`) — this preserves referential
   integrity and the audit trail's shape (a name still shows against
   historical actions) while removing the actual personal information.
3. Document the request and the action taken outside the platform (a
   POPIA data-subject-request log is an organisational, not a technical,
   requirement — see §4).

This procedure is intentionally manual rather than automated, because a
erasure request should be reviewed by a human (to confirm it's not
premature — e.g. an open corrective action still assigned to that person)
before irreversibly anonymising audit-trail attribution.

## 4. Remaining organisational/legal decisions (not implemented in code)

These are the deploying organisation's responsibility, not something this
codebase can decide for them:

- **Appoint an Information Officer** and register with the Information
  Regulator, as POPIA requires of every responsible party.
- **PAIA manual** — POPIA amended PAIA to require most organisations to
  have a manual describing what records they hold; this is a document the
  organisation writes, not generated by the platform. (Note: the
  `popia-auditor` skill available in this environment covers PAIA
  *website* compliance auditing for a separate, public-facing context —
  it is not a substitute for this platform-operator's own PAIA manual.)
- **Retention schedule** — how long each category of data (§1 above) is
  kept before deletion is a decision that depends on the organisation's
  own legal, tax, and regulatory obligations (which vary by industry and
  record type) — this platform does not auto-delete anything on a timer,
  by design, since GRC/audit records typically need multi-year retention
  precisely to demonstrate compliance history. Operators should define
  and document their own retention schedule and, if they want automated
  enforcement of it, that would be a specific, deliberate future feature
  built against that schedule (not a sensible default to hard-code now).
- **Operator/processor agreements** — if using a real (non-mock) AI
  provider, an SMS/email provider, or a hosting provider, POPIA requires
  a written agreement establishing that third party as an "operator"
  processing data on the responsible party's behalf, with appropriate
  security safeguard commitments. Check whether your chosen `AI_API_BASE`
  endpoint is hosted in South Africa or transfers data across borders —
  POPIA condition 9 (cross-border transfers) may apply.
- **Data subject request handling process** — who receives requests
  (access, correction, deletion, objection), how they're verified, and
  the SLA for responding, is an organisational process this platform
  supports (via §2/§3's technical capabilities) but does not itself
  define or track as a formal workflow.
- **Breach notification procedure** — POPIA requires notifying the
  Information Regulator and affected data subjects of a security
  compromise "as soon as reasonably possible." `incidents.Incident` with
  `personal_info_involved=True` is the platform's mechanism for
  *recording* such an event once identified — the actual notification
  obligation and timeline is the organisation's legal responsibility to
  execute, not an automated feature.
- **Special personal information** (POPIA §26 — e.g. health, biometric,
  criminal data) requires additional safeguards/consent basis beyond
  ordinary personal information if a tenant chooses to store it in a
  free-text field (e.g. an incident description); the platform does not
  restrict what tenants type into free-text fields, since it cannot know
  in advance what an organisation will describe there.
