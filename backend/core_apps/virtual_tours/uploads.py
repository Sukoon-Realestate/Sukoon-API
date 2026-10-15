import re
from datetime import timedelta
from django.core import signing
from django.utils import timezone
from . import storage
from .errors import require
from .models import TourAsset, TourUploadSession
from .policy import LIMITS, PART_SIZE, match_version, writable

ROLES = {
    "panorama": ("panorama_bytes", {"image/jpeg", "image/png"}),
    "visual": ("model_bytes", {"model/gltf-binary"}),
    "collision": ("collision_bytes", {"model/gltf-binary"}),
    "walk": ("walk_bytes", {"application/json"}),
}


def upload_payload(upload):
    return {
        "id": str(upload.id),
        "state": upload.state,
        "size": upload.size,
        "sha256": upload.sha256,
        "role": upload.role,
        "part_bytes": PART_SIZE,
        "received_parts": sorted(int(i) for i in upload.parts),
        "asset_id": str(upload.asset.id) if upload.asset_id else None,
        "expires_at": upload.expires_at.isoformat(),
    }


def create_upload(revision, body, etag):
    writable(revision)
    match_version(revision, etag)
    require(
        set(body) == {"role", "size", "sha256", "media_type"},
        "invalid_upload",
        "Provide role, size, sha256 and media_type.",
    )
    role = body.get("role")
    require(
        isinstance(role, str) and role in ROLES,
        "invalid_upload",
        "Unsupported asset role.",
    )
    require(
        (revision.tour.kind == "panorama_360") == (role == "panorama"),
        "invalid_upload",
        "Wrong asset role for tour kind.",
    )
    size = body.get("size")
    require(
        isinstance(size, int)
        and not isinstance(size, bool)
        and 0 < size <= LIMITS[ROLES[role][0]],
        "asset_too_large",
        "Invalid asset size.",
    )
    require(
        isinstance(body.get("media_type"), str)
        and body["media_type"] in ROLES[role][1]
        and bool(re.fullmatch(r"[0-9a-f]{64}", str(body.get("sha256", "")))),
        "invalid_upload",
        "Invalid asset type or SHA-256.",
    )
    retained = sum(revision.assets.values_list("size", flat=True))
    retained += sum(
        revision.uploads.exclude(state="complete")
        .filter(created_at__gt=timezone.now() - timedelta(days=7))
        .values_list("size", flat=True)
    )
    require(
        retained + size <= 2 * 1024**3,
        "revision_quota",
        "This revision has reached its 2 GiB source quota.",
        413,
    )
    upload = TourUploadSession.objects.create(
        revision=revision, **body, expires_at=timezone.now() + timedelta(days=7)
    )
    return upload_payload(upload), 201


def live(upload):
    writable(upload.revision)
    require(
        upload.state == "open" and upload.expires_at > timezone.now(),
        "upload_expired",
        "The upload is closed or expired.",
        410,
    )


def part_grant(upload, index):
    live(upload)
    count = (upload.size + PART_SIZE - 1) // PART_SIZE
    require(
        isinstance(index, int) and not isinstance(index, bool) and 1 <= index <= count,
        "invalid_part",
        "Invalid part number.",
    )
    return signing.dumps(
        {"upload": str(upload.id), "part": index},
        salt="tour-upload-part",
        compress=True,
    )


def receive_part(upload, index, chunks):
    live(upload)
    expected = min(PART_SIZE, upload.size - (index - 1) * PART_SIZE)
    require(expected > 0 and index > 0, "invalid_part", "Invalid part number.")
    blob, size, checksum = storage.write_blob(chunks, expected)
    if size != expected:
        storage.path(blob).unlink()
        require(False, "invalid_part", "Part length does not match the upload.")
    prior = upload.parts.get(str(index))
    if prior:
        storage.path(blob).unlink()
        require(
            prior["sha256"] == checksum,
            "part_conflict",
            "An accepted part cannot be replaced.",
            409,
        )
    else:
        upload.parts[str(index)] = {"blob": blob, "sha256": checksum, "size": size}
        upload.save(update_fields=["parts", "updated_at"])
    return upload_payload(upload)


def complete(upload):
    if upload.state == "complete":
        return upload_payload(upload), 200
    live(upload)
    count = (upload.size + PART_SIZE - 1) // PART_SIZE
    require(
        set(upload.parts) == {str(i) for i in range(1, count + 1)},
        "upload_incomplete",
        "Upload every part before completing.",
        409,
    )

    def chunks():
        for i in range(1, count + 1):
            yield from storage.file_chunks(
                storage.read_path(upload.parts[str(i)]["blob"])
            )

    blob, size, checksum = storage.write_blob(chunks(), upload.size)
    if checksum != upload.sha256 or size != upload.size:
        storage.path(blob).unlink()
        require(
            False, "checksum_mismatch", "The uploaded file failed its integrity check."
        )
    # Copying into a fresh blob isolates completed bytes from every staging URL.
    upload.asset = TourAsset.objects.create(
        revision=upload.revision,
        role=upload.role,
        blob=blob,
        size=size,
        sha256=checksum,
        media_type=upload.media_type,
    )
    upload.state = "complete"
    upload.save(update_fields=["asset", "state", "updated_at"])
    return upload_payload(upload), 200
