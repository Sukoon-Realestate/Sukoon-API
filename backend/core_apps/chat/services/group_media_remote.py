"""Durable private chat objects; URLs and provider credentials never reach clients."""

import hashlib
import re
import tempfile
from pathlib import Path

from django.conf import settings
from core_apps.virtual_tours import cloudinary_storage as cloud
from .group_limits import ChatUnavailable, limits


def configured():
    provider = getattr(settings, "CHAT_PRIVATE_STORAGE_PROVIDER", "local")
    if provider not in {"local", "cloudinary"}:
        raise ChatUnavailable("Private media storage is not configured.")
    return provider == "cloudinary"


def identity(key):
    if not re.fullmatch(r"[a-f0-9]{32}\.(jpg|m4a|bin|mp4)", key):
        raise ChatUnavailable("Invalid private attachment identity.")
    prefix = settings.CHAT_CLOUDINARY_PREFIX
    if prefix == settings.VIRTUAL_TOUR_CLOUDINARY_PREFIX:
        raise ChatUnavailable("Chat storage requires its own private namespace.")
    cloud.object_id(key[:32], "manifest", prefix=prefix)
    return key[:32], prefix


def persist(key, source):
    if not configured():
        return
    try:
        token, prefix = identity(key)
        cloud.persist(token, source, prefix=prefix)
    except Exception as exc:
        raise ChatUnavailable(
            "Private media could not be saved. Retry the upload."
        ) from exc


def materialize(key, target):
    if target.is_symlink():
        raise ChatUnavailable("Invalid private attachment cache.")
    if target.is_file():
        return target
    if not configured():
        raise FileNotFoundError()
    try:
        token, prefix = identity(key)
        kind = {"jpg": "image", "m4a": "voice", "bin": "file", "mp4": "video"}[
            key.rsplit(".", 1)[1]
        ]
        return cloud.materialize(
            token,
            target,
            prefix=prefix,
            maximum=limits()[f"{kind}_max_bytes"],
        )
    except Exception as exc:
        raise ChatUnavailable(
            "Private media is temporarily unavailable. Retry."
        ) from exc


def verify_backup(key, source):
    """Migration must prove remote bytes before the ephemeral service is replaced."""
    if not configured():
        raise ChatUnavailable("Durable private storage is not enabled.")
    with tempfile.TemporaryDirectory(prefix="chat-backfill-") as directory:
        restored = materialize(key, Path(directory) / key)
        if (
            hashlib.sha256(source.read_bytes()).digest()
            != hashlib.sha256(restored.read_bytes()).digest()
        ):
            raise ChatUnavailable("Private media backup did not match its source.")


def remove(key):
    if not configured():
        return
    try:
        token, prefix = identity(key)
        cloud.remove(token, prefix=prefix)
    except Exception as exc:
        raise ChatUnavailable("Private media removal will need to be retried.") from exc


def sweep(referenced, threshold):
    if not configured():
        return 0
    try:
        keys = {identity(key)[0] for key in referenced if key}
        _, prefix = identity("0" * 32 + ".jpg")
        return cloud.sweep(keys, threshold, prefix=prefix)
    except Exception as exc:
        raise ChatUnavailable("Private media cleanup will need to be retried.") from exc
