"""Listing media input contract (Sprint 02: A2-04, A2-06).

Images (cover, gallery):
* multipart file or ``data:image/...;base64,`` string only. Any other string
  (URL, provider public ID) is a 400 before any reservation or provider call:
  provider references are server-owned and never accepted from clients.
* decoded by Pillow; format JPEG/MPO, PNG, WebP, HEIF/HEIC, AVIF or GIF;
  at most ``IMAGE_MAX_BYTES`` encoded and ``IMAGE_MAX_PIXELS`` decoded pixels;
  decompression bombs and truncated files are rejected.
Video:
* multipart MP4/QuickTime only, at most ``VIDEO_MAX_BYTES``; container, codec,
  dimensions and duration (≤ 60 s) are measured by the shared bounded decoder
  (``common.private_media_policy.inspect_video_path``), not taken from the
  client. The stored ``video_duration`` is the measured value.
"""

import base64
import binascii
import hashlib
import math
import tempfile
import warnings
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import serializers

IMAGE_MAX_BYTES = 20 * 1024 * 1024
IMAGE_MAX_PIXELS = 50_000_000
IMAGE_FORMATS = {"JPEG", "MPO", "PNG", "WEBP", "HEIF", "AVIF", "GIF"}
IMAGE_MIME_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/heic": "heic",
    "image/heif": "heif",
    "image/avif": "avif",
    "image/gif": "gif",
}
VIDEO_MAX_BYTES = 50 * 1024 * 1024
VIDEO_MAX_DURATION_MS = 60_500  # 60 s product limit plus encoder rounding
VIDEO_EXTENSIONS = {"mp4", "mov", "m4v"}
LISTING_IMAGE_CAP = 25


def _decode_data_uri(data):
    header, separator, encoded = data.partition(";base64,")
    mime = header[5:].lower() if header.startswith("data:") else ""
    extension = IMAGE_MIME_EXTENSIONS.get(mime)
    if not separator or extension is None:
        raise serializers.ValidationError("Upload a valid supported image.")
    if len(encoded) > IMAGE_MAX_BYTES * 4 // 3 + 4:
        raise serializers.ValidationError("Images must not exceed 20 MiB.")
    try:
        content = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise serializers.ValidationError("Invalid base64 image data.")
    return SimpleUploadedFile(
        hashlib.sha256(content).hexdigest()[:16] + "." + extension,
        content,
        content_type=mime,
    )


def validate_listing_image(upload):
    """Return ``upload`` after a bounded decode; never re-encodes the bytes."""
    from PIL import Image, UnidentifiedImageError
    from pillow_heif import register_heif_opener

    register_heif_opener(thumbnails=False)
    size = getattr(upload, "size", None)
    if not hasattr(upload, "read") or not size:
        raise serializers.ValidationError("Upload a non-empty image file.")
    if size > IMAGE_MAX_BYTES:
        raise serializers.ValidationError("Images must not exceed 20 MiB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            upload.seek(0)
            with Image.open(upload) as source:
                if source.format not in IMAGE_FORMATS:
                    raise ValueError("format")
                if source.width * source.height > IMAGE_MAX_PIXELS:
                    raise ValueError("pixels")
                source.load()  # full decode: truncated/corrupt data fails here
                content_type = Image.MIME.get(source.format, "")
    except (
        OSError,
        ValueError,
        SyntaxError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise serializers.ValidationError(
            "Upload a valid JPEG, PNG, WebP, HEIC, AVIF or GIF image within the "
            "size limits."
        )
    finally:
        try:
            upload.seek(0)
        except (OSError, ValueError):
            pass
    if content_type and getattr(upload, "content_type", None) in (None, "", "application/octet-stream"):
        upload.content_type = content_type
    return upload


class ListingImageField(serializers.ImageField):
    """Cover/gallery input: an actual image, never a client-supplied reference."""

    def to_internal_value(self, data):
        if isinstance(data, str):
            if not data.startswith("data:"):
                raise serializers.ValidationError(
                    "Upload the image itself; existing provider references cannot be attached."
                )
            data = _decode_data_uri(data)
        return validate_listing_image(data)

    def to_representation(self, value):
        if not value:
            return None
        return value.url if hasattr(value, "url") else str(value)


def measure_listing_video(upload):
    """Return the decoded duration in ms for a listing video upload."""
    from core_apps.common.private_media_policy import inspect_video_path

    size = getattr(upload, "size", None)
    if not hasattr(upload, "read") or not size:
        raise serializers.ValidationError("Upload a non-empty video file.")
    if size > VIDEO_MAX_BYTES:
        raise serializers.ValidationError("Videos must not exceed 50 MiB.")
    upload.seek(0)
    head = upload.read(12)
    upload.seek(0)
    if len(head) < 12 or head[4:8] != b"ftyp":
        raise serializers.ValidationError("Upload an MP4 or QuickTime video.")
    try:
        if hasattr(upload, "temporary_file_path"):
            meta = inspect_video_path(
                Path(upload.temporary_file_path()),
                max_duration_ms=VIDEO_MAX_DURATION_MS,
            )
        else:
            with tempfile.TemporaryDirectory(prefix="sokoun-listing-video-") as folder:
                path = Path(folder) / "source.mp4"
                with path.open("wb") as target:
                    for chunk in upload.chunks():
                        target.write(chunk)
                meta = inspect_video_path(path, max_duration_ms=VIDEO_MAX_DURATION_MS)
    except (ValueError, TypeError, KeyError, OSError) as error:
        raise serializers.ValidationError(
            "Upload an H.264/HEVC/MPEG-4 MP4 or QuickTime video of at most 60 seconds."
        ) from error
    finally:
        upload.seek(0)
    return meta["duration_ms"]


class ListingVideoField(serializers.FileField):
    def to_internal_value(self, data):
        upload = super().to_internal_value(data)
        upload.sukoon_duration_ms = measure_listing_video(upload)
        return upload

    def to_representation(self, value):
        if not value:
            return None
        return value.url if hasattr(value, "url") else str(value)


def measured_seconds(duration_ms):
    return max(1, min(60, math.ceil(duration_ms / 1000 - 0.25)))
