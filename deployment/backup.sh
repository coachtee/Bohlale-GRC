#!/usr/bin/env bash
#
# Backs up the PostgreSQL database and the media volume into a single
# timestamped, compressed archive under $BACKUP_DIR.
#
#   ./deployment/backup.sh
#
# Safe to run on a live stack: pg_dump takes a consistent snapshot via a
# transaction, and the media volume is only read, never written.
# Suitable for cron (see deployment/README.md).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

main() {
    validate_docker
    validate_compose
    [ -f "$ENV_FILE" ] || die ".env not found. Run ./deployment/install.sh first."
    load_env

    mkdir -p "$BACKUP_DIR"
    local ts archive tmp_dir
    ts="$(timestamp)"
    archive="$BACKUP_DIR/backup_${COMPOSE_PROJECT_NAME}_${ts}.tar.gz"
    tmp_dir="$(mktemp -d)"
    trap 'rm -rf "$tmp_dir"' EXIT

    log_step "1/4 — Backing up PostgreSQL ($POSTGRES_DB)"
    if ! compose exec -T postgres pg_dump -U "$POSTGRES_USER" -F c -d "$POSTGRES_DB" > "$tmp_dir/database.dump"; then
        die "pg_dump failed - is the 'postgres' service running? (docker compose -f compose.yml ps)"
    fi
    [ -s "$tmp_dir/database.dump" ] || die "pg_dump produced an empty file - aborting, not writing a broken backup."
    log_success "Database dumped ($(du -h "$tmp_dir/database.dump" | cut -f1))."

    log_step "2/4 — Backing up the media volume"
    mkdir -p "$tmp_dir/media"
    docker run --rm \
        -v "${COMPOSE_PROJECT_NAME}_media:/source:ro" \
        -v "$tmp_dir/media:/dest" \
        alpine:latest \
        sh -c 'cp -a /source/. /dest/ 2>/dev/null || true'
    log_success "Media volume copied ($(du -sh "$tmp_dir/media" | cut -f1))."

    log_step "3/4 — Writing manifest"
    {
        echo "project=${COMPOSE_PROJECT_NAME}"
        echo "timestamp=${ts}"
        echo "image=${IMAGE_NAME}:${IMAGE_TAG}"
        if [ -d "$PROJECT_ROOT/.git" ]; then
            echo "git_commit=$(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo unknown)"
            echo "git_branch=$(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
        fi
        echo "postgres_db=${POSTGRES_DB}"
    } > "$tmp_dir/manifest.txt"

    log_step "4/4 — Compressing"
    tar czf "$archive" -C "$tmp_dir" .
    log_success "Backup written: $archive ($(du -h "$archive" | cut -f1))"

    apply_retention
}

apply_retention() {
    local days="${BACKUP_RETENTION_DAYS}"
    [ "$days" -gt 0 ] 2>/dev/null || return 0
    log_info "Applying retention: deleting backups older than ${days} days in $BACKUP_DIR..."
    find "$BACKUP_DIR" -maxdepth 1 -name 'backup_*.tar.gz' -mtime "+${days}" -print -delete | while read -r removed; do
        log_info "Removed old backup: $removed"
    done
}

main "$@"
