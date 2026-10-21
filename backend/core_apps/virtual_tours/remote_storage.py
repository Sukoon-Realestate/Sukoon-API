"""Optional private S3/Spaces backing store; no provider URLs reach clients."""

from functools import lru_cache
import os
import re
import uuid
from urllib.parse import urlsplit
from django.conf import settings
from .errors import require


def configured():
    if settings.VIRTUAL_TOUR_STORAGE_PROVIDER == "cloudinary":
        return True
    return bool(settings.VIRTUAL_TOUR_S3_BUCKET)


@lru_cache(maxsize=4)
def _client(endpoint, region):
    import boto3
    from botocore.config import Config

    require(
        not endpoint or urlsplit(endpoint).scheme == "https",
        "storage_unavailable",
        "Private object storage requires HTTPS.",
        503,
    )
    # Credentials come from the worker/API environment's normal AWS SDK chain.
    return boto3.client(
        "s3",
        endpoint_url=endpoint or None,
        region_name=region,
        config=Config(
            connect_timeout=10,
            read_timeout=60,
            retries={"mode": "standard", "max_attempts": 3},
            signature_version="s3v4",
        ),
    )


def client():
    return _client(settings.VIRTUAL_TOUR_S3_ENDPOINT, settings.VIRTUAL_TOUR_S3_REGION)


def object_key(key, child=None):
    prefix = settings.VIRTUAL_TOUR_S3_PREFIX.strip("/")
    require(
        bool(re.fullmatch(r"[A-Za-z0-9_-]{1,100}", prefix)),
        "storage_unavailable",
        "Configure a dedicated private storage prefix.",
        503,
    )
    return f"{prefix}/{key}" + (f"/{child}" if child else "")


def persist(key, source, child=None):
    if settings.VIRTUAL_TOUR_STORAGE_PROVIDER == "cloudinary":
        from . import cloudinary_storage

        return cloudinary_storage.persist(key, source, child)
    if not configured():
        return
    # All keys are allocated by the server as fresh UUIDs; clients can only write
    # staging parts through the gateway, never choose a completed asset key.
    with source.open("rb") as handle:
        client().put_object(
            Bucket=settings.VIRTUAL_TOUR_S3_BUCKET,
            Key=object_key(key, child),
            Body=handle,
            ContentLength=source.stat().st_size,
            ContentType="application/octet-stream",
            CacheControl="private, no-store",
        )


def materialize(key, target, child=None):
    if settings.VIRTUAL_TOUR_STORAGE_PROVIDER == "cloudinary":
        from . import cloudinary_storage

        cloudinary_storage.materialize(key, target, child)
    elif not target.is_file() and configured():
        from botocore.exceptions import ClientError

        temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".pending")
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            response = client().get_object(
                Bucket=settings.VIRTUAL_TOUR_S3_BUCKET, Key=object_key(key, child)
            )
            stream = response["Body"]
            try:
                with temporary.open("xb") as handle:
                    os.chmod(temporary, 0o600)
                    size = 0
                    for chunk in stream.iter_chunks(chunk_size=1024 * 1024):
                        size += len(chunk)
                        require(
                            size <= 250 * 1024**2,
                            "asset_too_large",
                            "Stored asset exceeds its limit.",
                            413,
                        )
                        handle.write(chunk)
                require(
                    size == response["ContentLength"],
                    "resource_missing",
                    "Stored asset is incomplete.",
                    503,
                )
            finally:
                stream.close()
            temporary.replace(target)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
                require(False, "resource_missing", "The resource is unavailable.", 404)
            raise
        finally:
            temporary.unlink(missing_ok=True)
    if target.is_file():
        os.utime(target, None)
        if child:
            os.utime(target.parent, None)
    return target


def sweep(referenced, threshold):
    if settings.VIRTUAL_TOUR_STORAGE_PROVIDER == "cloudinary":
        from . import cloudinary_storage

        return cloudinary_storage.sweep(referenced, threshold)
    if not configured():
        return 0
    removed = 0
    prefix = object_key("")
    for page in (
        client()
        .get_paginator("list_objects_v2")
        .paginate(Bucket=settings.VIRTUAL_TOUR_S3_BUCKET, Prefix=prefix)
    ):
        for entry in page.get("Contents", []):
            relative = entry["Key"][len(prefix) :]
            if not re.fullmatch(r"[a-f0-9]{32}", relative.split("/")[0]):
                continue
            if (
                relative.split("/")[0] in referenced
                or entry["LastModified"].timestamp() >= threshold
            ):
                continue
            client().delete_object(
                Bucket=settings.VIRTUAL_TOUR_S3_BUCKET, Key=entry["Key"]
            )
            removed += 1
    return removed
