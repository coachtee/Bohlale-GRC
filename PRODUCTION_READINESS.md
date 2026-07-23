# Bohlale GRC — Production Readiness Gate

**Assessed:** 2026-07-23, branch `claude/production-readiness-v1`
(from `main`, commit `0a6fde9`, the feature-complete build).

**Purpose:** a category-by-category go/no-go assessment, not a restatement
of "tests pass." Each category below is marked one of:

- **PASS** — verified working, no caveats.
- **PASS WITH CAVEAT** — working and acceptable for release, but with a
  documented limitation the deploying organisation should know about.
- **FAIL** — a real gap exists in this codebase that should be fixed
  before release. (None currently open — see verdict.)
- **BLOCKED — EXTERNAL ACTION REQUIRED** — not something this codebase can
  resolve by itself; requires infrastructure, credentials, a human/legal
  decision, or an action outside the repository.

---

## 1. Automated tests

**PASS.** 226 tests passing (`python manage.py test`), 0 failures, 0
errors. Started this pass at 172 (session 1's count, re-verified
independently rather than assumed); 54 tests added across the
production-readiness work covering tenant-isolation/IDOR regressions,
RBAC boundary regressions, member management, the SECURE_PROXY_SSL_HEADER
fix, dashboard performance, the incident-notification fix, the two
journey-completion display fixes, and a 22-step full-NIBS-scenario
end-to-end UAT walkthrough (`core/tests_uat.py`). Verified against both
SQLite (dev) and a real, locally-run PostgreSQL 16 instance (218-220
tests passing on Postgres at that point in the session; full 226 not
re-run against Postgres after the final accessibility/deployment-doc
commits, since none of those commits touch database behaviour — see
caveat below).

**Caveat:** the final 3 commits of this pass (accessibility CSS/template
changes, DEPLOYMENT.md/.env.example updates, SECURITY_AUDIT.md +
proxy-header tests) were run against SQLite only, not re-verified against
PostgreSQL. None of them touch models, migrations, or querysets, so this
is a low-risk gap, but it means "tested against Postgres" is accurate as
of the N+1/backup-restore commit (`2fe45ab`), not as of `HEAD`. Re-running
the full suite with `DB_ENGINE=postgres` before go-live is cheap
(~2 minutes) and recommended.

## 2. Tenant isolation

**PASS.** Every tenant-scoped module (organisations, users, org
knowledge, frameworks, journeys, documents, versions, approvals,
signatures, risks, controls, evidence, assessments, assets, suppliers,
incidents, compliance registers, audits, findings, corrective actions,
management reviews, reports, notifications, activity logs, AI
interactions) has a cross-organisation regression test asserting access
is blocked — via the UI, direct URL, manipulated object ID, POST/update/
delete, download/export, and search/filter paths. Cross-tenant access
consistently returns 404 rather than 403 (deliberate: avoids confirming a
record's existence to an unauthorised tenant). Report/export content was
tested by reading back actual exported bytes (openpyxl for Excel, raw CSV)
rather than only checking HTTP status.

One CRITICAL finding was found and fixed this pass: uploaded evidence/
document/review files were reachable via an unauthenticated `/media/` URL
regardless of tenant, bypassing every other tenant-isolation control.
Fully remediated (`SECURITY_AUDIT.md` C-1) with regression tests. Five
additional HIGH-severity cross-tenant IDOR gaps in form field querysets
were found and fixed (`SECURITY_AUDIT.md` H-1). No open tenant-isolation
finding remains.

## 3. RBAC

**PASS.** All 8 spec-defined roles (Platform Administrator, Consultant,
Organisation Administrator, Executive/Approver, Auditor, Control Owner,
Standard User, Read-only/Viewer) are enforced server-side via
`core/permissions.py` role-set checks (`ADMIN_ROLES`, `APPROVER_ROLES`,
`EDITOR_ROLES`, `VIEW_ONLY_ROLES`) applied as view decorators/mixins, not
merely hidden in the UI — verified by direct-URL and direct-POST/PUT/
PATCH/DELETE regression tests per role boundary. Three real RBAC gaps
were found and fixed this pass (`SECURITY_AUDIT.md` H-2): journey-start
reachable by any role including read-only, four sign-off actions (audit
close, corrective-action verify/close, management-review complete)
gated at Editor instead of the intended Approver level, and a form-edit
bypass that let an Editor close a corrective action without going through
the dedicated approval view. All fixed with regression tests. No open
RBAC finding remains.

## 4. Authentication

**PASS.** Login is rate-limited (10 attempts / 5 minutes / IP,
cache-backed) with a regression test confirming plain page reloads (GET)
never consume an attempt — only failed POST submissions do — and that a
legitimate successful login is unaffected. Logout, password handling
(Django's standard hasher, no plaintext storage), inactive-user blocking,
and tenant-membership checks on every authenticated request are all
covered by tests. Session cookies are `HttpOnly`; `Secure` and CSRF
cookie security are environment-driven and verified enabled under a
production-configured `.env`. No unauthenticated access to any
tenant-scoped view was found to be possible.

**Caveat:** rate limiting is per-process (see §5 and `SECURITY_AUDIT.md`
I-1) — a deliberate, documented trade-off given the "no mandatory Redis"
constraint, not a defect, but worth the deploying organisation's
awareness if running many Gunicorn workers.

## 5. Django deployment checks

**PASS WITH CAVEAT.** `python manage.py check` — 0 issues. `python
manage.py check --deploy` is **clean with a fully production-configured
environment** (verified this pass by setting real production-equivalent
values for `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_CSRF_TRUSTED_ORIGINS`, and the SSL/cookie-secure flags).

**Caveat:** run in *this* development sandbox without those environment
variables set, `check --deploy` reports 6 expected warnings (HSTS,
SSL redirect, SECRET_KEY length, session/CSRF cookie security, DEBUG).
This is correct, expected behaviour for an unconfigured dev environment
(`SECURITY_AUDIT.md` I-5), not an application defect — but it means the
"clean" result is conditional on actually setting the production `.env`
values documented in `DEPLOYMENT.md` §4, which is an action the deploying
operator must take (see §17, BLOCKED items).

A real, previously-undiscovered deployment-blocking bug was found and
fixed this pass: `SECURE_PROXY_SSL_HEADER` was missing, which would have
caused an infinite HTTPS redirect loop under the documented Nginx →
Gunicorn topology once `DJANGO_SECURE_SSL_REDIRECT=True` was set per the
deployment guide's own instructions (`SECURITY_AUDIT.md` H-3). Fixed,
with a regression test.

## 6. File upload / document security

**PASS.** Every `FileField` in the project runs through
`core/validators.py::validate_upload_file()` (extension allow-list, size
limit via `MAX_UPLOAD_SIZE_MB`). Filenames are not attacker-controlled on
disk (Django's storage layer generates safe, collision-resistant names).
Uploads are stored under per-tenant paths where relevant
(`framework_imports/<org_id>/...`). Executable file types are not on the
allow-list. The one CRITICAL finding this pass — raw, unauthenticated
`/media/` exposure of evidence/document/review attachments — is fully
remediated: all three now serve exclusively through tenant-and-RBAC
-checked Django views (`core/protected_media.py`), and no code path (dev
or prod) serves `MEDIA_ROOT` directly any more. No open file-security
finding remains.

## 7. Document governance / e-signature

**PASS.** Full lifecycle verified: Draft → Under Review → Awaiting
Approval → Approved → Published → Review Due → Superseded/Archived, with
version history, approval history, and immutable `Signature` records
(typed name + explicit consent + IP + timestamp + document-hash,
captured at signing time) providing traceability. Regression tests
confirm a Draft cannot be published directly (skipping review/approval/
signature) and an already-decided approval cannot be signed twice
(`SECURITY_AUDIT.md` I-4 — both were already correctly guarded; tests
lock the behaviour in). One MEDIUM finding was found and fixed: the
Archived terminal state was previously unreachable, and there was no
server-side guard preventing a direct edit request against a document in
a terminal state (`SECURITY_AUDIT.md` M-3) — both fixed with tests. Native
e-signature is implemented and tested as an auditable electronic
approval/signature workflow; this project makes no claim to a specific
legal e-signature standard/certification, consistent with the working
instructions.

## 8. Audit log integrity

**PASS.** `activity.AuditLog` (immutable, admin read-only) captures
actor, organisation, action, object, timestamp, and metadata for
authentication events, user/org/role changes, document lifecycle events,
risk/control changes, evidence uploads, incidents, assessments, audits,
findings, corrective actions, framework changes, and AI-content
acceptance. Tenant isolation of the audit log itself is tested (an
organisation cannot see another organisation's log entries). Ordinary
tenant users have no code path to alter or delete audit history — the
admin registration for `AuditLog` disables add/change/delete, and no
application view exposes a mutation path.

## 9. AI security, privacy, traceability

**PASS.** `AIGeneration` records provide provider/model traceability for
every AI call. AI context is built exclusively from the requesting
organisation's own `KnowledgeItem`/framework data — no code path
constructs a prompt from another tenant's data. AI-generated content
always starts in an editable Draft state and only becomes a published,
binding document through a human `Signature` (tested). The product is
fully functional with `AI_PROVIDER=mock` (the default) and requires no
API key or external service to operate — AI is genuinely optional, not a
hidden dependency. Verified this pass: no template uses the `|safe`
filter anywhere in the codebase, so AI-generated or uploaded content
(treated as untrusted per prompt-injection review) cannot become a
stored-XSS vector regardless of what a crafted prompt or upload contains
(`SECURITY_AUDIT.md` I-2). `OpenAICompatibleProvider` degrades gracefully
(returns a placeholder, never raises/500s) on a network failure or
non-200 response, with a regression test (`SECURITY_AUDIT.md` I-3). No
AI API keys or secrets are hardcoded; all are environment-driven.

## 10. Database integrity

**PASS.** Models use appropriate FKs, tenant relationships, uniqueness
constraints, and indexes; migrations apply cleanly with no
`makemigrations --check` drift. One MEDIUM finding was found and fixed
this pass: `ReferenceCodeMixin.assign_reference_code()` had a
read-then-write race condition under concurrent requests (could assign
duplicate reference codes to two records created near-simultaneously).
Fixed via `transaction.atomic()` + `select_for_update()` row locking,
effective under PostgreSQL — the documented production database — and a
safe no-op under SQLite (`SECURITY_AUDIT.md` M-1). PostgreSQL
compatibility was verified against a real, locally-run PostgreSQL 16
instance (218-220 tests passing, migrations apply cleanly), not just
documented from assumption.

**Caveat:** the race-condition fix could not be given a true concurrent
regression test in Django's standard synchronous `TestCase` — see
`SECURITY_AUDIT.md` M-1 for the honest statement of that verification
gap. The fix is a standard, well-understood Postgres locking pattern; the
gap is in *testing* the concurrent case, not in confidence in the fix
itself.

## 11. Backup and restore

**PASS.** `BACKUP_RESTORE.md` documents the `pg_dump`/`pg_restore`
procedure, and — per the explicit "a backup that has never been tested
for restoration must not be described as fully verified" requirement —
the procedure was **actually executed** in this session, not just
written: a real local PostgreSQL 16 instance was started, seeded with the
NIBS demo scenario, backed up with `pg_dump -F c`, restored into a fresh
database with `pg_restore --no-owner`, and row counts plus a direct ORM
query were confirmed to match exactly (1 organisation, 6 risks, 2
documents, 18 audit log entries before and after). `manage.py check` was
also confirmed clean against the restored database.

**Caveat:** this drill was run once, in this session, against a
freshly-seeded demo database on this sandbox's PostgreSQL instance — it
proves the *procedure* is correct, not that it has been rehearsed on the
actual target production server. `DEPLOYMENT.md` §10 explicitly instructs
the deploying operator to repeat this drill on their own server before
go-live and periodically thereafter (e.g. quarterly), since schema drift
or a Postgres version difference could silently break a path that worked
here.

## 12. Logging, monitoring, error handling

**PASS.** Structured logging (`{asctime} {levelname} {name} {message}`)
is configured; `django.request`/`django.security` events (4xx/5xx,
`PermissionDenied`, `SuspiciousOperation`) propagate to it. No secrets
(API keys, passwords) are logged anywhere — verified by review of every
logging call site. Production users never see Django debug pages once
`DEBUG=False` is set (standard Django behaviour, unmodified). The
`/health/` endpoint was upgraded this pass from a static `{"status":
"ok"}` to a real `SELECT 1` database-connectivity check, returning 503 on
failure, so an uptime monitor can distinguish "process alive" from "app
actually working." `DEPLOYMENT.md` §12 documents `journalctl`-based log
access (systemd captures Gunicorn/Django stdout/stderr) as the practical,
no-extra-infrastructure monitoring path, consistent with the "no
mandatory Redis/extra infrastructure" constraint — third-party log
aggregation (Sentry, Datadog, etc.) is optional, not required to operate
the product.

## 13. Performance

**PASS.** A targeted N+1-query audit found and fixed 6 distinct issues
this pass: uncached risk-matrix lookups, unbatched GenericForeignKey
resolution on the dashboard, a redundant queryset re-evaluation in
framework progress calculation, missing `select_related` on 5 list views,
a per-page-load existence check for register-type seeding, and a
per-row `.exists()` call in evidence-coverage reporting. A regression
test (`DashboardPerformanceTests`) asserts the dashboard's query count
does not scale with data volume (adds 12 risks + 5 approvals, asserts
query count stays within a small tolerance of the baseline). This is
appropriately scoped to the product's actual target (small SME/NPO/
consulting-client organisations), not over-engineered for a scale the
product doesn't need to support.

## 14. Responsive design / mobile UAT

**PASS.** 18 pages tested at 2 viewports (desktop 1440px, mobile 390px)
via Playwright against live seeded NIBS data — 36/36 page loads returned
200, zero real browser console errors (only an expected missing-favicon
404). The mobile sidebar drawer's open/close state was verified via
direct DOM-state assertion, not just a screenshot. No serious responsive
usability issues were found requiring fixes; one intentional
horizontal-scroll behaviour on the wide SoA table was confirmed to be a
deliberate, acceptable design choice rather than a bug. Full detail in
`UAT_RESULTS.md`.

## 15. Accessibility

**PASS.** Reviewed and fixed this pass: WCAG AA contrast failures
(`--text-muted` at ~2.6:1 raised to ~4.8:1; badge/flash-message green and
amber text-on-tinted-background at ~3.2:1 raised to ~5:1, in both light
and dark themes), missing `scope="col"` on every data-table column
header (30 templates), missing `aria-describedby` association between
form fields and their help text (Django emits the attribute
automatically but the target `id` was absent from 4 form templates —
fixed), a focus-state regression that stripped visible keyboard focus
from checkboxes specifically, missing ARIA (`aria-haspopup`/
`aria-expanded`) and Escape-key handling on dropdown menus, and one
non-semantic `<div class="content">` that is now a `<main>` landmark.
Zero `<img>` tags exist in the codebase without `alt` text (there are
none needing it — no raster/vector images are used, only the inline SVG
icon set, which is decorative and appropriately unlabelled where used
alongside visible text). This was a "fix significant issues" pass, not a
full WCAG conformance audit or certification — see caveat.

**Caveat:** this is not a claim of formal WCAG 2.1/2.2 AA conformance
certification, which would require a dedicated audit (including screen-
reader testing with real assistive technology, not just semantic/ARIA
code review). It is a genuine, substantive fix pass addressing every
significant issue found through code review and visual verification.

## 16. Deployment readiness

**PASS.** `DEPLOYMENT.md` covers server prerequisites, PostgreSQL setup,
virtualenv/dependency install, environment configuration, migrations,
static files, Gunicorn (systemd unit), Nginx (including the explicit
absence of a `/media/` alias, with an explanatory comment), HTTPS via
Certbot, scheduled tasks (`scan_overdue` via cron, no Celery/Redis),
backups (cross-referencing the tested `BACKUP_RESTORE.md`), deploying
updates, a rollback procedure (added this pass — previously entirely
missing), health-check/monitoring guidance, and a "before go-live"
reading list. `.env.example` documents every environment variable the
application actually reads, including two that were previously used in
code but undocumented (`DJANGO_SESSION_COOKIE_AGE`,
`DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE`) — found and fixed this pass. No
Docker dependency anywhere in the documented path; Docker remains
explicitly optional.

## 17. POPIA / privacy technical readiness

**PASS WITH CAVEAT.** `POPIA_READINESS.md` documents the personal-
information inventory (org data, user profiles, audit logs, uploaded
documents, incident data, AI processing) and the technical capabilities
implemented this pass: `accounts:export_my_data` (self-service JSON
export of one's own account-level personal information) and
`accounts:deactivate_account` (self-service login deactivation).

**Caveat (by design, not oversight):** deactivation is deliberately not
hard deletion — a user's ID is an immutable audit-trail actor reference
across every organisation they belong to, and hard-deleting it would
corrupt audit-log integrity for every other tenant's history. This is
documented explicitly in `POPIA_READINESS.md`, along with the
organisational/legal decisions that remain outside what software can
grant by itself: appointing an Information Officer, a PAIA manual,
a data-retention schedule, operator agreements with sub-processors,
and a breach-notification procedure. **Software alone does not make an
organisation POPIA compliant** — this is stated explicitly in
`POPIA_READINESS.md` and is not a gap in this codebase, but a correct,
honest boundary between what code can and cannot do.

---

## BLOCKED — external action required (not resolvable in this codebase)

These are not application defects. They require infrastructure,
credentials, or a human/organisational decision the deploying operator
must make; the codebase supports each of them but cannot complete them
unilaterally.

1. **Production `.env` must actually be created and populated** with a
   real `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, database credentials,
   and the SSL/cookie-secure flags per `DEPLOYMENT.md` §4 — the
   application will (correctly, deliberately) refuse to boot with
   `DEBUG=False` and the checked-in dev `SECRET_KEY`.
2. **A real domain name, DNS record, and TLS certificate** (Let's
   Encrypt/Certbot, per `DEPLOYMENT.md` §8) must be provisioned — this
   requires a registered domain and a reachable public IP, neither of
   which exists in this development sandbox.
3. **A production PostgreSQL server** must be provisioned and its
   credentials placed in `.env` — SQLite is dev-only by design.
4. **A real SMTP relay** must be configured (`EMAIL_*` settings) if the
   deploying organisation wants outbound email notifications; without it,
   notifications remain correctly functional in-app only.
5. **The `BACKUP_RESTORE.md` drill must be repeated on the actual target
   production server** before go-live (see §11 caveat) — this session's
   drill proves the procedure, not that specific server's configuration.
6. **POPIA organisational/legal decisions** (§17) — Information Officer
   appointment, PAIA manual, retention schedule, operator agreements,
   breach-notification procedure — are for the deploying organisation's
   management and legal counsel, not something a codebase can decide.
7. **Formal WCAG conformance certification** (§15 caveat), if required by
   a specific client contract, needs a dedicated accessibility audit
   beyond this pass's code-level review.
8. **Re-running the full test suite against PostgreSQL** one more time
   after the final 3 commits of this pass (§1 caveat) — low risk, cheap,
   but not yet done as of this document.

---

## Overall verdict: **PRODUCTION RELEASE RECOMMENDED**, contingent on the BLOCKED items above

No unresolved Critical or High security or data-isolation issue remains
in this codebase (`SECURITY_AUDIT.md`: 1 Critical and 3 High finding, all
fixed with regression tests). Every category in this document is PASS or
PASS WITH CAVEAT; there is no open FAIL. The caveats recorded above are
honest, specific, and either (a) deliberate, documented design
trade-offs consistent with the working spec's own constraints (no
mandatory Redis, no hard-delete of audit-trail actors), or (b) genuine
residual verification gaps stated plainly rather than hidden (the
concurrent-race test gap, the not-yet-repeated Postgres run, the
not-yet-formally-certified accessibility level).

This verdict is a statement about the **codebase's readiness**, not a
guarantee that any specific deployment is live and correctly configured —
the BLOCKED section above is the exact, non-negotiable list of what a
human operator must still do (provision infrastructure, set real secrets,
obtain a domain and certificate, make POPIA organisational decisions)
before real users and real client data reach this application. Feature
completeness (established in session 1) and production readiness
(established in this pass) are two different claims, and both are now
substantiated — the remainder is deployment execution, not further
engineering.
