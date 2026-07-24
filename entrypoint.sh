#!/usr/bin/env bash
#
# Generic container entrypoint for a Django project. Runs before every
# container start (the web server, and any one-off `docker compose run`
# management command alike):
#
#   1. wait for the database to accept connections (Postgres only)
#   2. run migrations
#   3. collect static files (for WhiteNoise)
#   4. optionally create a superuser from env vars, if one doesn't exist
#   5. exec the container's CMD (gunicorn by default)
#
# Nothing here is specific to Bohlale GRC - it only relies on `manage.py`
# existing at /app and on the DB_* / DJANGO_SUPERUSER_* env var convention,
# so this file can be reused unchanged by other Django projects.
#
# Each step can be individually disabled via env vars for special cases
# (e.g. running a one-off shell without re-running migrations):
#   RUN_MIGRATIONS=false
#   RUN_COLLECTSTATIC=false
#   WAIT_FOR_DB=false

set -euo pipefail

log() {
    printf '[entrypoint] %s\n' "$1"
}

RUN_MIGRATIONS="${RUN_MIGRATIONS:-true}"
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

run_migrations() {
    if [ "$RUN_MIGRATIONS" != "true" ]; then
        log "RUN_MIGRATIONS=false - skipping migrations."
        return 0
    fi
    log "Applying database migrations..."
    python manage.py migrate --noinput
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
    run_migrations
    collect_static
    create_superuser_if_configured

    log "Starting: $*"
    exec "$@"
}

main "$@"
