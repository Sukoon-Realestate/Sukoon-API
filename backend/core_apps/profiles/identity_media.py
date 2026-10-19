"""Identity assets are private provider resources, never public CDN links."""

import hashlib
import time
import requests
from cloudinary.models import CloudinaryField
from cloudinary.utils import private_download_url
from django.http import HttpResponse
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound

IDENTITY_FIELDS = frozenset({"id_face", "id_back", "confirmation_selfi"})
MAX_IDENTITY_BYTES = 10 * 1024 * 1024


class IdentityImageField(serializers.ImageField):
    """Keep multipart/base64 image inputs; reject borrowed URLs and public IDs."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            import base64
            import binascii
            import uuid
            from django.core.files.uploadedfile import SimpleUploadedFile

            if not data.startswith("data:image/") or ";base64," not in data:
                raise serializers.ValidationError("Upload the identity image itself.")
            header, encoded = data.split(";base64,", 1)
            extension = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
                "image/gif": "gif",
            }.get(header[5:])
            if extension is None:
                raise serializers.ValidationError("Use a JPEG, PNG, WebP or GIF image.")
            if len(encoded) > (MAX_IDENTITY_BYTES * 4 // 3 + 4):
                raise serializers.ValidationError(
                    "Identity images must not exceed 10 MiB."
                )
            try:
                content = base64.b64decode(encoded, validate=True)
            except (ValueError, binascii.Error):
                raise serializers.ValidationError("Invalid base64 image data.")
            data = SimpleUploadedFile(
                uuid.uuid4().hex + "." + extension, content, content_type=header[5:]
            )
        image = super().to_internal_value(data)
        if image.content_type not in {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        }:
            raise serializers.ValidationError("Use a JPEG, PNG, WebP or GIF image.")
        if image.size > MAX_IDENTITY_BYTES:
            raise serializers.ValidationError("Identity images must not exceed 10 MiB.")
        return image


def reference(value):
    if not value:
        return ""
    return value.get_prep_value() if hasattr(value, "get_prep_value") else str(value)


def version(value):
    return hashlib.sha256(reference(value).encode()).hexdigest()


def identity_bytes(value):
    """Fetch from the provider API after caller authorization; do not redirect."""
    raw = reference(value)
    # Legacy/public references require the separately audited storage conversion.
    if not raw.startswith("image/authenticated/"):
        raise NotFound("Protected identity evidence is unavailable.")
    asset = CloudinaryField().to_python(raw)
    if not asset.public_id or not asset.format:
        raise NotFound("Protected identity evidence is unavailable.")
    url = private_download_url(
        asset.public_id,
        asset.format,
        type="authenticated",
        resource_type="image",
        expires_at=int(time.time()) + 60,
    )
    try:
        with requests.get(
            url, stream=True, timeout=(5, 15), allow_redirects=False
        ) as response:
            if response.status_code != 200:
                raise ValueError("Provider read unconfirmed")
            content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
            if content_type not in {
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/gif",
            }:
                raise ValueError("Unsupported identity media")
            content = bytearray()
            for chunk in response.iter_content(64 * 1024):
                content.extend(chunk)
                if len(content) > MAX_IDENTITY_BYTES:
                    raise ValueError("Identity media exceeds the read limit")
    except (requests.RequestException, ValueError):
        error = APIException(
            "Identity evidence could not be retrieved. Retry the original document."
        )
        error.status_code = 503
        raise error
    result = HttpResponse(bytes(content), content_type=content_type)
    result["Cache-Control"] = "private, no-store, max-age=0"
    result["Pragma"] = "no-cache"
    result["X-Content-Type-Options"] = "nosniff"
    result["Content-Security-Policy"] = "default-src 'none'; sandbox"
    result["Content-Disposition"] = 'inline; filename="identity-evidence"'
    return result
