from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils import timezone
from rest_framework.decorators import parser_classes
from rest_framework.response import Response
from .views import endpoint, mutation, RawPartParser
from .policy import owner_property
from .errors import require
from .capture_models import (
    PropertyCaptureSession,
    CaptureRoom,
    CaptureAsset,
    CaptureProcessingJob,
    CaptureCoachSession,
)
from .capture_validation import fields, identifier, POLICY, MODES
from . import capture_services as services, capture_coach, capture_reconstruction
from . import storage


@endpoint(["POST"])
def select_outputs(request, session_id, job_id):
    """Selection creates a draft only; no publication or approval is implied."""
    from .models import PropertyVirtualTour, TourRevision
    from .services import create_tour, queue_processing, revision_payload
    from .capture_delivery import validate

    fields(request.data, {"authoring", "expectedManifestHash"})
    def execute():
        session = owned(request, session_id, True)
        job = get_object_or_404(CaptureProcessingJob.objects.select_for_update(), id=job_id, manifest__session=session)
        require(request.data["expectedManifestHash"] == job.manifest.sha256,
                "capture_source_changed", "Refresh the immutable input revision.", 409)
        document = request.data["authoring"]
        require(isinstance(document, dict) and document.get("kind") in ("model_3d", "panorama_360"), "invalid_kind", "Choose a capture output kind.")
        tour = PropertyVirtualTour.objects.select_for_update().filter(property=session.property, kind=document["kind"]).first()
        if not tour:
            create_tour(session.property, {"kind": document["kind"]})
            tour = PropertyVirtualTour.objects.get(property=session.property, kind=document["kind"])
        require(not tour.deleted, "tour_deleted", "Restore authoring access before selecting outputs.", 409)
        revision = tour.revisions.filter(review_state="not_submitted").order_by("-created_at").first()
        if revision and revision.authoring:
            require(revision.capture_job_id == job.pk and revision.authoring == document,
                    "draft_exists", "Finish or discard the existing tour draft first.", 409)
            return revision_payload(revision), 200
        revision = revision or TourRevision(tour=tour)
        revision.capture_job, revision.authoring = job, document
        validate(revision, document)
        revision.save()
        return queue_processing(revision, f'"draft-{revision.draft_version}"')
    return mutation(request, "capture.select_outputs", job_id, execute)


def owned(request, session_id, lock=False):
    qs = PropertyCaptureSession.objects.select_related("property")
    if lock:
        qs = qs.select_for_update(of=("self",))
    return get_object_or_404(
        qs,
        id=session_id,
        owner=request.user,
        property__owner=request.user,
        property__retired_at=None,
        deleted_at=None,
    )


@endpoint(["GET"])
def capabilities(request):
    return Response(
        {
            "schemaVersion": 1,
            "enabled": settings.PROPERTY_CAPTURE_ENABLED,
            "policyVersion": POLICY,
            "outputs": list(MODES),
            "releaseReady": False,
            "coachConfigured": bool(settings.GEMINI_API_KEY),
            "coachAvailable": bool(settings.PROPERTY_CAPTURE_ENABLED and settings.GEMINI_API_KEY and settings.GEMINI_COACH_MODEL and getattr(settings, "CAPTURE_COACH_ENABLED", True) and getattr(settings, "CAPTURE_COACH_PRIVATE_INPUTS_APPROVED", False)),
            "coachPolicyVersion": "coach-v2",
            "coachSessionSeconds": 180,
            "processingProfile": capture_reconstruction.profile_identity(),
        }
    )


@endpoint(["GET", "POST"])
def sessions(request, property_id):
    prop = owner_property(request.user, property_id)
    if request.method == "GET":
        return Response(
            {
                "sessions": [
                    services.session_payload(s)
                    for s in prop.capture_sessions.filter(
                        owner=request.user, deleted_at=None
                    )[:20]
                ]
            }
        )
    require(
        settings.PROPERTY_CAPTURE_ENABLED,
        "CAPTURE_UNSUPPORTED",
        "Phone capture is not enabled.",
        503,
    )
    fields(
        request.data,
        {"clientSessionId", "requestedOutputs", "capturePolicyVersion", "coachOptIn"},
        {"preferredLanguage"},
    )
    require(
        identifier(request.data["clientSessionId"])
        and request.data["requestedOutputs"] == list(MODES)
        and request.data["capturePolicyVersion"] == POLICY
        and type(request.data["coachOptIn"]) is bool
        and request.data.get("preferredLanguage", "ar") in ("ar", "en"),
        "MANIFEST_INVALID",
        "Invalid capture session request.",
    )

    def execute():
        session, created = PropertyCaptureSession.objects.get_or_create(
            owner=request.user,
            client_id=request.data["clientSessionId"],
            defaults={
                "property": prop,
                "coach_opt_in": request.data["coachOptIn"],
                "language": request.data.get("preferredLanguage", "ar"),
            },
        )
        require(
            session.property_id == prop.pk and session.deleted_at is None,
            "capture_identity_conflict",
            "This session identity is no longer available.",
            409,
        )
        return services.session_payload(session), 201 if created else 200

    return mutation(request, "capture.create", property_id, execute)


@endpoint(["GET", "PATCH", "DELETE"])
def session_detail(request, session_id):
    if request.method == "GET":
        return Response(services.session_payload(owned(request, session_id)))

    def execute():
        session = owned(request, session_id, True)
        if request.method == "DELETE":
            require(
                not request.data, "MANIFEST_INVALID", "Delete accepts an empty body."
            )
            session.deleted_at, session.state = timezone.now(), "cancelled"
            CaptureProcessingJob.objects.filter(manifest__session=session).update(
                cancel_requested=True
            )
            # Tombstone immediately revokes all delivery and new work. The retention
            # worker removes physical objects after any active lease has stopped.
        else:
            fields(request.data, {"state"}, {"coachOptIn"})
            require(
                request.data["state"] in ("capturing", "paused"),
                "MANIFEST_INVALID",
                "Choose capturing or paused.",
            )
            session.state = request.data["state"]
            if "coachOptIn" in request.data:
                require(
                    type(request.data["coachOptIn"]) is bool,
                    "MANIFEST_INVALID",
                    "Invalid coach consent.",
                )
                session.coach_opt_in = request.data["coachOptIn"]
        session.save()
        return services.session_payload(session), 200

    return mutation(request, "capture." + request.method.lower(), session_id, execute)


@endpoint(["POST"])
def rooms(request, session_id):
    fields(request.data, {"id", "label", "confirmed"})
    require(
        identifier(request.data["id"])
        and isinstance(request.data["label"], str)
        and 1 <= len(request.data["label"].strip()) <= 80
        and type(request.data["confirmed"]) is bool,
        "MANIFEST_INVALID",
        "Choose a valid room name.",
    )

    def execute():
        session = owned(request, session_id, True)
        require(
            session.rooms.filter(client_id=request.data["id"]).exists()
            or session.rooms.count() < 40,
            "MANIFEST_INVALID",
            "The room limit is reached.",
        )
        CaptureRoom.objects.update_or_create(
            session=session,
            client_id=request.data["id"],
            defaults={
                "label": request.data["label"].strip(),
                "confirmed": request.data["confirmed"],
            },
        )
        return services.session_payload(session), 200

    return mutation(request, "capture.room", session_id, execute)


@endpoint(["POST"])
def reserve(request, session_id):
    return mutation(
        request,
        "capture.upload",
        session_id,
        lambda: services.reserve(owned(request, session_id, True), request.data),
    )


def asset_for(request, session_id, asset_id, lock=False):
    session = owned(request, session_id, lock)
    qs = CaptureAsset.objects.select_for_update() if lock else CaptureAsset.objects
    return get_object_or_404(qs, session=session, id=asset_id)


@endpoint(["GET"])
def upload(request, session_id, asset_id):
    return Response(services.asset_payload(asset_for(request, session_id, asset_id)))


@endpoint(["PUT"])
@parser_classes([RawPartParser])
def part(request, session_id, asset_id, index):
    with transaction.atomic():
        return Response(
            services.receive_part(
                asset_for(request, session_id, asset_id, True), index, request.data
            )
        )


@endpoint(["POST"])
def complete(request, session_id, asset_id):
    require(not request.data, "MANIFEST_INVALID", "Complete accepts an empty body.")
    return mutation(
        request,
        "capture.complete",
        asset_id,
        lambda: services.complete(asset_for(request, session_id, asset_id, True)),
    )


@endpoint(["POST"])
def manifests(request, session_id):
    return mutation(
        request,
        "capture.manifest",
        session_id,
        lambda: services.finalize(owned(request, session_id, True), request.data),
    )


@endpoint(["POST"])
def jobs(request, session_id):
    return mutation(
        request,
        "capture.process",
        session_id,
        lambda: services.queue(owned(request, session_id, True), request.data),
    )


@endpoint(["GET", "POST"])
def job(request, session_id, job_id):
    session = owned(request, session_id)
    value = get_object_or_404(
        CaptureProcessingJob.objects.select_related("manifest"),
        id=job_id,
        manifest__session=session,
    )
    if request.method == "GET":
        return Response(services.job_payload(value))
    require(not request.data, "MANIFEST_INVALID", "Cancel accepts an empty body.")

    def execute():
        value.cancel_requested = True
        value.save(update_fields=["cancel_requested"])
        return services.job_payload(value), 200

    return mutation(request, "capture.cancel_job", job_id, execute)


@endpoint(["GET"])
def station_resource(request, session_id, job_id, station_id, resource):
    session = owned(request, session_id)
    job = get_object_or_404(
        CaptureProcessingJob,
        id=job_id,
        manifest__session=session,
        cancel_requested=False,
    )
    require(
        resource in ("image", "mask"),
        "resource_missing",
        "Capture preview unavailable.",
        404,
    )
    station = next(
        (
            s
            for s in job.outputs.get("panorama360", {}).get("stations", [])
            if s["id"] == str(station_id)
        ),
        None,
    )
    require(
        station is not None, "resource_missing", "Capture preview unavailable.", 404
    )
    value = station.get("resources", {}).get(resource)
    require(value is not None, "resource_missing", "Capture preview unavailable.", 404)
    return FileResponse(
        storage.read_path(value["blob"]).open("rb"), content_type="image/png"
    )


@endpoint(["GET"])
def component_resource(request, session_id, job_id, component_id, resource):
    session = owned(request, session_id)
    job = get_object_or_404(
        CaptureProcessingJob,
        id=job_id,
        manifest__session=session,
        cancel_requested=False,
    )
    require(
        resource in ("thumbnail", "preview", "preview_ply", "detail_ply", "cameras", "navigation"),
        "resource_missing", "Capture preview unavailable.", 404,
    )
    component = next(
        (value for value in job.outputs.get("walkthrough3d", {}).get("components", [])
         if value.get("id") == str(component_id)), None,
    )
    require(component is not None, "resource_missing", "Capture preview unavailable.", 404)
    value = component.get("resources", {}).get(resource)
    require(value is not None, "resource_missing", "Capture preview unavailable.", 404)
    content_type = value.get("mediaType", "application/octet-stream")
    if content_type not in ("image/jpeg", "application/json", "application/octet-stream"):
        content_type = "application/octet-stream"
    return FileResponse(storage.read_path(value["blob"]).open("rb"), content_type=content_type)


@endpoint(["POST"])
def coach(request, session_id):
    require(
        not request.data,
        "MANIFEST_INVALID",
        "Coach provisioning accepts an empty body.",
    )
    require(getattr(settings, "CAPTURE_COACH_PRIVATE_INPUTS_APPROVED", False), "COACH_UNAVAILABLE", "Contextual coaching is not enabled for private images.", 503)
    now = timezone.now()
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        session = owned(request, session_id, True)
        require(
            settings.PROPERTY_CAPTURE_ENABLED
            and getattr(settings, "CAPTURE_COACH_ENABLED", True)
            and session.state == "capturing"
            and session.coach_opt_in,
            "COACH_UNAVAILABLE",
            "Enable coaching on an active capture first.",
            409,
        )
        records = CaptureCoachSession.objects.filter(session__owner=request.user)
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
        # Consent/deletion may have changed while contacting the provider.
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
        return Response(payload, status=201)
    except Exception:
        record.state = "failed"
        record.save(update_fields=["state"])
        raise


@endpoint(["POST"])
def close_coach(request, session_id, coach_id):
    """Release the app lease; provider credentials still have their short TTL."""
    require(not request.data, "MANIFEST_INVALID", "Close accepts an empty body.")
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        session = owned(request, session_id, True)
        record = get_object_or_404(CaptureCoachSession, id=coach_id, session=session)
        if record.state not in {"closed", "failed"}:
            record.state = "closed"
            record.save(update_fields=["state"])
    return Response({"state": "closed"})
