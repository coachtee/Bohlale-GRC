#!/usr/bin/env bash
#
# Deploys the latest code: git pull, rebuild the image, migrate,
# collectstatic, restart. Tags the outgoing image as "<IMAGE_NAME>:previous"
# first so rollback.sh has something to fall back to, and takes a database
# backup before migrating so a bad migration is always recoverable.
#
#   ./deployment/update.sh
#
# Options (env vars):
#   SKIP_GIT_PULL=true     - deploy the working tree as-is, don't git pull
#   SKIP_BACKUP=true       - skip the pre-migration backup (not recommended)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

main() {
    validate_docker
    validate_compose
    [ -f "$ENV_FILE" ] || die ".env not found. Run ./deployment/install.sh first."
    load_env

    log_step "1/7 — Pulling latest code"
    if [ "${SKIP_GIT_PULL:-false}" = "true" ]; then
        log_info "SKIP_GIT_PULL=true - deploying the current working tree as-is."
    elif [ -d "$PROJECT_ROOT/.git" ]; then
        ( cd "$PROJECT_ROOT" && git pull --ff-only )
    else
        log_warn "$PROJECT_ROOT is not a git repository - skipping git pull."
    fi

    log_step "2/7 — Backing up the database before migrating"
    if [ "${SKIP_BACKUP:-false}" = "true" ]; then
        log_warn "SKIP_BACKUP=true - proceeding without a fresh backup."
    else
        "$SCRIPT_DIR/backup.sh" || die "Pre-update backup failed - aborting update. Fix the backup issue or set SKIP_BACKUP=true to override."
    fi

    log_step "3/7 — Tagging the current image for rollback"
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:previous"
        log_success "Tagged ${IMAGE_NAME}:${IMAGE_TAG} as ${IMAGE_NAME}:previous."
    else
        log_warn "No existing ${IMAGE_NAME}:${IMAGE_TAG} image found - nothing to tag as a rollback point (first deploy?)."
    fi

    log_step "4/7 — Building the new image"
    compose build

    log_step "5/7 — Applying database migrations"
    compose run --rm -e RUN_COLLECTSTATIC=false bohlale-grc python manage.py migrate --noinput

    log_step "6/7 — Collecting static files"
    compose run --rm -e RUN_MIGRATIONS=false bohlale-grc python manage.py collectstatic --noinput --clear

    log_step "7/7 — Restarting services"
    compose up -d

    log_info "Waiting for the app to report healthy after restart..."
    if ! wait_for_app_health 90; then
        log_error "The updated stack did not become healthy. Recent logs:"
        compose logs --tail=80 bohlale-grc || true
        log_error "Consider rolling back: ./deployment/rollback.sh"
        exit 1
    fi

    log_success "Update complete and healthy."
}

main "$@"
