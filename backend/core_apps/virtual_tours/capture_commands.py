"""Locked tour lifecycle commands, executed through the durable operation receipt."""

from . import selectors
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .policy import owner_property
from .errors import require
from .capture_models import (
    PropertyCaptureSession,
    CaptureRoom,
    CaptureProcessingJob,
    CaptureCoachSession,
)
from .capture_validation import fields
from core_apps.users.services.sessions import validate_session
from . import capture_services as services, capture_coach


def select_outputs(user, session_id, job_id, body, etag):
    from .capture_delivery import validate
    from .services import create_tour, queue_processing, revision_payload
    from .models import PropertyVirtualTour, TourRevision

    fields(body, {"authoring", "expectedManifestHash"})
    session = selectors.owned(user, session_id, True)
    job = get_object_or_404(
        CaptureProcessingJob.objects.select_for_update(),
        id=job_id,
        manifest__session=session,
    )
    require(
        body["expectedManifestHash"] == job.manifest.sha256,
        "capture_source_changed",
        "Refresh the immutable input revision.",
        409,
    )
    document = body["authoring"]
    require(
        isinstance(document, dict)
        and document.get("kind") in ("model_3d", "panorama_360"),
        "invalid_kind",
        "Choose a capture output kind.",
    )
    tour = (
        PropertyVirtualTour.objects.select_for_update()
        .filter(property=session.property, kind=document["kind"])
        .first()
    )
    if not tour:
        create_tour(session.property, {"kind": document["kind"]})
        tour = PropertyVirtualTour.objects.get(
            property=session.property, kind=document["kind"]
        )
    require(
        not tour.deleted,
        "tour_deleted",
        "Restore authoring access before selecting outputs.",
        409,
    )
    revision = (
        tour.revisions.filter(review_state="not_submitted")
        .order_by("-created_at")
        .first()
    )
    if revision and revision.authoring:
        require(
            revision.capture_job_id == job.pk and revision.authoring == document,
            "draft_exists",
            "Finish or discard the existing tour draft first.",
            409,
        )
        return (revision_payload(revision), 200)
    revision = revision or TourRevision(tour=tour)
    revision.capture_job, revision.authoring = (job, document)
    validate(revision, document)
    revision.save()
    return queue_processing(revision, f'"draft-{revision.draft_version}"')


def create_session(user, property_id, body, etag):
    prop = owner_property(user, property_id)
    prop = type(prop).objects.select_for_update().get(pk=prop.pk)
    owner_property(user, property_id)
    session, created = PropertyCaptureSession.objects.get_or_create(
        owner=user,
        client_id=body["clientSessionId"],
        defaults={
            "property": prop,
            "coach_opt_in": body["coachOptIn"],
            "language": body.get("preferredLanguage", "ar"),
        },
    )
    require(
        session.property_id == prop.pk and session.deleted_at is None,
        "capture_identity_conflict",
        "This session identity is no longer available.",
        409,
    )
    return (services.session_payload(session), 201 if created else 200)


def update_session(user, session_id, body, etag):
    session = selectors.owned(user, session_id, True)
    fields(body, {"state"}, {"coachOptIn"})
    require(
        body["state"] in ("capturing", "paused"),
        "MANIFEST_INVALID",
        "Choose capturing or paused.",
    )
    session.state = body["state"]
    if "coachOptIn" in body:
        require(
            type(body["coachOptIn"]) is bool,
            "MANIFEST_INVALID",
            "Invalid coach consent.",
        )
        session.coach_opt_in = body["coachOptIn"]
    session.save()
    return (services.session_payload(session), 200)


def delete_session(user, session_id, body, etag):
    session = selectors.owned(user, session_id, True)
    require(not body, "MANIFEST_INVALID", "Delete accepts an empty body.")
    session.deleted_at, session.state = (timezone.now(), "cancelled")
    CaptureProcessingJob.objects.filter(manifest__session=session).update(
        cancel_requested=True
    )
    session.save()
    return (services.session_payload(session), 200)


def set_room(user, session_id, body, etag):
    session = selectors.owned(user, session_id, True)
    require(
        session.rooms.filter(client_id=body["id"]).exists()
        or session.rooms.count() < 40,
        "MANIFEST_INVALID",
        "The room limit is reached.",
    )
    CaptureRoom.objects.update_or_create(
        session=session,
        client_id=body["id"],
        defaults={"label": body["label"].strip(), "confirmed": body["confirmed"]},
    )
    return (services.session_payload(session), 200)


def cancel_job(user, session_id, job_id, body, etag):
    locked_session = selectors.owned(user, session_id, True)
    current = get_object_or_404(
        CaptureProcessingJob.objects.select_for_update(),
        id=job_id,
        manifest__session=locked_session,
    )
    current.cancel_requested = True
    current.save(update_fields=["cancel_requested"])
    return (services.job_payload(current), 200)


def retry_job(user, session_id, job_id, body, etag):
    session = selectors.owned(user, session_id, True)
    value = get_object_or_404(
        CaptureProcessingJob.objects.select_for_update(),
        id=job_id,
        manifest__session=session,
    )
    return services.retry(value, body)


def receive_capture_part(user, auth, session_id, asset_id, index, stream_factory, grant):
    with transaction.atomic():
        user = locked_actor(user, auth)
        return services.receive_part(
            selectors.asset_for(user, session_id, asset_id, True), index, stream_factory()
        )


def provision_coach(user, auth, session_id, body, grant):
    require(not body, "MANIFEST_INVALID", "Coach provisioning accepts an empty body.")
    require(
        getattr(settings, "CAPTURE_COACH_PRIVATE_INPUTS_APPROVED", False),
        "COACH_UNAVAILABLE",
        "Contextual coaching is not enabled for private images.",
        503,
    )
    now = timezone.now()
    with transaction.atomic():
        user = locked_actor(user, auth)
        session = selectors.owned(user, session_id, True)
        require(
            settings.PROPERTY_CAPTURE_ENABLED
            and getattr(settings, "CAPTURE_COACH_ENABLED", True)
            and (session.state == "capturing")
            and session.coach_opt_in,
            "COACH_UNAVAILABLE",
            "Enable coaching on an active capture first.",
            409,
        )
        records = CaptureCoachSession.objects.filter(session__owner=user)
        require(
            not records.filter(
                expires_at__gt=now, state__in=["provisioning", "active"]
            ).exists(),
            "COACH_SESSION_ACTIVE",
            "A previous coaching connection is still expiring. Retry shortly.",
            409,
        )
        require(
            records.filter(created_at__gte=now - timedelta(days=1)).count()
            < settings.COACH_DAILY_SESSION_LIMIT,
            "COACH_BUDGET_EXHAUSTED",
            "Coaching budget is exhausted. Local guidance still works.",
            429,
        )
        record = CaptureCoachSession.objects.create(
            session=session,
            model=settings.GEMINI_COACH_MODEL,
            expires_at=now + timedelta(seconds=180),
        )
    try:
        payload = capture_coach.provision(record)
        session.refresh_from_db()
        require(
            session.deleted_at is None
            and session.state == "capturing"
            and session.coach_opt_in,
            "COACH_UNAVAILABLE",
            "Capture changed before coaching connected.",
            409,
        )
        record.state = "active"
        record.save(update_fields=["state"])
        return payload
    except Exception:
        record.state = "failed"
        record.save(update_fields=["state"])
        raise


def close_coach(user, auth, session_id, coach_id, body, grant):
    """Release the app lease; provider credentials still have their short TTL."""
    require(not body, "MANIFEST_INVALID", "Close accepts an empty body.")
    with transaction.atomic():
        user = locked_actor(user, auth)
        session = selectors.owned(user, session_id, True)
        record = get_object_or_404(CaptureCoachSession, id=coach_id, session=session)
        if record.state not in {"closed", "failed"}:
            record.state = "closed"
            record.save(update_fields=["state"])
    return {"state": "closed"}


def locked_actor(user, auth):
    current = get_user_model().objects.select_for_update().get(pk=user.pk)
    validate_session(current, auth or {})
    return current
