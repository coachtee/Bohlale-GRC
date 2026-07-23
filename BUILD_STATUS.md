# Bohlale GRC — Build Status

**Last updated:** 2026-07-23 (session 1, mid-build — through `journeys` app)
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

- **Foundation**: `config/settings.py` (env-driven, SQLite dev / Postgres prod), design-system CSS + base templates matching the dashboard mockup, htmx vendored locally, self-authored icon set.
- **accounts**: custom email-based `User` model, login/logout/profile. Tests: login success/failure, display name/initials.
- **tenancy**: `Organisation`/`Membership`/`OrganisationInvite` models, row-level multi-tenant `TenantMiddleware`, RBAC roles + permission helpers (`core/permissions.py`), org create/list/switch, member invite. Tests cover tenant isolation (cross-org access returns 404) and RBAC (read-only can't invite).
- **activity**: immutable `AuditLog` + `log_activity()` used by every other app. Admin is read-only.
- **notifications**: in-app + email `Notification`, topbar bell, mark-read/mark-all-read.
- **knowledge**: `KnowledgeItem` (Verified/AI Inference/Missing per spec §10), profile view grouped by category, verify action, `verified_context_text()` used as AI context.
- **ai**: `AIProvider` abstraction — `MockProvider` (default, offline, deterministic templated drafts per purpose) and `OpenAICompatibleProvider` (works with OpenAI- and Qwen-compatible endpoints via `AI_API_BASE`). `AIGeneration` governance/traceability model (spec §38). `ai.service.generate()` is the single entry point every app uses.
- **frameworks**: `Framework`/`Domain`/`Requirement`/`AssessmentQuestion`/`EvidenceExpectation`, `FrameworkAdoption` + `RequirementStatus` (progress tracking), Framework Studio (upload/paste → heading-detection extraction + AI summary → human-editable JSON review → publish). `seed_frameworks` management command creates global ISO 27001 / POPIA / King IV / SABS ISO 9001 skeletons (original text only, see Assumption 5).
- **journeys**: `JourneyTemplate`/`JourneyStep` (guided implementation engine, spec §8), `OrganisationJourney`/`StepProgress` (the "project" per Assumption 2) with auto-advancing current step and a PDCA stage stepper (`stage_summary()`). Full onboarding wizard (spec §7, all 9 goal options wired). AI Guided Interview Engine (spec §11) — per-step question sequence writing VERIFIED facts to the Knowledge Profile. Information Request Engine (spec §12) — in-app assignment to members, or secure single-use token link for external recipients, feeding AI-Inference facts. `seed_journey_templates` creates a hand-authored 13-step ISO 27001 "Build an ISMS from Scratch" template covering the full §47 demo path, plus auto-generated templates for the other 3 built-in frameworks.
  - Manually verified end-to-end via dev server: create org → onboarding wizard → ISO 27001 journey → guided interview → Knowledge Profile updated.
  - Not yet wired: the "document" step_type's "Generate draft document" button (`documents:generate_for_step`) — depends on the `documents` app, in progress now.

## Partially completed modules

- None currently mid-build (see "Exact next recommended task" — `documents` + `approvals` are next).

## Incomplete modules

documents, approvals, risks, controls (+ SoA), evidence, assessments, assets, suppliers, incidents (+ change events), registers, audits, actions (corrective actions), reviews (management review), reports, full dashboard (`core/dashboard.py` is still a stub), NIBS demo seed data (`seed_nibs_demo`), deployment docs (`DEPLOYMENT.md`), final requirement-by-requirement audit.

## Database migrations

All migrations up to and including `journeys.0001_initial` are generated and applied cleanly against SQLite. Run `python manage.py showmigrations` to confirm current state; `python manage.py migrate` is safe to re-run.

## Tests

56 tests passing (`python manage.py test`) across accounts, tenancy, activity, notifications, knowledge, ai, frameworks, journeys. Coverage focus per app: model correctness, tenant isolation (cross-org access blocked), RBAC (role-gated actions), and at least one full-flow integration test (onboarding wizard, interview flow, information request flow).

## Known issues

- `journeys/templates/journeys/journey_home.html`'s "Generate draft document" action link (`documents:generate_for_step`) resolves to `#` until the `documents` app is built (uses `safe_url` so it degrades gracefully rather than 500ing).
- Sidebar nav links for not-yet-built apps (risks, controls, evidence, incidents, registers, audits, actions, reports) currently resolve to `#` via the same `safe_url` mechanism — expected, not a bug; each will start working the moment that app's urls.py defines the matching name (see per-app "Exact next recommended task" convention: use `list`/`hub` as the primary landing URL name).

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

Build the **`documents` + `approvals` apps** next (spec §13–§16):
1. `documents.Document` / `documents.DocumentVersion` models — fields per spec §14 (title, doc_type, reference_number, version, owner, author, approver, dates, classification, status: Draft/Under Review/Awaiting Approval/Approved/Published/Superseded/Archived, M2M to frameworks/requirements/controls/risks/incidents, file attachment).
2. `documents:generate_for_step` view — the glue journeys already links to (`journeys/templates/journeys/journey_home.html` calls `safe_url 'documents:generate_for_step' focus_step.pk`): takes a `journeys.JourneyStep`, builds an AI prompt from `knowledge.services.verified_context_text(org)` + the step's guidance, calls `ai.service.generate(purpose="isms_scope"` or `"document_draft"`, ...)`, creates a Draft `Document` with the AI output as content, links `ai.AIGeneration.related_object` to it, and redirects into the document review UI.
3. `approvals.ApprovalRequest` / `approvals.Signature` — native e-signature workflow per spec §16 (typed signature + consent checkbox + timestamp + IP + document hash + audit event). Wire Document status transitions: Draft → Under Review → Awaiting Approval → Approved (via Signature) → Published.
4. Once published, call `journeys.services.mark_step_complete(...)` (or leave the user to click "Mark step complete" — either is fine, but document the choice) so the ISMS Scope / Information Security Policy steps in the ISO 27001 demo journey actually close the loop end-to-end per §47.
5. Tests: version history, status transitions, tenant isolation, e-signature immutability (a Signature/AIGeneration record must never be editable after creation), and — important — confirm AI-generated content never auto-transitions to Approved/Published without a human `Signature`.

After documents+approvals: risks → controls (+SoA) → evidence → assessments → assets/suppliers → incidents (+change events) → registers → audits → actions → reviews → reports → full dashboard → NIBS demo seed → final audit. This order matches the task list maintained for this build session; each app's sidebar link in `templates/core/_sidebar.html` already points at the URL name it should expose (e.g. `risks:list`, `controls:soa` referenced from `journey_home.html`, `reports:readiness`) — use those exact names so links that are currently `#` start resolving automatically.
