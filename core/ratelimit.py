"""
Minimal cache-based rate limiting (spec §45: "rate limiting where
appropriate"). No Redis/Celery required — uses Django's default cache
backend, which is enough to blunt brute-force/enumeration attempts on
the platform's unauthenticated entry points (login, the public
token-based information-request response page). Limits requests per
client IP within a rolling window.
"""

from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def rate_limit(key_prefix, limit=10, window_seconds=300, methods=None):
    """
    `methods` optionally restricts counting to specific HTTP verbs (e.g.
    ``["POST"]``) so plain page loads (GET) don't eat into the budget —
    important for a login page, which legitimate users reload/revisit
    far more often than they actually submit credentials.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if methods is None or request.method in methods:
                cache_key = f"ratelimit:{key_prefix}:{_client_ip(request)}"
                count = cache.get(cache_key, 0)
                if count >= limit:
                    return HttpResponse("Too many requests. Please try again later.", status=429)
                cache.set(cache_key, count + 1, window_seconds)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
