"""Private raw objects on an existing Cloudinary account.

Sources are split below the free plan's raw-file limit. A manifest is committed
last; neither provider URLs nor credentials are included in tour documents.
"""

import hashlib
import io
import json
import os
import re
import time
import uuid
from datetime import datetime

import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
import requests
from django.conf import settings

from .errors import TourError, require

CHUNK_BYTES = 8 * 1024**2
MAX_BYTES = 250 * 1024**2


def object_id(key, child, *, prefix=None):
    prefix = prefix or settings.VIRTUAL_TOUR_CLOUDINARY_PREFIX
    require(
        bool(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", prefix))
        and bool(re.fullmatch(r"[a-f0-9]{32}", key)),
        "storage_unavailable",
        "Invalid private storage namespace.",
        503,
    )
    return f"{prefix}/{key}/{child}"


def upload(identity, content):
    result = cloudinary.uploader.upload(
        io.BytesIO(content),
        public_id=identity,
        resource_type="raw",
        type="authenticated",
        overwrite=False,
        unique_filename=False,
        timeout=60,
    )
    require(
        result.get("public_id") == identity
        and result.get("type") == "authenticated"
        and result.get("bytes") == len(content),
        "storage_unavailable",
        "Private storage did not acknowledge the asset.",
        503,
    )


def download(identity, maximum):
    url = cloudinary.utils.private_download_url(
        identity,
        "",
        resource_type="raw",
        type="authenticated",
        expires_at=int(time.time()) + 60,
    )
    # The signed API URL is created by the SDK, never read from an uploaded file.
    with requests.get(url, stream=True, timeout=(10, 60)) as response:
        if response.status_code == 404:
            raise TourError("resource_missing", "The resource is unavailable.", 404)
        response.raise_for_status()
        result = bytearray()
        for chunk in response.iter_content(64 * 1024):
            require(
                len(result) + len(chunk) <= maximum,
                "asset_too_large",
                "Stored asset exceeds its limit.",
                413,
            )
            result.extend(chunk)
        return bytes(result)


def persist(key, source, child=None, *, prefix=None):
    try:
        if child:
            require(
                source.stat().st_size <= CHUNK_BYTES,
                "asset_too_large",
                "Tile exceeds its limit.",
                413,
            )
            upload(object_id(key, child, prefix=prefix), source.read_bytes())
            return
        size, parts = 0, []
        with source.open("rb") as handle:
            while chunk := handle.read(CHUNK_BYTES):
                size += len(chunk)
                require(
                    size <= MAX_BYTES,
                    "asset_too_large",
                    "Stored asset exceeds its limit.",
                    413,
                )
                digest = hashlib.sha256(chunk).hexdigest()
                part = {"sha256": digest, "bytes": len(chunk)}
                upload(
                    object_id(key, f"part-{len(parts)}-{digest}", prefix=prefix), chunk
                )
                parts.append(part)
        upload(
            object_id(key, "manifest", prefix=prefix),
            json.dumps(
                {
                    "version": 1,
                    "bytes": size,
                    "parts": parts,
                },
                separators=(",", ":"),
            ).encode(),
        )
    except TourError:
        raise
    except Exception as exc:
        raise TourError(
            "storage_unavailable", "Private storage is unavailable. Retry.", 503
        ) from exc


def materialize(key, target, child=None, *, prefix=None, maximum=MAX_BYTES):
    if target.is_file():
        return target
    temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".pending")
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        with temporary.open("xb") as handle:
            os.chmod(temporary, 0o600)
            if child:
                handle.write(
                    download(object_id(key, child, prefix=prefix), CHUNK_BYTES)
                )
            else:
                manifest = json.loads(
                    download(object_id(key, "manifest", prefix=prefix), 16 * 1024)
                )
                parts = manifest.get("parts")
                require(
                    manifest.get("version") == 1
                    and isinstance(parts, list)
                    and 0 < len(parts) <= 32
                    and type(manifest.get("bytes")) is int
                    and 0 < manifest["bytes"] <= min(maximum, MAX_BYTES),
                    "resource_missing",
                    "Stored asset manifest is invalid.",
                    503,
                )
                size = 0
                for index, part in enumerate(parts):
                    require(
                        isinstance(part, dict)
                        and bool(
                            re.fullmatch(r"[a-f0-9]{64}", str(part.get("sha256", "")))
                        )
                        and type(part.get("bytes")) is int
                        and 0 < part["bytes"] <= CHUNK_BYTES,
                        "resource_missing",
                        "Stored asset manifest is invalid.",
                        503,
                    )
                    chunk = download(
                        object_id(key, f"part-{index}-{part['sha256']}", prefix=prefix),
                        part["bytes"],
                    )
                    size += len(chunk)
                    require(
                        len(chunk) == part["bytes"]
                        and hashlib.sha256(chunk).hexdigest() == part["sha256"]
                        and size <= manifest["bytes"],
                        "resource_missing",
                        "Stored asset integrity check failed.",
                        503,
                    )
                    handle.write(chunk)
                require(
                    size == manifest["bytes"],
                    "resource_missing",
                    "Stored asset is incomplete.",
                    503,
                )
        temporary.replace(target)
    except TourError:
        raise
    except Exception as exc:
        raise TourError(
            "storage_unavailable", "Private storage is unavailable. Retry.", 503
        ) from exc
    finally:
        temporary.unlink(missing_ok=True)
    return target


def remove(key, *, prefix=None):
    folder = object_id(key, "", prefix=prefix)
    cursor = None
    while True:
        page = cloudinary.api.resources(
            resource_type="raw",
            type="authenticated",
            prefix=folder,
            max_results=500,
            **({"next_cursor": cursor} if cursor else {}),
        )
        for item in page.get("resources", []):
            identity = item["public_id"]
            require(
                identity.startswith(folder),
                "storage_unavailable",
                "Invalid private storage response.",
                503,
            )
            result = cloudinary.uploader.destroy(
                identity, resource_type="raw", type="authenticated"
            )
            require(
                result.get("result") in {"ok", "not found"},
                "storage_unavailable",
                "Private media removal needs retry.",
                503,
            )
        cursor = page.get("next_cursor")
        if not cursor:
            break


def sweep(referenced, threshold, *, prefix=None):
    # Only this application's dedicated namespace; never touch ordinary listing
    # photos, profile documents or any other Cloudinary folder.
    prefix = object_id("0" * 32, "", prefix=prefix).split("/", 1)[0] + "/"
    removed, cursor = 0, None
    while True:
        page = cloudinary.api.resources(
            resource_type="raw",
            type="authenticated",
            prefix=prefix,
            max_results=500,
            **({"next_cursor": cursor} if cursor else {}),
        )
        for item in page.get("resources", []):
            identity = item["public_id"]
            key = identity[len(prefix) :].split("/")[0]
            if not identity.startswith(prefix) or not re.fullmatch(
                r"[a-f0-9]{32}", key
            ):
                continue
            created = datetime.fromisoformat(
                item["created_at"].replace("Z", "+00:00")
            ).timestamp()
            if key not in referenced and created < threshold:
                cloudinary.uploader.destroy(
                    identity, resource_type="raw", type="authenticated"
                )
                removed += 1
        cursor = page.get("next_cursor")
        if not cursor:
            return removed
