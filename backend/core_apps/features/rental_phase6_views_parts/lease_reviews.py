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
    if not lease.handovers.filter(
        kind=RentalHandover.Kind.MOVE_IN, status=RentalHandover.Status.ACCEPTED
    ).exists():
        raise PermissionDenied("A review requires an actual tenancy.")
    request_key = request.data.get("request_key")
    if not request_key or int(request.data.get("expected_revision", -1)) != 0:
        raise ValidationError("request_key and expected_revision=0 are required.")
    operation = f"rental_review.create.{lease.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    rating = request.data.get("rating")
    if not isinstance(rating, int) or not 1 <= rating <= 5:
        raise ValidationError({"rating": "Must be 1 through 5."})
    try:
        item = RentalReview.objects.create(
            lease=lease,
            author=request.user,
            rating=rating,
            comment=request.data.get("comment", ""),
        )
    except IntegrityError:
        raise RentalConflict("This tenancy was already reviewed.")
    output = remember_mutation(
        user=request.user,
        operation=operation,
        request_key=request_key,
        payload=request.data,
        request_subject_id=lease.id,
        result_subject_id=item.id,
        result_revision=item.revision,
        resource=review_payload(item),
        response_status=201,
    )
    return Response(output, status=status.HTTP_201_CREATED)
