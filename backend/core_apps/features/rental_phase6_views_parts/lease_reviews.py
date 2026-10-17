"""Rental phase6 views: lease reviews."""

from datetime import timedelta
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import RentalChange, RentalDocument, RentalHandover, RentalReview
from ..providers import get_rental_provider
from ..renderers import FeatureJsonRenderer
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .final_settlement_propose import _lease
from .disputes import document_payload


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_documents(request, lease_id):
    lease = _lease(request, lease_id)
    if lease.document_id:
        RentalDocument.objects.get_or_create(
            lease=lease,
            document_type=RentalDocument.DocumentType.CONTRACT,
            title="Rental agreement",
            defaults={"requested_by": request.user},
        )
    for invoice in lease.invoices.exclude(receipt_id__isnull=True):
        RentalDocument.objects.get_or_create(
            lease=lease,
            document_type=RentalDocument.DocumentType.RECEIPT,
            title=f"Receipt {invoice.reference}",
            defaults={"requested_by": request.user},
        )
    for change in lease.rental_changes.filter(
        status__in=[RentalChange.Status.SIGNED, RentalChange.Status.APPLIED]
    ):
        RentalDocument.objects.get_or_create(
            lease=lease,
            document_type=RentalDocument.DocumentType.CHANGE,
            title=f"{change.get_kind_display()} {change.id}",
            defaults={"requested_by": request.user},
        )
    results = [document_payload(x) for x in lease.private_documents.all()]
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
    _lease(request, document.lease.id)
    if document.status != RentalDocument.Status.READY:
        raise RentalConflict("Document is not ready.")
    expires = timezone.now() + timedelta(minutes=5)
    return Response(
        {
            "id": str(document.id),
            "subject_id": str(document.lease.id),
            "url": get_rental_provider().create_private_download(document.id, expires),
            "expires_at": expires.isoformat(),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_statement_create(request):
    lease = _lease(request, request.data.get("lease_id"))
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"statement.create.{lease.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    document = RentalDocument.objects.create(
        lease=lease,
        requested_by=request.user,
        document_type=RentalDocument.DocumentType.STATEMENT,
        title="Rental statement",
        starts_on=request.data.get("starts_on"),
        ends_on_exclusive=request.data.get("ends_on_exclusive"),
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
