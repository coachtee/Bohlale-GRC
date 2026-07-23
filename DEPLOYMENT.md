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

Optionally seed the fictional NIBS demonstration tenant (safe to run in
any environment — it only ever creates fictional sample data, never real
client data, per the product's data-safety rule):

```bash
sudo -u bohlale .venv/bin/python manage.py seed_frameworks
sudo -u bohlale .venv/bin/python manage.py seed_journey_templates
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

## 11. Deploying updates

```bash
cd /opt/bohlale-grc/app
sudo -u bohlale git pull origin main
sudo -u bohlale .venv/bin/pip install -r requirements.txt
sudo -u bohlale .venv/bin/python manage.py migrate
sudo -u bohlale .venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart bohlale-grc
```

Per spec §42, production must not be edited directly — all changes flow
through the Git repository (source of truth) and are deployed via this
pull-and-restart sequence, whether triggered manually or by a CI/CD job.

## 12. Health check

After deployment, verify:

```bash
sudo -u bohlale .venv/bin/python manage.py check --deploy
curl -I https://grc.yourdomain.example/accounts/login/
sudo systemctl status bohlale-grc nginx postgresql
```

`manage.py check --deploy` flags any production security settings that
still need attention (e.g. if `.env` overrides were missed).

## Docker (optional, not required)

The spec requires Docker to be *optional*, never mandatory. This project
ships with none of the above assuming Docker, and no `Dockerfile` is
provided by default — the venv + Gunicorn + systemd approach above is the
supported path. If your infrastructure standardises on containers, the
same `requirements.txt` and `config.wsgi:application` entry point can be
wrapped in a container without any application code changes.
