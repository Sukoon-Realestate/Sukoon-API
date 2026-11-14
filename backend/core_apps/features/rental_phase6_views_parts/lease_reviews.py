"""Rental phase6 views: lease reviews."""

from core_apps.features.http import ActionPolicy, FeatureAPIView


from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from ..models import RentalDocument
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .final_settlement_propose import _lease
from .disputes import document_payload


def document_lease(
    request, lease_id, *, lock=False, provider_required=False, document_type=None
):
    from ..models import Lease

    lease = get_object_or_404(Lease, id=lease_id)
    if not lease.renter_company_id:
        return _lease(request, lease_id, lock=lock, provider_required=provider_required)
    from ..services.company.tenancy_access import get, commercial_read, financial_read
    from rest_framework.exceptions import NotFound

    item = get(request.user, lease.company_tenancy.id, lock=lock)
    financial = document_type in {"receipt", "settlement", "statement"}
    allowed = (
        financial_read(item.lease, request.user)
        if financial
        else commercial_read(item.lease, request.user)
    )
    if document_type is None:
        allowed = allowed or financial_read(item.lease, request.user)
    if not allowed:
        raise NotFound()
    return item.lease


class LeaseDocumentsView(FeatureAPIView):
    name = "Lease Documents"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "lease_reviews",
            "lease_documents",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = document_lease(request, lease_id)
        documents = lease.private_documents.all()
        if lease.renter_company_id:
            from ..services.company.tenancy_access import (
                financial_read,
                commercial_read,
            )

            types = []
            if commercial_read(lease, request.user):
                types += ["contract", "change"]
            if financial_read(lease, request.user):
                types += ["receipt", "settlement", "statement"]
            documents = documents.filter(document_type__in=types)
        from core_apps.common.pagination import StandardResultsSetPagination

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(
            documents.order_by("-created_at", "-id"), request
        )
        return paginator.get_paginated_response([document_payload(x) for x in page])


# Stable callable import for integrations; URLs use the explicit class.
lease_documents = LeaseDocumentsView.as_view()


class DocumentDownloadView(FeatureAPIView):
    name = "Document Download"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "lease_reviews",
            "document_download",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, document_id):
        document = get_object_or_404(
            RentalDocument.objects.select_related("lease"), id=document_id
        )
        document_lease(request, document.lease.id, document_type=document.document_type)
        if document.status != RentalDocument.Status.READY:
            raise RentalConflict("Document is not ready.")
        if not document.private_content:
            raise RentalConflict("The source document bytes are unavailable.")
        from ..services.private_rental_documents import download_url

        expires = timezone.now() + timedelta(minutes=5)
        return Response(
            {
                "id": str(document.id),
                "subject_id": str(document.lease.id),
                "revision": document.revision,
                "sha256": document.sha256,
                "url": download_url(request, document),
                "expires_at": expires.isoformat(),
            }
        )


# Stable callable import for integrations; URLs use the explicit class.
document_download = DocumentDownloadView.as_view()


class DocumentContentView(FeatureAPIView):
    name = "Document Content"
    http_method_names = ["get", "options"]
    permission_classes = [AllowAny]
    authentication_classes = []
    action_policies = {
        "get": ActionPolicy(
            "lease_reviews",
            "document_content",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, document_id):
        from ..services.private_rental_documents import content_response

        return content_response(document_id, request.query_params.get("token", ""))


# Stable callable import for integrations; URLs use the explicit class.
document_content = DocumentContentView.as_view()


class RentalStatementCreateView(FeatureAPIView):
    name = "Rental Statement Create"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "lease_reviews",
            "rental_statement_create",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    @transaction.atomic
    def post(self, request):
        from core_apps.users.models import User

        User.objects.select_for_update().get(pk=request.user.pk)
        lease = document_lease(
            request, request.data.get("lease_id"), lock=True, document_type="statement"
        )
        from django.utils.dateparse import parse_date

        starts, ends = request.data.get("starts_on"), request.data.get(
            "ends_on_exclusive"
        )
        try:
            if (
                (starts and not parse_date(starts))
                or (ends and not parse_date(ends))
                or (starts and ends and parse_date(starts) >= parse_date(ends))
            ):
                raise ValueError()
        except (ValueError, TypeError):
            raise ValidationError(
                "Supply valid statement dates with an exclusive end after the start."
            )
        request_key = request.data.get("request_key")
        if not request_key:
            raise ValidationError({"request_key": "Required."})
        operation = f"statement.create.{lease.id}"
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        from core_apps.users.services.sensitive_actions import consume

        if request.data.get("expected_revision") != lease.revision:
            raise RentalConflict(
                "Reload the current lease before exporting.", code="stale_revision"
            )
        consume(
            request,
            action="private.export",
            resource_id=lease.id,
            revision=lease.revision,
            payload={
                "lease_id": str(lease.id),
                "lease_revision": lease.revision,
                "starts_on": request.data.get("starts_on"),
                "ends_on_exclusive": request.data.get("ends_on_exclusive"),
                "request_key": str(request_key),
            },
        )
        document = RentalDocument.objects.create(
            lease=lease,
            requested_by=request.user,
            document_type=RentalDocument.DocumentType.STATEMENT,
            title="Rental statement",
            generation_requested_at=timezone.now(),
            starts_on=parse_date(starts) if starts else None,
            ends_on_exclusive=parse_date(ends) if ends else None,
        )
        return Response(
            remember_mutation(
                user=request.user,
                operation=operation,
                request_key=request_key,
                payload=request.data,
                request_subject_id=lease.id,
                result_subject_id=document.id,
                result_revision=document.revision,
                resource=document_payload(document),
                response_status=201,
            ),
            status=status.HTTP_201_CREATED,
        )


# Stable callable import for integrations; URLs use the explicit class.
rental_statement_create = RentalStatementCreateView.as_view()


def review_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "author_id": str(item.author.id),
        "rating": item.rating,
        "comment": item.comment,
        "revision": item.revision,
    }


class LeaseReviewsView(FeatureAPIView):
    name = "Lease Reviews"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "lease_reviews",
            "lease_reviews",
            boundary="standard",
            capability=None,
            typed=False,
        ),
        "post": ActionPolicy(
            "lease_reviews",
            "lease_reviews",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = _lease(request, lease_id)
        results = [
            review_payload(x) for x in lease.rental_reviews.select_related("author")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )

    def post(self, request, lease_id):
        _lease(request, lease_id)
        from ..services.reputation.policy import ReviewError

        raise ReviewError("client_update_required")


# Stable callable import for integrations; URLs use the explicit class.
lease_reviews = LeaseReviewsView.as_view()
