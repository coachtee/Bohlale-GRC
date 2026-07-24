# Bohlale GRC

Bohlale GRC is a multi-tenant Governance, Risk & Compliance platform built for South African SMEs, NPOs, NGOs and the consultants who serve them. It combines guided ISO/POPIA implementation, policy management, risk & control registers, evidence management and audit readiness in one Django application.

See `BOHLALE_GRC_MASTER_SPEC.md` for the full product specification and `BUILD_STATUS.md` for the current build state (what's done, what's next — read this first if you are resuming work on the project).

## Tech stack

- Python 3.11 / Django 5.2
- HTMX + vanilla CSS (no Node build pipeline)
- SQLite for local development, PostgreSQL for production
- No Redis, no Celery — a plain Django modular monolith. Deployable directly on a Linux VPS (Gunicorn + Nginx + systemd) or via Docker (`sudo ./deployment/install.sh`) — Docker is available, never required

## Local development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env if needed — defaults work out of the box with SQLite

python manage.py migrate
python manage.py seed_frameworks  # seeds the built-in Framework Library (idempotent)
python manage.py seed_nibs_demo   # creates fictional NIBS demo tenant + sample data (also seeds frameworks itself)
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and log in with the demo credentials printed by `seed_nibs_demo` (see command output / `BUILD_STATUS.md`).

`seed_frameworks` seeds the Framework Library — ISO/IEC 27001:2022, ISO/IEC 27701, POPIA, PAIA, ISO 22301, ISO 9001, ISO 31000, NIST Cybersecurity Framework, CIS Controls v8 and King IV — independently of the demo data, so it's the one step every real deployment needs even without `seed_nibs_demo`. It also runs automatically on every Docker container start (`entrypoint.sh`) and is a documented step in `DEPLOYMENT.md` for the non-Docker path.

## Running tests

```bash
python manage.py test
```

## Project layout

Bohlale GRC is a **Django modular monolith**. Each business capability from the spec is its own Django app under one project (`config`):

`core`, `accounts`, `tenancy`, `activity`, `notifications`, `knowledge`, `ai`, `frameworks`, `journeys`, `documents`, `approvals`, `assessments`, `risks`, `controls`, `evidence`, `assets`, `suppliers`, `incidents`, `registers`, `audits`, `actions`, `reviews`, `reports`.

Two deliberate consolidations vs. the spec's suggested module list are documented in `BUILD_STATUS.md` → Assumptions (the `organisations` concept lives inside `tenancy`, and `projects`/management-system instances live inside `journeys` as `OrganisationJourney`).

## Multi-tenancy model

Row-level multi-tenancy: every tenant-scoped model carries an `organisation` foreign key. A `TenantMiddleware` resolves the active organisation from the session against the signed-in user's `Membership` records and attaches it to the request. All querysets in views are explicitly filtered by `request.organisation`; there is no cross-tenant default-manager leakage. See `tenancy/` and the tenant-isolation tests in each app's `tests.py`.

## AI architecture

AI features are provider-independent (`ai/` app). A `MockProvider` is enabled by default so the whole product works fully offline/without any API key. Set `AI_PROVIDER=openai_compatible` plus `AI_API_BASE` / `AI_API_KEY` / `AI_MODEL` in `.env` to use a real OpenAI-compatible or Qwen-compatible (OpenAI-compatible mode) endpoint. Every AI generation is logged to `ai.AIGeneration` for traceability and always requires human review before becoming approved/published content.

## Deployment

Two fully supported paths:

- **VPS, no Docker**: see `DEPLOYMENT.md` (Nginx + Gunicorn + systemd + PostgreSQL directly on the host).
- **Docker**: `sudo ./deployment/install.sh` — one command builds the image, starts PostgreSQL and the app, and waits for it to report healthy. See `deployment/README.md` for the full guide (install, update, backup, restore, rollback, health-check). The same `Dockerfile`/`compose.yml`/`deployment/` toolkit is written generically enough to reuse for other Django projects (Bohlale Learn, Health, Notes, ...) — see the "Reusing this toolkit" section of `deployment/README.md`.

## Production readiness & security

This codebase has been through a dedicated production-readiness and
security-hardening pass (branch `claude/production-readiness-v1`), on top
of the feature-complete build. Start here before deploying:

- **`PRODUCTION_READINESS.md`** — the release gate: a category-by-category
  PASS / PASS WITH CAVEAT / FAIL / BLOCKED assessment (tests, tenant
  isolation, RBAC, security, backups, performance, accessibility, and
  more), plus the exact external actions (real secrets, domain/TLS,
  production database) a deploying operator must still complete.
- **`SECURITY_AUDIT.md`** — every security finding from that pass,
  classified CRITICAL/HIGH/MEDIUM/LOW/INFORMATIONAL with reproduction
  steps, remediation, and regression-test status.
- **`BACKUP_RESTORE.md`** — a PostgreSQL backup/restore procedure that was
  actually executed and verified in this repository, not just documented.
- **`POPIA_READINESS.md`** — what the software does and does not do for
  POPIA compliance (software alone cannot make an organisation compliant).
- **`UAT_PLAN.md`** / **`UAT_RESULTS.md`** — the full NIBS end-to-end
  acceptance scenario and its results.

## Demonstration data

The `seed_nibs_demo` management command creates a fictional demonstration tenant, **NIBS (Naleli Innovators Business School)**, and walks it through the ISO 27001 implementation journey described in the spec (§47). All data is fictional/sample data — no real client, employee or operational information is used anywhere in this repository.

## License / status

Internal product build in active development. Not yet released.
