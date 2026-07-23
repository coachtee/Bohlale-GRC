"""
Tenant-checked file delivery (spec §45/§7: sensitive tenant documents
must not become reachable by URL alone).

Every uploaded file that carries real compliance content (evidence,
document attachments, management-review attachments) must be streamed
through a Django view that first confirms the owning object belongs to
`request.organisation`, instead of being served directly by Nginx/
WhiteNoise from MEDIA_ROOT. Callers are expected to have already fetched
`obj` via `get_object_or_404_scoped`/a `Tenant*View` so the tenant check
has already happened by the time this runs — this helper only handles
the actual byte-streaming and a consistent 404 when the field is empty.
"""

import os

from django.http import FileResponse, Http404


def serve_tenant_file(obj, field_name):
    file_field = getattr(obj, field_name, None)
    if not file_field:
        raise Http404
    try:
        handle = file_field.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404
    filename = os.path.basename(file_field.name)
    return FileResponse(handle, as_attachment=True, filename=filename)
