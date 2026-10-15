"""One policy shared by validation, summary contracts and retention jobs."""

from django.conf import settings
from rest_framework.exceptions import APIException

DEFAULTS = {
    "text_max_code_points": 4000,
    "images_per_message": 5,
    "image_max_bytes": 10 * 1024 * 1024,
    "image_max_pixels": 20_000_000,
    "image_max_edge": 2560,
    "voice_min_duration_ms": 1000,
    "voice_max_duration_ms": 120000,
    "voice_max_bytes": 10 * 1024 * 1024,
    "history_page_size": 30,
    "history_max_page_size": 100,
    "upload_concurrency": 2,
    "orphan_retention_hours": 24,
    "image_mime_types": ["image/jpeg", "image/png", "image/webp"],
    "voice_mime_types": ["audio/mp4"],
}


def limits():
    return {**DEFAULTS, **getattr(settings, "CHAT_MEDIA_LIMITS", {})}


class ChatConflict(APIException):
    status_code = 409
    default_code = "chat_identity_conflict"
    default_detail = "This identity belongs to a different operation."


class ChatResync(APIException):
    status_code = 409
    default_code = "chat_resync_required"
    default_detail = "Reload the conversation before continuing."


class ChatUnavailable(APIException):
    status_code = 503
    default_code = "chat_unavailable"
    default_detail = "Chat is temporarily unavailable. Please try again."
