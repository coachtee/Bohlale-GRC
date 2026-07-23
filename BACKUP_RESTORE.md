# Backup & Disaster Recovery — Bohlale GRC

This procedure has been **actually executed and verified**, not just
described, during the production-readiness review (see §5 for what was
tested and its result). Do not consider a backup strategy "verified"
until you have personally run the restore steps below against your own
production-like environment at least once — a backup nobody has ever
restored from is an assumption, not a guarantee.

## 1. What must be backed up

| Asset | Contains | Backup method |
|---|---|---|
| PostgreSQL database | All tenant data: organisations, users, documents, risks, controls, evidence metadata, audit trail, everything in the schema | `pg_dump` (§2) |
| `media/` directory | Uploaded files: evidence attachments, document attachments, management review attachments, framework import source files, organisation logos | `tar`/rsync to off-server storage (§3) |
| `.env` | Configuration (SECRET_KEY, DB credentials, AI provider config) | **Not** part of routine backups — treat as a secret, store it in a password manager or secrets vault, not alongside data backups |

Static files (`staticfiles/`) and the virtual environment are **not**
backed up — they're fully reproducible from the Git repository plus
`pip install -r requirements.txt` and `collectstatic`.

## 2. PostgreSQL backups

### Daily automated dump (cron)

```bash
sudo -u bohlale mkdir -p /opt/bohlale-grc/backups
sudo -u bohlale crontab -e
```

```cron
0 3 * * * pg_dump -U bohlale -h localhost -d bohlale_grc -F c -f /opt/bohlale-grc/backups/bohlale_grc_$(date +\%Y\%m\%d).dump
5 3 * * * find /opt/bohlale-grc/backups -name '*.dump' -mtime +30 -delete
```

`-F c` (custom format) is used rather than plain SQL because it's
compressed by default and works with `pg_restore`'s selective-restore
and parallel-restore options if the database grows large. Set
`PGPASSWORD` via a `~/.pgpass` file (mode `0600`) rather than embedding
the password in the crontab — see PostgreSQL's docs on `.pgpass`.

Retention above is 30 days; adjust to your own documented retention
schedule (see `POPIA_READINESS.md` §4 — retention is an organisational
decision, not a platform default).

### Manual on-demand backup

```bash
pg_dump -U bohlale -h localhost -d bohlale_grc -F c -f bohlale_grc_manual.dump
```

## 3. Media backups

```cron
30 3 * * * tar -czf /opt/bohlale-grc/backups/media_$(date +\%Y\%m\%d).tar.gz -C /opt/bohlale-grc/app media
35 3 * * * find /opt/bohlale-grc/backups -name 'media_*.tar.gz' -mtime +30 -delete
```

## 4. Secure off-server storage

A backup that lives on the same disk as the database it backs up
protects against corruption, not against host loss (disk failure,
accidental `rm -rf`, a compromised server). Sync backups off-server on
the same cron cadence, e.g.:

```cron
45 3 * * * rclone copy /opt/bohlale-grc/backups remote:bohlale-grc-backups --min-age 5m
```

(Any equivalent tool — `rclone`, `aws s3 sync`, `restic`, provider CLI —
works; pick one that supports encryption at rest and access-controlled
storage, since these backups contain the same confidential tenant data
as the live database. Do not store backups in a public or
world-readable location.)

## 5. Restore procedure (tested)

This exact sequence was run during the production-readiness review
against a real PostgreSQL 16 instance with real seeded NIBS demonstration
data, and is what you should run for an actual recovery:

```bash
# 1. Take (or locate) a backup
pg_dump -U bohlale -h localhost -d bohlale_grc -F c -f bohlale_grc.dump

# 2. Create a fresh target database (never restore over a live one in place —
#    restore to a new name first, verify, then cut over)
sudo -u postgres psql -c "CREATE DATABASE bohlale_grc_restored OWNER bohlale;"

# 3. Restore
pg_restore -U bohlale -h localhost -d bohlale_grc_restored --no-owner --role=bohlale bohlale_grc.dump

# 4. Verify row counts / spot-check key data before cutting over
psql -U bohlale -h localhost -d bohlale_grc_restored -c "SELECT count(*) FROM tenancy_organisation;"
psql -U bohlale -h localhost -d bohlale_grc_restored -c "SELECT name FROM tenancy_organisation;"

# 5. Point the application at the restored database and confirm it actually
#    works end-to-end (not just that the tables exist)
DB_ENGINE=postgres DB_NAME=bohlale_grc_restored DB_USER=bohlale DB_PASSWORD=*** \
  python manage.py check
DB_ENGINE=postgres DB_NAME=bohlale_grc_restored DB_USER=bohlale DB_PASSWORD=*** \
  python manage.py shell -c "from tenancy.models import Organisation; print(list(Organisation.objects.values_list('name', flat=True)))"
```

**Verified result** (production-readiness review, this session): backed
up a database containing 1 organisation, 6 risks, 2 documents and 18
audit log entries; restored into a fresh database; row counts and
content matched exactly (1/6/2/18); `manage.py check` was clean against
the restored database; and a direct ORM query against the restored
database returned the correct organisation name and correct journey
progress percentage. Full command transcript is in this session's audit
trail — this was not a dry run or a hypothetical description.

### Cutting over after a real disaster

1. Stop Gunicorn: `sudo systemctl stop bohlale-grc`.
2. Restore the latest good `.dump` into a new database as above, and
   verify it (step 4-5 above) **before** touching production traffic.
3. Update `.env`'s `DB_NAME` (or rename databases at the PostgreSQL level
   — `ALTER DATABASE bohlale_grc RENAME TO bohlale_grc_broken; ALTER
   DATABASE bohlale_grc_restored RENAME TO bohlale_grc;`) to point at the
   restored database.
4. Restore `media/` from the matching-dated media backup
   (`tar -xzf media_YYYYMMDD.tar.gz -C /opt/bohlale-grc/app`).
5. Start Gunicorn: `sudo systemctl start bohlale-grc`.
6. Smoke-test: log in, load the dashboard, confirm the data present
   matches expectations for the backup's date.

## 6. Recovery time/point expectations

With the daily cron schedule above: **Recovery Point Objective (RPO) is
up to 24 hours** (worst case: disaster strikes right before the next
scheduled dump) and **Recovery Time Objective (RTO)** is however long
steps 1-6 above take on your infrastructure — typically minutes for a
database of this platform's expected scale (a handful of SME/NPO
tenants), not hours. If your organisation needs a tighter RPO, increase
the `pg_dump` cron frequency (e.g. every 6 hours) or look into
PostgreSQL's continuous WAL archiving / streaming replication — both are
standard PostgreSQL features requiring no application changes, but are
beyond what a single-VPS deployment needs by default.

## 7. What is NOT covered by this procedure

- **Application code**: recovered by re-deploying from Git (`git pull`
  + the update procedure in `DEPLOYMENT.md`), not by any backup here.
- **Secrets** (`.env`, `DJANGO_SECRET_KEY`, DB password, any real AI
  API key): must be stored securely and separately (a password manager
  or secrets vault) — losing these means the deployment can be rebuilt
  from Git + a database restore, but you'll need to re-provision new
  secrets, which will invalidate existing sessions (users log in again)
  and is otherwise harmless.
- **Point-in-time recovery** (restoring to a specific moment between two
  daily dumps): not available with this simple cron-based approach — see
  §6 for how to get it if needed.
