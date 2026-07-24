# Bohlale GRC — VPS Deployment Guide

This guide covers deploying Bohlale GRC to a plain Linux VPS using
**Nginx + Gunicorn + PostgreSQL**, per spec §41. Docker is not required
anywhere in this stack.

```
GitHub → VPS Staging → Nginx → Gunicorn → Django → PostgreSQL
```

Target OS: any recent Debian/Ubuntu LTS (commands below use `apt`; adjust
for other distributions).

## 1. Server prerequisites

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
    postgresql postgresql-contrib nginx git
```

Create a dedicated system user to run the app (never run it as root):

```bash
sudo adduser --system --group --home /opt/bohlale-grc bohlale
```

## 2. PostgreSQL setup

```bash
sudo -u postgres psql -c "CREATE DATABASE bohlale_grc;"
sudo -u postgres psql -c "CREATE USER bohlale WITH PASSWORD 'choose-a-strong-password';"
sudo -u postgres psql -c "ALTER ROLE bohlale SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE bohlale_grc TO bohlale;"
sudo -u postgres psql -c "ALTER DATABASE bohlale_grc OWNER TO bohlale;"
```

## 3. Fetch the code and create the virtualenv

```bash
sudo -u bohlale git clone <your-fork-or-repo-url> /opt/bohlale-grc/app
cd /opt/bohlale-grc/app
sudo -u bohlale python3 -m venv .venv
sudo -u bohlale .venv/bin/pip install --upgrade pip
sudo -u bohlale .venv/bin/pip install -r requirements.txt
```

`psycopg2-binary` and `gunicorn` are already in `requirements.txt`, so no
extra install step is needed for the production database driver or
application server.

## 4. Environment configuration (`.env`)

```bash
sudo -u bohlale cp .env.example .env
sudo -u bohlale nano .env
```

Set at minimum:

```bash
DJANGO_SECRET_KEY=<generate a long random value — see below>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=grc.yourdomain.example
DJANGO_CSRF_TRUSTED_ORIGINS=https://grc.yourdomain.example

DB_ENGINE=postgres
DB_NAME=bohlale_grc
DB_USER=bohlale
DB_PASSWORD=<the password you set in step 2>
DB_HOST=localhost
DB_PORT=5432

DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

`DJANGO_SESSION_COOKIE_AGE` (default 7 days) and
`DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE` (default `False`) are optional —
the defaults are reasonable for a business SaaS product; tighten them if
your organisation has a shorter session-timeout policy.

The app deliberately **refuses to start** with `DJANGO_DEBUG=False` if
`DJANGO_SECRET_KEY` is missing or still the checked-in development
default — this is intentional (see `config/settings.py`), not a bug, and
means a misconfigured `.env` fails loudly at boot instead of silently
running with a guessable key.

Generate a secret key:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Leave `AI_PROVIDER=mock` unless you have a real OpenAI-compatible or
Qwen-compatible endpoint and key to configure (`AI_API_BASE`, `AI_API_KEY`,
`AI_MODEL`) — the product works fully offline with the mock provider.

Configure `EMAIL_*` settings for a real SMTP relay if you want outbound
email notifications; otherwise notifications remain in-app only (the
console backend is dev-only and must not be used in production).

**Never commit `.env`.** It is already covered by `.gitignore`.

A Content-Security-Policy is applied to every response by
`core/middleware.py::SecurityHeadersMiddleware` (`script-src 'self'`, no
inline scripts, no third-party CDNs) — it is not configured via `.env`.
If you customise templates to pull in an external font, script or embed,
you must add that host to the relevant `-src` directive in
`core/middleware.py` or the browser will silently block it.

## 4a. Reverse-proxy trust (X-Forwarded-Proto)

Nginx terminates TLS and proxies to Gunicorn over a local Unix socket
(step 7), so Gunicorn itself only ever sees plain HTTP. Django is told to
trust the proxy's `X-Forwarded-Proto` header via
`SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` in
`config/settings.py`, so it knows a request was actually HTTPS at the
edge — without this, `DJANGO_SECURE_SSL_REDIRECT=True` (step 4) would
redirect-loop forever once HTTPS is enabled (step 8), since Django would
never see a request it considers secure. No action is needed as long as
you keep the `proxy_set_header X-Forwarded-Proto $scheme;` line from the
Nginx config in step 7, and — importantly — never expose Gunicorn's port
or socket directly to the internet, since trusting this header is only
safe when Nginx is the sole process able to set it.

## 5. Migrations and static files

```bash
cd /opt/bohlale-grc/app
sudo -u bohlale .venv/bin/python manage.py migrate
sudo -u bohlale .venv/bin/python manage.py collectstatic --noinput
```

`collectstatic` is required in production because `DEBUG=False` switches
`STORAGES["staticfiles"]` to `CompressedManifestStaticFilesStorage`
(hashed, cache-busted filenames) — see `config/settings.py`. Static files
are served directly by Nginx (step 7), with WhiteNoise as a fallback if
Nginx static serving is ever bypassed.

Create the first platform administrator:

```bash
sudo -u bohlale .venv/bin/python manage.py createsuperuser
```

Seed the built-in Framework Library (ISO 27001, ISO 27701, POPIA, PAIA,
ISO 22301, ISO 9001, ISO 31000, NIST CSF, CIS Controls v8, King IV).
**Not optional** — without this step the Framework Library is empty for
every organisation on a fresh deployment. Idempotent, safe to re-run
(e.g. after an update that changes the seeded content):

```bash
sudo -u bohlale .venv/bin/python manage.py seed_frameworks
sudo -u bohlale .venv/bin/python manage.py seed_journey_templates
```

Optionally, also seed the fictional NIBS demonstration tenant for a
guided demo/UAT walkthrough (safe to run in any environment — it only
ever creates fictional sample data, never real client data, per the
product's data-safety rule; it calls `seed_frameworks`/
`seed_journey_templates` again itself, so running it doesn't require the
step above first, but production deployments serving real organisations
should skip it):

```bash
sudo -u bohlale .venv/bin/python manage.py seed_nibs_demo
```

## 6. Gunicorn

Run Gunicorn behind Nginx, bound to a Unix socket. Create
`/etc/systemd/system/bohlale-grc.service`:

```ini
[Unit]
Description=Bohlale GRC Gunicorn daemon
After=network.target postgresql.service

[Service]
User=bohlale
Group=bohlale
WorkingDirectory=/opt/bohlale-grc/app
EnvironmentFile=/opt/bohlale-grc/app/.env
ExecStart=/opt/bohlale-grc/app/.venv/bin/gunicorn \
    config.wsgi:application \
    --bind unix:/opt/bohlale-grc/app/gunicorn.sock \
    --workers 3 \
    --timeout 60 \
    --access-logfile /opt/bohlale-grc/app/logs/gunicorn-access.log \
    --error-logfile /opt/bohlale-grc/app/logs/gunicorn-error.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

`--workers 3` is a reasonable starting point for a small VPS
(`2 × CPU cores + 1` is the usual Gunicorn rule of thumb — adjust to your
instance size). Create the log directory first:
`sudo -u bohlale mkdir -p /opt/bohlale-grc/app/logs`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bohlale-grc
sudo systemctl status bohlale-grc
```

## 7. Nginx

Create `/etc/nginx/sites-available/bohlale-grc`:

```nginx
server {
    listen 80;
    server_name grc.yourdomain.example;

    client_max_body_size 30M;  # match/exceed MAX_UPLOAD_SIZE_MB in .env

    location /static/ {
        alias /opt/bohlale-grc/app/staticfiles/;
    }

    # Deliberately no `location /media/ { alias ... }` block. Uploaded
    # evidence, document attachments and management-review attachments
    # contain confidential tenant compliance data and must never be
    # reachable by a raw filesystem path — they are downloaded through
    # tenant-and-RBAC-checked Django views instead (see
    # core/protected_media.py and SECURITY_AUDIT.md). Do not add a
    # `/media/` alias here; doing so would bypass those checks entirely.

    location / {
        proxy_pass http://unix:/opt/bohlale-grc/app/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/bohlale-grc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d grc.yourdomain.example
```

Certbot rewrites the Nginx server block to redirect HTTP → HTTPS and
installs a renewal timer automatically. Once HTTPS is live, keep
`DJANGO_SECURE_SSL_REDIRECT=True` / `DJANGO_SESSION_COOKIE_SECURE=True` /
`DJANGO_CSRF_COOKIE_SECURE=True` set in `.env` (step 4) so Django also
enforces HTTPS and HSTS (see `config/settings.py`, applied whenever
`DEBUG=False`).

## 9. Scheduled tasks (cron)

Bohlale GRC has no Celery/Redis dependency (per spec §39 — "no mandatory
Redis/microservices"). The overdue-item scan (spec §36: overdue corrective
actions, documents due/overdue for review, evidence nearing expiry,
overdue risk reviews) runs as a plain management command intended for
cron:

```bash
sudo -u bohlale crontab -e
```

Add (runs every morning at 06:00 server time):

```cron
0 6 * * * cd /opt/bohlale-grc/app && .venv/bin/python manage.py scan_overdue >> logs/scan_overdue.log 2>&1
```

`scan_overdue` is idempotent per run — it de-duplicates against existing
unread notifications by link, so re-running it (or running it more than
once a day) will not spam users with duplicate notifications.

## 10. Backups

PostgreSQL logical dump, daily, retained 14 days:

```bash
sudo -u bohlale crontab -e
```

```cron
0 3 * * * pg_dump -U bohlale -h localhost bohlale_grc | gzip > /opt/bohlale-grc/backups/bohlale_grc_$(date +\%Y\%m\%d).sql.gz
5 3 * * * find /opt/bohlale-grc/backups -name '*.sql.gz' -mtime +14 -delete
```

Create the backup directory first: `sudo -u bohlale mkdir -p /opt/bohlale-grc/backups`.

Also back up the `media/` directory (uploaded evidence, document
attachments, framework import source files) — it is not stored in
PostgreSQL:

```cron
30 3 * * * tar -czf /opt/bohlale-grc/backups/media_$(date +\%Y\%m\%d).tar.gz -C /opt/bohlale-grc/app media
```

Store backups off-server (e.g. synced to object storage) for real
disaster recovery — a same-host backup only protects against application
or database corruption, not host loss.

**See `BACKUP_RESTORE.md` for the full restore procedure** — including
the exact `pg_restore` commands and a real, previously-executed
verification run (backup → restore into a fresh database → row counts and
an ORM query confirmed to match). A backup nobody has ever restored from
is not a verified backup; test your restore procedure on this server
(against a scratch database, never production) before you need it for
real, and re-test periodically (e.g. quarterly) since Django version
upgrades or schema drift can silently break a restore path that worked
before.

## 11. Deploying updates

```bash
cd /opt/bohlale-grc/app
sudo -u bohlale git pull origin main
sudo -u bohlale .venv/bin/pip install -r requirements.txt
sudo -u bohlale .venv/bin/python manage.py migrate
sudo -u bohlale .venv/bin/python manage.py seed_frameworks
sudo -u bohlale .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart bohlale-grc
```

`seed_frameworks` is idempotent (safe on every deploy) and picks up any
Framework Library content changes shipped in that release.

Per spec §42, production must not be edited directly — all changes flow
through the Git repository (source of truth) and are deployed via this
pull-and-restart sequence, whether triggered manually or by a CI/CD job.

### Rollback procedure

If a deploy breaks something, roll back the code and, only if that
release included migrations that must also be reversed, the database:

```bash
cd /opt/bohlale-grc/app
sudo -u bohlale git log --oneline -5          # find the last known-good commit
sudo -u bohlale git checkout <previous-commit-or-tag>
sudo -u bohlale .venv/bin/pip install -r requirements.txt
sudo -u bohlale .venv/bin/python manage.py migrate   # safe no-op if no migrations changed
sudo -u bohlale .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart bohlale-grc
```

Django migrations are additive by default and usually safe to leave
applied even after rolling back application code a few commits (an unused
new column/table does no harm). Only run `manage.py migrate <app>
<previous_migration_name>` to reverse a specific migration if the rolled-
back code actually depends on the schema not having that change — check
`manage.py showmigrations <app>` first, and take a fresh `pg_dump` before
reversing any migration on a database with real data, since a reverse
migration that drops a column is not itself reversible.

Tag releases (`git tag -a v1.2.0 -m "..."` before merging to your deploy
branch) so "the previous commit" in an incident is unambiguous rather
than a guess from `git log`.

## 12. Health check and monitoring

After deployment, verify:

```bash
sudo -u bohlale .venv/bin/python manage.py check --deploy
curl -I https://grc.yourdomain.example/accounts/login/
curl -s https://grc.yourdomain.example/health/     # {"status": "ok"} with a real DB round-trip
sudo systemctl status bohlale-grc nginx postgresql
```

`manage.py check --deploy` flags any production security settings that
still need attention (e.g. if `.env` overrides were missed).

`/health/` (`core/views.py::health`) executes `SELECT 1` against the
database and returns HTTP 503 with `{"status": "error"}` if that fails —
point an uptime monitor (even a free one, e.g. UptimeRobot, or a simple
cron + curl + mail one-liner) at this URL rather than `/accounts/login/`,
since a page returning 200 doesn't prove the database is reachable.

**Logs**: Gunicorn's access/error logs go to
`/opt/bohlale-grc/app/logs/` (step 6); Django's own application logging
(auth failures, permission-denied events, 5xx errors — see
`config/settings.py`'s `LOGGING`) goes to stdout/stderr, which systemd
captures into the journal. View it with:

```bash
sudo journalctl -u bohlale-grc -f          # follow live
sudo journalctl -u bohlale-grc --since today
```

This is deliberately not a third-party log-aggregation service (Sentry,
Datadog, etc.) — none is required to run the product, consistent with the
"no mandatory extra infrastructure" principle. If your organisation
already has one, forwarding the systemd journal or the Gunicorn log files
to it is a config change on the ops side, not an application change.

## 13. Before go-live

Read these once, end to end, before pointing real users at a production
instance — they cover things this deployment guide intentionally doesn't
duplicate:

- **`SECURITY_AUDIT.md`** — every security finding from the production-
  readiness review, with severity and remediation status. Confirm nothing
  Critical/High is still open.
- **`PRODUCTION_READINESS.md`** — the pass/fail gate covering tests, tenant
  isolation, RBAC, Django deploy checks, backups, and more. Confirm it
  says production release is recommended, not blocked.
- **`POPIA_READINESS.md`** — what the software does and does not do for
  POPIA compliance. Software alone does not make an organisation
  compliant; read this before telling a client "the platform is POPIA
  compliant."
- **`BACKUP_RESTORE.md`** — do the restore drill yourself on this server
  before go-live, don't just trust that it worked once in a different
  environment.

## Docker (optional, not required)

The spec requires Docker to be *optional*, never mandatory, and everything
above (venv + Gunicorn + systemd + Nginx directly on the host) remains the
fully supported, Docker-free path — nothing here assumes Docker.

A second, equally supported deployment path is also available for
infrastructure that standardises on containers: `Dockerfile`,
`compose.yml`, and a one-command installer (`sudo ./deployment/install.sh`)
that builds the image, starts PostgreSQL and the app, waits for it to
report healthy, and prints connection details. It uses the same
`requirements.txt` and `config.wsgi:application` entry point as the VPS
path — no application code differs between the two. See
**`deployment/README.md`** for the full guide (install, update, backup,
restore, rollback, health-check).
