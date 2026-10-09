import hashlib
import uuid
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    renderer_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_apps.admin_api.models import StaffProfile

from .models import (
    DepositAgreement,
    InvoiceLine,
    OwnerPayable,
    OwnerPaymentProfile,
    PayoutAuditEvent,
    PayoutBatch,
    RentalEvidence,
    RentalHandover,
    RentalPayout,
    RentInvoice,
)
from .providers import get_rental_provider
from .renderers import FeatureJsonRenderer
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import post_ledger_transaction


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024


def _money(value):
    return {"amount_minor": value, "currency": "EGP", "exponent": 2}


def _lease(request, lease_id, lock=False):
    from .models import Lease

    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update()
    lease = get_object_or_404(queryset, id=lease_id)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    return lease


def evidence_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "name": item.original_name,
        "mime_type": item.content_type,
        "size_bytes": item.size_bytes,
        "status": (
            "ready"
            if item.malware_status == RentalEvidence.MalwareStatus.SAFE
            else item.malware_status
        ),
        "sha256": item.sha256,
        "revision": item.revision,
    }


def handover_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "kind": item.kind,
        "status": item.status,
        "possession_on": str(item.possession_on),
        "condition": item.condition,
        "keys": item.keys,
        "meters": item.meters,
        "inventory": item.inventory,
        "evidence": [evidence_payload(x) for x in item.evidence.all()],
        "accepted_by": item.approvals,
    }


def _handover(request, handover_id, lock=False):
    queryset = RentalHandover.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("evidence")
    if lock:
        queryset = queryset.select_for_update()
    handover = get_object_or_404(queryset, id=handover_id)
    if request.user not in (handover.lease.owner, handover.lease.tenant):
        raise NotFound()
    return handover


def _validate_evidence(lease, ids):
    if len(ids) > 5:
        raise ValidationError({"evidence_ids": "At most five images are supported."})
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=ids,
            lease=lease,
            malware_status=RentalEvidence.MalwareStatus.SAFE,
            deleted_at__isnull=True,
        )
    )
    if len(evidence) != len(set(map(str, ids))):
        raise ValidationError(
            {"evidence_ids": "Every item must be safe evidence for this lease."}
        )
    return evidence


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@parser_classes([MultiPartParser, FormParser])
def rental_evidence_upload(request):
    lease_id = request.data.get("lease_id")
    request_key = request.data.get("request_key")
    upload = request.FILES.get("file")
    claimed_type = request.data.get("mime_type")
    claimed_digest = request.data.get("sha256", "").lower()
    if not all([lease_id, request_key, upload, claimed_type, claimed_digest]):
        raise ValidationError(
            "lease_id, file, mime_type, sha256, and request_key are required."
        )
    try:
        request_key = uuid.UUID(str(request_key))
    except ValueError:
        raise ValidationError({"request_key": "Must be a UUID."})
    operation = f"rental_evidence.upload.{lease_id}"
    existing = RentalEvidence.objects.filter(
        uploader=request.user, lease__id=lease_id, request_key=request_key
    ).first()
    if existing:
        if existing.sha256 != claimed_digest:
            raise RentalConflict(
                "The request key belongs to different evidence.",
                code="idempotency_conflict",
            )
        record = replay_operation(
            request.user,
            operation,
            request_key,
            {"lease_id": str(lease_id), "sha256": claimed_digest},
        )
        if record:
            return Response(record[0], status=record[1])
    lease = _lease(request, lease_id)
    content = upload.read(MAX_EVIDENCE_BYTES + 1)
    if len(content) > MAX_EVIDENCE_BYTES:
        raise ValidationError({"file": "PNG files must be at most 5 MiB."})
    if (
        claimed_type != "image/png"
        or upload.content_type != "image/png"
        or not content.startswith(PNG_MAGIC)
    ):
        raise ValidationError({"file": "Only actual PNG images are accepted."})
    digest = hashlib.sha256(content).hexdigest()
    if digest != claimed_digest:
        raise ValidationError({"sha256": "Digest does not match the uploaded bytes."})
    with transaction.atomic():
        evidence = RentalEvidence(
            lease=lease,
            uploader=request.user,
            request_key=request_key,
            original_name=upload.name,
            content_type="image/png",
            size_bytes=len(content),
            sha256=digest,
            storage_provider="fake",
            private_content=content,
        )
        evidence.storage_key = get_rental_provider().store_private_evidence(
            lease.id, evidence.id, content
        )
        evidence.save()
        resource = evidence_payload(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload={"lease_id": str(lease.id), "sha256": digest},
            request_subject_id=lease.id,
            result_subject_id=evidence.id,
            result_revision=evidence.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


def _evidence(request, evidence_id):
    item = get_object_or_404(
        RentalEvidence.objects.select_related("lease__owner", "lease__tenant"),
        id=evidence_id,
        deleted_at__isnull=True,
    )
    if request.user not in (item.lease.owner, item.lease.tenant):
        raise NotFound()
    return item


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_evidence_detail(request, evidence_id):
    return Response(evidence_payload(_evidence(request, evidence_id)))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def rental_evidence_download(request, evidence_id):
    item = _evidence(request, evidence_id)
    if item.malware_status != RentalEvidence.MalwareStatus.SAFE:
        raise RentalConflict("Evidence is not ready for download.")
    expires = timezone.now() + timedelta(minutes=5)
    return Response(
        {
            "id": str(item.id),
            "subject_id": str(item.lease.id),
            "url": get_rental_provider().create_private_download(item.id, expires),
            "expires_at": expires.isoformat(),
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
@parser_classes([JSONParser])
def lease_handovers(request, lease_id):
    lease = _lease(request, lease_id)
    if request.method == "GET":
        items = [
            handover_payload(x)
            for x in lease.handovers.prefetch_related("evidence").all()
        ]
        return Response(
            {"count": len(items), "next": None, "previous": None, "results": items}
        )
    required = {
        "kind",
        "possession_on",
        "condition",
        "keys",
        "meters",
        "inventory",
        "evidence_ids",
        "request_key",
        "expected_revision",
    }
    if not required.issubset(request.data):
        raise ValidationError({"request": f"Required: {', '.join(sorted(required))}."})
    if (
        request.data["kind"] not in RentalHandover.Kind.values
        or int(request.data["expected_revision"]) != 0
    ):
        raise ValidationError("Invalid handover kind or initial revision.")
    operation = f"handover.create.{lease.id}.{request.data['kind']}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    evidence = _validate_evidence(lease, request.data["evidence_ids"])
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        handover = RentalHandover.objects.create(
            lease=lease,
            kind=request.data["kind"],
            status=RentalHandover.Status.PENDING_APPROVAL,
            possession_on=request.data["possession_on"],
            condition=request.data["condition"],
            keys=request.data["keys"],
            meters=request.data["meters"],
            inventory=request.data["inventory"],
        )
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def handover_detail(request, handover_id):
    handover = _handover(request, handover_id)
    if request.method == "GET":
        return Response(handover_payload(handover))
    expected = int(request.data.get("expected_revision", 0))
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"handover.update.{handover.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        handover = _handover(request, handover_id, lock=True)
        if handover.revision != expected:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        evidence = _validate_evidence(
            handover.lease, request.data.get("evidence_ids", [])
        )
        for field in ("possession_on", "condition", "keys", "meters", "inventory"):
            if field in request.data:
                setattr(handover, field, request.data[field])
        handover.approvals = []
        handover.status = RentalHandover.Status.PENDING_APPROVAL
        handover.revision += 1
        handover.save()
        handover.evidence.set(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=handover.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover),
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def handover_respond(request, handover_id):
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"accept", "dispute"} or not request.data.get("request_key"):
        raise ValidationError(
            "accept/dispute, expected_revision, and request_key are required."
        )
    handover = _handover(request, handover_id)
    operation = f"handover.respond.{handover.id}.{request.user.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        handover = _handover(request, handover_id, lock=True)
        if int(request.data.get("expected_revision", 0)) != handover.revision:
            raise RentalConflict("Handover revision conflict.", code="stale_revision")
        approvals = set(handover.approvals)
        if action == "dispute":
            handover.status = RentalHandover.Status.DISPUTED
            handover.lease.occupancy_status = "handover_disputed"
        else:
            approvals.add(str(request.user.id))
            handover.approvals = sorted(approvals)
            if {str(handover.lease.owner.id), str(handover.lease.tenant.id)}.issubset(
                approvals
            ):
                handover.status = RentalHandover.Status.ACCEPTED
                handover.accepted_at = timezone.now()
                if handover.kind == RentalHandover.Kind.MOVE_IN:
                    handover.lease.occupancy_status = "occupied"
                    evaluate_owner_payables(handover.lease)
                else:
                    handover.lease.occupancy_status = "returned"
                    from .models import RentalInventoryDayLock

                    RentalInventoryDayLock.objects.filter(
                        lease=handover.lease, kind=RentalInventoryDayLock.Kind.OCCUPIED
                    ).delete()
            else:
                handover.status = RentalHandover.Status.PENDING_APPROVAL
        handover.revision += 1
        handover.save()
        handover.lease.save(update_fields=["occupancy_status", "updated_at"])
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=handover.id,
            result_subject_id=handover.id,
            result_revision=handover.revision,
            resource=handover_payload(handover),
        )
    return Response(output)


def deposit_payload(deposit):
    remaining = max(
        deposit.collected_minor - deposit.returned_minor - deposit.applied_minor, 0
    )
    return {
        "id": str(deposit.id),
        "lease_id": str(deposit.lease.id),
        "revision": deposit.revision,
        "holder": deposit.lease.terms.get("deposit_holder", "platform"),
        "invoice_id": str(deposit.invoice.id) if deposit.invoice else None,
        "status": "collected" if deposit.collected_minor else "due",
        "agreed": _money(deposit.agreed_minor),
        "due": _money(deposit.due_minor),
        "collected": _money(deposit.collected_minor),
        "returned": _money(deposit.returned_minor),
        "applied": _money(deposit.applied_minor),
        "disputed": _money(deposit.disputed_minor),
        "remaining": _money(remaining),
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def lease_deposit(request, lease_id):
    lease = _lease(request, lease_id)
    raw = lease.terms.get("deposit", {})
    amount = int(raw.get("amount_minor", 0)) if isinstance(raw, dict) else 0
    with transaction.atomic():
        deposit, created = DepositAgreement.objects.select_for_update().get_or_create(
            lease=lease, defaults={"agreed_minor": amount, "due_minor": amount}
        )
        if created and amount:
            invoice = RentInvoice.objects.create(
                lease=lease,
                reference=f"DEPOSIT-{lease.id.hex[:12].upper()}",
                due_date=lease.start_date,
                due_at=timezone.now(),
                amount_minor=amount,
                charges_minor=amount,
                invoice_type=RentInvoice.InvoiceType.DEPOSIT,
                status=RentInvoice.Status.DUE,
            )
            InvoiceLine.objects.create(
                invoice=invoice,
                line_type="security_deposit",
                description="Security deposit",
                amount_minor=amount,
            )
            deposit.invoice = invoice
            deposit.save(update_fields=["invoice", "updated_at"])
    return Response(deposit_payload(deposit))


def evaluate_owner_payables(lease):
    profile = OwnerPaymentProfile.objects.filter(owner=lease.owner).first()
    move_in = lease.handovers.filter(
        kind=RentalHandover.Kind.MOVE_IN, status=RentalHandover.Status.ACCEPTED
    ).exists()
    for payable in lease.owner_payables.select_for_update():
        reasons = []
        if payable.settlement_status != "settled":
            reasons.append("PSP settlement is pending.")
        if not move_in:
            reasons.append("Move-in is not accepted.")
        if not profile or not profile.payout_ready:
            reasons.append("Owner beneficiary is not ready.")
        if not profile or "rental-policy-v1" not in profile.accepted_policy_versions:
            reasons.append("Required policy is not accepted.")
        payable.blocking_reasons = reasons
        payable.payout_status = "ready" if not reasons else "held"
        payable.revision += 1
        payable.save()
        if not reasons and payable.commission_minor:
            post_ledger_transaction(
                reference=f"commission-earned:{payable.id}",
                kind="commission_earned",
                lease=lease,
                invoice=payable.invoice,
                attempt=payable.payment_attempt,
                entries=[
                    ("commission_reserve", "debit", payable.commission_minor),
                    ("commission_revenue", "credit", payable.commission_minor),
                ],
            )


def payout_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "status": item.status,
        "amount": _money(item.amount_minor),
        "masked_beneficiary": item.masked_beneficiary,
        "reason": item.hold_reason or item.failure_code,
        "submitted_at": item.created_at.isoformat(),
        "succeeded_at": (
            item.updated_at.isoformat()
            if item.status == RentalPayout.Status.PAID
            else None
        ),
        "payable_ids": [str(x.id) for x in item.payables.all()],
    }


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payouts(request):
    if request.query_params.get("workspace") != "owner":
        raise ValidationError({"workspace": "Must be owner."})
    queryset = RentalPayout.objects.filter(owner=request.user).prefetch_related(
        "payables"
    )
    if request.query_params.get("lease_id"):
        queryset = queryset.filter(lease__id=request.query_params["lease_id"])
    results = [payout_payload(x) for x in queryset]
    return Response(
        {"count": len(results), "next": None, "previous": None, "results": results}
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payout_detail(request, payout_id):
    item = get_object_or_404(
        RentalPayout.objects.prefetch_related("payables"),
        id=payout_id,
        owner=request.user,
    )
    return Response(payout_payload(item))


def _require_payout_role(user):
    profile = getattr(user, "staff_profile", None)
    if not user.is_superuser and (
        not profile
        or not profile.is_active
        or profile.role_name != StaffProfile.RoleName.PAYOUT_OPERATOR
    ):
        raise PermissionDenied("Payout execution requires the payout operator role.")


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def operations_execute_payout(request):
    _require_payout_role(request.user)
    payable_ids = request.data.get("payable_ids", [])
    request_key = request.data.get("request_key")
    if not payable_ids or not request_key:
        raise ValidationError("payable_ids and request_key are required.")
    operation = "payout.execute"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        payables = list(
            OwnerPayable.objects.select_for_update()
            .select_related("lease__owner")
            .filter(id__in=payable_ids)
        )
        if len(payables) != len(set(payable_ids)) or any(
            x.payout_status != "ready" for x in payables
        ):
            raise RentalConflict(
                "Every payable must be eligible and unallocated.", code="payout_held"
            )
        if (
            len({x.lease.owner_id for x in payables}) != 1
            or len({x.lease_id for x in payables}) != 1
        ):
            raise ValidationError("A payout batch must target one owner and lease.")
        batch = PayoutBatch.objects.create(
            approved_by=request.user, request_key=request_key
        )
        profile = OwnerPaymentProfile.objects.get(owner=payables[0].lease.owner)
        payout = RentalPayout.objects.create(
            batch=batch,
            owner=payables[0].lease.owner,
            lease=payables[0].lease,
            amount_minor=sum(x.net_minor for x in payables),
            masked_beneficiary=profile.masked_beneficiary,
        )
        payout.payables.set(payables)
        for payable in payables:
            payable.payout_status = "submitted"
            payable.save(update_fields=["payout_status", "updated_at"])
        PayoutAuditEvent.objects.create(
            payout=payout, actor=request.user, action="approved"
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=payables[0].lease.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def operations_reconcile_payout(request, payout_id):
    _require_payout_role(request.user)
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"payout.reconcile.{payout_id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        payout = get_object_or_404(
            RentalPayout.objects.select_for_update().prefetch_related("payables"),
            id=payout_id,
        )
        if payout.status != RentalPayout.Status.PAID:
            payout.provider_payout_id = get_rental_provider().execute_payout(
                payout.id, payout.batch.request_key
            )
            payout.status = RentalPayout.Status.PAID
            payout.revision += 1
            payout.save()
            payout.payables.update(payout_status="succeeded", updated_at=timezone.now())
            post_ledger_transaction(
                reference=f"payout:{payout.id}",
                kind="owner_payout",
                lease=payout.lease,
                entries=[
                    ("owner_liability", "debit", payout.amount_minor),
                    ("platform_cash", "credit", payout.amount_minor),
                ],
            )
            PayoutAuditEvent.objects.create(
                payout=payout,
                actor=request.user,
                action="paid",
                metadata={"provider_payout_id": payout.provider_payout_id},
            )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=payout.id,
            result_subject_id=payout.id,
            result_revision=payout.revision,
            resource=payout_payload(payout),
        )
    return Response(output)
