# Docker deployment toolkit

Deploy the whole stack (Django + PostgreSQL, behind Gunicorn/WhiteNoise,
in Docker) with one command:

```bash
sudo ./deployment/install.sh
```

That's it. No manual editing is required except optionally changing the
generated password/secret values in `.env` afterward if you want your own
instead of the randomly generated ones (see "What install.sh does").

This toolkit is a second, optional deployment path alongside the
non-Docker VPS path in `DEPLOYMENT.md` (systemd + Gunicorn + Nginx
directly on the host) - both are fully supported; use whichever fits your
infrastructure. Docker was never required by this project and still
isn't; it's now available as an alternative.

---

## Prerequisites

- A Linux host with [Docker Engine](https://docs.docker.com/engine/install/)
  and the [Docker Compose plugin](https://docs.docker.com/compose/install/)
  installed (`docker compose version` should work).
- Enough disk for the PostgreSQL data volume, media uploads, and backups.
- If you're deploying behind an existing shared reverse proxy (e.g. a
  staging environment fronting multiple Bohlale apps), know its Docker
  network name. This project's default is `bohlale-health-staging_private`
  (`EXTERNAL_NETWORK` in `.env`) - `install.sh` creates it automatically if
  it doesn't exist yet, so a fresh host works too.

## What `install.sh` does

Every step is idempotent - re-running it is safe.

1. **Validates Docker and Docker Compose** are installed and the daemon
   is reachable.
2. **Creates `.env` from `.env.example`** if one doesn't already exist,
   generating a strong random `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`
   automatically - a fresh install never runs with placeholder secrets.
   If `.env` already exists, it is left completely untouched.
3. **Creates the external Docker network and named volumes** if missing.
4. **Builds the application image.**
5. **Migrates an existing `db.sqlite3`'s data into PostgreSQL**, if one is
   found at the project root (e.g. you're moving an existing non-Docker
   deployment onto this toolkit). The original file is never modified -
   it's read-only mounted for the dump, then renamed to
   `db.sqlite3.migrated-<timestamp>` afterward so a re-run of `install.sh`
   doesn't repeat the import. A JSON dump of the migrated data is kept
   under `./backups/` regardless. Skipped entirely if no `db.sqlite3`
   exists (a normal fresh install).
6. **Starts the stack** (`postgres`, then `bohlale-grc` once Postgres
   reports healthy). On every start, the container's own entrypoint
   applies migrations and seeds the built-in Framework Library (ISO
   27001, ISO 27701, POPIA, PAIA, ISO 22301, ISO 9001, ISO 31000, NIST
   CSF, CIS Controls v8, King IV) — idempotent, so a fresh deployment's
   Framework Library is populated automatically, never empty.
7. **Waits for the app to report healthy** (a real database round-trip
   via `/health/`, not just "the container is running") and prints
   connection details, useful commands, and admin-account instructions.

## Before you deploy for real

`install.sh` generates working secrets automatically and forces
`DJANGO_DEBUG=False` in the `.env` it creates (the `.env.example` this is
copied from defaults to `True` for the unrelated plain `manage.py
runserver` local-dev workflow — a fresh Docker install always overrides
it, so this is done for you). What's still a placeholder you must set for
your actual domain before exposing this to the internet:

```bash
DJANGO_ALLOWED_HOSTS=grc.yourdomain.example
DJANGO_CSRF_TRUSTED_ORIGINS=https://grc.yourdomain.example
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

Set the last three to `True` once you have HTTPS terminated in front of
this stack (by your shared reverse proxy on `EXTERNAL_NETWORK`, or your
own Nginx/Traefik/Caddy). This container does not terminate TLS itself.

To get an admin login without doing it by hand, set before running
`install.sh` (or `update.sh`):

```bash
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.example
DJANGO_SUPERUSER_PASSWORD=a-real-password
```

The entrypoint creates that account automatically on first start if it
doesn't already exist, and does nothing on every subsequent start (it's
idempotent, so it's safe to leave these set permanently).

---

## Day-to-day operations

| Task | Command |
|---|---|
| Deploy the latest code | `./deployment/update.sh` |
| Back up the database + media | `./deployment/backup.sh` |
| Restore the latest backup | `./deployment/restore.sh` |
| Restore a specific backup | `./deployment/restore.sh backups/backup_bohlale-grc_20260101-120000.tar.gz` |
| Undo the last deploy | `./deployment/rollback.sh` |
| Check stack health | `./deployment/health.sh` |
| Tail application logs | `docker compose -f compose.yml logs -f bohlale-grc` |
| Open a Django shell | `docker compose -f compose.yml exec bohlale-grc python manage.py shell` |
| Run any management command | `docker compose -f compose.yml exec bohlale-grc python manage.py <command>` |
| Stop everything | `docker compose -f compose.yml down` |
| Stop everything and delete data | `docker compose -f compose.yml down -v` **(destroys the database/media volumes - back up first)** |

### `update.sh`

Pulls the latest code, takes a backup, rebuilds the image (tagging the
outgoing one as `<IMAGE_NAME>:previous` so `rollback.sh` has something to
restore), migrates, collects static files, and restarts - then waits for
the app to report healthy. If it doesn't become healthy, it tells you to
run `rollback.sh`.

```bash
./deployment/update.sh
```

### `backup.sh`

Takes a single timestamped, compressed archive under `./backups/`
containing a `pg_dump` of the database, a full copy of the media volume,
and a small manifest (git commit, image tag, timestamp). Safe to run on a
live stack. Wire it into cron for scheduled backups, e.g. daily at 03:00:

```cron
0 3 * * * cd /opt/bohlale-grc && ./deployment/backup.sh >> logs/backup.log 2>&1
```

Old backups are deleted automatically after `BACKUP_RETENTION_DAYS` (14
by default; set to `0` in `.env` to keep everything).

**A backup that has never been restored is not a verified backup** - test
`restore.sh` against a non-production copy of this stack at least once
before you rely on it.

### `restore.sh` / `rollback.sh`

Both are destructive (they replace the current database and media) and
prompt for confirmation unless you pass `FORCE=true`. `restore.sh`
restores a backup archive on its own; `rollback.sh` additionally swaps
the running image back to the one from before the last `update.sh` run,
since the backup taken right before that update matches it in time.

```bash
./deployment/rollback.sh              # asks "type 'rollback' to continue"
FORCE=true ./deployment/rollback.sh   # non-interactive (e.g. from another script)
```

### `health.sh`

Prints container status, confirms Postgres is accepting connections and
the app's `/health/` endpoint responds, and exits non-zero if anything is
wrong - suitable for an external uptime check or a cron alert:

```cron
*/5 * * * * cd /opt/bohlale-grc && ./deployment/health.sh || mail -s "bohlale-grc is unhealthy" ops@example.com
```

---

## Reusing this toolkit for another Django project

Everything here was written generically on purpose - `entrypoint.sh`,
`gunicorn.conf.py`, `Dockerfile`, `.dockerignore`, and every script in
`deployment/` reference no project name directly; they read it from
`.env` (`COMPOSE_PROJECT_NAME`, `IMAGE_NAME`, ...) with sensible
fallbacks. To stand this up for **Bohlale Learn**, **Bohlale Health**,
**Bohlale Notes**, or any other Django project:

1. Copy `Dockerfile`, `.dockerignore`, `entrypoint.sh`, `gunicorn.conf.py`,
   `compose.yml`, and the `deployment/` directory into the new project.
2. In `compose.yml`, rename the `bohlale-grc:` service key to that
   project's own name (this is the one place a service name is
   hardcoded, per this deployment's specific requirements - everything
   under it is still variable-driven).
3. In `.env` (or `.env.example`), set `COMPOSE_PROJECT_NAME`,
   `IMAGE_NAME`, `POSTGRES_DB`/`POSTGRES_USER`, `WEB_PORT`, and
   `EXTERNAL_NETWORK` to that project's values.
4. Make sure the new project's `requirements.txt` includes `gunicorn`,
   `psycopg2-binary` (or `psycopg2` + keep `libpq-dev` in the Dockerfile's
   runtime stage), and `whitenoise`, and that its Django settings read
   `DB_ENGINE`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` from
   the environment the same way `config/settings.py` does here (copy that
   pattern if starting from scratch - see the "Database" section of
   `config/settings.py`).
5. If the new project doesn't use email as its `USERNAME_FIELD`, the
   automatic `DJANGO_SUPERUSER_EMAIL`-based superuser creation in
   `entrypoint.sh` still works unmodified - Django resolves
   `USERNAME_FIELD` dynamically via `get_user_model()`, it isn't hardcoded
   to "email" anywhere in this toolkit.
6. Run `sudo ./deployment/install.sh`.

Nothing else needs to change.
