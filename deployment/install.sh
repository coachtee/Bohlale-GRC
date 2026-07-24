#!/usr/bin/env bash
#
# One-command installer for the Dockerised deployment.
#
#   sudo ./deployment/install.sh
#
# Does everything needed to go from a bare Docker host to a running,
# healthy stack: validates Docker/Compose, creates .env (with generated
# secrets) if missing, creates the external network and named volumes if
# missing, migrates an existing db.sqlite3's data into PostgreSQL if one
# is found, builds the image, starts the stack, and waits for it to
# report healthy before printing connection details.
#
# Safe to re-run: every step is idempotent (an existing .env is never
# touched, an already-migrated db.sqlite3 is skipped, `docker compose up`
# only recreates what changed).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

migrate_sqlite_if_present() {
    local sqlite_path="$PROJECT_ROOT/db.sqlite3"
    if [ ! -f "$sqlite_path" ]; then
        return 0
    fi

    log_step "Existing db.sqlite3 found — migrating its data into PostgreSQL"
    mkdir -p "$BACKUP_DIR"
    local dump_name="sqlite-migration-$(timestamp).json"
    local dump_path="$BACKUP_DIR/$dump_name"

    log_info "Dumping data from db.sqlite3 (this reads db.sqlite3 read-only; it is never modified)..."
    docker run --rm \
        -v "$sqlite_path:/app/db.sqlite3:ro" \
        -v "$BACKUP_DIR:/app/backups" \
        -e DB_ENGINE=sqlite \
        -e DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-temporary-key-for-dumpdata-only}" \
        -e DJANGO_DEBUG=False \
        -e DJANGO_ALLOWED_HOSTS="*" \
        -e RUN_MIGRATIONS=false \
        -e RUN_COLLECTSTATIC=false \
        -e WAIT_FOR_DB=false \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        python manage.py dumpdata \
            --natural-foreign --natural-primary \
            --exclude contenttypes --exclude auth.permission --exclude sessions.session \
            --output "/app/backups/$dump_name"

    if [ ! -s "$dump_path" ]; then
        die "SQLite dump produced no output ($dump_path) - aborting before touching PostgreSQL. Check the docker run output above."
    fi
    log_success "Dumped SQLite data to $dump_path"

    log_info "Applying migrations to PostgreSQL..."
    compose run --rm -e RUN_COLLECTSTATIC=false bohlale-grc python manage.py migrate --noinput

    log_info "Loading dumped data into PostgreSQL..."
    compose run --rm -v "$BACKUP_DIR:/app/backups" -e RUN_MIGRATIONS=false -e RUN_COLLECTSTATIC=false \
        bohlale-grc python manage.py loaddata "/app/backups/$dump_name"

    local migrated_path="$sqlite_path.migrated-$(timestamp)"
    mv "$sqlite_path" "$migrated_path"
    log_success "Data loaded into PostgreSQL. Original file preserved as $(basename "$migrated_path") (safe to delete once you've verified the migration)."
    log_info "The dump itself is also kept at $dump_path."
}

print_success_banner() {
    local url="http://localhost:${WEB_PORT}/"
    echo
    printf '%s%s========================================================%s\n' "$C_GREEN" "$C_BOLD" "$C_RESET"
    printf '%s%s  Bohlale GRC is up and healthy%s\n' "$C_GREEN" "$C_BOLD" "$C_RESET"
    printf '%s%s========================================================%s\n' "$C_GREEN" "$C_BOLD" "$C_RESET"
    echo
    echo "  App:            $url"
    echo "  Health check:   ${url}health/"
    echo "  Compose file:   $COMPOSE_FILE"
    echo "  Env file:       $ENV_FILE"
    echo "  External net:   ${EXTERNAL_NETWORK}"
    echo
    echo "  Useful commands:"
    echo "    docker compose -f compose.yml logs -f bohlale-grc     # tail app logs"
    echo "    docker compose -f compose.yml ps                      # service status"
    echo "    ./deployment/health.sh                                 # health check"
    echo "    ./deployment/backup.sh                                 # backup DB + media"
    echo "    ./deployment/update.sh                                 # deploy the latest code"
    echo
    if [ -z "${DJANGO_SUPERUSER_EMAIL:-}" ]; then
        echo "  No admin account was auto-created (DJANGO_SUPERUSER_EMAIL was not set in .env)."
        echo "  Create one now with:"
        echo "    docker compose -f compose.yml exec bohlale-grc python manage.py createsuperuser"
    else
        echo "  Admin account: ${DJANGO_SUPERUSER_EMAIL} (created automatically from .env; use the DJANGO_SUPERUSER_PASSWORD you set there)."
    fi
    echo
    echo "  See deployment/README.md for backup/restore/rollback/update instructions."
    echo
}

main() {
    log_step "1/8 — Validating Docker"
    validate_docker

    log_step "2/8 — Validating Docker Compose"
    validate_compose

    log_step "3/8 — Preparing .env"
    ensure_env_file
    load_env

    log_step "4/8 — Preparing network and volumes"
    ensure_external_network
    mkdir -p "$BACKUP_DIR"

    log_step "5/8 — Building the application image"
    compose build
    ensure_named_volumes

    log_step "6/8 — Migrating existing SQLite data (if any)"
    migrate_sqlite_if_present

    log_step "7/8 — Starting services"
    compose up -d

    log_step "8/8 — Verifying health"
    if ! wait_for_app_health 120; then
        log_error "The stack did not become healthy in time. Recent logs:"
        compose logs --tail=80 bohlale-grc || true
        die "Install did not complete successfully - see logs above."
    fi

    print_success_banner
}

main "$@"
