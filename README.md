# Bohlale GRC

Bohlale GRC is a multi-tenant Governance, Risk & Compliance platform built for South African SMEs, NPOs, NGOs and the consultants who serve them. It combines guided ISO/POPIA implementation, policy management, risk & control registers, evidence management and audit readiness in one Django application.

See `BOHLALE_GRC_MASTER_SPEC.md` for the full product specification and `BUILD_STATUS.md` for the current build state (what's done, what's next — read this first if you are resuming work on the project).

## Tech stack

- Python 3.11 / Django 5.2
- HTMX + vanilla CSS (no Node build pipeline)
- SQLite for local development, PostgreSQL-ready for production
- No Docker, no Redis, no Celery — a plain Django modular monolith deployable with Gunicorn + Nginx on any Linux VPS

## Local development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env if needed — defaults work out of the box with SQLite

python manage.py migrate
python manage.py seed_nibs_demo   # creates fictional NIBS demo tenant + sample data
python manage.py runserver
```

Visit http://127.0.0.1:8000/ and log in with the demo credentials printed by `seed_nibs_demo` (see command output / `BUILD_STATUS.md`).

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

See `DEPLOYMENT.md` for the full VPS deployment guide (Nginx + Gunicorn + PostgreSQL, no Docker).

## Demonstration data

The `seed_nibs_demo` management command creates a fictional demonstration tenant, **NIBS (Naleli Innovators Business School)**, and walks it through the ISO 27001 implementation journey described in the spec (§47). All data is fictional/sample data — no real client, employee or operational information is used anywhere in this repository.

## License / status

Internal product build in active development. Not yet released.
