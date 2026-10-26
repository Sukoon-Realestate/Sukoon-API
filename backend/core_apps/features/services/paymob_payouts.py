"""Dispatch once after commit; inquire and account against that exact instruction."""

import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.db import connection, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import User
from core_apps.users.services.totp import require_sensitive_access
from ..models import OwnerPaymentProfile, PaymobPayout, PayoutAuditEvent, RentalPayout
from . import paymob_payout_client as client, paymob_payout_targets as targets
from .rental_phase2 import RentalConflict, fingerprint
from .rental_lifecycle.locks import lock_financial_lease
from .rental_lifecycle.provider_instructions import (
    validate_payout_instruction,
    hold_payout_for_review,
)
from .financial_authority import require_financial_actor, authorization_context


def stage(payout, recipient, *, actor=None, retry_of=None):
    if not connection.in_atomic_block:
        raise RuntimeError("Stage the payout inside its authorization transaction.")
    actor = actor or User.objects.get(pk=payout.batch.approved_by_id)
    item, created = PaymobPayout.objects.get_or_create(
        payout=payout,
        current=True,
        defaults={
            "retry_of": retry_of,
            "account_digest": client.account_digest(),
            "recipient_ciphertext": targets.seal(recipient),
            "recipient_digest": fingerprint(recipient),
            "amount_minor": payout.amount_minor,
            "currency": payout.currency,
            "authorization_context": authorization_context(actor),
        },
    )
    if not created and (
        item.recipient_digest != fingerprint(recipient)
        or item.amount_minor != payout.amount_minor
        or item.currency != payout.currency
    ):
        raise RentalConflict(
            "The original payout details changed.", code="idempotency_conflict"
        )
    return item


def _locked(identity, *, actor=False):
    candidate = PaymobPayout.objects.select_related(
        "payout__lease", "payout__batch"
    ).get(pk=identity)
    current = None
    if actor:
        current = User.objects.select_for_update().get(
            id=candidate.authorization_context["actor_id"]
        )
        StaffProfile.objects.select_for_update().filter(user=current).first()
    lock_financial_lease(candidate.payout.lease)
    payout = (
        RentalPayout.objects.select_for_update()
        .select_related("lease", "batch")
        .get(pk=candidate.payout_id)
    )
    item = PaymobPayout.objects.select_for_update().get(pk=identity)
    return item, payout, current


def _hold(item, payout, code):
    item.failure_code = code
    item.save(update_fields=["status", "failure_code", "next_query_at", "updated_at"])
    if payout.status != "held" or payout.failure_code != code:
        hold_payout_for_review(
            payout,
            RentalConflict(
                "Review the original payout before any further instruction.", code=code
            ),
        )


@transaction.atomic
def claim(identity):
    item, payout, actor = _locked(identity, actor=True)
    if item.status != "queued" or not item.current:
        return None
    try:
        require_financial_actor(
            actor, {StaffProfile.RoleName.PAYOUT_OPERATOR}, "payout.dispatch", lock=True
        )
        require_sensitive_access(actor)
        if authorization_context(actor) != item.authorization_context:
            raise PermissionDenied()
        validate_payout_instruction(payout)
        profile = OwnerPaymentProfile.objects.get(owner=payout.owner)
        recipient = targets.for_profile(profile)
        if (
            fingerprint(recipient) != item.recipient_digest
            or item.account_digest != client.account_digest()
        ):
            raise RentalConflict(
                "The provisioned beneficiary changed.", code="beneficiary_changed"
            )
        if (
            payout.amount_minor != item.amount_minor
            or payout.currency != item.currency
            or item.currency != "EGP"
            or payout.exponent != 2
        ):
            raise RentalConflict("The approved payout changed.", code="payout_changed")
    except (PermissionDenied, RentalConflict) as error:
        item.status = "held"
        _hold(
            item,
            payout,
            (
                "authorization_changed"
                if isinstance(error, PermissionDenied)
                else str(error.get_codes())
            ),
        )
        return None
    item.status, item.submitted_at = "submitting", timezone.now()
    item.next_query_at = timezone.now() + timedelta(minutes=2)
    item.save(update_fields=["status", "submitted_at", "next_query_at", "updated_at"])
    payout.status = "processing"
    payout.revision += 1
    payout.save(update_fields=["status", "revision", "updated_at"])
    payout.payables.update(payout_status="processing", updated_at=timezone.now())
    PayoutAuditEvent.objects.create(
        payout=payout,
        actor=actor,
        action="submitted",
        metadata={"instruction_id": str(item.id)},
    )
    from .payout_notifications import record

    record(payout, "submitted")
    return item


def _proof(item, recipient, proof, *, direct=False):
    if not isinstance(proof, dict):
        raise client.PayoutUnavailable()
    if ("currency" in proof and proof["currency"] != item.currency) or (
        "customer_bears_fees" in proof and proof["customer_bears_fees"] is not False
    ):
        raise client.PayoutUnavailable()
    identity = proof.get("transaction_id")
    if not isinstance(identity, str) or not re.fullmatch(
        r"[A-Za-z0-9_-]{1,80}", identity
    ):
        raise client.PayoutUnavailable()
    if item.provider_transaction_id and identity != item.provider_transaction_id:
        raise client.PayoutUnavailable()
    reference = proof.get("client_transaction_reference") or proof.get("reference")
    if (not direct and reference != str(item.reference)) or (
        reference and reference != str(item.reference)
    ):
        raise client.PayoutUnavailable()
    try:
        amount = Decimal(str(proof.get("amount")))
        if not amount.is_finite() or amount * 100 != item.amount_minor:
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise client.PayoutUnavailable() from None
    keys = (
        {"issuer", "msisdn"}
        if recipient["issuer"] in client.WALLETS
        else {
            "issuer",
            "bank_code",
            "bank_card_number",
            "full_name",
            "bank_transaction_type",
        }
    )
    if any(proof.get(key) != recipient[key] for key in keys):
        raise client.PayoutUnavailable()
    state = proof.get("disbursement_status")
    code = str(proof.get("status_code", ""))
    if state in {"success", "successful"} and code == "200":
        return identity, "confirmed"
    if state == "failed" and code and code != "200":
        return identity, "failed"
    return identity, "processing"


@transaction.atomic
def record_result(identity, recipient, proof, *, direct=False):
    item, payout, _ = _locked(identity)
    if item.status == "confirmed":
        return item
    if item.status not in {"submitting", "unknown", "processing"}:
        return item
    provider_id, state = _proof(item, recipient, proof, direct=direct)
    item.provider_transaction_id, item.status = provider_id, state
    item.failure_code = "provider_failed" if state == "failed" else ""
    item.confirmed_at = timezone.now() if state == "confirmed" else None
    item.next_query_at = (
        timezone.now() + timedelta(minutes=2) if state == "processing" else None
    )
    item.save()
    if state == "failed":
        _hold(item, payout, "provider_failed")
    return item


@transaction.atomic
def mark_unknown(identity):
    item, payout, _ = _locked(identity)
    if item.status not in {"submitting", "unknown", "processing"}:
        return
    item.status = "unknown"
    item.next_query_at = timezone.now() + timedelta(minutes=2)
    _hold(item, payout, "outcome_unknown")


def process(item, *, allow_submit=True):
    if connection.in_atomic_block:
        raise RuntimeError("Payout HTTP must run after the transaction commits.")
    item = PaymobPayout.objects.get(pk=item.pk)
    if not item.current:
        return item.payout
    if item.status == "confirmed":
        return finish_accounting(item)
    if item.status in {"held", "failed"} or (
        item.status == "queued" and not allow_submit
    ):
        return item.payout
    if item.account_digest != client.account_digest():
        raise client.PayoutUnavailable()
    recipient = targets.unseal(item)
    access_token = client.token()
    if item.status == "queued":
        claimed = claim(item.pk)
        if claimed is None:
            return RentalPayout.objects.get(pk=item.payout_id)
        item = claimed
        try:
            proof = client.submit(item, recipient, access_token)
            item = record_result(item.pk, recipient, proof, direct=True)
        except Exception:
            # Even a transport error cannot prove the provider did not submit.
            mark_unknown(item.pk)
            raise client.PayoutUnavailable() from None
    else:
        try:
            response = client.inquire(item, recipient, access_token)
            results = response.get("results")
            if (
                not isinstance(results, list)
                or len(results) != 1
                or response.get("next")
                or response.get("count") != 1
            ):
                raise client.PayoutUnavailable()
            item = record_result(item.pk, recipient, results[0])
        except Exception:
            mark_unknown(item.pk)
            raise client.PayoutUnavailable() from None
    return (
        finish_accounting(item)
        if item.status == "confirmed"
        else RentalPayout.objects.get(pk=item.payout_id)
    )


@transaction.atomic
def finish_accounting(candidate):
    from .rental_phase3 import post_ledger_transaction

    item, payout, _ = _locked(candidate.pk)
    if payout.status == "paid":
        return payout
    if item.status != "confirmed" or not item.provider_transaction_id:
        raise client.PayoutUnavailable()
    # Confirmation records the already executed transfer even when a role,
    # factor, beneficiary, or funding status has changed since dispatch.
    if payout.amount_minor != item.amount_minor or payout.currency != item.currency:
        raise RentalConflict(
            "Reconcile the original confirmed payout amount.", code="payout_changed"
        )
    payout.status, payout.provider_payout_id = "paid", item.provider_transaction_id
    payout.failure_code = payout.hold_reason = ""
    payout.revision += 1
    payout.save()
    payout.payables.update(payout_status="succeeded", updated_at=timezone.now())
    post_ledger_transaction(
        reference=f"payout:{payout.id}",
        kind="owner_payout",
        lease=payout.lease,
        entries=[
            ("owner_liability", "debit", item.amount_minor),
            ("platform_cash", "credit", item.amount_minor),
        ],
    )
    PayoutAuditEvent.objects.create(
        payout=payout,
        actor=payout.batch.approved_by,
        action="paid",
        metadata={
            "instruction_id": str(item.id),
            "provider_payout_id": item.provider_transaction_id,
        },
    )
    from .payout_notifications import record

    record(payout, "paid")
    return payout


def process_pending(*, limit=100):
    from django.db.models import Q
    from rest_framework.exceptions import APIException

    query = (
        PaymobPayout.objects.filter(current=True)
        .exclude(payout__status="paid")
        .filter(
            status__in=["queued", "submitting", "unknown", "processing", "confirmed"]
        )
        .filter(Q(next_query_at__isnull=True) | Q(next_query_at__lte=timezone.now()))
    )
    counts = {"paid": 0, "pending": 0, "unavailable": 0}
    for item in query.order_by("updated_at", "pk")[: max(1, min(limit, 1000))]:
        try:
            payout = process(item)
            counts["paid" if payout.status == "paid" else "pending"] += 1
        except APIException:
            counts["unavailable"] += 1
    return counts
