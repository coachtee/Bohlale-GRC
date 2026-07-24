# syntax=docker/dockerfile:1
#
# Generic production Dockerfile for a Django + Gunicorn + PostgreSQL project.
# Written for Bohlale GRC but deliberately project-agnostic: nothing below
# references "bohlale" or "grc" by name. To reuse for another Django project
# (Bohlale Learn, Bohlale Health, Bohlale Notes, ...), copy this file
# unchanged — only requirements.txt, the app code, and .env need to differ.
#
# Two stages:
#   builder  - installs build tooling + Python deps into a venv (discarded)
#   runtime  - slim image with only the venv + app code + a non-root user
#
# This keeps the final image small and avoids shipping compilers/headers
# into production.

ARG PYTHON_VERSION=3.11

########################################################################
# Stage 1: builder
########################################################################
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# build-essential + libpq-dev cover the common case of compiling any C
# extension a project's requirements.txt might pull in (e.g. a non-binary
# psycopg2, lxml, cryptography); harmless if unused.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

########################################################################
# Stage 2: runtime
########################################################################
FROM python:${PYTHON_VERSION}-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}" \
    DJANGO_SETTINGS_MODULE=config.settings \
    APP_HOME=/app

# libpq5   - Postgres client library (runtime counterpart of libpq-dev)
# curl     - used by the container HEALTHCHECK below and deployment/health.sh
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv

WORKDIR ${APP_HOME}

# Copy application code. .dockerignore keeps .git, .venv, local media/db,
# and other dev-only artifacts out of the build context entirely.
COPY --chown=app:app . .

RUN mkdir -p staticfiles media logs \
    && chown -R app:app staticfiles media logs \
    && chmod +x entrypoint.sh

USER app

EXPOSE 8000

# Matches core/views.py::health — a real DB round-trip, not just "process
# alive". Compose also defines its own healthcheck (with depends_on
# service_healthy wiring); this one lets `docker inspect`/`docker ps`
# report container health even when run standalone (docker run), and is
# the same check deployment/health.sh polls from outside the container.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "-c", "gunicorn.conf.py", "config.wsgi:application"]
