import hashlib
import math
import copy
from django.conf import settings
from django.db.models import Sum
from PIL import Image, UnidentifiedImageError
from . import storage, capture_reconstruction
from .capture_models import CaptureAsset, CaptureManifestRevision, CaptureProcessingJob
from .capture_validation import (
    frame,
    manifest,
    fields,
    identifier,
    PART_BYTES,
    MAX_ASSET,
    MODES,
)
from .errors import require
from .policy import digest


def job_payload(job):
    from .services import revision_payload
    outputs = copy.deepcopy(job.outputs)
    for station in outputs.get("panorama360", {}).get("stations", []):
        for name, resource in station.get("resources", {}).items():
            resource.pop("blob", None)
            resource["path"] = (
                f"property-captures/{job.manifest.session.id}/processing-jobs/{job.id}/stations/{station['id']}/{name}/"
            )
    for component in outputs.get("walkthrough3d", {}).get("components", []):
        for name, resource in component.get("resources", {}).items():
            resource.pop("blob", None)
            resource["path"] = (
                f"property-captures/{job.manifest.session.id}/processing-jobs/{job.id}/components/{component['id']}/{name}/"
            )
    return {
        "id": str(job.id),
        "manifestRevision": job.manifest.revision,
        "manifestHash": job.manifest.sha256,
        "capturedAt": job.manifest.created_at.date().isoformat(),
        "state": job.state,
        "stage": job.stage,
        "outputs": outputs,
        "attempt": job.attempt,
        "cancelRequested": job.cancel_requested,
        "selectedRevisions": [revision_payload(r) for r in job.tour_revisions.order_by("-created_at")[:2]],
    }


def session_payload(session):
    jobs = (
        CaptureProcessingJob.objects.filter(manifest__session=session)
        .select_related("manifest")
        .order_by("-manifest__revision", "-created_at")
    )
    return {
        "id": str(session.id),
        "propertyId": str(session.property.id),
        "clientSessionId": str(session.client_id),
        "state": session.state,
        "revision": session.revision,
        "policyVersion": session.policy_version,
        "coachOptIn": session.coach_opt_in,
        "rooms": [
            {"id": str(r.client_id), "label": r.label, "confirmed": r.confirmed}
            for r in session.rooms.all()
        ],
        "jobs": [job_payload(j) for j in jobs[:20]],
        "outputs": list(MODES),
        "partBytes": PART_BYTES,
        "maxSessionBytes": settings.CAPTURE_MAX_SESSION_BYTES,
    }


def asset_payload(asset):
    return {
        "id": str(asset.id),
        "frameId": str(asset.client_id),
        "state": asset.state,
        "sha256": asset.sha256,
        "size": asset.size,
        "partBytes": PART_BYTES,
        "receivedParts": sorted(int(k) for k in asset.parts),
    }


def reserve(session, body):
    require(
        settings.PROPERTY_CAPTURE_ENABLED,
        "CAPTURE_UNSUPPORTED",
        "Phone capture is not enabled.",
        503,
    )
    fields(body, {"size", "metadata"})
    metadata = frame(body["metadata"])
    size = body["size"]
    require(
        type(size) is int and 0 < size <= MAX_ASSET,
        "MANIFEST_INVALID",
        "Invalid image size.",
    )
    require(
        session.rooms.filter(client_id=metadata["roomId"]).exists(),
        "MANIFEST_INVALID",
        "Choose a room in this capture.",
    )
    previous = session.assets.filter(client_id=metadata["frameId"]).first()
    if previous:
        require(
            previous.metadata == metadata and previous.size == size,
            "capture_asset_conflict",
            "Original capture identity cannot change.",
            409,
        )
        return asset_payload(previous), 200
    total = session.assets.aggregate(total=Sum("size"))["total"] or 0
    require(
        total + size <= settings.CAPTURE_MAX_SESSION_BYTES
        and session.assets.count() < 5000,
        "STORAGE_INSUFFICIENT",
        "The session upload budget is exhausted.",
        413,
    )
    asset = CaptureAsset.objects.create(
        session=session,
        client_id=metadata["frameId"],
        size=size,
        sha256=metadata["image"]["sha256"],
        metadata=metadata,
    )
    return asset_payload(asset), 201


def receive_part(asset, index, stream):
    require(
        asset.state in ("open", "verified")
        and 1 <= index <= math.ceil(asset.size / PART_BYTES),
        "MANIFEST_INVALID",
        "Invalid upload part.",
    )
    expected = min(PART_BYTES, asset.size - (index - 1) * PART_BYTES)
    data = stream.read(expected + 1)
    require(
        len(data) == expected,
        "MANIFEST_INVALID",
        "Upload part has an incorrect byte length.",
    )
    checksum = hashlib.sha256(data).hexdigest()
    previous = asset.parts.get(str(index))
    if previous:
        require(
            previous["sha256"] == checksum,
            "capture_part_conflict",
            "An uploaded part cannot change.",
            409,
        )
    else:
        require(
            asset.state == "open",
            "capture_asset_conflict",
            "Verified original is immutable.",
            409,
        )
        key, size, actual = storage.write_blob([data], expected)
        asset.parts[str(index)] = {"blob": key, "size": size, "sha256": actual}
        asset.save(update_fields=["parts"])
    return asset_payload(asset)


def complete(asset):
    if asset.state == "verified":
        return asset_payload(asset), 200
    count = math.ceil(asset.size / PART_BYTES)
    require(
        set(asset.parts) == {str(i) for i in range(1, count + 1)},
        "ASSET_NOT_VERIFIED",
        "Resume the missing upload parts.",
    )

    def chunks():
        for i in range(1, count + 1):
            part = asset.parts[str(i)]
            source = storage.read_path(part["blob"])
            data = source.read_bytes()
            require(
                len(data) == part["size"]
                and hashlib.sha256(data).hexdigest() == part["sha256"],
                "ASSET_NOT_VERIFIED",
                "A stored upload part failed integrity verification.",
            )
            yield data

    key, size, checksum = storage.write_blob(chunks(), asset.size)
    require(
        size == asset.size and checksum == asset.sha256,
        "ASSET_NOT_VERIFIED",
        "Original checksum does not match uploaded bytes.",
    )
    try:
        with Image.open(storage.read_path(key)) as image:
            require(
                image.format == "JPEG"
                and image.size
                == (asset.metadata["image"]["width"], asset.metadata["image"]["height"])
                and image.getexif().get(274, 1) == 1,
                "MANIFEST_INVALID",
                "Original pixels do not match their calibration.",
            )
            image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        require(False, "MANIFEST_INVALID", "The original image could not be decoded.")
    asset.blob, asset.state = key, "verified"
    asset.save(update_fields=["blob", "state"])
    return asset_payload(asset), 200


def finalize(session, body):
    fields(body, {"document", "expectedRevision"})
    document = manifest(body["document"], session)
    checksum = digest(document)
    previous = session.manifests.filter(sha256=checksum).first()
    if previous:
        return {"revision": previous.revision, "sha256": previous.sha256}, 200
    require(
        type(body["expectedRevision"]) is int
        and body["expectedRevision"] == session.revision,
        "capture_revision_conflict",
        "Refresh the session before finalizing this capture.",
        409,
    )
    session.revision += 1
    revision = CaptureManifestRevision.objects.create(
        session=session, revision=session.revision, sha256=checksum, document=document
    )
    session.state = "captureComplete"
    session.save(update_fields=["revision", "state"])
    return {"revision": revision.revision, "sha256": checksum}, 201


def queue(session, body):
    require(
        settings.PROPERTY_CAPTURE_ENABLED,
        "CAPTURE_UNSUPPORTED",
        "Phone capture is not enabled.",
        503,
    )
    fields(body, {"manifestRevision"})
    require(
        type(body["manifestRevision"]) is int,
        "MANIFEST_INVALID",
        "Choose a capture revision.",
    )
    revision = session.manifests.filter(revision=body["manifestRevision"]).first()
    require(
        revision is not None,
        "MANIFEST_INVALID",
        "Choose a verified immutable capture revision.",
    )
    job, created = CaptureProcessingJob.objects.get_or_create(
        manifest=revision,
        profile=capture_reconstruction.profile_identity(),
        defaults={"outputs": {mode: {"status": "pending"} for mode in MODES}},
    )
    return job_payload(job), 202 if created else 200
