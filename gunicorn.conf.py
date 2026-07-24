"""
Generic production Gunicorn configuration, entirely environment-driven so
this file can be reused unchanged across projects (Bohlale GRC, Learn,
Health, Notes, ...). See .env.example for the GUNICORN_* variables.
"""

import multiprocessing
import os

bind = f"0.0.0.0:{os.environ.get('GUNICORN_PORT', '8000')}"

# Default: (2 x CPU cores) + 1, the standard Gunicorn rule of thumb.
# Override with GUNICORN_WORKERS for a specific VPS/container size.
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")
threads = int(os.environ.get("GUNICORN_THREADS", "1"))

timeout = int(os.environ.get("GUNICORN_TIMEOUT", "60"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

# Recycle workers periodically to bound the impact of any slow memory
# leak over long uptimes; jitter avoids every worker restarting at once.
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.environ.get("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# Load the application once in the master process before forking workers:
# lower memory use and faster worker startup. Safe here because Django
# does not open the database connection at import time - each worker
# lazily connects on its first query after forking.
preload_app = True

accesslog = "-"  # stdout - captured by `docker logs` / systemd journal
errorlog = "-"   # stderr
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
access_log_format = (
    '%(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sus'
)

# Don't let a client hold a worker open indefinitely uploading a large
# document - matches Django's own MAX_UPLOAD_SIZE_MB expectations.
limit_request_line = int(os.environ.get("GUNICORN_LIMIT_REQUEST_LINE", "4094"))
