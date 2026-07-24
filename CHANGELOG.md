# Changelog

All notable changes to Bohlale GRC are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

**Foundation**
- Repository scaffolding: `BOHLALE_GRC_MASTER_SPEC.md`, `BUILD_STATUS.md`, `README.md`, `CHANGELOG.md`, `.env.example`, `DEPLOYMENT.md`.
- Django project scaffold (`config`) with 22 business-capability apps plus `core`/`accounts`/`tenancy`/`activity` foundation, per the spec's suggested module list (§40).
- Design system CSS matching the Bohlale monochrome mockup, base templates, locally-vendored htmx, self-authored SVG icon set. Reusable tenant-scoped CRUD view bases with built-in RBAC and audit logging (`core/base_views.py`).

**Identity, tenancy & governance**
- `accounts`: custom email-based `User` model, authentication, profile.
- `tenancy`: `Organisation`/`Membership`/`OrganisationInvite`, row-level multi-tenant `TenantMiddleware`, RBAC roles and permission helpers, organisation create/list/switch, member invitation.
- `activity`: immutable `AuditLog` and `log_activity()` used across the whole platform.
- `notifications`: in-app + email notifications, topbar bell, mark-read; `scan_overdue` cron-intended management command covering overdue actions, document reviews, evidence expiry, risk reviews, and (added in the final audit pass) audit dates; new-incident and audit-assignment notifications sent immediately.

**Knowledge & AI**
- `knowledge`: Organisation Knowledge Profile with Verified / AI Inference / Missing classification.
- `ai`: provider-independent AI abstraction (`MockProvider` default/offline, `OpenAICompatibleProvider` for real or Qwen-compatible endpoints), `AIGeneration` governance/traceability record.

**Frameworks & guided implementation**
- `frameworks`: framework engine (Framework → Domain → Requirement → AssessmentQuestion → EvidenceExpectation), Framework Library (category-grouped browse UI, South African Compliance pinned first, Create Framework Manually, empty states) alongside Framework Studio (upload/paste → AI-assisted extraction → human review → publish), Model CISO Assistant panel (explain control / suggest evidence / draft guidance). `seed_frameworks` seeds 10 built-in frameworks — ISO/IEC 27001:2022, ISO/IEC 27701, POPIA, PAIA, ISO 22301, SABS ISO 9001, ISO 31000, NIST CSF, CIS Controls v8, King IV — auto-run on every deployment.
- `journeys`: Guided Implementation Engine, PDCA stage stepper, full 9-goal onboarding wizard, AI Guided Interview Engine, Information Request Engine (secure token-based external responses), `seed_journey_templates` (13-step ISO 27001 "Build an ISMS from Scratch" template).

**Documents & policy management**
- `documents` + `approvals`: full document lifecycle (Draft → Under Review → Awaiting Approval → Approved → Published → Superseded/Archived) with version history, content hashing, AI Document Generation, and native electronic sign-off (typed signature, consent, IP/timestamp/hash).

**Risk, controls & evidence**
- `risks`: configurable risk register and risk matrix.
- `controls`: common control library shared across frameworks, Statement of Applicability with CSV export.
- `evidence`: evidence records with secure file-upload validation (extension allow-list + size limit), applied project-wide.
- `assessments`: gap/baseline/maturity/compliance/readiness/internal-control/custom assessments.

**Operational registers**
- `assets`, `suppliers`: dedicated registers.
- `incidents`: incident reporting plus 10-type organisational change events with register-review suggestions.
- `registers`: unified register hub aggregating dedicated and generic registers (Interested Parties, Legal & Regulatory, Processing Activities, Training, plus filtered Data Breach and Audit Findings views).

**Audit lifecycle & continual improvement**
- `audits`: audit planning through closure, findings, open-major-findings tracking.
- `actions`: corrective actions with generic source linking (audit findings, incidents, management reviews).
- `reviews`: management review with auto-seeded required-inputs checklist.
- `reports`: 11 export-ready reports (Excel via openpyxl, PDF via print-styled HTML).

**Dashboard & demonstration data**
- Full dashboard matching the reference mockup: stat cards, implementation journey stepper, quick actions, tasks/reviews/activity panels, pure-CSS donut charts.
- `seed_nibs_demo`: idempotent end-to-end fictional demonstration walkthrough (spec §47) covering the full NIBS reference scenario from organisation creation through audit readiness.

**Security hardening (final audit pass)**
- Cache-based rate limiting (`core/ratelimit.py`) applied to login and the public information-request response endpoint.
- New-incident and audit-scheduling notifications closing the last gaps in spec §36's notification-trigger list.

### Fixed
- Oversized unconstrained SVG icons outside `.nav-link` context (missing base `.nav-icon` sizing rule).
- CSS Grid layout collapse caused by `.sidebar-backdrop` being grid-auto-placed into column 1 on desktop viewports.
- Sidebar "Dashboard" link showing as permanently active due to an overly broad `nav_active` prefix match.
- `User.__str__` leaking raw email addresses into the UI (owner/actor/approver fields across ~28 templates); now renders the display name only, with `UserAdmin` still showing email separately in Django admin.
- Missing Recent Activity entries for demo-seeded data (`log_activity()` now accepts an explicit `actor` for non-request contexts, used throughout `seed_nibs_demo`).

172 tests passing (`python manage.py test`). See `BUILD_STATUS.md` for full build state, documented assumptions, and the final-audit findings.

## Production readiness, security hardening & UAT pass

A dedicated pass (branch `claude/production-readiness-v1`) taking the
feature-complete build above through security hardening, tenant-isolation
and RBAC verification, UAT, accessibility, and deployment-readiness work.
Full detail in `SECURITY_AUDIT.md` and `PRODUCTION_READINESS.md`.

### Security
- **Critical**: uploaded evidence/document/management-review attachments
  were served from an unauthenticated `/media/` URL with no tenant check
  — replaced with tenant-and-RBAC-checked download views
  (`core/protected_media.py`); raw media serving removed entirely.
- **High**: fixed 5 cross-tenant IDOR gaps in form field querysets
  (risk/control/evidence/audit-finding/document forms accepting another
  organisation's requirement/framework primary keys).
- **High**: closed 4 RBAC gaps where journey-start and sign-off actions
  (audit close, corrective-action verify/close, management-review
  complete) were reachable at a lower privilege level than intended, plus
  a form-edit bypass around the corrective-action approval gate.
- **High**: added the missing `SECURE_PROXY_SSL_HEADER` setting — the
  documented Nginx/Gunicorn deployment would otherwise HTTPS-redirect-loop
  once TLS was enabled.
- **Medium**: fixed a reference-code assignment race condition
  (`transaction.atomic()` + `select_for_update()`), an incident-reporting
  notification gap that could reach nobody in realistic small-org
  staffing, an unreachable document Archived state with no server-side
  edit guard, and added organisation member role-change/removal
  (previously invite-only, no way to revoke access).
- New `core/middleware.py::SecurityHeadersMiddleware` (Content-Security-
  Policy, Permissions-Policy); every inline `onclick`/`onchange`/
  `onsubmit` handler replaced with CSP-safe `data-*` attributes.
  `SECRET_KEY` insecure-default now refuses to boot with `DEBUG=False`.

### Added
- POPIA self-service capabilities: `accounts:export_my_data`,
  `accounts:deactivate_account`; `POPIA_READINESS.md`.
- `BACKUP_RESTORE.md` — a PostgreSQL backup/restore procedure that was
  actually executed against a real PostgreSQL 16 instance and verified
  (row counts and content matched exactly after restore).
- `/health/` upgraded from a static response to a real `SELECT 1`
  database-connectivity check.
- `core/tests_uat.py` — a 22-step, 3-persona, real-HTTP end-to-end UAT
  walkthrough of the full NIBS reference scenario, asserting persisted
  business outcomes, not just HTTP status codes. `UAT_PLAN.md` /
  `UAT_RESULTS.md`.
- A small Bohlale visual identity (infinity-mark icon, completion panels,
  a loading indicator) introduced at onboarding/journey-completion
  moments only — the dashboard stays professional and monochrome.
- Accessibility fixes: WCAG AA contrast corrections, `scope="col"` on
  every data table, `aria-describedby` form help-text association,
  visible focus states on all interactive elements including checkboxes,
  ARIA/Escape-key handling on dropdown menus.
- `DEPLOYMENT.md`: rollback procedure, reverse-proxy trust notes,
  `/health/` monitoring guidance, a "before go-live" reading list.
- `SECURITY_AUDIT.md`, `PRODUCTION_READINESS.md`.

### Fixed
- N+1 queries in the risk matrix, dashboard (GenericForeignKey
  resolution), framework progress calculation, and 5 list views.
- A completed guided-implementation journey kept displaying step 1 as
  "current" instead of a completion state, and vanished from the
  dashboard entirely once its status became "completed" rather than
  "in progress."
- The topbar Help link pointed at an unrelated third-party documentation
  site instead of Bohlale support.

226 tests passing (up from 172 at the start of this pass), verified
against both SQLite and a real PostgreSQL 16 instance. `manage.py check`
and `manage.py check --deploy` (with production-equivalent environment
variables) both clean. See `PRODUCTION_READINESS.md` for the full release
gate assessment.
