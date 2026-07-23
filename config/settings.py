"""
Django settings for the Bohlale GRC project.

Configuration is environment-driven (see .env.example) so the same
codebase runs unmodified in local development (SQLite) and on a
production VPS (PostgreSQL + Gunicorn + Nginx). See DEPLOYMENT.md.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    value = os.environ.get(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# --- Core / security -------------------------------------------------

_INSECURE_DEFAULT_SECRET_KEY = "django-insecure-dev-only-key-change-in-production-4f8c2e9a1b3d"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", _INSECURE_DEFAULT_SECRET_KEY)

DEBUG = env_bool("DJANGO_DEBUG", default=True)

if not DEBUG and SECRET_KEY == _INSECURE_DEFAULT_SECRET_KEY:
    # Refuse to boot in production with the checked-in dev key rather
    # than silently running with a well-known, guessable SECRET_KEY
    # (spec §45: "environment-based secrets"). Generate a real one with:
    #   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    raise RuntimeError(
        "DJANGO_SECRET_KEY is not set (or still the insecure dev default) while "
        "DJANGO_DEBUG=False. Set a real, random DJANGO_SECRET_KEY in the "
        "environment before running with DEBUG off. See DEPLOYMENT.md."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

# DEPLOYMENT.md's documented topology terminates TLS at Nginx and proxies
# to Gunicorn over a filesystem Unix socket (never a TCP port reachable
# from outside the box), so Nginx is the only process that can set this
# header — trusting it here is safe under that topology and is required:
# without it, request.is_secure() is always False behind the proxy, and
# DJANGO_SECURE_SSL_REDIRECT=True would redirect-loop forever once HTTPS
# is enabled (step 8). Do not change this to trust a TCP-exposed Gunicorn.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=False)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # HTMX needs to read the CSRF cookie from JS
SESSION_COOKIE_AGE = int(os.environ.get("DJANGO_SESSION_COOKIE_AGE", 60 * 60 * 24 * 7))  # 7 days
SESSION_EXPIRE_AT_BROWSER_CLOSE = env_bool("DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE", default=False)
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# --- Applications ------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

# Bohlale GRC modular monolith apps.
# Order matters only where migrations depend on one another; Django
# resolves FK ordering via migrations regardless of INSTALLED_APPS order.
LOCAL_APPS = [
    "core",
    "accounts",
    "tenancy",
    "activity",
    "notifications",
    "knowledge",
    "ai",
    "frameworks",
    "journeys",
    "documents",
    "approvals",
    "risks",
    "controls",
    "evidence",
    "assessments",
    "assets",
    "suppliers",
    "incidents",
    "registers",
    "audits",
    "actions",
    "reviews",
    "reports",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.SecurityHeadersMiddleware",
    "tenancy.middleware.TenantMiddleware",
    "activity.middleware.CurrentUserMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tenancy.context_processors.active_organisation",
                "notifications.context_processors.notification_counts",
                "core.context_processors.build_info",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Database ------------------------------------------------------------

if os.environ.get("DB_ENGINE", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "bohlale_grc"),
            "USER": os.environ.get("DB_USER", "bohlale"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# --- Auth ------------------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"


# --- Internationalization -------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True


# --- Static & media files -------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
            if not DEBUG
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}

WHITENOISE_USE_FINDERS = DEBUG
WHITENOISE_AUTOREFRESH = DEBUG

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "25"))
ALLOWED_UPLOAD_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".ppt", ".pptx",
    ".png", ".jpg", ".jpeg", ".gif", ".txt", ".zip", ".msg", ".eml",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Email -----------------------------------------------------------

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Bohlale GRC <no-reply@bohlalegrc.example>"
)


# --- AI provider abstraction (see ai/ app) --------------------------------

AI_PROVIDER = os.environ.get("AI_PROVIDER", "mock")
AI_API_BASE = os.environ.get("AI_API_BASE", "")
AI_API_KEY = os.environ.get("AI_API_KEY", "")
AI_MODEL = os.environ.get("AI_MODEL", "gpt-4o-mini")


# --- Logging -------------------------------------------------------------
# Deliberately console-only (stdout/stderr), not a file handler with its
# own rotation: the documented production setup (DEPLOYMENT.md) runs
# under systemd, which already captures stdout/stderr into the journal
# with its own rotation/retention (`journalctl -u bohlale-grc`) — adding
# a second, independently-rotated log file would just be a second
# thing to keep in sync with no real benefit for a single-VPS deployment.
# Never logs request bodies, passwords, or the AI_API_KEY — see
# SECURITY_AUDIT.md for what was checked here.

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "structured"},
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        # django.request/django.security (4xx/5xx, PermissionDenied,
        # SuspiciousOperation) inherit this and propagate up to it.
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "bohlale": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
