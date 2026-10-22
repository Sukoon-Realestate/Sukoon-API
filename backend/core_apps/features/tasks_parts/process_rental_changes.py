"""Tasks: process rental changes."""

from celery import shared_task
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from ..models import (
    RentalEvidence,
    RentalPayout,
    RentalChange,
    ChangeSigningSession,
    Lease,
)
from ..providers import get_rental_provider
from ..services.rental_phase2 import RentalConflict


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def scan_rental_evidence(self):
    from uuid import uuid4
    from django.db.models import Q
    from ..services import evidence_storage

    if not evidence_storage.available():
        return {"safe": 0, "unsafe": 0, "unavailable": 1}
    safe = unsafe = failed = 0
    now = timezone.now()
    ids = list(RentalEvidence.objects.filter(
        malware_status="pending", deleted_at__isnull=True
    ).filter(Q(scan_until__isnull=True) | Q(scan_until__lte=now)).order_by("created_at").values_list("pk", flat=True)[:100])
    for identity in ids:
        token = uuid4()
        with transaction.atomic():
            item = RentalEvidence.objects.select_for_update().get(pk=identity)
            if item.deleted_at or item.malware_status != "pending" or (item.scan_until and item.scan_until > timezone.now()):
                continue
            item.scan_token, item.scan_until = token, timezone.now() + timedelta(minutes=5)
            item.save(update_fields=["scan_token", "scan_until"])
        import hashlib
        original = bytes(item.private_content or b"")
        if len(original) != item.size_bytes or hashlib.sha256(original).hexdigest() != item.sha256:
            # Permanent corruption needs operator review. Scheduling it every
            # minute cannot repair it and must never reinterpret it as safe.
            RentalEvidence.objects.filter(pk=identity, scan_token=token, deleted_at__isnull=True).update(
                malware_status="failed", scan_token=None, scan_until=None, scan_error_code="integrity_mismatch"
            )
            failed += 1
            continue
        try:
            provider, storage_key = evidence_storage.persist(item)
            result = evidence_storage.scan(bytes(item.private_content or b""))
            if result.sha256 != item.sha256:
                raise ValueError("Evidence changed during inspection")
        except Exception:
            # Retain original bytes and a durable retry time. No error strings or
            # document content enter logs, and an outage never produces SAFE.
            RentalEvidence.objects.filter(pk=identity, scan_token=token, deleted_at__isnull=True).update(
                scan_token=None, scan_until=timezone.now() + timedelta(minutes=1), scan_error_code="inspection_unavailable"
            )
            failed += 1
            continue
        with transaction.atomic():
            current = RentalEvidence.objects.select_for_update().get(pk=identity)
            if current.scan_token != token or current.deleted_at or current.malware_status != "pending" or current.sha256 != result.sha256:
                continue
            current.storage_provider, current.storage_key = provider, storage_key
            current.malware_status = "safe" if result.safe else "unsafe"
            current.scan_engine, current.scan_sha256 = result.engine, result.sha256
            current.scan_token = current.scan_until = None
            current.scan_error_code = ""
            current.revision += 1
            # Keep originals until a separately reviewed retention/backfill run;
            # writing remote data never silently destroys the durable DB copy.
            current.save()
            safe += int(result.safe)
            unsafe += int(not result.safe)
    return {"safe": safe, "unsafe": unsafe, "failed": failed}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def reconcile_approved_payouts(self):
    from ..services.rental_phase3 import post_ledger_transaction

    paid = 0
    for candidate in RentalPayout.objects.filter(status=RentalPayout.Status.CREATED)[
        :100
    ]:
        with transaction.atomic():
            from ..services.rental_lifecycle.locks import lock_financial_lease

            lock_financial_lease(Lease.objects.get(pk=candidate.lease_id))
            payout = RentalPayout.objects.select_for_update().get(pk=candidate.pk)
            if payout.status != RentalPayout.Status.CREATED:
                continue
            from ..services.rental_lifecycle.provider_instructions import (
                execute_local_instruction,
                hold_payout_for_review,
            )

            try:
                payout.provider_payout_id = execute_local_instruction(
                    kind="payout",
                    subject=payout,
                    request_key=payout.batch.request_key,
                    payload={
                        "amount_minor": payout.amount_minor,
                        "currency": payout.currency,
                        "beneficiary": payout.masked_beneficiary,
                    },
                )
            except RentalConflict as error:
                hold_payout_for_review(payout, error)
                continue
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
            paid += 1
    return {"paid": paid}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_rental_changes(self):
    from datetime import date
    from ..services.rental_phase2 import reserve_inventory_days
    from ..services.rental_phase3 import generate_billing_schedule

    now = timezone.now()
    expired_sessions = ChangeSigningSession.objects.filter(
        change__lease__renter_company__isnull=True,
        status="pending",
        expires_at__lte=now,
    ).update(status="expired", updated_at=now)
    applied = 0
    for candidate in RentalChange.objects.filter(
        lease__renter_company__isnull=True,
        status__in=[RentalChange.Status.ACCEPTED, RentalChange.Status.SIGNED],
        effective_on__lte=timezone.localdate(),
    ).select_related("lease")[:100]:
        with transaction.atomic():
            from core_apps.properties.models import Property

            Property.objects.select_for_update().get(pk=candidate.lease.property_id)
            lease = Lease.objects.select_for_update().get(pk=candidate.lease_id)
            change = (
                RentalChange.objects.select_for_update(of=("self",))
                .select_related("lease__property")
                .get(pk=candidate.pk)
            )
            if change.status not in {
                RentalChange.Status.ACCEPTED,
                RentalChange.Status.SIGNED,
            }:
                continue
            change.lease = lease
            if change.kind in {RentalChange.Kind.AMENDMENT, RentalChange.Kind.RENEWAL}:
                from rest_framework.exceptions import ValidationError
                from ..services.change_terms import validate_changed_terms
                from ..services.rental_lifecycle.cases import open_system_case

                if change.status != RentalChange.Status.SIGNED:
                    continue
                try:
                    validate_changed_terms(change.terms)
                    if not change.document_id or not change.document_hash:
                        raise ValidationError(
                            "The signed document identity is missing."
                        )
                except ValidationError:
                    # Preserve signed consent and all existing obligations. A bad
                    # historical row must not abort every other due change.
                    open_system_case(
                        kind="agreement_terms_review",
                        source_key=f"change-terms:{change.id}:{change.revision}",
                        lease=lease,
                        reason="The signed change has unsupported terms or missing document provenance.",
                        next_action="Review the original signed change with both parties. Do not rewrite signed terms or infer new consent.",
                    )
                    continue
            if change.kind == RentalChange.Kind.AMENDMENT:
                if change.status != RentalChange.Status.SIGNED:
                    continue
                lease.terms = change.terms
                rent = change.terms.get("monthly_rent", {})
                if isinstance(rent.get("amount_minor"), int):
                    lease.rent_amount_minor = rent["amount_minor"]
                lease.revision += 1
                lease.save()
            elif change.kind == RentalChange.Kind.RENEWAL:
                if change.status != RentalChange.Status.SIGNED:
                    continue
                from ..services.planning_transitions import require_no_departure

                try:
                    require_no_departure(lease, activating=True)
                except RentalConflict:
                    # Legacy or concurrently imported departures require explicit
                    # resolution before a signed renewal can allocate inventory.
                    continue
                if change.terms.get("renewal_commission_rate_bps") != 0:
                    raise ValueError("Renewals must have zero acquisition commission.")
                starts_on = date.fromisoformat(change.terms["starts_on"])
                ends_on = date.fromisoformat(change.terms["ends_on_exclusive"])
                if (
                    starts_on != lease.end_date
                    or starts_on > timezone.localdate()
                    or ends_on <= timezone.localdate()
                ):
                    continue
                renewal = Lease.objects.create(
                    property=lease.property,
                    owner=lease.owner,
                    tenant=lease.tenant,
                    template_id=change.terms["template_id"],
                    template_version=change.terms["template_version"],
                    start_date=starts_on,
                    end_date=ends_on,
                    rent_amount_minor=change.terms["monthly_rent"]["amount_minor"],
                    status=Lease.Status.ACTIVE,
                    occupancy_status=lease.occupancy_status,
                    legacy_read_only=False,
                    offer_id=lease.offer_id,
                    offer_snapshot=lease.offer_snapshot,
                    tenancy_root_id=lease.tenancy_root_id,
                    terms=change.terms,
                    policy_version=change.terms["policy_version"],
                    document_id=change.document_id,
                    document_hash=change.document_hash,
                    activated_at=now,
                )
                change.result_lease = renewal
                change.save(update_fields=["result_lease", "updated_at"])
                reserve_inventory_days(
                    renewal, starts_on, ends_on, now + timedelta(minutes=30)
                )
                from ..services.rental_phase2 import activate_inventory

                activate_inventory(renewal)
                generate_billing_schedule(renewal)
                change.result_lease = renewal
            elif change.kind == RentalChange.Kind.TERMINATION:
                from ..services.legal_lifecycle import end_lease_if_due

                end_lease_if_due(lease)
            else:
                continue
            change.status = RentalChange.Status.APPLIED
            change.applied_at = now
            change.revision += 1
            change.save()
            applied += 1
    return {"expired_signing_sessions": expired_sessions, "applied": applied}
