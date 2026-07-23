# Bohlale GRC — Build Status

**Last updated:** 2026-07-23 (session 1, foundation)
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

_(none yet — foundation session in progress)_

## Partially completed modules

- **Repository scaffolding** — `BOHLALE_GRC_MASTER_SPEC.md`, `BUILD_STATUS.md`, `README.md`, `CHANGELOG.md`, `.env.example` created. Django project (`config`) and 23 apps scaffolded via `startapp` (empty boilerplate only, not yet wired into `INSTALLED_APPS` or built out).

## Incomplete modules

Everything else in the spec: settings/design system, accounts, tenancy/RBAC, activity/audit log, notifications, knowledge profile, AI service layer, frameworks engine + Framework Studio, journeys/guided implementation/onboarding/interview/info-request engine, documents + approvals (e-signature), risks, controls + SoA, evidence, assessments, assets, suppliers, incidents + change events, registers, audits, actions (corrective actions), reviews (management review), reports, dashboard UI, NIBS demo seed data, test suite, deployment docs.

## Database migrations

None generated yet (no models written).

## Tests

None written yet. Target: every app ships model tests + tenant-isolation tests + permission tests + at least one view smoke test.

## Known issues

None yet.

## Assumptions made (documented per working instruction #24)

1. **`organisations` + `tenancy` merged into one app (`tenancy`)** — the spec's suggested module list (§40) lists both `organisations` and `tenancy` separately but §5–§7 describe a single coherent concept (Organisation model, membership, roles, onboarding). Splitting them would create an artificial boundary. `tenancy` owns `Organisation`, `Membership`, invites, the tenant middleware, RBAC helpers, and the onboarding entry point (which then hands off to `journeys` for the guided wizard).
2. **`projects` folded into `journeys` as `OrganisationJourney`** — §5's hierarchy mentions "Projects / Management Systems" under Organisation; §9's PDCA journey and §47's demo scenario describe the same concept (an organisation's instance of implementing a framework). Rather than a duplicate `projects` app, `journeys.OrganisationJourney` is the project/management-system instance (e.g. "NIBS — ISO 27001 Implementation").
3. **Multi-tenancy strategy: row-level, shared schema.** Every tenant-scoped model has an `organisation` FK (or inherits `TenantScopedModel`). No django-tenants / schema-per-tenant, no separate databases — keeps SQLite-for-dev / Postgres-for-prod simple and avoids infra the spec explicitly says is not mandatory. Enforcement: `TenantMiddleware` resolves `request.organisation` from session + `Membership`; a `TenantRequiredMixin` / `OrgQuerysetMixin` on all list/detail views filters by `request.organisation`; cross-tenant access attempts return 404 (not 403, to avoid confirming record existence to unauthorised tenants).
4. **Roles are per-membership, not global**, except `Platform Administrator` which is modelled as Django `is_superuser`/`is_staff` (platform staff, not tied to any one organisation). A user can hold different roles in different organisations (e.g. Consultant in one, Contributor in another) via `Membership.role`.
5. **ISO/IEC 27001 and other standards content is NOT reproduced verbatim.** The framework seed data uses original, descriptive summaries of clause/domain structure (e.g. "Context of the Organisation", "Leadership", "Planning") and original guidance text written for this build — never copied text from the copyrighted standard. POPIA is South African legislation (not subject to the same copyright restriction) but content is still written as original summaries/guidance, not a verbatim copy of the Act, and the product is explicit that it is not legal advice.
6. **AI provider default is a local, deterministic `MockProvider`** requiring no API key, so the whole product (including the NIBS demo) works fully offline. `AI_PROVIDER=openai_compatible` in `.env` switches to a real OpenAI-compatible HTTP endpoint. A distinct "Qwen adapter" is not separately coded — Qwen's OpenAI-compatible mode (e.g. DashScope) is reached via the same `openai_compatible` provider by pointing `AI_API_BASE` at it, per §37's own diagram showing both as sibling adapters behind one interface shape. If a genuinely different Qwen wire protocol is required later, add `ai/providers/qwen.py` implementing the same `AIProvider` interface — the abstraction already supports this without touching call sites.
7. **PDF export uses print-styled HTML (browser "Print to PDF") plus server-side Excel/CSV (openpyxl)**, not WeasyPrint/wkhtmltopdf, to avoid system-level native dependencies that may not be available on arbitrary VPS targets without extra apt packages. Documented as a v1 limitation; `reports/` includes a `?format=print` view styled for clean PDF output via the browser print dialog.
8. **Scheduled/background jobs (notification digests, overdue scans) run via a Django management command intended for cron**, not Celery/Redis, per §39's "no mandatory Redis/microservices" instruction. Documented in `DEPLOYMENT.md` with a sample crontab line.
9. **Electronic sign-off (§16) is natively implemented** as typed-signature + explicit consent checkbox + timestamp + IP + document hash, recorded as an immutable `Signature` record — not integrated with a third-party e-signature provider in v1. The `approvals` app is structured so a provider adapter could be added later without schema changes to the approval workflow itself.

## Exact next recommended task

Proceed with **Task: Core project settings & design system** (config/settings.py env-driven config; base template + CSS design system matching the provided dashboard mockup; vendor htmx.js locally under static/). Then **accounts** (custom User) and **tenancy** (Organisation/Membership/middleware/RBAC) — these three are foundational and everything else depends on them. Continue strictly in the module order listed in the task list maintained for this build (see commit history / this file's "Completed modules" section as it grows) — do not skip ahead into UI-heavy modules before tenancy + RBAC + audit logging exist, since every later app depends on `TenantScopedModel`, `log_activity()`, and the base templates.
