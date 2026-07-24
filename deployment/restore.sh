#!/usr/bin/env bash
#
# Restores the database and media from a backup produced by backup.sh.
# Defaults to the most recent backup in $BACKUP_DIR; pass a specific
# archive path to restore a different one.
#
#   ./deployment/restore.sh                        # restores the latest backup
#   ./deployment/restore.sh backups/backup_x.tar.gz  # restores a specific one
#   FORCE=true ./deployment/restore.sh              # skip the confirmation prompt
#
# DESTRUCTIVE: replaces the current database and media contents entirely.
# Prompts for confirmation unless FORCE=true.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

find_latest_backup() {
    find "$BACKUP_DIR" -maxdepth 1 -name 'backup_*.tar.gz' -printf '%T@ %p\n' 2>/dev/null \
        | sort -rn | head -n1 | cut -d' ' -f2-
}

main() {
    validate_docker
    validate_compose
    [ -f "$ENV_FILE" ] || die ".env not found. Run ./deployment/install.sh first."
    load_env

    local archive="${1:-}"
    if [ -z "$archive" ]; then
        archive="$(find_latest_backup)"
        [ -n "$archive" ] || die "No backups found in $BACKUP_DIR. Run ./deployment/backup.sh first, or pass an archive path explicitly."
        log_info "No archive specified - using the most recent: $archive"
    fi
    [ -f "$archive" ] || die "Backup archive not found: $archive"

    if [ "${FORCE:-false}" != "true" ]; then
        log_warn "This will REPLACE the current database and media contents with the contents of:"
        log_warn "  $archive"
        read -r -p "Type 'restore' to continue: " confirmation
        [ "$confirmation" = "restore" ] || die "Aborted - confirmation not given."
    fi

    local tmp_dir
    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "$tmp_dir"' EXIT

    log_step "1/5 — Extracting archive"
    tar xzf "$archive" -C "$tmp_dir"
    [ -f "$tmp_dir/database.dump" ] || die "Archive doesn't contain database.dump - not a valid backup.sh archive?"
    [ -f "$tmp_dir/manifest.txt" ] && { log_info "Backup manifest:"; sed 's/^/    /' "$tmp_dir/manifest.txt"; }

    log_step "2/5 — Ensuring services are running"
    compose up -d postgres
    compose exec -T postgres sh -c "until pg_isready -U '$POSTGRES_USER' -d '$POSTGRES_DB'; do sleep 1; done"

    log_step "3/5 — Restoring PostgreSQL"
    compose exec -T postgres pg_restore \
        --clean --if-exists --no-owner \
        -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$tmp_dir/database.dump" \
        || log_warn "pg_restore reported warnings above (often harmless - e.g. 'role does not exist' for --no-owner statements). Verify the app after restore."

    log_step "4/5 — Restoring media"
    if [ -d "$tmp_dir/media" ]; then
        docker run --rm \
            -v "${COMPOSE_PROJECT_NAME}_media:/dest" \
            -v "$tmp_dir/media:/source:ro" \
            alpine:latest \
            sh -c 'rm -rf /dest/* /dest/.[!.]* 2>/dev/null; cp -a /source/. /dest/ 2>/dev/null || true'
        log_success "Media restored."
    else
        log_warn "Archive has no media/ directory - skipping media restore."
    fi

    log_step "5/5 — Restarting the application"
    compose up -d bohlale-grc
    if ! wait_for_app_health 90; then
        log_error "App did not become healthy after restore. Check logs: docker compose -f compose.yml logs bohlale-grc"
        exit 1
    fi

    log_success "Restore complete from $archive."
}

main "$@"
