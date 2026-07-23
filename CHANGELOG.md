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
- `frameworks`: framework engine (Framework → Domain → Requirement → AssessmentQuestion → EvidenceExpectation), Framework Studio (upload/paste → AI-assisted extraction → human review → publish), `seed_frameworks` (ISO 27001, POPIA, King IV, SABS ISO 9001 skeletons).
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
