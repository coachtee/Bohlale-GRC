# Bohlale GRC — Docker Deployment Checklist (Ubuntu 24.04 + Docker Compose v2)

This is a copy/paste command checklist for deploying Bohlale GRC via the
Docker toolkit (`deployment/`) onto a fresh Ubuntu 24.04 LTS ("Noble")
VPS. It assumes the target host either already runs, or will run, a
shared reverse proxy on the `bohlale-health-staging_private` Docker
network (per this project's requirements) — a standalone-Nginx branch is
included for hosts that don't have one.

This checklist is the "what to run" companion to `deployment/README.md`
(what each script does and why) and `PRODUCTION_READINESS.md` (the
codebase-level release gate). Read this file top to bottom on a **new**
deployment; on a **repeat** deployment (redeploying an already-installed
host) skip straight to §7.

Where you see `grc.yourdomain.example`, replace it with your real domain
throughout.

---

## 0. Before you start

- [ ] You have root or `sudo` access to the target Ubuntu 24.04 VPS.
- [ ] DNS: an `A`/`AAAA` record for `grc.yourdomain.example` already
      points at this VPS's public IP (or you're ready to create one —
      TLS issuance in §6 needs it to resolve first).
- [ ] You know which reverse-proxy topology applies to this host (pick
      one, both are covered below):
  - **Shared proxy** — this host already runs (or will run) a reverse
    proxy container on the `bohlale-health-staging_private` network
    that fronts multiple apps (this is what `compose.yml` is written
    for).
  - **Standalone** — this app gets its own host-level Nginx + Certbot,
    no shared proxy network involved.

---

## 1. System preparation

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl git ufw
```

Set the hostname/timezone if not already done (optional):

```bash
sudo timedatectl set-timezone Africa/Johannesburg
```

---

## 2. Install Docker Engine + Compose v2 plugin

Official Docker apt repository (works on Ubuntu 24.04/Noble):

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Let your deploy user run Docker without `sudo` (optional but convenient
— log out/in, or `newgrp docker`, for it to take effect):

```bash
sudo usermod -aG docker "$USER"
newgrp docker
```

Verify:

```bash
docker --version
docker compose version   # must show a v2.x Compose plugin, not the old standalone docker-compose
```

- [ ] `docker compose version` reports Compose v2.

---

## 3. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

**If this host uses the shared-proxy topology**, `compose.yml` also
publishes the app on `${WEB_PORT:-8000}` (default `8000`) directly to
the host, so the app is reachable *bypassing* the proxy/TLS unless you
block it. Decide one of:

```bash
# Option A: firewall port 8000 off from the public internet entirely
sudo ufw deny 8000/tcp

# Option B: instead, bind the compose port mapping to localhost only —
# edit compose.yml's bohlale-grc.ports to "127.0.0.1:${WEB_PORT:-8000}:8000"
# before starting the stack (do this if another local process, e.g. the
# proxy itself, needs to reach it via localhost).
```

- [ ] Port 8000 is not reachable from the public internet unless that's
      genuinely intended (standalone topology with no separate proxy).

---

## 4. Clone the application

```bash
sudo mkdir -p /opt/bohlale-grc
sudo chown "$USER":"$USER" /opt/bohlale-grc
git clone https://github.com/coachtee/Bohlale-GRC.git /opt/bohlale-grc
cd /opt/bohlale-grc
git checkout main   # or the specific release branch/tag you're deploying
```

---

## 5. First run: `install.sh`

```bash
cd /opt/bohlale-grc
sudo ./deployment/install.sh
```

This one command: validates Docker/Compose, generates `.env` from
`.env.example` with a random `DJANGO_SECRET_KEY` and `POSTGRES_PASSWORD`
(and forces `DJANGO_DEBUG=False`), creates the external network and
named volumes if missing, builds the image, starts `postgres` then
`bohlale-grc`, and waits for `/health/` to report healthy. **Safe to
re-run** — see §11.

- [ ] Script finished with `Bohlale GRC is up and healthy`.

If it created `.env` for you (first run only), it printed a warning to
review it — that's §6 below.

---

## 6. Configure `.env` for your real domain

```bash
nano .env   # or vim/your editor of choice
```

Set (and save):

```bash
DJANGO_ALLOWED_HOSTS=grc.yourdomain.example
DJANGO_CSRF_TRUSTED_ORIGINS=https://grc.yourdomain.example
```

Leave `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, and
`DJANGO_CSRF_COOKIE_SECURE` as `False` for now — flip them to `True` in
§8, only once HTTPS is actually live end-to-end (turning them on before
TLS works will lock you out with a redirect loop).

Optional, recommended — get an admin account without doing it by hand
(safe to leave set permanently, this is idempotent):

```bash
# add to .env:
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.example
DJANGO_SUPERUSER_PASSWORD=<a-real-strong-password>
```

Apply the change:

```bash
sudo ./deployment/update.sh
```

- [ ] `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` set to the
      real domain.
- [ ] `DJANGO_DEBUG=False` (installer sets this automatically — confirm
      nobody flipped it back while editing).

---

## 7. Reverse proxy + TLS

### 7a. Shared-proxy topology

If the shared proxy on `bohlale-health-staging_private` doesn't exist
yet on this host:

```bash
docker network create bohlale-health-staging_private
```

(`install.sh` also does this automatically in §5 if the network was
missing, so this is only needed if you're standing up the proxy
separately before running `install.sh`.)

Point your reverse-proxy container's config at this app by its
container name/port on that network — `bohlale-grc-web:8000` (Docker
DNS resolves the container name on the shared network; no host port
needed for this path). Consult your proxy's own config docs (Nginx
Proxy Manager, Traefik, Caddy, etc.) for how it issues/renews the TLS
certificate for `grc.yourdomain.example`.

- [ ] Proxy container is on `bohlale-health-staging_private`.
- [ ] Proxy is configured to route `grc.yourdomain.example` →
      `bohlale-grc-web:8000`.
- [ ] TLS certificate issued and auto-renewing.

### 7b. Standalone topology (no shared proxy)

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

Nginx site config (`/etc/nginx/sites-available/bohlale-grc`):

```nginx
server {
    listen 80;
    server_name grc.yourdomain.example;

    location / {
        proxy_pass http://127.0.0.1:8000;
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
sudo certbot --nginx -d grc.yourdomain.example
```

Certbot rewrites the Nginx config to add the HTTPS server block and
redirect automatically.

- [ ] `https://grc.yourdomain.example/` loads over TLS.
- [ ] `sudo certbot renew --dry-run` succeeds (auto-renewal works).

---

## 8. Turn on secure cookies/redirect now that HTTPS is live

```bash
nano .env
```

```bash
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
```

```bash
sudo ./deployment/update.sh
```

- [ ] Visiting `http://grc.yourdomain.example/` redirects to `https://`.
- [ ] Login works over HTTPS (session cookie is only sent over TLS now).

---

## 9. Verify the deployment

```bash
docker compose -f compose.yml ps
./deployment/health.sh
curl -fsS https://grc.yourdomain.example/health/
```

- [ ] `health.sh` reports `Overall: healthy`.
- [ ] `/health/` returns `{"status": "ok"}` over the public domain.
- [ ] You can log in at `https://grc.yourdomain.example/` with the admin
      account from §6 (or create one now:
      `docker compose -f compose.yml exec bohlale-grc python manage.py createsuperuser`).

---

## 10. Backups: schedule + verify a real restore

Cron (daily backup at 03:00, health check every 5 minutes):

```bash
crontab -e
```

```cron
0 3 * * * cd /opt/bohlale-grc && ./deployment/backup.sh >> logs/backup.log 2>&1
*/5 * * * * cd /opt/bohlale-grc && ./deployment/health.sh || true
```

```bash
mkdir -p /opt/bohlale-grc/logs
```

**A backup that has never been restored is not a verified backup.**
Run one real restore drill now, before go-live, against this actual
server (not just against the sandbox this toolkit was built in):

```bash
./deployment/backup.sh
./deployment/restore.sh          # will prompt "Type 'restore' to continue"
./deployment/health.sh
```

- [ ] `backup.sh` produced a `.tar.gz` under `./backups/`.
- [ ] `restore.sh` completed and the app is healthy afterward.
- [ ] Cron entries for `backup.sh` and `health.sh` are installed.

---

## 11. Confirm `install.sh` re-runs are safe (idempotency)

You do not need to do this as a matter of routine, but if you ever want
to confirm the toolkit's idempotency claim on your own host:

```bash
sudo ./deployment/install.sh
```

Expected: `.env already exists — leaving it untouched`, the external
network/volumes report `already exists`, the image rebuilds (Docker
layer cache makes this fast if nothing changed), and the stack reports
healthy again — no data loss, no duplicated resources.

---

## 12. Day-2 operations reference

| Task | Command |
|---|---|
| Deploy new code | `cd /opt/bohlale-grc && sudo ./deployment/update.sh` |
| Back up now | `./deployment/backup.sh` |
| Restore latest backup | `./deployment/restore.sh` |
| Undo the last deploy | `./deployment/rollback.sh` |
| Check health | `./deployment/health.sh` |
| Tail app logs | `docker compose -f compose.yml logs -f bohlale-grc` |
| Django shell | `docker compose -f compose.yml exec bohlale-grc python manage.py shell` |
| Any management command | `docker compose -f compose.yml exec bohlale-grc python manage.py <command>` |
| Stop everything | `docker compose -f compose.yml down` |

---

## 13. Final sign-off

- [ ] `manage.py check --deploy` is clean when run inside the container
      with production env vars:
      `docker compose -f compose.yml exec bohlale-grc python manage.py check --deploy`
- [ ] Real SMTP configured in `.env` (`EMAIL_*`) if outbound email
      notifications are wanted — otherwise notifications stay correctly
      in-app-only.
- [ ] `POPIA_READINESS.md` organisational items (Information Officer,
      PAIA manual, retention schedule, breach-notification procedure)
      are being handled by the deploying organisation — these are legal/
      organisational decisions, not something this checklist's commands
      can complete.
- [ ] `SECURITY_AUDIT.md` and `PRODUCTION_READINESS.md` have been read
      by whoever is accountable for this deployment.

Once every box above is checked, this deployment is live and matches
the codebase's documented production-readiness posture.
