"""
Security response headers not covered by Django's built-in
SecurityMiddleware settings (spec §45: "Content Security Policy where
practical").

A custom middleware (rather than a third-party package) keeps the
dependency list small, per the project's "no mandatory Redis/extra
infrastructure" principle — this is a few lines of pure Python with no
new package to track.

The policy is strict on script-src (no 'unsafe-inline', no CDNs — htmx
and app.js are the only scripts, both vendored locally and loaded via
<script src>, and every inline onclick/onchange handler in the templates
has been replaced with data-attributes handled centrally in app.js) but
allows 'unsafe-inline' for style-src, since several dashboard widgets
(donut charts, progress bars) use server-computed inline `style="..."`
attributes rather than a JS charting library — refactoring those to
nonce'd/external CSS was judged not worth the added complexity for a
low-risk surface (attacker-controlled data never reaches those inline
styles; they're built from server-side aggregate numbers).
"""

CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "object-src 'none'"
)


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", CSP_POLICY)
        # Referrer-Policy is set natively via Django's SECURE_REFERRER_POLICY
        # setting (config/settings.py) — no need to duplicate it here.
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response
