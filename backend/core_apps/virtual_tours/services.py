import copy
from django.db import transaction
from django.utils import timezone
from .errors import require
from .models import PropertyVirtualTour, TourRevision, TourAsset, TourReviewEvent
from .policy import KINDS, enabled, match_version, writable, uuid_value
from .validation import validate_authoring


def revision_payload(revision):
    return {
        "id": str(revision.id),
        "tour_id": str(revision.tour.id),
        "draft_version": revision.draft_version,
        "etag": f'"draft-{revision.draft_version}"',
        "authoring": revision.authoring,
        "processing_state": revision.processing_state,
        "review_state": revision.review_state,
        "source_hash": revision.source_hash,
        "stage": revision.stage,
        "report": revision.report,
        "assets": [
            {
                "id": str(a.id),
                "role": a.role,
                "sha256": a.sha256,
                "size": a.size,
                "media_type": a.media_type,
            }
            for a in revision.assets.all()
        ],
        "variants": [
            {
                "id": str(v.id),
                "context": v.context,
                "scope_fingerprint": v.scope_fingerprint,
            }
            for v in revision.variants.all()
        ],
    }


def tour_payload(tour):
    latest = tour.revisions.order_by("-created_at").first()
    return {
        "id": str(tour.id),
        "property_id": str(tour.property.id),
        "kind": tour.kind,
        "disabled": tour.disabled,
        "deleted": tour.deleted,
        "active_revision_id": (
            str(tour.active_revision.id) if tour.active_revision_id else None
        ),
        "latest_revision": revision_payload(latest) if latest else None,
    }


def create_tour(prop, body):
    require(
        set(body) == {"kind"} and body.get("kind") in KINDS,
        "invalid_kind",
        "Choose a supported tour kind.",
    )
    require(
        enabled(body["kind"], True),
        "tour_disabled",
        "Tour preparation is unavailable.",
        503,
    )
    # A saved property must have completed its required ordinary-media cycle.
    # Cover is separate from PropertyImage on legacy listings.
    images = set(str(i.image) for i in prop.images.all())
    if prop.main_image:
        images.add(str(prop.main_image))
    require(
        10 <= len(images) <= 25
        and prop.video
        and prop.video_duration
        and 1 <= prop.video_duration <= 60,
        "listing_media_incomplete",
        "Complete the property's required photos and video before preparing a tour.",
        409,
    )
    existing = (
        PropertyVirtualTour.objects.select_for_update()
        .filter(property=prop, kind=body["kind"])
        .first()
    )
    if existing and existing.deleted:
        # Restore authoring access only. Previously approved bytes stay unpublished
        # until a new immutable revision passes review.
        existing.deleted, existing.disabled = False, True
        existing.save(update_fields=["deleted", "disabled", "updated_at"])
        if not existing.revisions.exists():
            TourRevision.objects.create(tour=existing)
        return tour_payload(existing), 200
    require(
        not existing,
        "tour_exists",
        "Open the existing tour and create a revision.",
        409,
    )
    tour = PropertyVirtualTour.objects.create(property=prop, kind=body["kind"])
    TourRevision.objects.create(tour=tour)
    return tour_payload(tour), 201


def clone_revision(tour, body):
    require(
        enabled(tour.kind, True),
        "tour_disabled",
        "Tour preparation is unavailable.",
        503,
    )
    require(
        set(body).issubset({"from_revision_id"}),
        "invalid_revision",
        "Unsupported revision field.",
    )
    source = None
    if body.get("from_revision_id"):
        source_id = uuid_value(body["from_revision_id"])
        require(source_id, "invalid_revision", "Provide a valid source revision UUID.")
        source = tour.revisions.filter(id=source_id).first()
        require(
            source,
            "invalid_revision",
            "Source revision does not belong to this tour.",
            404,
        )
    require(
        not tour.revisions.filter(review_state="not_submitted")
        .exclude(id=source.id if source else None)
        .exists(),
        "draft_exists",
        "Resume the existing draft.",
        409,
    )
    if source:
        require(
            source.review_state != "not_submitted",
            "draft_exists",
            "Resume this editable draft.",
            409,
        )
    revision = TourRevision.objects.create(tour=tour)
    if source:
        mapping = {}
        for asset in source.assets.all():
            cloned = TourAsset.objects.create(
                revision=revision,
                role=asset.role,
                blob=asset.blob,
                sha256=asset.sha256,
                size=asset.size,
                media_type=asset.media_type,
            )
            mapping[str(asset.id)] = str(cloned.id)

        def remap(value):
            if isinstance(value, dict):
                return {k: remap(v) for k, v in value.items()}
            if isinstance(value, list):
                return [remap(v) for v in value]
            return mapping.get(value, value) if isinstance(value, str) else value

        revision.authoring = remap(copy.deepcopy(source.authoring))
        revision.save(update_fields=["authoring"])
    tour.deleted = False
    tour.save(update_fields=["deleted", "updated_at"])
    return revision_payload(revision), 201


def patch_revision(revision, body, etag):
    writable(revision)
    match_version(revision, etag)
    require(
        set(body) == {"authoring"},
        "invalid_revision",
        "Only the authoring document may be edited.",
    )
    import json

    require(
        len(json.dumps(body)) <= 512 * 1024,
        "manifest_too_large",
        "Authoring document exceeds 512 KiB.",
        413,
    )
    validate_authoring(revision, body["authoring"])
    revision.authoring = body["authoring"]
    revision.draft_version += 1
    revision.source_hash, revision.processing_state, revision.stage, revision.report = (
        "",
        "draft",
        "",
        {},
    )
    revision.variants.all().delete()
    revision.save()
    return revision_payload(revision), 200


def queue_processing(revision, etag):
    writable(revision)
    match_version(revision, etag)
    source_hash, _ = validate_authoring(revision, revision.authoring)
    if revision.processing_state == "ready" and revision.source_hash == source_hash:
        return revision_payload(revision), 200
    revision.source_hash, revision.processing_state, revision.stage = (
        source_hash,
        "queued",
        "queued",
    )
    revision.report = {}
    revision.save(
        update_fields=[
            "source_hash",
            "processing_state",
            "stage",
            "report",
            "updated_at",
        ]
    )
    from .tasks import dispatch_revision

    transaction.on_commit(lambda: dispatch_revision(str(revision.id), source_hash))
    return revision_payload(revision), 202


def submit_review(revision, body, etag):
    writable(revision)
    match_version(revision, etag)
    expected, _ = validate_authoring(revision, revision.authoring)
    require(
        set(body) == {"source_hash"}
        and body["source_hash"] == revision.source_hash == expected,
        "source_changed",
        "Refresh and process the current content before submitting.",
        409,
    )
    require(
        revision.processing_state == "ready" and revision.variants.exists(),
        "not_ready",
        "Processing must finish before review.",
        409,
    )
    revision.review_state, revision.submitted_at = "pending", timezone.now()
    revision.save(update_fields=["review_state", "submitted_at", "updated_at"])
    return revision_payload(revision), 200


def review(revision, user, body):
    require(
        user.is_staff and user.has_perm("virtual_tours.change_tourrevision"),
        "review_forbidden",
        "Tour review permission is required.",
        403,
    )
    require(
        set(body) == {"decision", "expected_source_hash", "reason"}
        and body["decision"] in ("approved", "rejected"),
        "invalid_review",
        "Provide decision, expected_source_hash and reason.",
    )
    require(
        isinstance(body["reason"], str) and 1 <= len(body["reason"].strip()) <= 4000,
        "review_reason_required",
        "Record the privacy and package review, or rejection reason.",
    )
    require(
        revision.review_state == "pending" and revision.processing_state == "ready",
        "review_conflict",
        "Only a ready, submitted revision can be reviewed.",
        409,
    )
    current_hash, _ = validate_authoring(revision, revision.authoring)
    require(
        body["expected_source_hash"] == revision.source_hash == current_hash
        and all(v.source_hash == current_hash for v in revision.variants.all()),
        "source_changed",
        "Content or inventory changed after processing.",
        409,
    )
    require(
        revision.variants.exists(), "not_ready", "No processed variants exist.", 409
    )
    revision.review_state = body["decision"]
    revision.save(update_fields=["review_state", "updated_at"])
    TourReviewEvent.objects.create(
        revision=revision,
        reviewer=user,
        decision=body["decision"],
        source_hash=current_hash,
        reason=body["reason"],
    )
    if body["decision"] == "approved":
        tour = PropertyVirtualTour.objects.select_for_update().get(pk=revision.tour_id)
        require(
            not tour.deleted, "tour_deleted", "A deleted tour cannot be published.", 409
        )
        tour.active_revision, tour.disabled = revision, False
        tour.save(update_fields=["active_revision", "disabled", "updated_at"])
    return revision_payload(revision), 200
