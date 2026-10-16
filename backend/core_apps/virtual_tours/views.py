"""Account APIs use normal JWT auth. Viewer APIs accept only tour credentials."""

from datetime import timedelta
from functools import wraps
from django.core import signing
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    renderer_classes,
    parser_classes,
)
from rest_framework.parsers import BaseParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from core_apps.features.renderers import FeatureJsonRenderer
from core_apps.properties.models import Property
from . import services, sessions, storage, uploads
from .errors import require
from .models import (
    PropertyVirtualTour,
    TourRevision,
    TourUploadSession,
    TourOperation,
    TourViewerSession,
)
from .operations import mutate
from .policy import KINDS, LIMITS, enabled, owner_property, target_model


def endpoint(methods, public=False, viewer=False):
    def decorate(fn):
        original = fn

        @wraps(original)
        def fn(request, *args, **kwargs):
            if request.method in ("POST", "PATCH", "DELETE"):
                require(
                    isinstance(request.data, dict),
                    "invalid_request",
                    "A JSON object is required.",
                    400,
                )
            response = original(request, *args, **kwargs)
            response["Cache-Control"] = "private, no-store"
            response["Referrer-Policy"] = "no-referrer"
            response["X-Content-Type-Options"] = "nosniff"
            return response

        fn = renderer_classes([FeatureJsonRenderer])(fn)
        fn = permission_classes([AllowAny if public else IsAuthenticated])(fn)
        if viewer:
            fn = authentication_classes([])(fn)
        return api_view(methods)(fn)

    return decorate


def mutation(request, action, resource, execute):
    data, status, replayed = mutate(request, action, resource, execute)
    return Response(
        data, status=status, headers={"Idempotency-Replayed": str(replayed).lower()}
    )


def asset_kind_for(request):
    return request.resolver_match.kwargs.get("asset_kind", "property")


def owned_tour(request, property_id, tour_id, lock=False):
    prop = owner_property(request.user, property_id, asset_kind_for(request))
    qs = PropertyVirtualTour.objects.select_related("property", "active_revision")
    if lock:
        qs = qs.select_for_update(of=("self",))
    return get_object_or_404(qs, id=tour_id, **{asset_kind_for(request): prop})


def owned_revision(request, property_id, tour_id, revision_id):
    tour = owned_tour(request, property_id, tour_id)
    return get_object_or_404(
        TourRevision.objects.select_for_update(of=("self",)).select_related(
            "tour__property"
        ),
        id=revision_id,
        tour=tour,
    )


@endpoint(["GET"], public=True)
def capabilities(request):
    return Response(
        {
            "schema_version": 1,
            "kinds": {
                kind: {
                    "read": enabled(kind),
                    "write": enabled(kind, True) and request.user.is_authenticated,
                }
                for kind in KINDS
            },
            "supported_manifest_versions": [1],
            "limits": LIMITS,
        }
    )


@endpoint(["GET", "POST"])
def tours(request, property_id, asset_kind="property"):
    prop = owner_property(request.user, property_id, asset_kind_for(request))
    if request.method == "GET":
        return Response(
            {"tours": [services.tour_payload(t) for t in prop.virtual_tours.all()]}
        )
    return mutation(
        request,
        "tour.create",
        property_id,
        lambda: services.create_tour(prop, request.data),
    )


@endpoint(["POST"])
def revisions(request, property_id, tour_id, asset_kind="property"):
    return mutation(
        request,
        "revision.create",
        tour_id,
        lambda: services.clone_revision(
            owned_tour(request, property_id, tour_id, True), request.data
        ),
    )


@endpoint(["GET", "PATCH"])
def revision(request, property_id, tour_id, revision_id, asset_kind="property"):
    if request.method == "GET":
        tour = owned_tour(request, property_id, tour_id)
        value = get_object_or_404(tour.revisions, id=revision_id)
        return Response(
            services.revision_payload(value),
            headers={"ETag": f'"draft-{value.draft_version}"'},
        )
    return mutation(
        request,
        "revision.patch",
        revision_id,
        lambda: services.patch_revision(
            owned_revision(request, property_id, tour_id, revision_id),
            request.data,
            request.headers.get("If-Match"),
        ),
    )


@endpoint(["POST"])
def revision_action(
    request, property_id, tour_id, revision_id, action, asset_kind="property"
):
    def execute():
        value = owned_revision(request, property_id, tour_id, revision_id)
        etag = request.headers.get("If-Match")
        if action == "uploads":
            return uploads.create_upload(value, request.data, etag)
        if action == "process":
            require(
                not request.data, "invalid_request", "Processing accepts an empty body."
            )
            return services.queue_processing(value, etag)
        return services.submit_review(value, request.data, etag)

    return mutation(request, f"revision.{action}", revision_id, execute)


def disable_tour(request, property_id, tour_id):
    require(not request.data, "invalid_request", "This action accepts an empty body.")

    def execute():
        tour = owned_tour(request, property_id, tour_id, True)
        tour.disabled = True
        if request.method == "DELETE":
            tour.deleted = True
        tour.save(update_fields=["disabled", "deleted", "updated_at"])
        return services.tour_payload(tour), 200

    return mutation(
        request,
        "tour.delete" if request.method == "DELETE" else "tour.unpublish",
        tour_id,
        execute,
    )


@endpoint(["POST"])
def unpublish_tour(request, property_id, tour_id, asset_kind="property"):
    return disable_tour(request, property_id, tour_id)


@endpoint(["DELETE"])
def delete_tour(request, property_id, tour_id, asset_kind="property"):
    return disable_tour(request, property_id, tour_id)


def owned_upload(request, upload_id, lock=False):
    qs = TourUploadSession.objects.select_related("revision__tour__property", "asset")
    if lock:
        qs = qs.select_for_update(of=("self",))
    return get_object_or_404(
        qs.filter(
            Q(revision__tour__property__owner=request.user)
            | Q(revision__tour__building__manager=request.user)
            | Q(revision__tour__complex__manager=request.user)
        ),
        id=upload_id,
    )


@endpoint(["GET", "DELETE"])
def upload_detail(request, upload_id):
    if request.method == "GET":
        return Response(uploads.upload_payload(owned_upload(request, upload_id)))

    def execute():
        upload = owned_upload(request, upload_id, True)
        require(not request.data, "invalid_request", "Abort accepts an empty body.")
        require(
            upload.state != "complete",
            "upload_completed",
            "A completed asset cannot be aborted.",
            409,
        )
        upload.state = "aborted"
        upload.save(update_fields=["state"])
        return uploads.upload_payload(upload), 200

    return mutation(request, "upload.abort", upload_id, execute)


@endpoint(["POST"])
def upload_parts(request, upload_id):
    require(
        set(request.data) == {"part_number"},
        "invalid_request",
        "Provide part_number only.",
    )
    upload = owned_upload(request, upload_id)
    index = request.data.get("part_number")
    grant = uploads.part_grant(upload, index)
    return Response(
        {
            "part_number": index,
            "put_path": f"/api/v1/virtual-tour-uploads/{upload.id}/parts/{index}/?grant={grant}",
            "expires_in": 300,
        }
    )


class RawPartParser(BaseParser):
    media_type = "application/octet-stream"

    def parse(self, stream, media_type=None, parser_context=None):
        # Stream read in bounded chunks by receive_part, never request.body.
        return stream


@endpoint(["PUT"], public=True, viewer=True)
@parser_classes([RawPartParser])
def upload_part_bytes(request, upload_id, part):
    try:
        grant = signing.loads(
            request.query_params.get("grant", ""), salt="tour-upload-part", max_age=300
        )
    except signing.BadSignature:
        require(False, "upload_grant_expired", "Obtain a fresh part upload grant.", 401)
    require(
        grant == {"upload": str(upload_id), "part": part},
        "upload_grant_invalid",
        "Invalid upload grant.",
        403,
    )
    with transaction.atomic():
        upload = get_object_or_404(
            TourUploadSession.objects.select_for_update(of=("self",)).select_related(
                "revision__tour__property"
            ),
            id=upload_id,
        )
        stream = request.data
        chunks = iter(lambda: stream.read(1024 * 1024), b"")
        return Response(uploads.receive_part(upload, part, chunks))


@endpoint(["POST"])
def upload_complete(request, upload_id):
    require(not request.data, "invalid_request", "Complete accepts an empty body.")
    return mutation(
        request,
        "upload.complete",
        upload_id,
        lambda: uploads.complete(owned_upload(request, upload_id, True)),
    )


@endpoint(["GET"])
def operation(request, operation_id=None, key=None):
    query = {"id": operation_id} if operation_id else {"key": key}
    value = get_object_or_404(TourOperation, user=request.user, **query)
    require(
        value.expires_at > timezone.now(),
        "operation_expired",
        "The receipt expired. Reconcile the resource before continuing.",
        410,
    )
    return Response(
        {
            "id": str(value.id),
            "key": value.key,
            "action": value.action,
            "resource": value.resource,
            "request_hash": value.request_hash,
            "status": value.status,
            "result": value.result,
            "http_status": value.http_status,
            "expires_at": value.expires_at.isoformat(),
        }
    )


@endpoint(["GET"], public=True)
def availability(request, property_id, asset_kind="property"):
    prop = get_object_or_404(target_model(asset_kind), id=property_id)
    return Response(
        {
            "tours": sessions.available(
                prop, request.query_params.get("offer_id") or "overview"
            )
        }
    )


@endpoint(["POST"], public=True)
def viewer_sessions(request, property_id, tour_id, asset_kind="property"):
    tour = get_object_or_404(
        PropertyVirtualTour.objects.select_related("property", "active_revision"),
        id=tour_id,
        **{asset_kind + "__id": property_id},
    )
    return Response(
        sessions.create_session(tour, request.user, request.data), status=201
    )


def session_query(lock=False):
    qs = TourViewerSession.objects.select_related(
        "variant__revision__tour__property", "user"
    )
    return qs.select_for_update(of=("self",)) if lock else qs


@endpoint(["POST"], public=True, viewer=True)
def exchange(request):
    require(
        set(request.data) == {"bootstrap_token"},
        "invalid_request",
        "Provide bootstrap_token only.",
    )
    token = request.data.get("bootstrap_token", "")
    require(
        isinstance(token, str) and 20 <= len(token) <= 100,
        "invalid_bootstrap",
        "Invalid bootstrap token.",
        401,
    )
    with transaction.atomic():
        session = get_object_or_404(
            session_query(True), bootstrap_hash=sessions.token_hash(token)
        )
        return Response(sessions.exchange(session))


def viewer_session(request, session_id, lock=False):
    session = get_object_or_404(session_query(lock), id=session_id)
    sessions.authenticate_session(session, request.headers.get("X-Tour-Credential", ""))
    return session


@endpoint(["GET"], public=True, viewer=True)
def manifest(request, session_id):
    session = viewer_session(request, session_id)
    return Response(
        {
            **session.variant.manifest,
            "session_id": str(session.id),
            "variant_id": str(session.variant.id),
        }
    )


def session_lifecycle(request, session_id):
    require(
        not request.data, "invalid_request", "Session lifecycle accepts an empty body."
    )
    with transaction.atomic():
        session = viewer_session(request, session_id, True)
        if request.method == "DELETE":
            session.revoked_at = timezone.now()
        else:
            session.expires_at = timezone.now() + timedelta(minutes=15)
        session.save(update_fields=["expires_at", "revoked_at"])
        return Response(
            {
                "expires_at": session.expires_at.isoformat(),
                "revoked": bool(session.revoked_at),
            }
        )


@endpoint(["POST"], public=True, viewer=True)
def renew_session(request, session_id):
    return session_lifecycle(request, session_id)


@endpoint(["DELETE"], public=True, viewer=True)
def revoke_session(request, session_id):
    return session_lifecycle(request, session_id)


@endpoint(["GET"], public=True, viewer=True)
def resource_access(request, session_id, resource_id):
    session = viewer_session(request, session_id)
    resource = session.variant.resources.get(resource_id)
    require(
        resource, "resource_forbidden", "Resource is outside this viewing package.", 404
    )
    grant = signing.dumps(
        {"session": str(session.id), "resource": resource_id}, salt="tour-resource"
    )
    base = f"/api/v1/virtual-tour-viewer/sessions/{session.id}/resources/{resource_id}/bytes/"
    suffix = "{face}/{level}/{x}/{y}/" if resource["type"] == "tiles" else ""
    return Response(
        {
            "resource_id": resource_id,
            "url_template" if suffix else "url": f"{base}{suffix}?grant={grant}",
            "expires_in": 120,
        }
    )


@endpoint(["GET"], public=True, viewer=True)
def resource_bytes(
    request, session_id, resource_id, face=None, level=None, x=None, y=None
):
    try:
        grant = signing.loads(
            request.query_params.get("grant", ""), salt="tour-resource", max_age=120
        )
    except signing.BadSignature:
        require(False, "resource_grant_expired", "Refresh asset access.", 401)
    require(
        grant == {"session": str(session_id), "resource": resource_id},
        "resource_forbidden",
        "Invalid resource grant.",
        403,
    )
    session = get_object_or_404(session_query(), id=session_id)
    sessions.active_session(session)
    resource = session.variant.resources.get(resource_id)
    require(
        resource, "resource_forbidden", "Resource is outside this viewing package.", 404
    )
    tile = None
    if resource["type"] == "tiles":
        require(
            face in resource["faces"]
            and level is not None
            and 0 <= level < len(resource["levels"]),
            "invalid_tile",
            "Invalid cube tile.",
            404,
        )
        count = resource["levels"][level] // 512
        require(
            x is not None and y is not None and 0 <= x < count and 0 <= y < count,
            "invalid_tile",
            "Invalid cube tile.",
            404,
        )
        tile = f"{face}_{level}_{x}_{y}.jpg"
    else:
        require(face is None, "invalid_resource", "Invalid resource path.", 404)
    target = storage.read_path(resource["blob"], tile)
    require(target.is_file(), "resource_missing", "The resource is unavailable.", 404)
    response = FileResponse(target.open("rb"), content_type=resource["media_type"])
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["Referrer-Policy"] = "no-referrer"
    return response


@endpoint(["POST"])
def review_decision(request, property_id, tour_id, revision_id, asset_kind="property"):
    def execute():
        value = get_object_or_404(
            TourRevision.objects.select_for_update(of=("self",)).select_related(
                "tour__property"
            ),
            id=revision_id,
            tour__id=tour_id,
            **{"tour__" + asset_kind + "__id": property_id},
        )
        return services.review(value, request.user, request.data)

    return mutation(request, "revision.review", revision_id, execute)
