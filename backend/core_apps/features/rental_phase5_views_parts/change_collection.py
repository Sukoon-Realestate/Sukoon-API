"""Rental phase5 views: change collection."""

from datetime import time
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from ..models import RentalChange, RentInvoice
from ..services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from ..services.rental_phase3 import cairo_instant
from .maintenance_payload import _lease, _safe_evidence
from .maintenance_action import change_payload


def change_collection(request, lease_id, kind):
    if request.method == "POST" and kind == RentalChange.Kind.EXTERNAL_PAYMENT:
        from ..services.platform_rent_payments import reject_external_claim

        invoice = get_object_or_404(
            RentInvoice,
            id=request.data.get("invoice_id"),
            lease__id=lease_id,
            purpose="rent",
        )
        return reject_external_claim(request, invoice)
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

    def optional_date(field):
        value = request.data.get(field)
        if value in (None, ""):
            return None
        try:
            parsed = parse_date(value) if isinstance(value, str) else None
        except ValueError:
            parsed = None
        if parsed is None:
            raise ValidationError({field: "Use a valid YYYY-MM-DD date."})
        return parsed

    requested_date = optional_date("requested_date")
    effective_date = optional_date("effective_on")
    terms = request.data.get("terms", {})
    if not isinstance(terms, dict):
        raise ValidationError({"terms": "Supply an object."})
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
    if kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
        from ..services.change_terms import validate_changed_terms

        validate_changed_terms(terms)
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
        replay = replay_operation(
            request.user, operation, request.data["request_key"], request.data
        )
        if replay:
            return Response(replay[0], status=replay[1])
        if int(request.data.get("lease_revision", 0)) != lease.revision:
            raise RentalConflict("Lease revision conflict.", code="stale_revision")
        if kind == RentalChange.Kind.RENEWAL:
            from ..services.planning_transitions import require_no_departure

            require_no_departure(lease)
            if (
                lease.rental_changes.filter(kind=kind)
                .exclude(status=RentalChange.Status.REJECTED)
                .exists()
            ):
                raise RentalConflict(
                    "Resolve the existing renewal before creating another."
                )
            terms = request.data["terms"]
            try:
                starts = parse_date(terms.get("starts_on", ""))
                ends = parse_date(terms.get("ends_on_exclusive", ""))
                handover = parse_date(terms.get("handover_on", ""))
            except (TypeError, ValueError):
                raise ValidationError({"terms": "Use valid civil dates."}) from None
            if not starts or starts != lease.end_date or not ends or ends <= starts:
                raise ValidationError(
                    {
                        "terms": "A continuous renewal starts at the current end date and ends later."
                    }
                )
            if effective_date is not None and effective_date != starts:
                raise ValidationError(
                    {
                        "effective_on": "A renewal takes effect on its reviewed start date."
                    }
                )
            from ..services.commands import money_minor

            if money_minor(terms.get("monthly_rent")) <= 0:
                raise ValidationError({"terms": "Renewal rent must be positive."})
            if handover is None or not starts <= handover < ends:
                raise ValidationError(
                    {"terms": "The handover date must be inside the renewal term."}
                )
            if any(
                not isinstance(terms.get(field), str) or not terms[field].strip()
                for field in ("template_id", "template_version")
            ):
                raise ValidationError(
                    {"terms": "A reviewed agreement template and version are required."}
                )
            effective_date = starts
        from ..services.platform_rent_payments import reviewed_terms

        reviewed = request.data.get("terms", {})
        if kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
            reviewed = reviewed_terms(reviewed)
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
            requested_date=requested_date,
            original_due_at=original_due,
            deferred_until=deferred,
            effective_on=effective_date,
            amount_minor=(request.data.get("amount") or {}).get("amount_minor"),
            method=request.data.get("method", ""),
            terms=reviewed,
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
        from ..services.planning_notifications import record_event

        record_event(item, request.user, operation)
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
