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
from .providers import (
    mock_completion_metadata,
    get_rental_provider,
    require_rental_provider,
)
from .renderers import FeatureJsonRenderer
from .services.cycle_permissions import MAINTENANCE_TRANSITIONS, cycle_actions
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
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_rental_provider(request.user)
    queryset = Lease.objects.select_related("owner", "tenant")
    if lock:
        queryset = queryset.select_for_update(of=("self",))
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


def maintenance_payload(item, user=None):
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
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
        queryset = queryset.select_for_update(of=("self",))
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
            maintenance_payload(x, request.user)
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
            resource=maintenance_payload(item, request.user),
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_detail(request, request_id):
    return Response(
        maintenance_payload(_maintenance(request, request_id), request.user)
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def maintenance_action(request, request_id):
    action = request.data.get("action") or request.data.get("decision")
    if action not in MAINTENANCE_ACTIONS or not request.data.get("request_key"):
        raise ValidationError({"action": "Unsupported action or missing request key."})
    item = _maintenance(request, request_id)
    operation = f"maintenance.action.{item.id}.{action}"
    replay = replay_operation(
        request.user, operation, request.data["request_key"], request.data
    )
    if replay:
        return Response(replay[0], status=replay[1])
    transitions = MAINTENANCE_TRANSITIONS
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
            resource=maintenance_payload(item, request.user),
        )
    return Response(output)


def change_payload(item, user=None):
    return {
        "allowed_actions": cycle_actions(user, item),
        "blocking_reasons": [],
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
    if lock:
        lease = Lease.objects.select_for_update().get(pk=item.lease_id)
        item = queryset.select_for_update(of=("self",)).get(pk=item.pk)
        item.lease = lease
    return item


def change_collection(request, lease_id, kind):
    lease = _lease(request, lease_id)
    if request.method == "GET":
        results = [
            change_payload(x, request.user)
            for x in lease.rental_changes.filter(kind=kind)
        ]
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
    if kind == RentalChange.Kind.TERMINATION:
        effective = parse_date(request.data.get("effective_on", ""))
        if (
            not effective
            or effective < max(lease.start_date, timezone.localdate())
            or effective > lease.end_date
        ):
            raise ValidationError(
                {
                    "effective_on": "Choose a current or future date within this lease term."
                }
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
            resource=change_payload(item, request.user),
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
    return Response(change_payload(_change(request, change_id, kind), request.user))


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
        if item.status not in {
            RentalChange.Status.PROPOSED,
            RentalChange.Status.CHANGES_REQUESTED,
            RentalChange.Status.REVIEW_REQUIRED,
        }:
            raise RentalConflict("This change is no longer awaiting a response.")
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
                elif kind == RentalChange.Kind.TERMINATION:
                    from .services.legal_lifecycle import accept_termination

                    accept_termination(item)
                    if item.effective_on <= timezone.localdate():
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
            resource=change_payload(item, request.user),
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
    operation = f"rental_change.submit.{item.id}"
    with transaction.atomic():
        item = _change(request, change_id, kind, lock=True)
        if request.user != item.lease.owner:
            raise PermissionDenied("Only the owner can submit the change.")
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if item.status != RentalChange.Status.ACCEPTED:
            raise RentalConflict("Both participants must accept the exact change.")
        if int(request.data.get("expected_revision", 0)) != item.revision:
            raise RentalConflict("Change revision conflict.", code="stale_revision")
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
            resource=change_payload(item, request.user),
        )
    return Response(output)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@renderer_classes([FeatureJsonRenderer])
def change_signing_session(request, change_id, kind):
    item = _change(request, change_id, kind)
    request_key = request.data.get("request_key")
    if not request_key:
        raise ValidationError({"request_key": "Required."})
    operation = f"rental_change.signing_session.{item.id}.{request.user.id}"
    with transaction.atomic():
        item = _change(request, change_id, kind, lock=True)
        replay = replay_operation(request.user, operation, request_key, request.data)
        if replay:
            return Response(replay[0], status=replay[1])
        if item.status != RentalChange.Status.PENDING_SIGNATURES:
            raise RentalConflict("Change is not awaiting signatures.")
        if str(request.user.id) in item.signed_by:
            raise RentalConflict("You already signed this change document.")
        if (
            int(request.data.get("expected_revision", 0)) != item.revision
            or str(request.data.get("document_id")) != str(item.document_id)
            or request.data.get("document_hash") != item.document_hash
        ):
            raise RentalConflict(
                "The change document is stale.", code="document_changed"
            )
        hosted = get_rental_provider().create_signing_session(
            item.id, request.user.id, request_key
        )
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
            **mock_completion_metadata(
                "change-signing-sessions", session.id, item.revision
            ),
            "expires_at": session.expires_at.isoformat(),
        }
        output = remember_mutation(
            user=request.user,
            operation=operation,
            request_key=request_key,
            payload=request.data,
            request_subject_id=item.id,
            result_subject_id=session.id,
            result_revision=item.revision,
            resource=resource,
            response_status=201,
        )
    return Response(output, status=status.HTTP_201_CREATED)


def complete_change_signature(provider_session_id):
    with transaction.atomic():
        session = get_object_or_404(
            ChangeSigningSession, provider_session_id=provider_session_id
        )
        item = RentalChange.objects.select_for_update().get(pk=session.change_id)
        session = ChangeSigningSession.objects.select_for_update().get(pk=session.pk)
        if session.status == "completed":
            return item
        if (
            item.status != RentalChange.Status.PENDING_SIGNATURES
            or session.expires_at <= timezone.now()
            or session.change_revision != item.revision
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
