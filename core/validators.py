import os

from django.conf import settings
from django.core.exceptions import ValidationError


def validate_upload_file(uploaded_file):
    """Secure file upload validation (spec §45): restrict to an
    allow-list of extensions and enforce a maximum size."""
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Allowed types: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}."
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if uploaded_file.size > max_bytes:
        raise ValidationError(f"File is too large — maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB.")
