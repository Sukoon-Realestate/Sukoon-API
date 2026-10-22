"""Private files with an optional durable backing store and a disposable cache.

Storage URLs are never returned. Authorization remains at each resource's API.
Existing FileField names are stable so enabling the remote store needs no rewrite
of references. Backfill must verify remote bytes before removing old originals.
"""

import hashlib
import os
import tempfile
from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from rest_framework.exceptions import APIException


class PrivateStorageUnavailable(APIException):
    status_code = 503
    default_detail = "Private file storage is temporarily unavailable. Retry."
    default_code = "private_storage_unavailable"


class DurablePrivateStorage(FileSystemStorage):
    root_setting = ""
    provider_setting = ""
    prefix_setting = ""
    default_root = "private_media"
    default_prefix = ""
    maximum_bytes = 5 * 1024 * 1024

    def __init__(self):
        super().__init__(file_permissions_mode=0o600, directory_permissions_mode=0o700)

    @property
    def base_location(self):
        return getattr(settings, self.root_setting, str(settings.BASE_DIR / self.default_root))

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def remote(self):
        provider = getattr(settings, self.provider_setting, "local")
        if provider not in {"local", "cloudinary"}:
            raise PrivateStorageUnavailable()
        return provider == "cloudinary"

    @property
    def prefix(self):
        return getattr(settings, self.prefix_setting, self.default_prefix)

    def identity(self, name):
        # path() rejects traversal even when the cache is empty.
        self.path(name)
        return hashlib.sha256(name.encode("utf-8")).hexdigest()[:32]

    def _materialize(self, name, target=None):
        from core_apps.virtual_tours import cloudinary_storage as remote
        from core_apps.virtual_tours.errors import TourError

        target = Path(target or self.path(name))
        if target.is_file():
            return target
        if not self.remote:
            raise FileNotFoundError(name)
        try:
            return remote.materialize(
                self.identity(name), target, prefix=self.prefix, maximum=self.maximum_bytes
            )
        except TourError as error:
            if error.status_code == 404:
                raise FileNotFoundError(name) from error
            raise PrivateStorageUnavailable() from error

    def _open(self, name, mode="rb"):
        if mode not in {"r", "rb"}:
            raise ValueError("Private evidence is immutable.")
        self._materialize(name)
        return super()._open(name, mode)

    def exists(self, name):
        if super().exists(name):
            return True
        if not self.remote:
            return False
        try:
            self._materialize(name)
            return True
        except FileNotFoundError:
            return False

    def size(self, name):
        self._materialize(name)
        return super().size(name)

    def _save(self, name, content):
        if content.size > self.maximum_bytes:
            raise ValueError("Private file exceeds its size limit.")
        saved = super()._save(name, content)
        try:
            if self.remote:
                self.ensure_remote(saved)
        except Exception:
            # A failed upload must not become a successful database reference.
            # Remote orphans retain a random identity and are never exposed.
            super().delete(saved)
            raise
        return saved

    def ensure_remote(self, name):
        """Copy once and verify from a fresh download, bypassing the local cache."""
        from core_apps.virtual_tours import cloudinary_storage as remote

        if not self.remote:
            raise PrivateStorageUnavailable("A durable private store is not configured.")
        source = Path(self.path(name))
        if not source.is_file():
            self._materialize(name)
        if not 0 < source.stat().st_size <= self.maximum_bytes:
            raise PrivateStorageUnavailable("Invalid private file size.")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix="sokoun-private-verify-") as folder:
                target = Path(folder) / "original"
                try:
                    self._materialize(name, target)
                except FileNotFoundError:
                    remote.persist(self.identity(name), source, prefix=self.prefix)
                    self._materialize(name, target)
                if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise PrivateStorageUnavailable("Private backup integrity check failed.")
        except PrivateStorageUnavailable:
            raise
        except Exception as error:
            raise PrivateStorageUnavailable() from error
        return digest

    def delete(self, name):
        if self.remote:
            from core_apps.virtual_tours import cloudinary_storage as remote

            try:
                remote.remove(self.identity(name), prefix=self.prefix)
            except Exception as error:
                raise PrivateStorageUnavailable() from error
        super().delete(name)

    def url(self, name):
        raise NotImplementedError("Private files require an authorized read.")
