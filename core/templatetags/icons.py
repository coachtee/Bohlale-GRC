"""
A small, self-authored set of minimal line icons (24x24, stroke-based)
used throughout the UI, in keeping with the "simple icons" design
requirement — no external icon-font or icon-library dependency.
"""

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_ICONS = {
    "dashboard": '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
    "org": '<path d="M4 21V5a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v16"/><path d="M14 21v-9a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v9"/><path d="M8 8h0M8 12h0M8 16h0"/><path d="M2 21h20"/>',
    "journey": '<circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.5 7 15.5 17"/><circle cx="18" cy="6" r="2.5"/><path d="M15.7 6.8 9 16.2"/>',
    "framework": '<path d="M4 19.5V5a2 2 0 0 1 2-2h11a1 1 0 0 1 1 1v13H6a2 2 0 0 0 0 4h12"/>',
    "document": '<path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h6"/>',
    "risk": '<path d="M12 3 2 20h20L12 3Z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    "control": '<path d="m9 12 2 2 4-4"/><path d="M12 3c3 1.5 5 2 8 2v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V5c3 0 5-.5 8-2Z"/>',
    "evidence": '<path d="M12 2 3 6v6c0 5 4 9 9 10 5-1 9-5 9-10V6l-9-4Z"/><path d="M9 12h6M9 8h6M9 16h4"/>',
    "asset": '<rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/>',
    "supplier": '<path d="M3 10 12 4l9 6"/><path d="M5 10v9h14v-9"/><path d="M9 19v-5h6v5"/>',
    "incident": '<path d="M10.3 3.9 2.6 17a1.6 1.6 0 0 0 1.4 2.4h16a1.6 1.6 0 0 0 1.4-2.4L13.7 3.9a1.6 1.6 0 0 0-2.8 0Z"/><path d="M12 9.5v4"/><path d="M12 16.5h.01"/>',
    "register": '<path d="M6 2h9l5 5v13a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "audit": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m20 20-4.4-4.4"/><path d="m8 10.5 1.7 1.7L13.5 8"/>',
    "action": '<circle cx="12" cy="12" r="9"/><path d="m9 12 2 2 4-4"/>',
    "report": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "settings": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.2.63.76 1.09 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>',
    "help": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.8.4-1.5 1-1.5 2.2"/><path d="M12 17h.01"/>',
    "headset": '<path d="M4 13v-1a8 8 0 0 1 16 0v1"/><rect x="3" y="13" width="4" height="6" rx="1.5"/><rect x="17" y="13" width="4" height="6" rx="1.5"/><path d="M19 19v1a3 3 0 0 1-3 3h-2"/>',
    "bell": '<path d="M18 8a6 6 0 1 0-12 0c0 6-2.5 7-2.5 7h17S18 14 18 8Z"/><path d="M10.5 20a1.7 1.7 0 0 0 3 0"/>',
    "question": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.8.4-1.5 1-1.5 2.2"/><path d="M12 17h.01"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "menu": '<path d="M3 6h18M3 12h18M3 18h18"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "upload": '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    "message": '<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "arrow-right": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "check": '<path d="m5 12 5 5 9-9"/>',
    "building": '<path d="M4 21V5a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v16"/><path d="M14 21v-9a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v9"/><path d="M2 21h20"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="M16 17l5-5-5-5"/><path d="M21 12H9"/>',
    "x": '<path d="M18 6 6 18M6 6l12 12"/>',
    "alert": '<path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.3 3.9 2.6 17a1.6 1.6 0 0 0 1.4 2.4h16a1.6 1.6 0 0 0 1.4-2.4L13.7 3.9a1.6 1.6 0 0 0-2.8 0Z"/>',
    "sparkle": '<path d="M12 3v4M12 17v4M3 12h4M17 12h4"/><path d="m6.5 6.5 2 2M15.5 15.5l2 2M17.5 6.5l-2 2M8.5 15.5l-2 2"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v5h1"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
    "trash": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13"/>',
    "edit": '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    "download": '<path d="M12 4v12M7 11l5 5 5-5"/><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/>',
    "link": '<path d="M9 17H7a5 5 0 0 1 0-10h2"/><path d="M15 7h2a5 5 0 0 1 0 10h-2"/><path d="M8 12h8"/>',
    "shield-check": '<path d="M12 3l8 3v6c0 5-3.4 8.5-8 9-4.6-.5-8-4-8-9V6Z"/><path d="m9 12 2 2 4-4"/>',
    # The Bohlale mark: an infinity loop, in the same minimal stroke
    # style as every other icon here — used sparingly (spec §19) for
    # onboarding/completion moments, not as a general-purpose icon.
    "bohlale_mark": '<path d="M18.2 8.5c-2.9 0-4.7 2-6.2 3.9C10.5 10.5 8.7 8.5 5.8 8.5 3.7 8.5 2 10.3 2 12.5s1.7 4 3.8 4c2.9 0 4.7-2 6.2-3.9 1.5 1.9 3.3 3.9 6.2 3.9 2.1 0 3.8-1.8 3.8-4s-1.7-4-3.8-4Z"/>',
}


@register.simple_tag
def icon(name, css_class="nav-icon"):
    body = _ICONS.get(name, _ICONS["info"])
    svg = (
        f'<svg class="{css_class}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" aria-hidden="true">{body}</svg>'
    )
    return mark_safe(svg)
