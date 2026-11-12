"Account APIs use normal JWT auth. Viewer APIs accept only tour credentials."
from . import viewer_commands
from . import selectors, authoring_commands as commands
from .http import mutation, RawPartParser, ReviewerTourAPIView
from .http import OwnerTourAPIView, PublicTourAPIView, ViewerTourAPIView
from django.core import signing
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from . import services, sessions, storage, uploads
from .errors import require
from .models import PropertyVirtualTour, TourOperation
from .policy import KINDS, LIMITS, enabled, owner_property, target_model


class OwnerUpdateAPIView(OwnerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Owner Update"

    def get(self, request, event_id):
        from core_apps.features.planning_models import PlanningEvent
        from .notifications import ACTION, update_payload

        event = get_object_or_404(
            PlanningEvent.objects.select_related("recipient"),
            id=event_id,
            recipient=request.user,
            destination__action_type=ACTION,
        )
        return Response(update_payload(event))


class CapabilitiesAPIView(PublicTourAPIView):
    http_method_names = ["get", "options"]
    name = "Capabilities"

    def get(self, request):
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
                "supported_manifest_versions": [1, 2],
                "limits": LIMITS,
            }
        )


class ToursAPIView(OwnerTourAPIView):
    http_method_names = ["get", "post", "options"]
    name = "Tours"

    def get(self, request, property_id, asset_kind="property"):
        owner_property(request.user, property_id, asset_kind)
        return Response(selectors.owner_tours(request.user, property_id, asset_kind))

    def post(self, request, property_id, asset_kind="property"):
        owner_property(request.user, property_id, asset_kind)
        return mutation(
            request,
            "tour.create",
            property_id,
            lambda actor: commands.create(actor, property_id, asset_kind, request.data),
        )


class RevisionsAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Revisions"

    def post(self, request, property_id, tour_id, asset_kind="property"):
        return mutation(
            request,
            "revision.create",
            tour_id,
            lambda actor: services.clone_revision(
                selectors.owned_tour(
                    actor, property_id, tour_id, True, asset_kind=asset_kind
                ),
                request.data,
            ),
        )


class RevisionAPIView(OwnerTourAPIView):
    http_method_names = ["get", "patch", "options"]
    name = "Revision"

    def get(self, request, property_id, tour_id, revision_id, asset_kind="property"):
        tour = selectors.owned_tour(
            request.user, property_id, tour_id, asset_kind=asset_kind
        )
        value = get_object_or_404(tour.revisions, id=revision_id)
        return Response(
            services.revision_payload(value),
            headers={"ETag": f'"draft-{value.draft_version}"'},
        )

    def patch(self, request, property_id, tour_id, revision_id, asset_kind="property"):
        return mutation(
            request,
            "revision.patch",
            revision_id,
            lambda actor: services.patch_revision(
                selectors.owned_revision(
                    actor, property_id, tour_id, revision_id, asset_kind=asset_kind
                ),
                request.data,
                request.headers.get("If-Match"),
            ),
        )


class RevisionActionAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Revision Action"

    def post(
        self, request, property_id, tour_id, revision_id, action, asset_kind="property"
    ):
        return mutation(
            request,
            f"revision.{action}",
            revision_id,
            lambda actor: commands.apply_revision_action(
                actor,
                property_id,
                tour_id,
                revision_id,
                action,
                asset_kind,
                request.data,
                request.headers.get("If-Match"),
            ),
        )


class UnpublishTourAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Unpublish Tour"

    def post(self, request, property_id, tour_id, asset_kind="property"):
        require(
            not request.data, "invalid_request", "This action accepts an empty body."
        )
        return mutation(
            request,
            "tour.unpublish",
            tour_id,
            lambda actor: commands.disable(
                actor, property_id, tour_id, asset_kind, delete=False
            ),
        )


class DeleteTourAPIView(OwnerTourAPIView):
    http_method_names = ["delete", "options"]
    name = "Delete Tour"

    def delete(self, request, property_id, tour_id, asset_kind="property"):
        require(
            not request.data, "invalid_request", "This action accepts an empty body."
        )
        return mutation(
            request,
            "tour.delete",
            tour_id,
            lambda actor: commands.disable(
                actor, property_id, tour_id, asset_kind, delete=True
            ),
        )


class UploadDetailAPIView(OwnerTourAPIView):
    http_method_names = ["get", "delete", "options"]
    name = "Upload Detail"

    def get(self, request, upload_id):
        return Response(
            uploads.upload_payload(selectors.owned_upload(request.user, upload_id))
        )

    def delete(self, request, upload_id):
        return mutation(
            request,
            "upload.abort",
            upload_id,
            lambda actor: commands.abort_upload(
                actor, upload_id, request.data, request.headers.get("If-Match")
            ),
        )


class UploadPartsAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Upload Parts"

    def post(self, request, upload_id):
        require(
            set(request.data) == {"part_number"},
            "invalid_request",
            "Provide part_number only.",
        )
        upload = selectors.owned_upload(request.user, upload_id)
        index = request.data.get("part_number")
        grant = uploads.part_grant(upload, index)
        return Response(
            {
                "part_number": index,
                "put_path": f"/api/v1/virtual-tour-uploads/{upload.id}/parts/{index}/?grant={grant}",
                "expires_in": 300,
            }
        )


class UploadPartBytesAPIView(ViewerTourAPIView):
    http_method_names = ["put", "options"]
    name = "Upload Part Bytes"
    parser_classes = [RawPartParser]

    def put(self, request, upload_id, part):
        return Response(
            viewer_commands.receive_tour_part(
                upload_id,
                part,
                lambda: request.data,
                request.query_params.get("grant", ""),
            )
        )


class UploadCompleteAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Upload Complete"

    def post(self, request, upload_id):
        require(not request.data, "invalid_request", "Complete accepts an empty body.")
        return mutation(
            request,
            "upload.complete",
            upload_id,
            lambda actor: uploads.complete(
                selectors.owned_upload(actor, upload_id, True)
            ),
        )


class OperationAPIView(OwnerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Operation"

    def get(self, request, operation_id=None, key=None):
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


class AvailabilityAPIView(PublicTourAPIView):
    http_method_names = ["get", "options"]
    name = "Availability"

    def get(self, request, property_id, asset_kind="property"):
        prop = get_object_or_404(target_model(asset_kind), id=property_id)
        return Response(
            {
                "tours": sessions.available(
                    prop, request.query_params.get("offer_id") or "overview"
                )
            }
        )


class ViewerSessionsAPIView(PublicTourAPIView):
    http_method_names = ["post", "options"]
    name = "Viewer Sessions"

    def post(self, request, property_id, tour_id, asset_kind="property"):
        tour = get_object_or_404(
            PropertyVirtualTour.objects.select_related("property", "active_revision"),
            id=tour_id,
            **{asset_kind + "__id": property_id},
        )
        return Response(
            sessions.create_session(tour, request.user, request.data), status=201
        )


class ExchangeAPIView(ViewerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Exchange"

    def post(self, request):
        return Response(
            viewer_commands.exchange_bootstrap(
                request.data, request.query_params.get("grant", "")
            )
        )


class ManifestAPIView(ViewerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Manifest"

    def get(self, request, session_id):
        session = selectors.viewer_session(
            session_id, request.headers.get("X-Tour-Credential", "")
        )
        return Response(
            {
                **session.variant.manifest,
                "session_id": str(session.id),
                "variant_id": str(session.variant.id),
            }
        )


class RenewSessionAPIView(ViewerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Renew Session"

    def post(self, request, session_id):
        return Response(
            viewer_commands.change_session(
                session_id,
                request.headers.get("X-Tour-Credential", ""),
                request.data,
                revoke=False,
            )
        )


class RevokeSessionAPIView(ViewerTourAPIView):
    http_method_names = ["delete", "options"]
    name = "Revoke Session"

    def delete(self, request, session_id):
        return Response(
            viewer_commands.change_session(
                session_id,
                request.headers.get("X-Tour-Credential", ""),
                request.data,
                revoke=True,
            )
        )


class ResourceAccessAPIView(ViewerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Resource Access"

    def get(self, request, session_id, resource_id):
        session = selectors.viewer_session(
            session_id, request.headers.get("X-Tour-Credential", "")
        )
        resource = session.variant.resources.get(resource_id)
        require(
            resource,
            "resource_forbidden",
            "Resource is outside this viewing package.",
            404,
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


class ResourceBytesAPIView(ViewerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Resource Bytes"

    def get(
        self, request, session_id, resource_id, face=None, level=None, x=None, y=None
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
        session = get_object_or_404(selectors.session_query(), id=session_id)
        sessions.active_session(session)
        resource = session.variant.resources.get(resource_id)
        require(
            resource,
            "resource_forbidden",
            "Resource is outside this viewing package.",
            404,
        )
        tile = None
        if resource["type"] == "tiles":
            require(
                face in resource["faces"]
                and level is not None
                and (0 <= level < len(resource["levels"])),
                "invalid_tile",
                "Invalid cube tile.",
                404,
            )
            count = resource["levels"][level] // 512
            require(
                x is not None
                and y is not None
                and (0 <= x < count)
                and (0 <= y < count),
                "invalid_tile",
                "Invalid cube tile.",
                404,
            )
            tile = f"{face}_{level}_{x}_{y}.jpg"
        else:
            require(face is None, "invalid_resource", "Invalid resource path.", 404)
        target = storage.read_path(resource["blob"], tile)
        require(
            target.is_file(), "resource_missing", "The resource is unavailable.", 404
        )
        response = FileResponse(target.open("rb"), content_type=resource["media_type"])
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "no-referrer"
        return response


class ReviewDecisionAPIView(ReviewerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Review Decision"

    def post(self, request, property_id, tour_id, revision_id, asset_kind="property"):
        from .review_access import reviewer

        reviewer(request.user, write=True)
        return mutation(
            request,
            "revision.review",
            revision_id,
            lambda actor: commands.review_revision(
                actor,
                property_id,
                tour_id,
                revision_id,
                asset_kind,
                request.data,
                request.headers.get("If-Match"),
            ),
        )


class PlaceOfferAPIView(ViewerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Place Offer"

    def get(self, request, session_id, place_id):
        from .place_offers import resolve

        session = selectors.viewer_session(
            session_id, request.headers.get("X-Tour-Credential", "")
        )
        return Response(resolve(session, place_id))
