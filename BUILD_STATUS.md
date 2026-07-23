# Bohlale GRC — Build Status

**Last updated:** 2026-07-23 (session 1, mid-build — through `registers`/`audits`/`actions`)
**Branch:** `claude/bohlale-grc-build-nki122`

> Read this file fully before resuming work. Then read `BOHLALE_GRC_MASTER_SPEC.md`, inspect the repo tree, check `git log`, and run `python manage.py test`. Continue from "Exact next recommended task" at the bottom — do not restart completed modules.

## How to resume this build (for the next Claude session)

1. `source .venv/bin/activate` (create venv + `pip install -r requirements.txt` if missing).
2. `python manage.py check` and `python manage.py test` — confirm current state is green before adding more.
3. Read the "Completed modules", "Partially completed", "Incomplete" sections below.
4. Continue module-by-module in spec order. Do not re-do a module marked Completed unless it is demonstrably broken (cite the failing test/behaviour in your commit message if you touch it).
5. Update this file whenever you finish a module or stop, then commit.

---

## Completed modules

- **Foundation**: `config/settings.py` (env-driven, SQLite dev / Postgres prod), design-system CSS + base templates matching the dashboard mockup, htmx vendored locally, self-authored icon set. Reusable tenant-scoped CRUD view bases (`core/base_views.py`) and generic templates (`templates/core/generic_form.html`, `generic_confirm_delete.html`) power every "register-style" app below — this pattern is now proven across 9 apps.
- **accounts**: custom email-based `User` model, login/logout/profile.
- **tenancy**: `Organisation`/`Membership`/`OrganisationInvite`, row-level multi-tenant `TenantMiddleware`, RBAC roles + permission helpers (`core/permissions.py`), org create/list/switch, member invite.
- **activity**: immutable `AuditLog` + `log_activity()` used by every other app. Admin is read-only.
- **notifications**: in-app + email `Notification`, topbar bell, mark-read/mark-all-read.
- **knowledge**: `KnowledgeItem` (Verified/AI Inference/Missing per spec §10), profile view grouped by category, verify action, `verified_context_text()` used as AI context.
- **ai**: `AIProvider` abstraction — `MockProvider` (default, offline, deterministic templated drafts per purpose) and `OpenAICompatibleProvider` (OpenAI- and Qwen-compatible via `AI_API_BASE`). `AIGeneration` governance/traceability model (spec §38). `ai.service.generate()` is the entry point every app uses.
- **frameworks**: `Framework`/`Domain`/`Requirement`/`AssessmentQuestion`/`EvidenceExpectation`, `FrameworkAdoption` + `RequirementStatus` (progress tracking), Framework Studio (upload/paste → heading-detection extraction + AI summary → human-editable JSON review → publish). `seed_frameworks` creates global ISO 27001 / POPIA / King IV / SABS ISO 9001 skeletons (original text only, see Assumption 5).
- **journeys**: Guided implementation engine (spec §8), PDCA stage stepper, full onboarding wizard (spec §7, all 9 goals wired), AI Guided Interview Engine (spec §11), Information Request Engine (spec §12, token-based external responses). `seed_journey_templates` creates a hand-authored 13-step ISO 27001 "Build an ISMS from Scratch" template covering the full §47 demo path.
- **documents + approvals**: Full document lifecycle (spec §14-15): Draft → Under Review → Awaiting Approval → Approved → Published → Superseded/Archived, auto reference codes, content hashing, version snapshots, revision-on-edit-of-published. `generate_draft_for_step()` implements AI Document Generation (spec §13) — this is what the journeys "Generate draft document" button calls. Native e-signature (spec §16): typed full-name signature validated against the approver's profile, mandatory consent, IP/timestamp/version/hash captured immutably. **Verified**: AI drafts always start as Draft and only reach Published through a real human Signature (tested).
- **risks**: `Risk` + configurable `RiskMatrixConfig` (spec §21), auto RISK-0001... codes, `risk_overview()` for the dashboard donut.
- **controls**: `Control` (shared across frameworks — one control maps to many `frameworks.Requirement`, spec §19), `ensure_baseline_controls()` seeds a 17-control common library on first use, Statement of Applicability (`SoAEntry`, spec §24) with CSV export.
- **evidence**: `Evidence` model (spec §23) + `core.validators.validate_upload_file()` (extension allow-list + size limit) now applied to every FileField in the project (Evidence, Document, FrameworkImport).
- **assessments**: `Assessment`/`AssessmentResult` (spec §20, 7 types, 6-value rating scale), `create_assessment_from_framework()` pre-populates one result row per requirement.
- **assets, suppliers**: dedicated registers per spec §28-29.
- **incidents**: `Incident` (spec §25) + `ChangeEvent` (spec §26, all 10 event types) with a suggestion mapping that surfaces "Consider reviewing: ..." register links, then a human marks it reviewed.
- **registers**: unified hub (spec §27) aggregating every register (dedicated + generic), plus a generic `RegisterType`/`RegisterEntry` engine (dynamic form from a JSON `field_schema`) pre-seeded with Interested Parties / Legal & Regulatory / Processing Activities / Training registers — new registers need no migration.
- **audits**: `Audit`/`AuditFinding` (spec §30 lifecycle), open-major-findings count feeds readiness.
- **actions**: `CorrectiveAction` (spec §31) with a generic link back to the source record (audit finding, incident, etc.), `create_from_incident`/`create_from_finding` pre-fill flows, verify & close.

138 tests passing across all of the above. Manually verified end-to-end via dev server: create org → onboarding wizard → ISO 27001 journey → guided interview → Knowledge Profile updated.

## Partially completed modules

- None currently mid-build (see "Exact next recommended task" — `reviews` (management review) is next).

## Incomplete modules

reviews (management review), reports, full dashboard (`core/dashboard.py` is still a stub — needs to assemble the cards shown in the mockup: Implementation Progress, Compliance Overview, Open Actions, Risk Overview, Journey widget, Tasks Due Soon, Upcoming Reviews, Recent Activity, Quick Actions), notifications' scheduled overdue-scan management command (spec §36 — the `Notification` model/views/email exist; the cron-driven scan that *creates* overdue-action/review/evidence-expiry notifications does not exist yet), NIBS demo seed data (`seed_nibs_demo`), `DEPLOYMENT.md`, final requirement-by-requirement audit against the spec.

## Database migrations

All migrations up to and including `registers.0001_initial` are generated and applied cleanly against SQLite. Run `python manage.py showmigrations` to confirm current state; `python manage.py migrate` is safe to re-run.

## Tests

138 tests passing (`python manage.py test`). Coverage per app: model correctness, tenant isolation (cross-org access blocked, verified on every single tenant-scoped app), RBAC (role-gated actions), and at least one full-flow integration test per major workflow (onboarding wizard, AI interview → Knowledge Profile, information request token flow, AI draft → review → approve → sign → publish → journey step auto-complete, SoA auto-seeding, register hub aggregation).

## Known issues

- Sidebar/cross-app links to not-yet-built apps (`reviews:list`, `reports:readiness`, `reports:hub`) currently resolve to `#` via the `safe_url` template tag — expected, not a bug; each starts working the moment that app's `urls.py` defines the matching name.
- `core/dashboard.py` / `templates/core/dashboard.html` are stubs — the full dashboard (spec §34) is deliberately being built last, once every module it aggregates data from exists, per the standard "build the parts, then the summary view" ordering documented in the original task list for this session.
- No scheduled/cron-triggered notification generation yet (evidence expiry, review due dates, overdue actions) — only manually-triggered notifications (e.g. "submitted for approval") exist so far. Needed before `DEPLOYMENT.md`'s crontab example has something real to point at.

## Assumptions made (documented per working instruction #24)

1. **`organisations` + `tenancy` merged into one app (`tenancy`)** — the spec's suggested module list (§40) lists both `organisations` and `tenancy` separately but §5–§7 describe a single coherent concept (Organisation model, membership, roles, onboarding). Splitting them would create an artificial boundary. `tenancy` owns `Organisation`, `Membership`, invites, the tenant middleware, RBAC helpers, and the onboarding entry point (which then hands off to `journeys` for the guided wizard).
2. **`projects` folded into `journeys` as `OrganisationJourney`** — §5's hierarchy mentions "Projects / Management Systems" under Organisation; §9's PDCA journey and §47's demo scenario describe the same concept (an organisation's instance of implementing a framework). Rather than a duplicate `projects` app, `journeys.OrganisationJourney` is the project/management-system instance (e.g. "NIBS — ISO 27001 Implementation").
3. **Multi-tenancy strategy: row-level, shared schema.** Every tenant-scoped model has an `organisation` FK (or inherits `TenantScopedModel`). No django-tenants / schema-per-tenant, no separate databases — keeps SQLite-for-dev / Postgres-for-prod simple and avoids infra the spec explicitly says is not mandatory. Enforcement: `TenantMiddleware` resolves `request.organisation` from session + `Membership`; `core.base_views.TenantQuerysetMixin`/`get_object_or_404_scoped` on every view filters by `request.organisation`; cross-tenant access attempts return 404 (not 403, to avoid confirming record existence to unauthorised tenants). Verified by a tenant-isolation test in every single tenant-scoped app.
4. **Roles are per-membership, not global**, except `Platform Administrator` which is modelled as Django `is_superuser`/`is_staff` (platform staff, not tied to any one organisation). A user can hold different roles in different organisations (e.g. Consultant in one, Contributor in another) via `Membership.role`.
5. **ISO/IEC 27001 and other standards content is NOT reproduced verbatim.** The framework seed data uses original, descriptive summaries of clause/domain structure (e.g. "Context of the Organisation", "Leadership", "Planning") and original guidance text written for this build — never copied text from the copyrighted standard. The seeded common-control-library names (e.g. "Access Control", "Cryptographic Controls") are likewise original category labels, not copied Annex A control text. POPIA is South African legislation (not subject to the same copyright restriction) but content is still written as an original summary, not a verbatim copy of the Act, and the product is explicit that it is not legal advice.
6. **AI provider default is a local, deterministic `MockProvider`** requiring no API key, so the whole product (including the NIBS demo) works fully offline. `AI_PROVIDER=openai_compatible` in `.env` switches to a real OpenAI-compatible HTTP endpoint. A distinct "Qwen adapter" is not separately coded — Qwen's OpenAI-compatible mode (e.g. DashScope) is reached via the same `openai_compatible` provider by pointing `AI_API_BASE` at it. If a genuinely different Qwen wire protocol is required later, add `ai/providers/qwen.py` implementing the same `AIProvider` interface.
7. **PDF export will use print-styled HTML (browser "Print to PDF") plus server-side Excel/CSV (openpyxl)**, not WeasyPrint/wkhtmltopdf, to avoid system-level native dependencies that may not be available on arbitrary VPS targets. Not yet built (`reports` app is pending) — SoA CSV export in `controls` already follows this pattern.
8. **Scheduled/background jobs (notification digests, overdue scans) will run via a Django management command intended for cron**, not Celery/Redis, per §39's "no mandatory Redis/microservices" instruction. Not yet built — see "Known issues".
9. **Electronic sign-off (§16) is natively implemented** as typed-signature + explicit consent checkbox + timestamp + IP + document hash, recorded as an immutable `Signature` record — not integrated with a third-party e-signature provider in v1.
10. **Organisational change-event "AI suggestions" (spec §26) use a deterministic mapping** (`incidents.models.EVENT_TYPE_SUGGESTIONS`) rather than an actual AI call — simpler, free, instant, and just as effective for "which register should I check" given the mapping is small and well-defined. A human still confirms/reviews, matching the spec's intent.
11. **Registers app owns only the registers without a natural dedicated app** (Interested Parties, Legal & Regulatory, Processing Activities, Training). Risk/Asset/Supplier/Incident/Corrective Action/Audit Findings each already have a first-class Django app with real business logic (scoring, lifecycle, generic FKs) — forcing them through the generic engine too would have thrown away that logic. The `registers:hub` page aggregates both kinds so the user experiences one coherent "Registers" section regardless of implementation.

## Exact next recommended task

Build the **`reviews`** app (Management Review, spec §32) next:
1. `ManagementReview` model: organisation FK, framework FK (nullable), meeting_date, attendees (M2M to accounts.User or free text — free text is simpler and matches "attendees" as a list of names, some of whom may not have platform accounts, so prefer a TextField or a simple M2M-to-User plus a free-text "other attendees" field), agenda text, decisions text, approved_by FK, attachments (reuse `core.validators.validate_upload_file`), status (draft/completed).
2. `ManagementReviewInput` — a checklist of required inputs the organisation should cover (spec §32: "guide the organisation through required management-review inputs for the selected management system"). Model this as a small fixed list of input categories (e.g. "Status of actions from previous reviews", "Changes in external/internal issues", "Information security performance incl. nonconformities and corrective actions, monitoring/measurement results, audit results, achievement of objectives", "Feedback from interested parties", "Results of risk assessment and status of risk treatment plan", "Opportunities for continual improvement") with a boolean "covered" flag + notes per review — a through-model `ManagementReviewInputRecord(review FK, label, covered bool, notes)`, seeded automatically when a review is created (mirrors how `create_assessment_from_framework` pre-populates rows).
3. Link decisions to `actions.CorrectiveAction` via the same generic-source pattern already used by audits/incidents (`actions.views.create_from_source`-style helper — consider factoring `_create_from_source` out of `actions/views.py` into `actions/services.py` if reused a third time).
4. CRUD views following the established `core.base_views` pattern; a `reviews:list` landing URL (sidebar doesn't show Reviews directly per the mockup, but the journeys "management_review" step_type already links to `reviews:list` via `safe_url` in `journey_home.html` — wire that name).
5. Tests: input checklist auto-seeding, tenant isolation, decision-to-action linking.

After reviews: **reports** (spec §35 — Executive Compliance Summary, Gap Assessment Report, Risk Register, Risk Treatment Plan, SoA export, Policy Register, Incident Register, Audit Report, Corrective Action Report, Audit Readiness Report, Framework Compliance Report; PDF via print-styled view, Excel via openpyxl per Assumption 7) → **full dashboard** (`core/dashboard.py`, wire every module's data into the mockup's cards — this is where `risks.services.risk_overview`, `frameworks.services.framework_progress`, `controls.services.soa_coverage`, overdue counts across documents/actions/evidence all get assembled) → **notifications cron command** (overdue scan) → **NIBS demo seed** (`seed_nibs_demo` management command walking the full §47 scenario with fictional data) → **final audit**: run full test suite, `manage.py check`, verify migrations, re-verify tenant isolation and RBAC spot-checks, verify the NIBS demo end-to-end in a live dev server, then update `BUILD_STATUS.md`/`README.md`/`CHANGELOG.md` and write `DEPLOYMENT.md` (Gunicorn + Nginx + Postgres, no Docker, per spec §41).
