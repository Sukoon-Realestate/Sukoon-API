"""Rental phase3: payment attempt payload."""

import hashlib
import json
from django.utils import timezone
from ...models import Lease, RentInvoice, RentalTimelineEvent
from ..rental_phase2 import RentalConflict, activate_inventory, assert_owner_ready


def invoice_balance_minor(invoice):
    return max(invoice.charges_minor - invoice.credits_minor - invoice.applied_minor, 0)


def invoice_payment_allowed(user, invoice):
    from ...providers import checkout_available

    lease = invoice.lease
    from ..company.tenancy_access import can_pay

    if (
        lease.terms.get("deposit_holder") == "owner"
        and invoice.lines.filter(
            line_type="security_deposit", amount_minor__gt=0
        ).exists()
    ):
        return False
    return bool(
        user
        and user.is_active
        and user.is_verified
        and can_pay(lease, user)
        and checkout_available()
        and not lease.legacy_read_only
        and (
            lease.status
            in {
                Lease.Status.SIGNED,
                Lease.Status.ACTIVE,
                Lease.Status.TERMINATION_PENDING,
            }
            or (
                lease.status in {Lease.Status.ENDED, Lease.Status.CANCELLED}
                and getattr(getattr(lease, "final_settlement", None), "status", "")
                == "accepted"
            )
        )
        and (
            lease.status != Lease.Status.SIGNED
            or (lease.hold_expires_at and lease.hold_expires_at > timezone.now())
        )
        and invoice.status
        in {
            RentInvoice.Status.DUE,
            RentInvoice.Status.OVERDUE,
            RentInvoice.Status.PARTIALLY_PAID,
        }
        and invoice_balance_minor(invoice) > 0
        and not invoice.payment_attempts.filter(
            payment_status__in=["created", "pending", "authorized"]
        ).exists()
    )


def quote_fingerprint(invoice, request_key, amount_minor, expires_at):
    payload = {
        "invoice_id": str(invoice.id),
        "invoice_revision": invoice.revision,
        "request_key": str(request_key),
        "amount_minor": amount_minor,
        "currency": invoice.currency,
        "expires_at": expires_at.isoformat(),
        "policy_version": "rental-policy-v1",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def payment_attempt_payload(attempt, user=None):
    if attempt.invoice.purpose != "rent":
        from ..billing_projection import purchase_attempt_payload

        return purchase_attempt_payload(attempt)
    from ...providers import mock_completion_metadata
    from ..refunds import remaining_components

    invoice = attempt.invoice
    receipt = getattr(attempt, "receipt", None)
    refundable_components = remaining_components(attempt)
    refundable = sum(refundable_components.values())
    return {
        **mock_completion_metadata("payment-attempts", attempt.id, attempt.revision),
        "refundable_balance": {
            "amount_minor": refundable,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "refundable_allocations": refundable_components,
        "allowed_actions": (
            ["request_refund"]
            if user is not None
            and user.pk == attempt.payer_id
            and attempt.payment_status == "captured"
            and refundable > 0
            else []
        ),
        "blocking_reasons": (
            ["payment_outcome_unknown"]
            if attempt.payment_status in {"created", "pending", "authorized"}
            else []
        ),
        "outcome_known": attempt.payment_status
        not in {"created", "pending", "authorized"},
        "may_start_new_attempt": False,
        "revision": attempt.revision,
        "lease_id": str(invoice.lease.id),
        "payment_attempt_id": str(attempt.id),
        "invoice_id": str(invoice.id),
        "request_key": str(attempt.request_key),
        "quote_id": str(attempt.quote.id),
        "invoice_revision": attempt.invoice_revision,
        "policy_version": attempt.policy_version,
        "quote_fingerprint": attempt.quote_fingerprint,
        "payment_status": attempt.payment_status,
        "failure_code": attempt.failure_code,
        "invoice_status": invoice.status,
        "amount": {
            "amount_minor": attempt.amount_minor,
            "currency": attempt.currency,
            "exponent": attempt.exponent,
        },
        "confirmed_at": (
            attempt.confirmed_at.isoformat() if attempt.confirmed_at else None
        ),
        "receipt_id": str(receipt.id) if receipt else "",
        "payout_status": attempt.payout_status,
        "settlement_status": attempt.settlement_status,
        "updated_at": attempt.updated_at.isoformat(),
    }


def _activate_after_initial_capture(lease, attempt):
    """Record real captures even when expiry/readiness prevents activation."""
    from rest_framework.exceptions import PermissionDenied

    try:
        if (
            lease.status != Lease.Status.SIGNED
            or not lease.hold_expires_at
            or lease.hold_expires_at <= timezone.now()
        ):
            raise RentalConflict("The payment hold has expired.", code="hold_expired")
        assert_owner_ready(lease.owner, lease.property)
        activate_inventory(lease)
    except (RentalConflict, PermissionDenied) as exc:
        attempt.failure_code = "activation_review_required"
        attempt.save(update_fields=["failure_code", "updated_at"])
        from ..rental_lifecycle.cases import open_system_case

        open_system_case(
            kind="capture_after_release",
            source_key=f"late-capture:{attempt.id}",
            lease=lease,
            attempt=attempt,
            reason="Captured money could not activate the original agreement.",
            next_action="Review allocation and execute the authorized financial remedy; do not allocate over another booking.",
        )
        RentalTimelineEvent.objects.create(
            lease=lease,
            kind="activation_blocked",
            label="Captured payment needs review",
            description=str(exc.detail),
            resource_id=attempt.id,
        )
        return
    lease.status = Lease.Status.ACTIVE
    lease.activated_at = timezone.now()
    lease.revision += 1
    lease.save(update_fields=["status", "activated_at", "revision", "updated_at"])
    if lease.renter_company_id:
        from ...models import CompanyBudgetReservation

        item = lease.company_tenancy
        item.lease = lease
        booking = item.preparation.booking
        booking.status = "active"
        booking.revision += 1
        booking.save()
        CompanyBudgetReservation.objects.filter(item=booking, status="reserved").update(
            status="committed"
        )
        from ..company.tenancy_access import notify

        notify(item)
    RentalTimelineEvent.objects.create(
        lease=lease,
        kind="activated",
        label="Agreement activated after payment",
        resource_id=attempt.id,
    )
