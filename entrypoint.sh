#!/usr/bin/env bash
#
# Generic container entrypoint for a Django project. Runs before every
# container start (the web server, and any one-off `docker compose run`
# management command alike):
#
#   1. wait for the database to accept connections (Postgres only)
#   2. refuse to start if any model has changed without a matching migration
#   3. run migrations
#   4. seed the built-in Framework Library, if this project has one
#   5. collect static files (for WhiteNoise)
#   6. optionally create a superuser from env vars, if one doesn't exist
#   7. exec the container's CMD (gunicorn by default)
#
# Nothing here is specific to Bohlale GRC - it only relies on `manage.py`
# existing at /app and on the DB_* / DJANGO_SUPERUSER_* env var convention,
# so this file can be reused unchanged by other Django projects. Step 4
# specifically checks the `seed_frameworks` management command actually
# exists before calling it, so this stays true for a project (Bohlale
# Learn/Health/Notes) that doesn't have one - it's skipped, not an error.
#
# Step 2 exists because of a real incident: a model field was widened
# (max_length 40 -> 255) directly on `main` without running
# `makemigrations`, so the live Postgres column stayed at varchar(40).
# `migrate` itself didn't fail - it had nothing new to apply - so the
# container sailed past it and only crashed later, deep inside
# `seed_frameworks`, the first command to actually try inserting a value
# over 40 characters. That crash happened *before* gunicorn ever
# `exec`'d, so the container never bound to its port and looked
# identical to a hung/unreachable-database failure from the outside.
# This step catches that whole class of drift immediately, with an
# unambiguous message, before any data-writing command runs.
#
# Each step can be individually disabled via env vars for special cases
# (e.g. running a one-off shell without re-running migrations):
#   RUN_MIGRATIONS=false
#   CHECK_MIGRATION_DRIFT=false
#   SEED_FRAMEWORK_LIBRARY=false
#   RUN_COLLECTSTATIC=false
#   WAIT_FOR_DB=false

set -euo pipefail

log() {
    printf '[entrypoint] %s\n' "$1"
}

RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
CHECK_MIGRATION_DRIFT="${CHECK_MIGRATION_DRIFT:-true}"
SEED_FRAMEWORK_LIBRARY="${SEED_FRAMEWORK_LIBRARY:-true}"
RUN_COLLECTSTATIC="${RUN_COLLECTSTATIC:-true}"
WAIT_FOR_DB="${WAIT_FOR_DB:-true}"
DB_WAIT_TIMEOUT="${DB_WAIT_TIMEOUT:-60}"

wait_for_postgres() {
    if [ "$WAIT_FOR_DB" != "true" ]; then
        log "WAIT_FOR_DB=false - skipping DB wait."
        return 0
    fi
    if [ "${DB_ENGINE:-sqlite}" != "postgres" ]; then
        log "DB_ENGINE is not 'postgres' (got '${DB_ENGINE:-sqlite}') - skipping DB wait."
        return 0
    fi

    log "Waiting for PostgreSQL at ${DB_HOST:-localhost}:${DB_PORT:-5432} (timeout: ${DB_WAIT_TIMEOUT}s)..."

    local waited=0
    until python - <<'PYEOF'
import os
import sys

import psycopg2

try:
    psycopg2.connect(
        dbname=os.environ.get("DB_NAME", "postgres"),
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", ""),
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "5432"),
        connect_timeout=3,
    ).close()
except psycopg2.OperationalError as exc:
    print(f"not ready: {exc}".strip(), file=sys.stderr)
    sys.exit(1)
PYEOF
    do
        waited=$((waited + 2))
        if [ "$waited" -ge "$DB_WAIT_TIMEOUT" ]; then
            log "ERROR: PostgreSQL did not become ready within ${DB_WAIT_TIMEOUT}s. Giving up."
            exit 1
        fi
        sleep 2
    done

    log "PostgreSQL is ready."
}

check_migration_drift() {
    if [ "$CHECK_MIGRATION_DRIFT" != "true" ]; then
        log "CHECK_MIGRATION_DRIFT=false - skipping migration-drift check."
        return 0
    fi
    log "Checking for model changes missing a migration..."
    if ! python manage.py makemigrations --check --dry-run --noinput >/tmp/migration_drift_check.log 2>&1; then
        log "FATAL: one or more models have changed without a matching migration."
        cat /tmp/migration_drift_check.log
        log "This container will NOT start. A model was edited (directly or via a"
        log "hand-made commit) without running 'python manage.py makemigrations'"
        log "afterward, so the code and the database schema have drifted apart -"
        log "starting anyway risks a hard crash the first time mismatched data is"
        log "written (as happened in production), or silent data truncation."
        log "Fix: run 'python manage.py makemigrations' locally, commit the"
        log "generated migration file(s), and redeploy."
        exit 1
    fi
    log "No migration drift detected."
}

run_migrations() {
    if [ "$RUN_MIGRATIONS" != "true" ]; then
        log "RUN_MIGRATIONS=false - skipping migrations."
        return 0
    fi
    log "Applying database migrations..."
    python manage.py migrate --noinput
}

seed_framework_library() {
    if [ "$SEED_FRAMEWORK_LIBRARY" != "true" ]; then
        log "SEED_FRAMEWORK_LIBRARY=false - skipping Framework Library seed."
        return 0
    fi
    if ! python manage.py help seed_frameworks >/dev/null 2>&1; then
        log "No 'seed_frameworks' management command in this project - skipping (this entrypoint is shared across Bohlale projects)."
        return 0
    fi
    log "Seeding the built-in Framework Library (idempotent)..."
    python manage.py seed_frameworks
}

collect_static() {
    if [ "$RUN_COLLECTSTATIC" != "true" ]; then
        log "RUN_COLLECTSTATIC=false - skipping collectstatic."
        return 0
    fi
    log "Collecting static files..."
    python manage.py collectstatic --noinput --clear
}

create_superuser_if_configured() {
    if [ -z "${DJANGO_SUPERUSER_EMAIL:-}" ] || [ -z "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        log "DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD not both set - skipping automatic superuser creation."
        return 0
    fi

    log "Ensuring the configured superuser account exists..."
    # Idempotent: does nothing if a user with this email already exists.
    # Uses the project's own createsuperuser management command (Django
    # reads DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD itself for
    # --noinput), so this works for any custom user model whose
    # USERNAME_FIELD is "email" without hardcoding a model import here.
    python manage.py shell <<'PYEOF'
import os

from django.contrib.auth import get_user_model

User = get_user_model()
email = os.environ["DJANGO_SUPERUSER_EMAIL"]

if User.objects.filter(**{User.USERNAME_FIELD: email}).exists():
    print(f"[entrypoint] Superuser '{email}' already exists - not recreated.")
else:
    from django.core.management import call_command

    # interactive=False triggers Django's --noinput path, which reads
    # DJANGO_SUPERUSER_PASSWORD (and DJANGO_SUPERUSER_<FIELD> for any
    # other required fields) straight from the environment.
    call_command("createsuperuser", interactive=False, email=email)
    print(f"[entrypoint] Created superuser '{email}'.")
PYEOF
}

main() {
    wait_for_postgres
    check_migration_drift
    run_migrations
    seed_framework_library
    collect_static
    create_superuser_if_configured

    log "Starting: $*"
    exec "$@"
}

main "$@"
