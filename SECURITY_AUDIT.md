# Bohlale GRC — Security Audit

**Scope:** production-readiness and security-hardening pass performed on
branch `claude/production-readiness-v1`, starting from the feature-complete
`main` (172 tests passing, `manage.py check` clean). This document records
every security-relevant finding from that pass, classified by severity, per
the working instruction's Section 23 format: description, affected
component, risk, reproduction method, remediation, remediation status, and
regression test status.

**Methodology:** systematic audit (parallel targeted codebase reviews for
file-upload exposure, IDOR/tenant-scoping, RBAC coverage, and N+1 queries),
live browser/UAT verification (which itself surfaced findings that static
review missed), and a real, executed PostgreSQL backup/restore drill — not
a checklist review from documentation alone. All findings below were found
in *this* codebase, by inspecting the actual code, not assumed from prior
session claims.

**Summary:** 1 Critical, 3 High, 4 Medium, 2 Low, 5 Informational findings.
**Every Critical and High finding has been remediated and has a regression
test.** No unresolved Critical or High security/data-isolation issue
remains as of this document. See `PRODUCTION_READINESS.md` for the overall
release gate decision.

---

## CRITICAL

### C-1: Uploaded tenant documents served from an unauthenticated `/media/` URL

- **Affected component:** `Evidence.file`, `Document.attachment`,
  `ManagementReview.attachment` (all `FileField`s); `config/urls.py`;
  the documented Nginx configuration.
- **Description:** Uploaded files were served directly from `MEDIA_ROOT` —
  via `django.contrib.staticfiles`' `static()` helper in `DEBUG` mode, and
  via a plain Nginx `location /media/ { alias ...; }` block in the
  documented production config — with **no authentication and no tenant
  check**. Every uploaded evidence file, document attachment, and
  management-review attachment had a stable, guessable-pattern URL
  (`/media/evidence/<file>`, etc.) that served the raw file to anyone who
  requested it, logged in or not, regardless of organisation membership.
- **Risk:** Any tenant's confidential compliance evidence (ISMS policies,
  incident reports, audit findings, risk assessments) was downloadable by
  an unauthenticated party who obtained or guessed a URL — a direct
  cross-tenant confidentiality breach, and a breach reachable by users
  with *no account at all*. This is the most severe class of finding for a
  multi-tenant GRC platform explicitly built to keep client compliance
  data isolated.
- **Reproduction (pre-fix):** Upload an `Evidence` file as Organisation A,
  note its `file.url`. Log out entirely (or log in as Organisation B) and
  `GET` that URL directly — the file was served with a `200` and the raw
  file bytes.
- **Remediation:** Added `core/protected_media.py::serve_tenant_file()`,
  streaming files via `FileResponse(..., as_attachment=True)` from views
  that first call `get_object_or_404_scoped()` (tenant-filtered) and check
  the requesting user's role can view that record. Wired new
  `evidence:download`, `documents:download`, `reviews:download` views.
  Removed `MEDIA_ROOT` serving from `config/urls.py` entirely (not
  conditional on `DEBUG` — there is no code path, dev or prod, that serves
  raw media). Removed the `/media/` alias from the documented Nginx config
  in `DEPLOYMENT.md`, replaced with an explanatory comment so a future
  editor doesn't reintroduce it.
- **Remediation status:** **Fixed.**
- **Regression test status:** **Yes** — tenant-isolation tests for all
  three download views assert a cross-org request returns 404, and that
  same-org requests with insufficient role return 403/404 as appropriate
  (`evidence/tests.py`, `documents/tests.py`, `reviews/tests.py`).

---

## HIGH

### H-1: Cross-tenant IDOR via unscoped form querysets (5 forms)

- **Affected component:** `risks/forms.py::RiskForm.related_requirements`,
  `controls/forms.py::ControlForm.framework_requirements`,
  `evidence/forms.py::EvidenceForm.related_requirements`,
  `audits/forms.py::AuditFindingForm.requirement`,
  `documents/forms.py::DocumentForm.related_frameworks`.
- **Description:** These five `ModelForm` fields built their `queryset`
  from *all* `Requirement`/`Framework` rows in the database, with no
  organisation filter. A user could POST the primary key of another
  organisation's private, custom-imported framework content (via
  Framework Studio) into any of these fields and have it silently accepted
  and linked, since Django's default `ModelChoiceField` validation only
  checks the pk exists in the (unscoped) queryset — not whether the
  submitting user's organisation owns it.
- **Risk:** A user could link their own risk/control/evidence/finding/
  document records to another tenant's private framework content by
  guessing or enumerating primary keys, and — depending on how that linked
  data is later rendered (titles, clause references, requirement text) —
  could infer the existence and content of another organisation's
  confidential framework customisations. Classic Insecure Direct Object
  Reference (IDOR).
- **Reproduction (pre-fix):** As Organisation A, import a custom framework
  via Framework Studio (private, organisation-scoped). Note a
  `Requirement` pk from it. As Organisation B, open the Risk create form
  and POST that pk in `related_requirements` — pre-fix, the form validated
  and saved the link.
- **Remediation:** Scoped each queryset to
  `Q(framework__organisation__isnull=True) | Q(framework__organisation=self.organisation)`
  (global/built-in frameworks OR the requesting organisation's own),
  matching a pattern already used elsewhere in the same files. A pk
  belonging to another tenant's private framework is no longer a valid
  choice, so Django's own field validation now rejects it with a normal
  form error instead of silently accepting it.
- **Remediation status:** **Fixed**, all 5 forms.
- **Regression test status:** **Yes** — a cross-tenant IDOR regression
  test was added per affected form, asserting the form is invalid when
  submitted with another organisation's requirement/framework pk.

### H-2: RBAC gaps on sign-off and journey-start actions

- **Affected component:** `journeys/views.py::onboarding_start`,
  `audits/views.py::audit_close`, `actions/views.py::action_verify_close`,
  `reviews/views.py::review_complete`,
  `actions/views.py::CorrectiveActionUpdateView.form_valid()`.
- **Description:** `onboarding_start` required only an active organisation
  membership (`@require_organisation`) — any role, including a Read-only
  viewer, could start a new guided implementation journey. `audit_close`,
  `action_verify_close`, and `review_complete` are independent sign-off/
  verification actions that the spec's role model expects to require
  Approver-level authority, but were only gated at `@require_editor`, the
  same level as day-to-day record editing — collapsing the intended
  segregation between "does the work" and "signs off the work" is a
  meaningful control weakness for a governance/compliance product.
  Separately, `CorrectiveActionUpdateView`'s plain edit form allowed
  setting `status` directly to `STATUS_CLOSED` through a normal field
  edit, bypassing the dedicated verify/close view's approval gate
  entirely — an Editor could close their own corrective action without
  ever going through `action_verify_close`.
- **Risk:** Privilege escalation within a tenant (horizontal-adjacent):
  a lower-privileged or self-interested user could close audits, close
  corrective actions (including their own, defeating independent
  verification), and complete management reviews without the sign-off
  authority the workflow is designed to require. In a compliance product,
  this undermines the audit trail's claim that closure/sign-off actions
  reflect genuine independent approval.
- **Reproduction (pre-fix):** As a Contributor/Editor-level user, `POST`
  directly to `audits:audit_close`, `actions:action_verify_close`, or
  `reviews:review_complete` for a record in your organisation — pre-fix,
  these succeeded despite the UI only exposing these actions to Approvers.
  Separately, `POST` a `CorrectiveActionUpdateView` edit with
  `status=closed` as an Editor — pre-fix, this saved successfully.
- **Remediation:** All four views changed from `@require_editor` to
  `@require_approver`. `CorrectiveActionUpdateView.form_valid()` now
  explicitly checks `can_approve(self.request)` before allowing a
  transition to `STATUS_CLOSED`, raising `PermissionDenied` otherwise.
- **Remediation status:** **Fixed.**
- **Regression test status:** **Yes** — RBAC boundary tests assert an
  Editor/Contributor gets 403 on all four endpoints, and that an Approver
  succeeds.

### H-3: Missing `SECURE_PROXY_SSL_HEADER` — documented deployment steps would cause an HTTPS redirect loop

- **Affected component:** `config/settings.py`; `DEPLOYMENT.md`'s
  documented Nginx/Gunicorn topology.
- **Description:** `DEPLOYMENT.md` documents Nginx terminating TLS and
  proxying to Gunicorn over a local Unix socket (plain HTTP between them),
  and instructs setting `DJANGO_SECURE_SSL_REDIRECT=True` once HTTPS is
  live. Without `SECURE_PROXY_SSL_HEADER` configured, Django has no way to
  know a request arriving over that internal plain-HTTP hop was actually
  HTTPS at the public edge — `request.is_secure()` is always `False`
  behind the proxy. Combined with `SECURE_SSL_REDIRECT=True`, this
  produces an infinite redirect loop (every request looks insecure, so
  Django redirects to `https://`, which arrives at Nginx, which forwards
  plain HTTP again, forever).
- **Risk:** Following the project's own deployment documentation exactly
  would have broken HTTPS enforcement in production. The realistic
  operational failure mode is worse than "site is down and obviously
  broken": a deploying admin encountering the loop would most likely
  "fix" it by setting `DJANGO_SECURE_SSL_REDIRECT=False`, silently
  disabling the HTTPS-enforcement and HSTS-adjacent protection the spec
  explicitly requires (§45), rather than diagnosing the real cause. Found
  while writing accurate deployment documentation for this pass — not
  discovered by a test, since no existing test exercised proxy headers at
  all.
- **Reproduction (pre-fix):** Deploy per `DEPLOYMENT.md` exactly (Nginx →
  Gunicorn over Unix socket, `DJANGO_SECURE_SSL_REDIRECT=True`, HTTPS via
  certbot). Request `https://<host>/` — pre-fix, the browser reports
  `ERR_TOO_MANY_REDIRECTS`.
- **Remediation:** Added
  `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` to
  `config/settings.py`. This is safe under the documented topology because
  Gunicorn is only ever reachable via a local Unix socket (never a TCP
  port exposed to the network), so Nginx is the only process able to set
  that header — `DEPLOYMENT.md` now states this constraint explicitly
  (§4a) so a future change to expose Gunicorn directly doesn't silently
  reintroduce a header-spoofing risk.
- **Remediation status:** **Fixed.**
- **Regression test status:** **Yes** — `core/tests.py::ReverseProxyHttpsTests`
  asserts `settings.SECURE_PROXY_SSL_HEADER` is configured and that a
  request carrying `X-Forwarded-Proto: https` is treated as secure by
  Django while a request without it is not.

---

## MEDIUM

### M-1: Reference-code assignment race condition

- **Affected component:** `core/models.py::ReferenceCodeMixin` (used by
  `Risk`, `Control`, `Evidence`, `Asset`, `Supplier`, `Incident`, `Audit`,
  `CorrectiveAction`, `Document`, `ManagementReview`).
- **Description:** `assign_reference_code()` read the current count of
  existing records for the organisation (`.count()`) and used it to build
  the next sequential code (e.g. `RISK-0005`), then saved — with no
  locking between the read and the write. Under concurrent requests (the
  normal case with multiple Gunicorn workers), two requests creating a
  record for the same organisation at nearly the same moment could both
  read the same count and both be assigned the identical reference code.
- **Risk:** Duplicate reference codes break the assumption that a
  reference code uniquely identifies a record for audit-trail and
  cross-referencing purposes (e.g. in exported reports, corrective-action
  source links, or when a user quotes "RISK-0005" to a colleague) —  a
  data-integrity issue with downstream implications for audit-trail
  reliability, not a confidentiality/access-control breach.
- **Reproduction:** Two near-simultaneous `POST` requests creating a
  `Risk` for the same organisation, timed to land between another
  process's count-read and save. Difficult to reproduce deterministically
  in a single-threaded test; found by code review (database-integrity
  audit), not a test failure.
- **Remediation:** `ReferenceCodeMixin` gained its own `save()`, wrapping
  `assign_reference_code()` and the actual write in one
  `transaction.atomic()` block that first takes a
  `select_for_update()` lock on the owning `Organisation` row — effective
  under PostgreSQL (the documented production database); a safe no-op
  under SQLite, which doesn't support row-level locking the same way but
  is dev-only per the project's own database policy. Ten models' redundant
  `save()` overrides (which duplicated the old two-line pattern) were
  removed in favour of this single fix, relying on Python MRO to route
  `super().save()` correctly.
- **Remediation status:** **Fixed.**
- **Regression test status:** **Partial.** The full test suite (which
  exercises `save()` for every affected model) continues to pass,
  confirming normal-path behaviour is unchanged and no migration was
  required. A true concurrent-race regression test (two real overlapping
  transactions) is not practical in Django's standard synchronous
  `TestCase` and was not added — documented here as a known verification
  gap rather than claimed as fully tested.

### M-2: Incident reporting could notify nobody

- **Affected component:** `incidents/views.py::IncidentCreateView.form_valid()`.
- **Description:** Reporting an incident notified organisation members
  with `role__in=["org_admin", "consultant"]`, excluding the reporter
  themselves. In a realistic small-organisation staffing pattern — exactly
  what the fictional NIBS reference client represents — an organisation
  might have a Consultant and an Executive but no separate Org Admin. If
  the only Consultant/Org Admin in the organisation is also the person
  reporting the incident, the notification loop excludes them (as
  reporter) and has nobody else in-scope left to notify.
- **Risk:** A reported security/compliance incident could go completely
  unnoticed by anyone except the reporter — a real gap in incident-
  response timeliness for a GRC platform whose core value proposition
  includes incident tracking and notification.
- **Reproduction (pre-fix):** Create an organisation with one Consultant
  (no separate Org Admin) and one Executive. Have the Consultant report an
  incident — pre-fix, zero notifications were created (the Consultant is
  excluded as reporter; the Executive was never in the notified role set).
- **Remediation:** Broadened the notified-role filter from a hardcoded
  `["org_admin", "consultant"]` list to `tenancy.constants.APPROVER_ROLES`
  (adds Executive), imported rather than duplicated.
- **Remediation status:** **Fixed.**
- **Regression test status:** **Yes** —
  `incidents/tests.py::test_reporting_incident_also_notifies_executives`.
  This finding was itself surfaced by the deliberately realistic
  3-persona end-to-end UAT walkthrough (`core/tests_uat.py`), not by an
  isolated per-feature test set up with a convenience admin account — see
  `UAT_RESULTS.md`.

### M-3: Document lifecycle had an unreachable Archived state and no server-side edit guard for it

- **Affected component:** `documents/models.py`, `documents/views.py`,
  `documents/services.py`.
- **Description:** `STATUS_ARCHIVED` was declared as a model choice but no
  code path ever set a document to it — there was no way to actually reach
  the terminal "retained for audit history only" state the spec's document
  lifecycle requires. Separately, even where the UI didn't render an Edit
  button for a document in a terminal state, there was no server-side
  guard preventing a direct `POST` to the edit view regardless of status —
  "a hidden menu item is not access control," per this project's own
  standing instruction.
- **Risk:** No functional/business-logic vulnerability by itself (no
  cross-tenant or cross-user exposure), but a governance-integrity gap: a
  document that should be immutable history could still be edited via a
  direct request, undermining the audit trail's claim that a
  superseded/archived policy's content is fixed.
- **Reproduction (pre-fix):** No UI path reached Archived at all. For the
  edit-guard half: directly `POST` to a document's edit URL for a document
  in a state the UI no longer shows an Edit button for — pre-fix, the
  server accepted it.
- **Remediation:** Added `documents/services.py::archive()` and a real
  `document_archive` view (Editor + org-admin-level check), reachable from
  Published; added an explicit server-side guard in `document_edit`
  raising `PermissionDenied` when `document.status == "archived"`.
- **Remediation status:** **Fixed.**
- **Regression test status:** **Yes** — tests cover reaching Archived via
  the new action and confirm the edit view rejects a direct POST against
  an archived document.

### M-4: No self-service way to change or remove an organisation member's access

- **Affected component:** `tenancy/views.py`, `tenancy/urls.py`,
  `templates/tenancy/member_list.html`.
- **Description:** The invite flow existed, but once a member joined an
  organisation, there was no view or endpoint for an admin to change their
  role or remove their access — membership was effectively permanent
  short of direct database intervention.
- **Risk:** An access-control *completeness* gap rather than a classic
  vulnerability: an organisation had no way to revoke a departed
  employee's or a compromised account's access to tenant data through the
  product itself, which matters for a compliance platform's own access-
  governance story.
- **Remediation:** Added `tenancy:member_update_role` and
  `tenancy:member_remove`, both admin-only (`can_administer()`), with
  guards preventing demoting/removing the organisation's last admin and
  preventing self-removal; removal soft-deactivates the `Membership`
  (`is_active=False`) rather than hard-deleting it, preserving audit-trail
  referential integrity.
- **Remediation status:** **Fixed** (new capability, not a regression).
- **Regression test status:** **Yes** — tests cover the last-admin guard,
  the self-removal guard, non-admin 403, and successful role change/removal
  by an admin.

---

## LOW

### L-1: Topbar "Help" link pointed to an unrelated third-party documentation site

- **Affected component:** `templates/core/_topbar.html`.
- **Description:** The Help icon-button's `href` was
  `https://code.claude.com/docs/en/claude-code-on-the-web` — the AI coding
  assistant's own product documentation, not anything related to Bohlale
  GRC — while its `aria-label`/`title` correctly said "Help"/"Documentation."
- **Risk:** Not independently exploitable, but a real, user-facing defect:
  a production user clicking "Help" would be sent to a completely
  unrelated external site with no relevance to their task, which is
  confusing at best and could read as suspicious/phishing-adjacent at
  worst (an unexplained external redirect from a compliance product's
  "Help" button). Classified Low because it requires no attacker action
  and leaks no data, but included here because trust and unexplained
  external redirects are a legitimate part of a security review of a
  product handling confidential compliance data.
- **Reproduction (pre-fix):** Click the Help icon in the topbar while
  logged in — pre-fix, this opened `code.claude.com`.
- **Remediation:** Changed to `mailto:support@bohlalegrc.example`,
  matching the sidebar's existing "Bohlale Support" convention; removed
  the now-unnecessary `target="_blank" rel="noopener"` attributes (a
  `mailto:` link doesn't need them).
- **Remediation status:** **Fixed.**
- **Regression test status:** No dedicated automated test (a static
  template string is a poor fit for a regression test); caught by visual/
  UAT review, which is the appropriate control for this class of issue.

### L-2: Checkbox and other interactive elements lost visible keyboard focus indication

- **Affected component:** `static/css/base.css`.
- **Description:** A blanket `input:focus, select:focus, textarea:focus {
  outline: none; border-color: var(--color-black); }` rule stripped the
  native focus outline from every input type, including checkboxes and
  radios, where the `border-color` replacement doesn't render meaningfully
  — leaving keyboard-only users with no visible indication of which
  checkbox/radio had focus while tabbing through forms (e.g. the SoA
  applicability checkboxes, control/risk multi-select lists).
- **Risk:** Not a confidentiality/integrity issue, but a genuine
  accessibility/usability defect that specifically disadvantages
  keyboard-only and assistive-technology users navigating compliance
  forms — relevant to this project's explicit accessibility review scope.
- **Remediation:** Scoped the `outline: none` removal to text-style inputs
  only; added a visible `box-shadow` focus ring for those; gave checkboxes
  their own explicit `:focus-visible` outline; added a global
  `:focus-visible` ring for every interactive element (links, buttons,
  nav items, icon buttons) so focus is always visible regardless of
  element type. See the accessibility commit for the full set of related
  fixes (contrast, table header semantics, form help-text association,
  dropdown ARIA) — tracked in `BUILD_STATUS.md`, not duplicated here since
  these are accessibility rather than security findings.
- **Remediation status:** **Fixed.**
- **Regression test status:** No automated test (CSS visual behaviour);
  verified via Playwright screenshot review during the accessibility pass.

---

## INFORMATIONAL

### I-1: Rate limiting is per-process, not shared across Gunicorn workers

`core/ratelimit.py` uses Django's default cache backend (`LocMemCache`
unless `CACHES` is overridden), which is per-process. With
`--workers 3` as documented in `DEPLOYMENT.md`, the effective limit is
roughly `configured_limit × worker_count` per IP, since each worker keeps
an independent counter. This is a **deliberate, documented design
trade-off**, not an oversight: the working spec explicitly prohibits
making Redis mandatory, and this still meaningfully blunts brute-force/
enumeration attempts against login and the public information-request
token endpoint. If stricter enforcement is needed later, pointing
`CACHES` at a shared backend (`django-redis` or a Postgres-backed cache)
requires no change to `core/ratelimit.py`'s interface. No action taken
this pass beyond re-confirming the behaviour with tests (GET never
consumes an attempt; only POST failures count; successful auth is
unaffected; a regression test confirms plain page reloads don't count
against the limit).

### I-2: AI-generated and uploaded content cannot become a stored-XSS vector

Verified (repo-wide search) that no Django template uses the `|safe`
filter anywhere in the codebase — AI-generated draft content, uploaded
document metadata, and framework-import content are always rendered
through Django's default auto-escaping. Combined with the fact that AI
output always starts in an editable Draft state and only reaches
Published through a real human `Signature` record (tested), this closes
off the most direct prompt-injection-to-stored-XSS path. No gap found;
recorded here as a verified control, not a finding requiring remediation.

### I-3: AI provider failure handling degrades gracefully

Added tests confirming `OpenAICompatibleProvider` returns a placeholder
result rather than raising or 500ing on a network failure or non-200
response from the configured endpoint, alongside the pre-existing
mock-provider-by-default behaviour (the whole product, including the
NIBS demo, works fully offline with `AI_PROVIDER=mock`). No gap found;
recorded as a verified control.

### I-4: Document workflow transition guards already correctly prevented invalid states

Added regression tests explicitly proving a Draft document cannot be
published directly (skipping Review/Approval/Signature), and that an
already-decided `ApprovalRequest` cannot be signed a second time. Both
protections already existed in `documents/services.py` prior to this
pass; these tests exist to lock in that behaviour going forward, not
because a gap was found.

### I-5: `manage.py check --deploy` warnings in the development sandbox are expected, not a defect

Running `check --deploy` in this development/CI sandbox (no production
`.env` present) reports 6 warnings — `SECURE_HSTS_SECONDS`,
`SECURE_SSL_REDIRECT`, `SECRET_KEY` length, `SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`, and `DEBUG=True`. All six are resolved by the
production environment variables documented in `DEPLOYMENT.md` §4
(verified clean in this pass with a fully production-configured `.env`).
This is expected behaviour for an unconfigured dev environment, not an
application defect — recorded here so a future reviewer doesn't mistake
the dev-sandbox output for an unresolved finding.

---

## Findings not applicable / out of scope for this document

- **Tenant isolation** beyond the specific IDOR items above (C-1, H-1) was
  audited across every tenant-scoped module (organisations, users, org
  knowledge, frameworks, journeys, documents, versions, approvals,
  signatures, risks, controls, evidence, assessments, assets, suppliers,
  incidents, compliance registers, audits, findings, corrective actions,
  management reviews, reports, notifications, activity logs, AI
  interactions) with a cross-org regression test per app returning 404
  (not 403, to avoid confirming record existence to an unauthorised
  tenant) — see `PRODUCTION_READINESS.md` for the consolidated pass/fail
  status of that coverage.
- **Accessibility findings** (contrast, table semantics, focus states
  beyond L-2, ARIA/keyboard handling) are tracked in the accessibility
  commit and `BUILD_STATUS.md` rather than duplicated in full here, since
  they are usability/inclusion findings, not security findings — L-2 is
  included above only because it specifically concerns visible security-
  relevant state (focus) on form controls used to make compliance
  decisions.
- **POPIA/privacy** technical-readiness findings and remediations are in
  `POPIA_READINESS.md`.
- **Backup/restore** verification is in `BACKUP_RESTORE.md`.
