"""Evidence storage and inspection independent of the signing/payment provider."""

import hashlib
import io
import shutil
import subprocess
from dataclasses import dataclass

from django.conf import settings
from PIL import Image, UnidentifiedImageError
from rest_framework.exceptions import PermissionDenied, ValidationError

from core_apps.common.private_storage import (
    DurablePrivateStorage,
    PrivateStorageUnavailable,
)
from core_apps.common.private_media_policy import MIME_EXTENSIONS, maximum

MAX_BYTES = 5 * 1024 * 1024


class EvidencePrivateStorage(DurablePrivateStorage):
    maximum_bytes = 50 * 1024 * 1024
    root_setting = "EVIDENCE_PRIVATE_ROOT"
    provider_setting = "EVIDENCE_STORAGE_PROVIDER"
    prefix_setting = "EVIDENCE_CLOUDINARY_PREFIX"
    default_root = "private_evidence"
    default_prefix = "sokoun-evidence-private"

    @property
    def remote(self):
        # This adapter is selected from each file's persisted backend. Turning
        # off NEW uploads must not strand previously stored private evidence.
        return True


def fake_scanner_allowed():
    return getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production") in {
        "development",
        "test",
        "staging",
    } and getattr(settings, "RENTAL_FAKE_PROVIDER_ALLOWED", False)


def available():
    storage = getattr(settings, "EVIDENCE_STORAGE_PROVIDER", "disabled")
    scanner = getattr(settings, "EVIDENCE_SCANNER_BACKEND", "disabled")
    return storage in {"database", "cloudinary"} and (
        (scanner == "fake" and fake_scanner_allowed())
        or (scanner == "clamav" and bool(shutil.which(settings.EVIDENCE_CLAMSCAN_PATH)))
    )


def require_available():
    if not available():
        raise PermissionDenied(
            {
                "code": "evidence_unavailable",
                "message": "Private evidence storage and inspection are not configured.",
            }
        )


def validate_png(content, claimed_digest, claimed_type="image/png"):
    if not 0 < len(content) <= MAX_BYTES or claimed_type != "image/png":
        raise ValidationError({"file": "Use a PNG image up to 5 MiB."})
    try:
        with Image.open(io.BytesIO(content)) as source:
            if (
                source.format != "PNG"
                or getattr(source, "n_frames", 1) != 1
                or source.width * source.height > 20_000_000
            ):
                raise ValueError()
            source.verify()
        with Image.open(io.BytesIO(content)) as source:
            source.load()  # Headers/CRC alone do not establish a decodable image.
    except (
        ValueError,
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
    ) as error:
        raise ValidationError(
            {"file": "Supply a complete, non-animated PNG image."}
        ) from error
    digest = hashlib.sha256(content).hexdigest()
    if digest != claimed_digest:
        raise ValidationError({"sha256": "Digest does not match the uploaded bytes."})
    return digest


def persist(item):
    content = bytes(item.private_content or b"")
    if (
        len(content) != item.size_bytes
        or hashlib.sha256(content).hexdigest() != item.sha256
    ):
        raise PrivateStorageUnavailable("Evidence integrity check failed.")
    provider = getattr(settings, "EVIDENCE_STORAGE_PROVIDER", "disabled")
    if provider == "database":
        return provider, f"database/{item.id}/{item.sha256}"
    if provider != "cloudinary":
        raise PrivateStorageUnavailable()
    storage = EvidencePrivateStorage()
    name = f"{item.id.hex}.{MIME_EXTENSIONS.get(item.content_type, 'bin')}"
    # A retry reconciles the exact deterministic identity. Never allocate another
    # name after an ambiguous remote write.
    storage.save_immutable(name, content, item.sha256)
    return provider, name


def read(item):
    if item.storage_provider == "cloudinary":
        with EvidencePrivateStorage().open(item.storage_key, "rb") as stream:
            content = stream.read(maximum(item.content_type) + 1)
    elif item.storage_provider == "database" or (
        item.storage_provider == "fake" and fake_scanner_allowed()
    ):
        content = bytes(item.private_content or b"")
    else:
        raise PrivateStorageUnavailable()
    if (
        len(content) != item.size_bytes
        or hashlib.sha256(content).hexdigest() != item.sha256
    ):
        raise PrivateStorageUnavailable("Evidence integrity check failed.")
    return content


@dataclass(frozen=True)
class ScanResult:
    safe: bool
    engine: str
    sha256: str


def scan(content):
    digest = hashlib.sha256(content).hexdigest()
    scanner = getattr(settings, "EVIDENCE_SCANNER_BACKEND", "disabled")
    if scanner == "fake" and fake_scanner_allowed():
        return ScanResult(
            b"EICAR-STANDARD-ANTIVIRUS-TEST-FILE" not in content,
            "synthetic-test-only",
            digest,
        )
    if scanner != "clamav":
        raise PrivateStorageUnavailable("Evidence inspection is unavailable.")
    binary = shutil.which(settings.EVIDENCE_CLAMSCAN_PATH)
    if not binary:
        raise PrivateStorageUnavailable("Evidence inspection is unavailable.")
    try:
        version = (
            subprocess.run(
                [binary, "--version"], capture_output=True, timeout=5, check=True
            )
            .stdout.decode("utf-8", errors="replace")
            .strip()
        )
        if not version.startswith("ClamAV ") or "/" not in version:
            raise ValueError("Scanner signature database is unavailable")
        result = subprocess.run(
            [binary, "--no-summary", "--stdout", "-"],
            input=content,
            capture_output=True,
            timeout=45,
        )
        if result.returncode not in {0, 1}:
            raise ValueError("Inspection did not complete")
        return ScanResult(result.returncode == 0, version[:200], digest)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise PrivateStorageUnavailable(
            "Evidence inspection did not complete. Retry."
        ) from error
