from datetime import time, timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core_apps.admin_api.models import StaffProfile

from .models import (
    ChangeSigningSession,
    Lease,
    MaintenanceEvent,
    MaintenanceRequest,
    RentalChange,
    RentalEvidence,
    RentInvoice,
)
from .providers import get_rental_provider
from .renderers import FeatureJsonRenderer
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import cairo_instant


MAINTENANCE_ACTIONS = {
    "acknowledge",
    "reply",
    "propose_appointment",
    "accept_appointment",
    "start_work",
    "report_resolved",
    "confirm_resolved",
    "reopen",
    "cancel",
    "propose_cost",
    "approve_cost",
    "reject_cost",
}


def _money(value):
    return (
        None
        if value is None
        else {"amount_minor": value, "currency": "EGP", "exponent": 2}
    )


def _lease(request, lease_id, lock=False):
    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update()
    lease = get_object_or_404(queryset, id=lease_id)
    if request.user not in (lease.owner, lease.tenant):
        raise NotFound()
    if lease.legacy_read_only:
        raise PermissionDenied("Legacy rentals are read-only.")
    return lease


def _safe_evidence(lease, ids):
    items = list(
        RentalEvidence.objects.filter(
            id__in=ids, lease=lease, malware_status=RentalEvidence.MalwareStatus.SAFE
        )
    )
    if len(items) != len(set(map(str, ids))):
        raise ValidationError(
            {"evidence_ids": "Evidence must be safe and belong to this lease."}
        )
    return items


def maintenance_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "revision": item.revision,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "priority": item.priority,
        "access_times": item.access_times,
        "status": item.status,
        "appointment_at": (
            item.appointment_at.isoformat() if item.appointment_at else None
        ),
        "proposed_cost": _money(item.proposed_cost_minor),
        "cost_payer": item.cost_payer or None,
        "cost_version": item.cost_version,
        "approved_cost_version": item.approved_cost_version,
        "events": [
            {
                "id": str(x.id),
                "label": x.action,
                "note": x.note,
                "at": x.created_at.isoformat(),
                "appointment_at": (
                    x.appointment_at.isoformat() if x.appointment_at else None
                ),
                "cost": _money(x.cost_minor),
            }
            for x in item.events.all()
        ],
        "evidence": [
            {"id": str(x.id), "sha256": x.sha256, "status": "ready"}
            for x in item.evidence.all()
        ],
    }


def _maintenance(request, request_id, lock=False):
    queryset = MaintenanceRequest.objects.select_related(
        "lease__owner", "lease__tenant"
    ).prefetch_related("events", "evidence")
    if lock:
        queryset = queryset.select_for_update()
    item = get_object_or_404(queryset, id=request_id)
    if request.user not in (item.lease.owner, item.lease.tenant):
        raise NotFound()
    return item


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_requests(request, lease_id):
    lease = _lease(request, lease_id)
    if request.method == "GET":
        results = [
            maintenance_payload(x)
            for x in lease.maintenance_requests.prefetch_related("events", "evidence")
        ]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    required = {
        "title",
        "description",
        "category",
        "priority",
        "access_times",
        "evidence_ids",
        "request_key",
        "expected_revision",
    }
    if (
        not required.issubset(request.data)
        or int(request.data["expected_revision"]) != 0
    ):
        raise ValidationError(
            "Complete maintenance body with expected_revision=0 is required."
        )
    operation = f"maintenance.create.{lease.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    evidence = _safe_evidence(lease, request.data["evidence_ids"])
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        item = MaintenanceRequest.objects.create(
            lease=lease,
            reporter=request.user,
            title=request.data["title"],
            description=request.data["description"],
            category=request.data["category"],
            priority=request.data["priority"],
            access_times=request.data["access_times"],
        )
        item.evidence.set(evidence)
        MaintenanceEvent.objects.create(
            maintenance_request=item, actor=request.user, action="created"
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_detail(request, request_id):
    return Response(maintenance_payload(_maintenance(request, request_id)))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_action(request, request_id):
    action = request.data.get("action")
    if action not in MAINTENANCE_ACTIONS or not request.data.get("request_key"):
        raise ValidationError({"action": "Unsupported action or missing request key."})
    item = _maintenance(request, request_id)
    operation = f"maintenance.action.{item.id}.{action}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    transitions = {
        "acknowledge": ({"open"}, "acknowledged"),
        "propose_appointment": ({"open", "acknowledged"}, "appointment_proposed"),
        "accept_appointment": ({"appointment_proposed"}, "scheduled"),
        "start_work": ({"acknowledged", "scheduled"}, "in_progress"),
        "report_resolved": ({"in_progress"}, "resolution_reported"),
        "confirm_resolved": ({"resolution_reported"}, "resolved"),
        "reopen": ({"resolution_reported", "resolved"}, "open"),
        "cancel": (
            {"open", "acknowledged", "appointment_proposed", "scheduled"},
            "cancelled",
        ),
    }
    with transaction.atomic():
        item = _maintenance(request, request_id, lock=True)
        if int(request.data.get("expected_revision", 0)) != item.revision:
            raise RentalConflict(
                "Maintenance revision conflict.", code="stale_revision"
            )
        if action in transitions:
            allowed, target = transitions[action]
            if item.status not in allowed:
                raise RentalConflict("Unsupported maintenance transition.")
            item.status = target
        elif action == "reply":
            if item.status == MaintenanceRequest.Status.CANCELLED:
                raise RentalConflict("Cancelled requests cannot receive replies.")
        elif action == "propose_cost":
            cost = request.data.get("cost", {})
            payer = request.data.get("cost_payer")
            if (
                payer not in {"owner", "tenant"}
                or not isinstance(cost.get("amount_minor"), int)
                or cost["amount_minor"] <= 0
            ):
                raise ValidationError(
                    "A positive EGP cost and owner/tenant payer are required."
                )
            item.proposed_cost_minor = cost["amount_minor"]
            item.cost_payer = payer
            item.cost_version += 1
            item.approved_cost_version = None
        elif action in {"approve_cost", "reject_cost"}:
            responsible = (
                item.lease.owner if item.cost_payer == "owner" else item.lease.tenant
            )
            if request.user != responsible:
                raise PermissionDenied(
                    "Only the responsible payer may decide this cost."
                )
            if (
                int(request.data.get("cost_version", 0)) != item.cost_version
                or not item.proposed_cost_minor
            ):
                raise RentalConflict("Cost version conflict.", code="stale_revision")
            item.approved_cost_version = (
                item.cost_version if action == "approve_cost" else None
            )
        if action == "propose_appointment":
            if not request.data.get("appointment_at"):
                raise ValidationError({"appointment_at": "Required."})
            item.appointment_at = parse_datetime(request.data["appointment_at"])
            if not item.appointment_at:
                raise ValidationError({"appointment_at": "Must be an ISO date-time."})
        item.revision += 1
        item.save()
        MaintenanceEvent.objects.create(
            maintenance_request=item,
            actor=request.user,
            action=action,
            note=request.data.get("note", ""),
            appointment_at=(
                item.appointment_at
                if action in {"propose_appointment", "accept_appointment"}
                else None
            ),
            cost_minor=item.proposed_cost_minor if "cost" in action else None,
            metadata={"cost_version": item.cost_version} if "cost" in action else {},
        )
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=maintenance_payload(item),
        )
    return Response(output)


def change_payload(item):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "invoice_id": str(item.invoice.id) if item.invoice else None,
        "revision": item.revision,
        "kind": item.kind,
        "status": item.status,
        "reason": item.reason,
        "requested_date": str(item.requested_date) if item.requested_date else None,
        "original_due_at": (
            item.original_due_at.isoformat() if item.original_due_at else None
        ),
        "deferred_until": (
            item.deferred_until.isoformat() if item.deferred_until else None
        ),
        "effective_on": str(item.effective_on) if item.effective_on else None,
        "amount": _money(item.amount_minor),
        "terms": item.terms,
        "previous_terms": item.previous_terms,
        "document_id": str(item.document_id) if item.document_id else None,
        "document_hash": item.document_hash,
        "signature_document_id": str(item.document_id) if item.document_id else None,
        "accepted_by": item.approvals,
        "signed_by": item.signed_by,
    }


def _change(request, change_id, expected_kind=None, lock=False):
    queryset = RentalChange.objects.select_related(
        "lease__owner", "lease__tenant", "invoice"
    )
    if lock:
        queryset = queryset.select_for_update()
    item = get_object_or_404(queryset, id=change_id)
    if expected_kind and item.kind != expected_kind:
        raise NotFound()
    profile = getattr(request.user, "staff_profile", None)
    operations_external = item.kind == RentalChange.Kind.EXTERNAL_PAYMENT and (
        request.user.is_superuser
        or (
            profile
            and profile.is_active
            and profile.role_name
            in {
                StaffProfile.RoleName.FINANCIAL_APPROVER,
                StaffProfile.RoleName.PSP_RECONCILIATION,
            }
        )
    )
    if (
        request.user not in (item.lease.owner, item.lease.tenant)
        and not operations_external
    ):
        raise NotFound()
    return item


def change_collection(request, lease_id, kind):
    lease = _lease(request, lease_id)
    if request.method == "GET":
        results = [change_payload(x) for x in lease.rental_changes.filter(kind=kind)]
        return Response(
            {"count": len(results), "next": None, "previous": None, "results": results}
        )
    if int(request.data.get("expected_revision", -1)) != 0 or not request.data.get(
        "request_key"
    ):
        raise ValidationError("expected_revision=0 and request_key are required.")
    operation = f"rental_change.create.{kind}.{lease.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    if int(request.data.get("lease_revision", 0)) != lease.revision:
        raise RentalConflict("Lease revision conflict.", code="stale_revision")
    invoice = None
    original_due = deferred = None
    if kind in {
        RentalChange.Kind.PAYMENT_EXTENSION,
        RentalChange.Kind.EXTERNAL_PAYMENT,
    }:
        invoice = get_object_or_404(
            RentInvoice, id=request.data.get("invoice_id"), lease=lease
        )
    if kind == RentalChange.Kind.PAYMENT_EXTENSION:
        original_due = invoice.due_at
        requested = parse_date(request.data.get("requested_date", ""))
        if not requested:
            raise ValidationError({"requested_date": "A valid date is required."})
        deferred = cairo_instant(requested, time.max)
    if kind in {
        RentalChange.Kind.AMENDMENT,
        RentalChange.Kind.RENEWAL,
    } and not request.data.get("terms"):
        raise ValidationError({"terms": "Full proposed terms are required."})
    if (
        kind == RentalChange.Kind.RENEWAL
        and request.data["terms"].get("renewal_commission_rate_bps") != 0
    ):
        raise ValidationError(
            {"terms": "Continuous renewals require zero acquisition commission."}
        )
    evidence = _safe_evidence(lease, request.data.get("evidence_ids", []))
    with transaction.atomic():
        lease = _lease(request, lease_id, lock=True)
        item = RentalChange.objects.create(
            lease=lease,
            invoice=invoice,
            requester=request.user,
            kind=kind,
            status=(
                RentalChange.Status.REVIEW_REQUIRED
                if kind == RentalChange.Kind.EXTERNAL_PAYMENT
                else RentalChange.Status.PROPOSED
            ),
            reason=request.data.get("reason", ""),
            requested_date=request.data.get("requested_date"),
            original_due_at=original_due,
            deferred_until=deferred,
            effective_on=request.data.get("effective_on"),
            amount_minor=(request.data.get("amount") or {}).get("amount_minor"),
            method=request.data.get("method", ""),
            terms=request.data.get("terms", {}),
            previous_terms=(
                lease.terms
                if kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}
                else {}
            ),
            approvals=(
                [str(request.user.id)]
                if kind != RentalChange.Kind.EXTERNAL_PAYMENT
                else []
            ),
        )
        item.evidence.set(evidence)
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=lease.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=change_payload(item),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def payment_extensions(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.PAYMENT_EXTENSION)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def amendments(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.AMENDMENT)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def renewals(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.RENEWAL)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def terminations(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.TERMINATION)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def external_claims(request, lease_id):
    return change_collection(request, lease_id, RentalChange.Kind.EXTERNAL_PAYMENT)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def external_claim_create(request, invoice_id):
    invoice = get_object_or_404(
        RentInvoice.objects.select_related("lease"), id=invoice_id
    )
    mutable = request.data.copy()
    mutable["invoice_id"] = str(invoice.id)
    request._full_data = mutable
    return change_collection(
        request, invoice.lease.id, RentalChange.Kind.EXTERNAL_PAYMENT
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_detail(request, change_id, kind):
    return Response(change_payload(_change(request, change_id, kind)))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_respond(request, change_id, kind):
    action = request.data.get("action") or request.data.get("decision")
    if action not in {"accept", "reject", "request_changes"} or not request.data.get(
        "request_key"
    ):
        raise ValidationError(
            "accept/reject/request_changes and request_key are required."
        )
    item = _change(request, change_id, kind)
    if kind == RentalChange.Kind.EXTERNAL_PAYMENT:
        profile = getattr(request.user, "staff_profile", None)
        if not request.user.is_superuser and (
            not profile
            or not profile.is_active
            or profile.role_name
            not in {
                StaffProfile.RoleName.FINANCIAL_APPROVER,
                StaffProfile.RoleName.PSP_RECONCILIATION,
            }
        ):
            raise PermissionDenied("External payment claims require operations review.")
    operation = f"rental_change.respond.{item.id}.{request.user.id}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        item = _change(request, change_id, kind, lock=True)
        if int(request.data.get("expected_revision", 0)) != item.revision:
            raise RentalConflict("Change revision conflict.", code="stale_revision")
        if action == "reject":
            item.status = RentalChange.Status.REJECTED
        elif action == "request_changes":
            item.status = RentalChange.Status.CHANGES_REQUESTED
            item.approvals = []
        elif kind == RentalChange.Kind.EXTERNAL_PAYMENT:
            item.status = RentalChange.Status.ACCEPTED
        else:
            approvals = set(item.approvals)
            approvals.add(str(request.user.id))
            item.approvals = sorted(approvals)
            if {str(item.lease.owner.id), str(item.lease.tenant.id)}.issubset(
                approvals
            ):
                item.status = RentalChange.Status.ACCEPTED
                if kind == RentalChange.Kind.PAYMENT_EXTENSION:
                    item.invoice.deferred_until = item.deferred_until
                    item.invoice.revision += 1
                    item.invoice.save(
                        update_fields=["deferred_until", "revision", "updated_at"]
                    )
                    item.status = RentalChange.Status.APPLIED
                    item.applied_at = timezone.now()
                elif (
                    kind == RentalChange.Kind.TERMINATION
                    and item.effective_on
                    and item.effective_on <= timezone.localdate()
                ):
                    item.lease.occupancy_status = Lease.OccupancyStatus.MOVE_OUT_PENDING
                    item.lease.save(update_fields=["occupancy_status", "updated_at"])
                    item.status = RentalChange.Status.APPLIED
                    item.applied_at = timezone.now()
        item.revision += 1
        item.save()
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request.data["request_key"],
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=change_payload(item),
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def submit_change_for_signature(request, change_id, kind):
    item = _change(request, change_id, kind)
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    if request.user != item.lease.owner:
        raise PermissionDenied("Only the owner can submit the change.")
    if item.status != RentalChange.Status.ACCEPTED:
        raise RentalConflict("Both participants must accept the exact change.")
    if int(request.data.get("expected_revision", 0)) != item.revision:
        raise RentalConflict("Change revision conflict.", code="stale_revision")
    operation = f"rental_change.submit.{item.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    with transaction.atomic():
        item = _change(request, change_id, kind, lock=True)
        generated = get_rental_provider().generate_agreement(
            item.id, item.revision, item.terms
        )
        item.document_id = generated.document_id
        item.document_hash = generated.digest
        item.status = RentalChange.Status.PENDING_SIGNATURES
        item.signed_by = []
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
            resource=change_payload(item),
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_signing_session(request, change_id, kind):
    item = _change(request, change_id, kind)
    if item.status != RentalChange.Status.PENDING_SIGNATURES:
        raise RentalConflict("Change is not awaiting signatures.")
    if (
        int(request.data.get("expected_revision", 0)) != item.revision
        or str(request.data.get("document_id")) != str(item.document_id)
        or request.data.get("document_hash") != item.document_hash
    ):
        raise RentalConflict("The change document is stale.", code="document_changed")
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"rental_change.signing_session.{item.id}.{request.user.id}"
    replay = replay_operation(request.user, operation, request_key, request.data)
    if replay:
        return Response(replay[0], status=replay[1])
    hosted = get_rental_provider().create_signing_session(
        item.id, request.user.id, request_key
    )
    with transaction.atomic():
        session = ChangeSigningSession.objects.create(
            change=item,
            signer=request.user,
            request_key=request_key,
            change_revision=item.revision,
            document_id=item.document_id,
            document_hash=item.document_hash,
            provider_session_id=hosted.provider_session_id,
            hosted_url=hosted.hosted_url,
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        resource = {
            "session_id": str(session.id),
            "subject_id": str(item.id),
            "request_key": str(request_key),
            "revision": item.revision,
            "document_id": str(item.document_id),
            "document_hash": item.document_hash,
            "hosted_url": session.hosted_url,
            "expires_at": session.expires_at.isoformat(),
        }
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=item.id,
            result_revision=item.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


def complete_change_signature(provider_session_id):
    with transaction.atomic():
        session = get_object_or_404(
            ChangeSigningSession.objects.select_for_update().select_related(
                "change__lease__owner", "change__lease__tenant"
            ),
            provider_session_id=provider_session_id,
        )
        item = RentalChange.objects.select_for_update().get(pk=session.change_id)
        if session.status == "completed":
            return item
        if (
            session.change_revision != item.revision
            or session.document_id != item.document_id
            or session.document_hash != item.document_hash
        ):
            raise RentalConflict(
                "The signed change document is stale.", code="document_changed"
            )
        session.status = "completed"
        session.completed_at = timezone.now()
        session.save()
        signed = set(item.signed_by)
        signed.add(str(session.signer.id))
        item.signed_by = sorted(signed)
        if {str(item.lease.owner.id), str(item.lease.tenant.id)}.issubset(signed):
            item.status = RentalChange.Status.SIGNED
            item.revision += 1
        item.save()
        return item
