#!/usr/bin/env bash
#
# Shared helpers sourced by every script in deployment/. Not meant to be
# run directly. Generic - no project-specific values are hardcoded here;
# everything comes from .env via load_env, with PROJECT_NAME_DEFAULT as
# the only per-project fallback (used only if .env doesn't set it).
#
# shellcheck shell=bash

PROJECT_NAME_DEFAULT="bohlale-grc"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"
ENV_EXAMPLE_FILE="$PROJECT_ROOT/.env.example"

# --- Output -----------------------------------------------------------

if [ -t 1 ]; then
    C_RED=$'\033[0;31m'; C_GREEN=$'\033[0;32m'; C_YELLOW=$'\033[0;33m'
    C_BLUE=$'\033[0;34m'; C_BOLD=$'\033[1m'; C_RESET=$'\033[0m'
else
    C_RED=""; C_GREEN=""; C_YELLOW=""; C_BLUE=""; C_BOLD=""; C_RESET=""
fi

log_info()    { printf '%s[INFO]%s  %s\n'  "$C_BLUE"  "$C_RESET" "$1"; }
log_success() { printf '%s[ OK ]%s  %s\n'  "$C_GREEN" "$C_RESET" "$1"; }
log_warn()    { printf '%s[WARN]%s  %s\n'  "$C_YELLOW" "$C_RESET" "$1"; }
log_error()   { printf '%s[FAIL]%s  %s\n'  "$C_RED"   "$C_RESET" "$1" >&2; }
log_step()    { printf '\n%s%s==>%s %s%s\n' "$C_BOLD" "$C_BLUE" "$C_RESET" "$C_BOLD" "$1$C_RESET"; }

die() { log_error "$1"; exit "${2:-1}"; }

# --- Environment --------------------------------------------------------

# Loads .env into the current shell's environment (does NOT create it -
# callers that need it to exist should call ensure_env_file first).
load_env() {
    if [ -f "$ENV_FILE" ]; then
        set -a
        # shellcheck disable=SC1090
        source "$ENV_FILE"
        set +a
    fi
    : "${COMPOSE_PROJECT_NAME:=$PROJECT_NAME_DEFAULT}"
    : "${IMAGE_NAME:=$PROJECT_NAME_DEFAULT}"
    : "${IMAGE_TAG:=latest}"
    : "${WEB_PORT:=8000}"
    : "${POSTGRES_DB:=bohlale_grc}"
    : "${POSTGRES_USER:=bohlale}"
    : "${BACKUP_DIR:=$PROJECT_ROOT/backups}"
    : "${BACKUP_RETENTION_DAYS:=14}"
    : "${EXTERNAL_NETWORK:=bohlale-health-staging_private}"
    export COMPOSE_PROJECT_NAME IMAGE_NAME IMAGE_TAG WEB_PORT POSTGRES_DB POSTGRES_USER \
        BACKUP_DIR BACKUP_RETENTION_DAYS EXTERNAL_NETWORK
}

# Creates .env from .env.example if missing, generating strong random
# values for the two secrets that must never ship with a placeholder
# (DJANGO_SECRET_KEY, POSTGRES_PASSWORD) so a first run never starts a
# stack with a guessable password. Existing .env files are never touched.
ensure_env_file() {
    if [ -f "$ENV_FILE" ]; then
        log_info ".env already exists - leaving it untouched."
        return 0
    fi

    [ -f "$ENV_EXAMPLE_FILE" ] || die ".env.example not found at $ENV_EXAMPLE_FILE - cannot create .env."

    log_info "No .env found - creating one from .env.example with freshly generated secrets..."
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"

    local secret_key postgres_password
    secret_key="$(generate_secret 50)"
    postgres_password="$(generate_secret 32)"

    replace_env_value "DJANGO_SECRET_KEY" "$secret_key"
    replace_env_value "POSTGRES_PASSWORD" "$postgres_password"
    replace_env_value "DB_PASSWORD" "$postgres_password"
    # .env.example ships DJANGO_DEBUG=True for the plain `manage.py runserver`
    # local-dev workflow it's primarily written for. This function only ever
    # runs for a Docker deployment (install.sh/update.sh/etc.), which is never
    # the local-dev case, so force it off here rather than let a fresh
    # production install silently boot with DEBUG=True (stack traces/settings
    # exposed on error pages) until someone happens to notice.
    replace_env_value "DJANGO_DEBUG" "False"

    chmod 600 "$ENV_FILE"

    log_success "Created .env with a randomly generated DJANGO_SECRET_KEY and POSTGRES_PASSWORD (DJANGO_DEBUG set to False)."
    log_warn "Review $ENV_FILE before going live: set DJANGO_ALLOWED_HOSTS, DJANGO_CSRF_TRUSTED_ORIGINS," \
        "and DJANGO_SECURE_SSL_REDIRECT/DJANGO_SESSION_COOKIE_SECURE/DJANGO_CSRF_COOKIE_SECURE=True once HTTPS is live."
}

# Generates a URL-safe random string of (at least) $1 bytes of entropy.
generate_secret() {
    local bytes="${1:-32}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 "$bytes" | tr -d '\n=+/' | cut -c1-"$bytes"
    else
        head -c "$bytes" /dev/urandom | base64 | tr -d '\n=+/' | cut -c1-"$bytes"
    fi
}

# Replaces (or appends) KEY=value in .env, without disturbing comments or
# ordering. Portable sed -i (GNU and BSD/macOS both handled).
replace_env_value() {
    local key="$1" value="$2"
    local escaped_value
    escaped_value=$(printf '%s' "$value" | sed -e 's/[\/&]/\\&/g')

    if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
        if sed --version >/dev/null 2>&1; then
            sed -i "s/^${key}=.*/${key}=${escaped_value}/" "$ENV_FILE"
        else
            sed -i '' "s/^${key}=.*/${key}=${escaped_value}/" "$ENV_FILE"
        fi
    else
        printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
    fi
}

# --- Docker / Compose ---------------------------------------------------

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "Required command '$1' not found on PATH. $2"
}

validate_docker() {
    require_cmd docker "Install Docker: https://docs.docker.com/engine/install/"
    docker info >/dev/null 2>&1 || die "Docker is installed but the daemon isn't reachable. Is it running? Do you have permission (try sudo, or add your user to the 'docker' group)?"
    log_success "Docker is installed and the daemon is reachable."
}

# Sets $DC to the working compose invocation ("docker compose" or the
# legacy standalone "docker-compose"), validating it works.
validate_compose() {
    if docker compose version >/dev/null 2>&1; then
        DC="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        DC="docker-compose"
    else
        die "Neither 'docker compose' (plugin) nor 'docker-compose' (standalone) is available. Install the Docker Compose plugin: https://docs.docker.com/compose/install/"
    fi
    export DC
    log_success "Using compose command: $DC"
}

# Wrapper: always runs compose against this project's compose.yml/.env
# from the project root, regardless of the caller's current directory.
compose() {
    ( cd "$PROJECT_ROOT" && $DC --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@" )
}

ensure_external_network() {
    local network="${EXTERNAL_NETWORK:-bohlale-health-staging_private}"
    if docker network inspect "$network" >/dev/null 2>&1; then
        log_success "External network '$network' already exists."
    else
        log_warn "External network '$network' does not exist yet - creating it."
        docker network create "$network" >/dev/null
        log_success "Created external network '$network'."
    fi
}

ensure_named_volumes() {
    local volume
    for volume in $(compose config --volumes 2>/dev/null); do
        local full_name="${COMPOSE_PROJECT_NAME}_${volume}"
        if docker volume inspect "$full_name" >/dev/null 2>&1; then
            log_info "Volume '$full_name' already exists."
        else
            docker volume create "$full_name" >/dev/null
            log_success "Created volume '$full_name'."
        fi
    done
}

# Polls the app's /health/ endpoint (a real DB round-trip, not just
# "container running" - see core/views.py::health) until it responds 200
# or the timeout elapses.
wait_for_app_health() {
    local timeout="${1:-90}" waited=0 url="http://localhost:${WEB_PORT}/health/"
    log_info "Waiting for $url to report healthy (timeout: ${timeout}s)..."
    while ! curl -fsS "$url" >/dev/null 2>&1; do
        waited=$((waited + 3))
        if [ "$waited" -ge "$timeout" ]; then
            log_error "App did not become healthy within ${timeout}s."
            return 1
        fi
        sleep 3
    done
    log_success "App is healthy: $(curl -fsS "$url")"
}

timestamp() { date +%Y%m%d-%H%M%S; }
