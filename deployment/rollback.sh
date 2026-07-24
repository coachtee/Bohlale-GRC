#!/usr/bin/env bash
#
# Rolls back to the previous deploy: restores the "<IMAGE_NAME>:previous"
# image tag (set automatically by update.sh before each deploy) and
# restores the most recent backup (taken automatically by update.sh
# immediately before it migrated/restarted into the version you're now
# rolling back from - so "latest backup" and "previous image" describe
# the same point in time).
#
#   ./deployment/rollback.sh
#   FORCE=true ./deployment/rollback.sh   # skip the confirmation prompt
#
# DESTRUCTIVE: replaces the current database/media and the running image,
# same as restore.sh (which this script delegates the data restore to).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

main() {
    validate_docker
    validate_compose
    [ -f "$ENV_FILE" ] || die ".env not found. Run ./deployment/install.sh first."
    load_env

    if ! docker image inspect "${IMAGE_NAME}:previous" >/dev/null 2>&1; then
        die "No '${IMAGE_NAME}:previous' image found - nothing to roll back to. update.sh tags this automatically before every deploy, so this is expected if you've never run an update, or already rolled back once."
    fi

    if [ "${FORCE:-false}" != "true" ]; then
        log_warn "This will:"
        log_warn "  1. Replace the running image with '${IMAGE_NAME}:previous'"
        log_warn "  2. Restore the most recent database/media backup (taken automatically before the last update)"
        read -r -p "Type 'rollback' to continue: " confirmation
        [ "$confirmation" = "rollback" ] || die "Aborted - confirmation not given."
    fi

    log_step "1/2 — Restoring the previous image"
    # Keep the current (bad) image under a timestamped tag rather than
    # discarding it outright, in case you need to inspect it afterward.
    if docker image inspect "${IMAGE_NAME}:${IMAGE_TAG}" >/dev/null 2>&1; then
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${IMAGE_NAME}:rolled-back-$(timestamp)"
    fi
    docker tag "${IMAGE_NAME}:previous" "${IMAGE_NAME}:${IMAGE_TAG}"
    log_success "'${IMAGE_NAME}:${IMAGE_TAG}' now points at the previous image."

    log_step "2/2 — Restoring the matching database/media backup"
    FORCE=true "$SCRIPT_DIR/restore.sh"

    log_success "Rollback complete."
}

main "$@"
