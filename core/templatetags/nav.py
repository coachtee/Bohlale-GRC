from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag
def safe_url(name, *args):
    """
    Like {% url %} but returns '#' instead of raising when the target
    view hasn't been implemented yet. Used by the sidebar so navigation
    can be wired to final URL names ahead of each module landing,
    without breaking earlier modules while later ones are still WIP.
    """
    try:
        return reverse(name, args=args)
    except NoReverseMatch:
        return "#"


@register.simple_tag(takes_context=True)
def nav_active(context, *prefixes):
    request = context.get("request")
    if not request:
        return ""
    path = request.path
    for prefix in prefixes:
        if path.startswith(prefix):
            return "active"
    return ""
