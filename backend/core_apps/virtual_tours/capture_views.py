from . import capture_reads
from . import selectors, capture_commands as commands
from .http import OwnerTourAPIView
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from rest_framework.response import Response
from .http import mutation, RawPartParser
from .policy import owner_property
from .errors import require
from .capture_models import CaptureProcessingJob
from .capture_validation import fields, identifier, POLICY, MODES
from . import capture_services as services, capture_reconstruction
from . import storage


class SelectOutputsAPIView(OwnerTourAPIView):
    description = (
        "Selection creates a draft only; no publication or approval is implied."
    )
    http_method_names = ["post", "options"]
    name = "Select Outputs"

    def post(self, request, session_id, job_id):
        """Selection creates a draft only; no publication or approval is implied."""
        fields(request.data, {"authoring", "expectedManifestHash"})
        return mutation(
            request,
            "capture.select_outputs",
            job_id,
            lambda actor: commands.select_outputs(
                actor, session_id, job_id, request.data, request.headers.get("If-Match")
            ),
        )


class CapabilitiesAPIView(OwnerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Capabilities"

    def get(self, request):
        return Response(
            {
                "schemaVersion": 1,
                "enabled": settings.PROPERTY_CAPTURE_ENABLED,
                "policyVersion": POLICY,
                "outputs": list(MODES),
                "releaseReady": False,
                "coachConfigured": bool(settings.GEMINI_API_KEY),
                "coachAvailable": bool(
                    settings.PROPERTY_CAPTURE_ENABLED
                    and settings.GEMINI_API_KEY
                    and settings.GEMINI_COACH_MODEL
                    and getattr(settings, "CAPTURE_COACH_ENABLED", True)
                    and getattr(
                        settings, "CAPTURE_COACH_PRIVATE_INPUTS_APPROVED", False
                    )
                ),
                "coachPolicyVersion": "coach-v2",
                "coachSessionSeconds": 180,
                "processingProfile": capture_reconstruction.profile_identity(),
            }
        )


class SessionsAPIView(OwnerTourAPIView):
    http_method_names = ["get", "post", "options"]
    name = "Sessions"

    def get(self, request, property_id):
        from core_apps.common.pagination import StandardResultsSetPagination

        if request.query_params.get("summary") == "true":
            rows = capture_reads.summary_rows(capture_reads.session_rows(request.user, property_id))
            pagination = StandardResultsSetPagination()
            page = pagination.paginate_queryset(rows, request)
            return pagination.get_paginated_response([capture_reads.session_summary(row) for row in page])
        return Response(capture_reads.collection(request.user, property_id))

    def post(self, request, property_id):
        owner_property(request.user, property_id)
        require(
            settings.PROPERTY_CAPTURE_ENABLED,
            "CAPTURE_UNSUPPORTED",
            "Phone capture is not enabled.",
            503,
        )
        fields(
            request.data,
            {
                "clientSessionId",
                "requestedOutputs",
                "capturePolicyVersion",
                "coachOptIn",
            },
            {"preferredLanguage"},
        )
        require(
            identifier(request.data["clientSessionId"])
            and request.data["requestedOutputs"] == list(MODES)
            and (request.data["capturePolicyVersion"] == POLICY)
            and (type(request.data["coachOptIn"]) is bool)
            and (request.data.get("preferredLanguage", "ar") in ("ar", "en")),
            "MANIFEST_INVALID",
            "Invalid capture session request.",
        )
        return mutation(
            request,
            "capture.create",
            property_id,
            lambda actor: commands.create_session(
                actor, property_id, request.data, request.headers.get("If-Match")
            ),
        )


class SessionDetailAPIView(OwnerTourAPIView):
    http_method_names = ["get", "patch", "delete", "options"]
    name = "Session Detail"

    def get(self, request, session_id):
        return Response(capture_reads.detail(request.user, session_id))

    def patch(self, request, session_id):
        return mutation(
            request,
            "capture." + "PATCH".lower(),
            session_id,
            lambda actor: commands.update_session(
                actor, session_id, request.data, request.headers.get("If-Match")
            ),
        )

    def delete(self, request, session_id):
        return mutation(
            request,
            "capture." + "DELETE".lower(),
            session_id,
            lambda actor: commands.delete_session(
                actor, session_id, request.data, request.headers.get("If-Match")
            ),
        )


class RoomsAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Rooms"

    def post(self, request, session_id):
        fields(request.data, {"id", "label", "confirmed"})
        require(
            identifier(request.data["id"])
            and isinstance(request.data["label"], str)
            and (1 <= len(request.data["label"].strip()) <= 80)
            and (type(request.data["confirmed"]) is bool),
            "MANIFEST_INVALID",
            "Choose a valid room name.",
        )
        return mutation(
            request,
            "capture.room",
            session_id,
            lambda actor: commands.set_room(
                actor, session_id, request.data, request.headers.get("If-Match")
            ),
        )


class ReserveAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Reserve"

    def post(self, request, session_id):
        return mutation(
            request,
            "capture.upload",
            session_id,
            lambda actor: services.reserve(
                selectors.owned(actor, session_id, True), request.data
            ),
        )


class UploadAPIView(OwnerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Upload"

    def get(self, request, session_id, asset_id):
        return Response(
            services.asset_payload(
                selectors.asset_for(request.user, session_id, asset_id)
            )
        )


class PartAPIView(OwnerTourAPIView):
    http_method_names = ["put", "options"]
    name = "Part"
    parser_classes = [RawPartParser]

    def put(self, request, session_id, asset_id, index):
        return Response(
            commands.receive_capture_part(
                request.user,
                request.auth,
                session_id,
                asset_id,
                index,
                lambda: request.data,
                request.query_params.get("grant", ""),
            )
        )


class CompleteAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Complete"

    def post(self, request, session_id, asset_id):
        require(not request.data, "MANIFEST_INVALID", "Complete accepts an empty body.")
        return mutation(
            request,
            "capture.complete",
            asset_id,
            lambda actor: services.complete(
                selectors.asset_for(actor, session_id, asset_id, True)
            ),
        )


class ManifestsAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Manifests"

    def post(self, request, session_id):
        return mutation(
            request,
            "capture.manifest",
            session_id,
            lambda actor: services.finalize(
                selectors.owned(actor, session_id, True), request.data
            ),
        )


class JobsAPIView(OwnerTourAPIView):
    http_method_names = ["get", "post", "options"]
    name = "Jobs"

    def get(self, request, session_id):
        from core_apps.common.pagination import StandardResultsSetPagination

        rows = capture_reads.job_rows(request.user, session_id)
        pagination = StandardResultsSetPagination()
        page = pagination.paginate_queryset(rows, request)
        return pagination.get_paginated_response([capture_reads.job_summary(row) for row in page])

    def post(self, request, session_id):
        return mutation(
            request,
            "capture.process",
            session_id,
            lambda actor: services.queue(
                selectors.owned(actor, session_id, True), request.data
            ),
        )


class JobAPIView(OwnerTourAPIView):
    http_method_names = ["get", "post", "options"]
    name = "Job"

    def get(self, request, session_id, job_id):
        session = selectors.owned(request.user, session_id)
        value = get_object_or_404(
            CaptureProcessingJob.objects.select_related("manifest"),
            id=job_id,
            manifest__session=session,
        )
        return Response(services.job_payload(value))

    def post(self, request, session_id, job_id):
        session = selectors.owned(request.user, session_id)
        get_object_or_404(
            CaptureProcessingJob.objects.select_related("manifest"),
            id=job_id,
            manifest__session=session,
        )
        require(not request.data, "MANIFEST_INVALID", "Cancel accepts an empty body.")
        return mutation(
            request,
            "capture.cancel_job",
            job_id,
            lambda actor: commands.cancel_job(
                actor, session_id, job_id, request.data, request.headers.get("If-Match")
            ),
        )


class RetryJobAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Retry Job"

    def post(self, request, session_id, job_id):
        return mutation(
            request,
            "capture.retry_job",
            job_id,
            lambda actor: commands.retry_job(
                actor, session_id, job_id, request.data, request.headers.get("If-Match")
            ),
        )


class StationResourceAPIView(OwnerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Station Resource"

    def get(self, request, session_id, job_id, station_id, resource):
        session = selectors.owned(request.user, session_id)
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
        require(
            value is not None, "resource_missing", "Capture preview unavailable.", 404
        )
        return FileResponse(
            storage.read_path(value["blob"]).open("rb"), content_type="image/png"
        )


class ComponentResourceAPIView(OwnerTourAPIView):
    http_method_names = ["get", "options"]
    name = "Component Resource"

    def get(self, request, session_id, job_id, component_id, resource):
        session = selectors.owned(request.user, session_id)
        job = get_object_or_404(
            CaptureProcessingJob,
            id=job_id,
            manifest__session=session,
            cancel_requested=False,
        )
        require(
            resource
            in (
                "thumbnail",
                "preview",
                "preview_ply",
                "detail_ply",
                "cameras",
                "navigation",
            ),
            "resource_missing",
            "Capture preview unavailable.",
            404,
        )
        component = next(
            (
                value
                for value in job.outputs.get("walkthrough3d", {}).get("components", [])
                if value.get("id") == str(component_id)
            ),
            None,
        )
        require(
            component is not None,
            "resource_missing",
            "Capture preview unavailable.",
            404,
        )
        value = component.get("resources", {}).get(resource)
        require(
            value is not None, "resource_missing", "Capture preview unavailable.", 404
        )
        content_type = value.get("mediaType", "application/octet-stream")
        if content_type not in (
            "image/jpeg",
            "application/json",
            "application/octet-stream",
        ):
            content_type = "application/octet-stream"
        return FileResponse(
            storage.read_path(value["blob"]).open("rb"), content_type=content_type
        )


class CoachAPIView(OwnerTourAPIView):
    http_method_names = ["post", "options"]
    name = "Coach"

    def post(self, request, session_id):
        return Response(
            commands.provision_coach(
                request.user,
                request.auth,
                session_id,
                request.data,
                request.query_params.get("grant", ""),
            ),
            status=201,
        )


class CloseCoachAPIView(OwnerTourAPIView):
    description = (
        "Release the app lease; provider credentials still have their short TTL."
    )
    http_method_names = ["post", "options"]
    name = "Close Coach"

    def post(self, request, session_id, coach_id):
        return Response(
            commands.close_coach(
                request.user,
                request.auth,
                session_id,
                coach_id,
                request.data,
                request.query_params.get("grant", ""),
            )
        )
