#!/usr/bin/env bash
#
# Quick health/status check for the stack. Exits non-zero if anything is
# unhealthy, so it can be wired into external monitoring or a cron alert
# (e.g. `./deployment/health.sh || mail -s "bohlale-grc is down" ops@example.com`).
#
#   ./deployment/health.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=./_lib.sh
source "$SCRIPT_DIR/_lib.sh"

main() {
    validate_docker
    validate_compose
    [ -f "$ENV_FILE" ] || die ".env not found. Run ./deployment/install.sh first."
    load_env

    local exit_code=0

    log_step "Container status"
    compose ps || exit_code=1

    log_step "PostgreSQL"
    if compose exec -T postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        log_success "postgres: accepting connections"
    else
        log_error "postgres: NOT ready"
        exit_code=1
    fi

    log_step "Application"
    local url="http://localhost:${WEB_PORT}/health/"
    local response
    if response="$(curl -fsS --max-time 5 "$url" 2>&1)"; then
        log_success "bohlale-grc: healthy - $response"
    else
        log_error "bohlale-grc: NOT healthy ($url unreachable or returned an error)"
        exit_code=1
    fi

    log_step "Disk usage (backups)"
    if [ -d "$BACKUP_DIR" ]; then
        echo "  $BACKUP_DIR: $(du -sh "$BACKUP_DIR" 2>/dev/null | cut -f1) ($(find "$BACKUP_DIR" -maxdepth 1 -name 'backup_*.tar.gz' | wc -l) backups)"
    else
        log_warn "No backups directory yet ($BACKUP_DIR) - run ./deployment/backup.sh."
    fi

    echo
    if [ "$exit_code" -eq 0 ]; then
        log_success "Overall: healthy"
    else
        log_error "Overall: UNHEALTHY - see above"
    fi
    exit "$exit_code"
}

main "$@"
