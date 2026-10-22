"""Private local transport/cache with optional private S3/Spaces backing storage.

Only signed, session-checked gateways expose bytes. No MEDIA_URL or public keys.
"""

import hashlib
import os
import re
import uuid
from pathlib import Path
from django.conf import settings
from .errors import require
from . import remote_storage


def root():
    directory = Path(settings.VIRTUAL_TOUR_PRIVATE_ROOT).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return directory


def path(key):
    require(
        bool(re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", key)),
        "invalid_resource",
        "Invalid private resource.",
        404,
    )
    return root() / key


def write_blob(chunks, maximum):
    key = uuid.uuid4().hex
    destination = path(key)
    checksum, size = hashlib.sha256(), 0
    try:
        with destination.open("xb") as output:
            os.chmod(destination, 0o600)
            for chunk in chunks:
                size += len(chunk)
                require(
                    size <= maximum,
                    "asset_too_large",
                    "The asset exceeds its byte limit.",
                    413,
                )
                checksum.update(chunk)
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        directory = os.open(root(), os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
        remote_storage.persist(key, destination)
        return key, size, checksum.hexdigest()
    except BaseException:
        destination.unlink(missing_ok=True)
        raise


def read_path(key, child=None):
    target = path(key)
    if child is not None:
        require(
            bool(re.fullmatch(r"[fblrud]_[0-2]_[0-3]_[0-3]\.jpg", child)),
            "invalid_tile",
            "Invalid tile path.",
            404,
        )
        target = target / child
    return remote_storage.materialize(key, target, child)


def persist_tiles(key, *, progress=lambda: None):
    if remote_storage.configured():
        for tile in path(key).iterdir():
            progress()
            remote_storage.persist(key, tile, tile.name)
            progress()


def file_chunks(source):
    with source.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            yield chunk
