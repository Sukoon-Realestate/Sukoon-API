"""Rental phase6 views: lease reviews."""

from datetime import timedelta
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    authentication_classes,
)
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from ..models import RentalChange, RentalDocument, RentalHandover, RentalReview
from ..providers import get_rental_provider
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_documents(request, lease_id):
    lease = document_lease(request, lease_id)
    if lease.document_id:
        RentalDocument.objects.get_or_create(
            lease=lease,
            document_type=RentalDocument.DocumentType.CONTRACT,
            source_reference=str(lease.document_id),
            defaults={"requested_by": request.user, "title": "Rental agreement"},
        )
    for invoice in lease.invoices.exclude(receipt_id__isnull=True):
        RentalDocument.objects.get_or_create(
            lease=lease,
            document_type=RentalDocument.DocumentType.RECEIPT,
            source_reference=str(invoice.receipt_id),
            defaults={
                "requested_by": request.user,
                "title": f"Receipt record {invoice.reference} (JSON)",
            },
        )
    for change in lease.rental_changes.filter(
        status__in=[RentalChange.Status.SIGNED, RentalChange.Status.APPLIED]
    ):
        RentalDocument.objects.get_or_create(
            lease=lease,
            document_type=RentalDocument.DocumentType.CHANGE,
            source_reference=str(change.id),
            defaults={
                "requested_by": request.user,
                "title": f"{change.get_kind_display()} {change.id}",
            },
        )
    documents = lease.private_documents.all()
    if lease.renter_company_id:
        from ..services.company.tenancy_access import financial_read, commercial_read

        types = []
        if commercial_read(lease, request.user):
            types += ["contract", "change"]
        if financial_read(lease, request.user):
            types += ["receipt", "settlement", "statement"]
        documents = documents.filter(document_type__in=types)
    results = [document_payload(x) for x in documents]
    return Response(
        {"count": len(results), "next": None, "previous": None, "results": results}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def document_download(request, document_id):

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
            "url": download_url(request, document),
            "expires_at": expires.isoformat(),
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def document_content(request, document_id):
    from ..services.private_rental_documents import content_response

    return content_response(document_id, request.query_params.get("token", ""))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@transaction.atomic
def rental_statement_create(request):
    # Sensitive authorization and account revocation use account -> resource order.
    from core_apps.users.models import User

    User.objects.select_for_update().get(pk=request.user.pk)
    lease = document_lease(
        request, request.data.get("lease_id"), lock=True, document_type="statement"
    )
    from django.utils.dateparse import parse_date

    starts, ends = request.data.get("starts_on"), request.data.get("ends_on_exclusive")
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


def review_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "author_id": str(item.author.id),
        "rating": item.rating,
        "comment": item.comment,
        "revision": item.revision,
    }


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_reviews(request, lease_id):
    lease = _lease(request, lease_id)
    if request.method == "GET":
        results = [
            review_payload(x) for x in lease.rental_reviews.select_related("author")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    # Old clients cannot explain immutable submission or select canonical targets.
    from ..services.reputation.policy import ReviewError

    raise ReviewError("client_update_required")
