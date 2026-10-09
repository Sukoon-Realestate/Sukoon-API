import uuid
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_apps.admin_api.models import StaffProfile

from .models import (
    DepositAgreement,
    FinalSettlement,
    Lease,
    MaintenanceRequest,
    PaymentAttempt,
    PrivateAccessRevocation,
    RefundRequest,
    RentalChange,
    RentalDispute,
    RentalDocument,
    RentalEvidence,
    RentalHandover,
    RentalPayout,
    RentalReview,
    RentInvoice,
)
from .providers import get_rental_provider
from .renderers import FeatureJsonRenderer
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase6 import (
    evaluate_financial_closure,
    refundable_balance_minor,
    settlement_balances,
)


def _money(value):
    return {"amount_minor": value, "currency": "EGP", "exponent": 2}


def _lease(request, lease_id, lock=False):
    queryset = Lease.objects.select_related("owner", "tenant", "property")
    if lock:
        queryset = queryset.select_for_update()
    lease = get_object_or_404(queryset, id=lease_id)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    if PrivateAccessRevocation.objects.filter(lease=lease, user=request.user).exists():
        raise NotFound()
    return lease


def settlement_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "lines": item.lines,
        "rent_balance": _money(item.rent_balance_minor),
        "deposit_to_return": _money(item.deposit_to_return_minor),
        "refund_due": _money(item.refund_due_minor),
        "total_due": _money(item.total_due_minor),
        "accepted_by": item.accepted_by,
        "disputed_item_ids": item.disputed_item_ids,
    }


def _settlement(lease):
    item, _ = FinalSettlement.objects.get_or_create(lease=lease)
    return item


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def final_settlement_detail(request, lease_id):
    return Response(settlement_payload(_settlement(_lease(request, lease_id))))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def final_settlement_propose(request, lease_id):
    lease = _lease(request, lease_id)
    request_key = request.data.get("request_key")
    if not request_key or int(request.data.get("expected_revision", 0)) < 1:
        raise ValidationError("expected_revision and request_key are required.")
    operation = f"settlement.propose.{lease.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    allowed_types = {
        "damage",
        "cleaning",
        "utilities",
        "rent_adjustment",
        "deposit_return",
        "refund",
    }
    lines = []
    seen = set()
    for raw in request.data.get("lines", []):
        line_id = str(raw.get("id") or uuid.uuid4())
        amount = (raw.get("amount") or {}).get("amount_minor")
        if (
            line_id in seen
            or raw.get("type") not in allowed_types
            or not isinstance(amount, int)
        ):
            raise ValidationError(
                {
                    "lines": "Each line needs a unique ID, supported type, and integer EGP amount."
                }
            )
        evidence_ids = raw.get("evidence_ids", [])
        if RentalEvidence.objects.filter(
            id__in=evidence_ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
        ).count() != len(set(evidence_ids)):
            raise ValidationError(
                {"lines": "Line evidence must be safe and belong to this lease."}
            )
        seen.add(line_id)
        lines.append(
            {
                "id": line_id,
                "type": raw["type"],
                "label": raw.get("label", raw["type"]),
                "amount": _money(amount),
                "evidence_ids": list(evidence_ids),
            }
        )
    balances = settlement_balances(lease, lines)
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        item = FinalSettlement.objects.select_for_update().get(lease=lease)
        if item.revision != int(request.data["expected_revision"]):
            raise RentalConflict("Settlement revision conflict.", code="stale_revision")
        item.lines = lines
        (
            item.rent_balance_minor,
            item.deposit_to_return_minor,
            item.refund_due_minor,
            item.total_due_minor,
        ) = balances
        item.status = FinalSettlement.Status.PROPOSED
        item.accepted_by = [str(request.user.id)]
        item.disputed_item_ids = []
        item.proposed_by = request.user
        item.revision += 1
        item.save()
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=settlement_payload(item),
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def final_settlement_respond(request, lease_id):
    lease = _lease(request, lease_id)
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"accept", "dispute"} or not request.data.get("request_key"):
        raise ValidationError("accept/dispute and request_key are required.")
    operation = f"settlement.respond.{lease.id}.{request.user.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        item = FinalSettlement.objects.select_for_update().get(lease=lease)
        if item.revision != int(request.data.get("expected_revision", 0)):
            raise RentalConflict("Settlement revision conflict.", code="stale_revision")
        current_ids = {line["id"] for line in item.lines}
        if action == "dispute":
            disputed = set(map(str, request.data.get("item_ids", [])))
            if not disputed or not disputed.issubset(current_ids):
                raise ValidationError(
                    {"item_ids": "Choose persisted settlement item IDs."}
                )
            item.disputed_item_ids = sorted(disputed)
            item.status = FinalSettlement.Status.DISPUTED
            item.accepted_by = []
        else:
            accepted = set(item.accepted_by)
            accepted.add(str(request.user.id))
            item.accepted_by = sorted(accepted)
            if {str(lease.owner.id), str(lease.tenant.id)}.issubset(accepted):
                item.status = FinalSettlement.Status.ACCEPTED
        item.revision += 1
        item.save()
        if item.status == FinalSettlement.Status.ACCEPTED:
            RentalDocument.objects.get_or_create(
                lease=lease,
                document_type=RentalDocument.DocumentType.SETTLEMENT,
                title="Final settlement",
                defaults={"requested_by": request.user},
            )
        evaluate_financial_closure(lease)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=settlement_payload(item),
        )
    return Response(output)


def refund_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "payment_attempt_id": str(item.payment_attempt.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "refundable_balance": _money(refundable_balance_minor(item.payment_attempt)),
        "reason": item.reason,
        "provider_refund_id": item.provider_refund_id,
        "failure_code": item.failure_code,
    }


def _refund(request, refund_id, allow_operations=False, lock=False):
    queryset = RefundRequest.objects.select_related(
        "lease__owner", "lease__tenant", "payment_attempt__invoice"
    )
    if lock:
        queryset = queryset.select_for_update()
    item = get_object_or_404(queryset, id=refund_id)
    profile = getattr(request.user, "staff_profile", None)
    operator = allow_operations and (
        request.user.is_superuser
        or (
            profile
            and profile.is_active
            and profile.role_name
            in {
                StaffProfile.RoleName.REFUND_OPERATOR,
                StaffProfile.RoleName.FINANCIAL_APPROVER,
            }
        )
    )
    if request.user not in (item.lease.owner, item.lease.tenant) and not operator:
        raise NotFound()
    return item


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_requests(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        queryset = (
            RefundRequest.objects.filter(lease__owner=request.user)
            if workspace == "owner"
            else RefundRequest.objects.filter(lease__tenant=request.user)
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        results = [
            refund_payload(x)
            for x in queryset.select_related("lease", "payment_attempt__invoice")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    attempt = get_object_or_404(
        PaymentAttempt.objects.select_related("invoice__lease"),
        id=request.data.get("payment_attempt_id"),
    )
    lease = _lease(request, attempt.invoice.lease.id)
    if request.user != attempt.payer:
        raise PermissionDenied("Only the captured payer can request a refund.")
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"refund.create.{attempt.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    amount = (request.data.get("amount") or {}).get("amount_minor")
    if (
        not isinstance(amount, int)
        or amount <= 0
        or amount > refundable_balance_minor(attempt)
    ):
        raise RentalConflict(
            "Refund exceeds the remaining refundable capture balance.",
            code="refund_exceeds_balance",
        )
    with transaction.atomic():
        attempt = PaymentAttempt.objects.select_for_update().get(pk=attempt.pk)
        item = RefundRequest.objects.create(
            lease=lease,
            payment_attempt=attempt,
            requester=request.user,
            amount_minor=amount,
            refundable_balance_snapshot_minor=refundable_balance_minor(attempt),
            reason=request.data.get("reason", ""),
            request_key=request_key,
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=refund_payload(item),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_detail(request, refund_id):
    return Response(refund_payload(_refund(request, refund_id)))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def refund_respond(request, refund_id):
    item = _refund(request, refund_id, allow_operations=True)
    profile = getattr(request.user, "staff_profile", None)
    if not request.user.is_superuser and (
        not profile
        or not profile.is_active
        or profile.role_name
        not in {
            StaffProfile.RoleName.REFUND_OPERATOR,
            StaffProfile.RoleName.FINANCIAL_APPROVER,
        }
    ):
        raise PermissionDenied("Refund approval requires an operations role.")
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"approve", "reject"}:
        raise ValidationError({"action": "Must be approve or reject."})
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"refund.respond.{item.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        item = _refund(request, refund_id, allow_operations=True, lock=True)
        if item.revision != int(request.data.get("expected_revision", 0)):
            raise RentalConflict("Refund revision conflict.", code="stale_revision")
        item.status = (
            RefundRequest.Status.APPROVED
            if action == "approve"
            else RefundRequest.Status.REJECTED
        )
        item.approved_by = request.user
        item.revision += 1
        item.save()
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=refund_payload(item),
        )
    return Response(output)


SUBJECT_MODELS = {
    "invoice": RentInvoice,
    "deposit": DepositAgreement,
    "handover": RentalHandover,
    "maintenance": MaintenanceRequest,
    "change": RentalChange,
    "payout": RentalPayout,
    "refund": RefundRequest,
    "settlement": FinalSettlement,
}


def dispute_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "subject_kind": item.subject_kind,
        "subject_id": str(item.subject_id),
        "revision": item.revision,
        "status": item.status,
        "reason": item.reason,
        "resolution": item.resolution,
        "responses": item.responses,
        "evidence": [
            {"id": str(x.id), "sha256": x.sha256, "status": "ready"}
            for x in item.evidence.all()
        ],
    }


def _dispute(request, dispute_id, allow_operations=False, lock=False):
    queryset = RentalDispute.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("evidence")
    if lock:
        queryset = queryset.select_for_update()
    item = get_object_or_404(queryset, id=dispute_id)
    profile = getattr(request.user, "staff_profile", None)
    operator = allow_operations and (
        request.user.is_superuser
        or (
            profile
            and profile.is_active
            and profile.role_name == StaffProfile.RoleName.DISPUTE_RESOLVER
        )
    )
    if request.user not in (item.lease.owner, item.lease.tenant) and not operator:
        raise NotFound()
    return item


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def disputes(request):
    if request.method == "GET":
        workspace = request.query_params.get("workspace")
        queryset = (
            RentalDispute.objects.filter(lease__owner=request.user)
            if workspace == "owner"
            else RentalDispute.objects.filter(lease__tenant=request.user)
        )
        if request.query_params.get("lease_id"):
            queryset = queryset.filter(lease__id=request.query_params["lease_id"])
        results = [dispute_payload(x) for x in queryset.prefetch_related("evidence")]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    lease = _lease(request, request.data.get("lease_id"))
    kind = request.data.get("subject_kind")
    model = SUBJECT_MODELS.get(kind)
    if not model:
        raise ValidationError({"subject_kind": "Unsupported dispute subject."})
    subject = get_object_or_404(model, id=request.data.get("subject_id"))
    if getattr(subject, "lease_id", None) != lease.pk:
        raise ValidationError({"subject_id": "Subject does not belong to this lease."})
    evidence_ids = request.data.get("evidence_ids", [])
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=evidence_ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
        )
    )
    if len(evidence) != len(set(evidence_ids)):
        raise ValidationError({"evidence_ids": "Invalid evidence."})
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"dispute.create.{lease.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    item = RentalDispute.objects.create(
        lease=lease,
        opened_by=request.user,
        subject_kind=kind,
        subject_id=subject.id,
        reason=request.data.get("reason", ""),
    )
    item.evidence.set(evidence)
    return Response(
        remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=dispute_payload(item),
            response_status=201,
        ),
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def dispute_detail(request, dispute_id):
    return Response(dispute_payload(_dispute(request, dispute_id)))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def dispute_respond(request, dispute_id):
    item = _dispute(request, dispute_id, allow_operations=True)
    action = request.data.get("action", "reply")
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"dispute.respond.{item.id}.{request.user.id}.{action}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        item = _dispute(request, dispute_id, allow_operations=True, lock=True)
        if item.revision != int(request.data.get("expected_revision", 0)):
            raise RentalConflict("Dispute revision conflict.", code="stale_revision")
        if action == "reply":
            if request.user not in (item.lease.owner, item.lease.tenant):
                raise PermissionDenied("Only parties may reply.")
            item.responses = [
                *item.responses,
                {
                    "id": str(uuid.uuid4()),
                    "author_id": str(request.user.id),
                    "note": request.data.get("note", ""),
                    "at": timezone.now().isoformat(),
                },
            ]
        elif action in {"resolve", "reject"}:
            profile = getattr(request.user, "staff_profile", None)
            if not request.user.is_superuser and (
                not profile
                or profile.role_name != StaffProfile.RoleName.DISPUTE_RESOLVER
            ):
                raise PermissionDenied("Resolution requires the dispute resolver role.")
            item.status = (
                RentalDispute.Status.RESOLVED
                if action == "resolve"
                else RentalDispute.Status.REJECTED
            )
            item.resolution = request.data.get("note", "")
            item.resolved_by = request.user
        else:
            raise ValidationError({"action": "Unsupported dispute action."})
        item.revision += 1
        item.save()
        evaluate_financial_closure(item.lease)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=dispute_payload(item),
        )
    return Response(output)


def document_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "type": item.document_type,
        "title": item.title,
        "status": item.status,
        "sha256": item.sha256,
        "starts_on": str(item.starts_on) if item.starts_on else None,
        "ends_on_exclusive": (
            str(item.ends_on_exclusive) if item.ends_on_exclusive else None
        ),
    }


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_center(request, lease_id):
    lease = _lease(request, lease_id)
    reasons = evaluate_financial_closure(lease)
    balance = sum(
        max((x.charges_minor or x.amount_minor) - x.credits_minor - x.applied_minor, 0)
        for x in lease.invoices.all()
    )
    next_action = (
        {
            "action": "resolve_closure",
            "resource_id": str(lease.id),
            "description": reasons[0],
            "kind": "closure",
        }
        if reasons
        else None
    )
    return Response(
        {
            "id": str(lease.id),
            "tenancy_root_id": str(lease.tenancy_root_id),
            "revision": lease.revision,
            "property_title": lease.property.title,
            "lease_status": lease.status,
            "status": lease.status,
            "occupancy_status": lease.occupancy_status,
            "financial_closure_status": lease.financial_closure_status,
            "terms": lease.terms,
            "balance": _money(balance),
            "next_action": next_action,
            "timeline": [],
            "billing_schedule": [],
            "chat_thread_id": None,
            "last_updated_at": lease.updated_at.isoformat(),
            "legacy_read_only": lease.legacy_read_only,
            "offer_snapshot": lease.offer_snapshot,
            "closure_blocking_reasons": reasons,
        }
    )
