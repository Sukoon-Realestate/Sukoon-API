from celery import shared_task
from datetime import timedelta
from django.db import models, transaction
from django.utils import timezone

from .models import (
    OwnerOnboardingSession,
    RentalInventoryDayLock,
    SigningSession,
    TenancyInvitation,
    BillingPeriod,
    PaymentAttempt,
    ProviderWebhookEvent,
    RentInvoice,
    RentalEvidence,
    RentalPayout,
    RentalChange,
    ChangeSigningSession,
    Lease,
    RefundRequest,
    RentalDocument,
    PrivateAccessRevocation,
)
from .providers import get_rental_provider
from .services.rental_phase3 import issue_invoice, process_provider_event


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def expire_rental_sources_and_holds(self):
    now = timezone.now()
    with transaction.atomic():
        invitations = TenancyInvitation.objects.select_for_update().filter(
            status__in=[
                TenancyInvitation.Status.PENDING,
                TenancyInvitation.Status.ACCEPTED,
            ],
            lease__isnull=True,
            expires_at__lte=now,
        )
        expired_invitations = invitations.update(
            status=TenancyInvitation.Status.EXPIRED,
            revision=models.F("revision") + 1,
            updated_at=now,
        )
        expired_holds = RentalInventoryDayLock.objects.filter(
            kind=RentalInventoryDayLock.Kind.HOLD,
            expires_at__lte=now,
        ).delete()[0]
    return {
        "expired_invitations": expired_invitations,
        "expired_holds": expired_holds,
    }


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def reconcile_rental_provider_sessions(self):
    now = timezone.now()
    onboarding = OwnerOnboardingSession.objects.filter(
        status="created", expires_at__lte=now
    ).update(status="expired", updated_at=now)
    signing = SigningSession.objects.filter(
        status="pending", expires_at__lte=now
    ).update(status="expired", updated_at=now)
    return {"expired_onboarding": onboarding, "expired_signing": signing}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def run_rental_billing_cycle(self):
    now = timezone.now()
    issued = 0
    with transaction.atomic():
        for period in BillingPeriod.objects.select_for_update().filter(
            status=BillingPeriod.Status.SCHEDULED, issue_at__lte=now
        ):
            issue_invoice(period)
            issued += 1
        overdue = (
            RentInvoice.objects.filter(
                status=RentInvoice.Status.DUE,
                due_at__lt=now,
            )
            .filter(
                models.Q(deferred_until__isnull=True) | models.Q(deferred_until__lt=now)
            )
            .update(
                status=RentInvoice.Status.OVERDUE,
                revision=models.F("revision") + 1,
                updated_at=now,
            )
        )
    return {"issued": issued, "overdue": overdue}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def reconcile_ambiguous_rental_payments(self):
    processed = 0
    for event in ProviderWebhookEvent.objects.filter(processed=False).order_by(
        "sequence", "created_at"
    )[:100]:
        process_provider_event(event)
        processed += 1
    expired = PaymentAttempt.objects.filter(
        payment_status__in=[
            PaymentAttempt.Status.CREATED,
            PaymentAttempt.Status.PENDING,
        ],
        checkout_session__expires_at__lte=timezone.now(),
    ).update(
        payment_status=PaymentAttempt.Status.EXPIRED,
        revision=models.F("revision") + 1,
        updated_at=timezone.now(),
    )
    return {"events_processed": processed, "attempts_expired": expired}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def scan_rental_evidence(self):
    safe = unsafe = 0
    for item in RentalEvidence.objects.filter(
        malware_status=RentalEvidence.MalwareStatus.PENDING
    )[:100]:
        with transaction.atomic():
            item = RentalEvidence.objects.select_for_update().get(pk=item.pk)
            if item.malware_status != RentalEvidence.MalwareStatus.PENDING:
                continue
            is_safe = get_rental_provider().scan_evidence(
                bytes(item.private_content or b"")
            )
            item.malware_status = (
                RentalEvidence.MalwareStatus.SAFE
                if is_safe
                else RentalEvidence.MalwareStatus.UNSAFE
            )
            item.revision += 1
            item.save(update_fields=["malware_status", "revision", "updated_at"])
            safe += int(is_safe)
            unsafe += int(not is_safe)
    return {"safe": safe, "unsafe": unsafe}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def reconcile_approved_payouts(self):
    from .services.rental_phase3 import post_ledger_transaction

    paid = 0
    for candidate in RentalPayout.objects.filter(status=RentalPayout.Status.CREATED)[
        :100
    ]:
        with transaction.atomic():
            payout = RentalPayout.objects.select_for_update().get(pk=candidate.pk)
            if payout.status != RentalPayout.Status.CREATED:
                continue
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
    from .services.rental_phase2 import reserve_inventory_days
    from .services.rental_phase3 import generate_billing_schedule

    now = timezone.now()
    expired_sessions = ChangeSigningSession.objects.filter(
        status="pending", expires_at__lte=now
    ).update(status="expired", updated_at=now)
    applied = 0
    for candidate in RentalChange.objects.filter(
        status__in=[RentalChange.Status.ACCEPTED, RentalChange.Status.SIGNED],
        effective_on__lte=timezone.localdate(),
    ).select_related("lease")[:100]:
        with transaction.atomic():
            change = (
                RentalChange.objects.select_for_update()
                .select_related("lease__property")
                .get(pk=candidate.pk)
            )
            if change.status not in {
                RentalChange.Status.ACCEPTED,
                RentalChange.Status.SIGNED,
            }:
                continue
            lease = Lease.objects.select_for_update().get(pk=change.lease_id)
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
                if change.terms.get("renewal_commission_rate_bps") != 0:
                    raise ValueError("Renewals must have zero acquisition commission.")
                starts_on = date.fromisoformat(change.terms["starts_on"])
                ends_on = date.fromisoformat(change.terms["ends_on_exclusive"])
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
                    occupancy_status=Lease.OccupancyStatus.NOT_STARTED,
                    legacy_read_only=False,
                    offer_id=lease.offer_id,
                    offer_snapshot=lease.offer_snapshot,
                    tenancy_root_id=lease.tenancy_root_id,
                    terms=change.terms,
                    activated_at=now,
                )
                reserve_inventory_days(
                    renewal, starts_on, ends_on, now + timedelta(minutes=30)
                )
                from .services.rental_phase2 import activate_inventory

                activate_inventory(renewal)
                generate_billing_schedule(renewal)
                change.result_lease = renewal
            elif change.kind == RentalChange.Kind.TERMINATION:
                lease.occupancy_status = Lease.OccupancyStatus.MOVE_OUT_PENDING
                lease.save(update_fields=["occupancy_status", "updated_at"])
            else:
                continue
            change.status = RentalChange.Status.APPLIED
            change.applied_at = now
            change.revision += 1
            change.save()
            applied += 1
    return {"expired_signing_sessions": expired_sessions, "applied": applied}


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
    acks_late=True,
)
def process_rental_closure(self):
    import hashlib
    import json
    from .services.rental_phase6 import evaluate_financial_closure, execute_refund

    refunded = generated = evaluated = revoked = 0
    for refund in RefundRequest.objects.filter(status=RefundRequest.Status.APPROVED)[
        :100
    ]:
        execute_refund(refund)
        refunded += 1
    for candidate in RentalDocument.objects.filter(
        status=RentalDocument.Status.QUEUED
    ).select_related("lease")[:100]:
        with transaction.atomic():
            document = RentalDocument.objects.select_for_update().get(pk=candidate.pk)
            if document.status != RentalDocument.Status.QUEUED:
                continue
            ledger = [
                {
                    "reference": tx.reference,
                    "kind": tx.kind,
                    "entries": list(
                        tx.entries.values(
                            "account",
                            "direction",
                            "amount_minor",
                            "currency",
                            "exponent",
                        )
                    ),
                }
                for tx in document.lease.ledger_transactions.prefetch_related(
                    "entries"
                ).order_by("occurred_at", "pkid")
                if (
                    not document.starts_on
                    or tx.occurred_at.date() >= document.starts_on
                )
                and (
                    not document.ends_on_exclusive
                    or tx.occurred_at.date() < document.ends_on_exclusive
                )
            ]
            content = json.dumps(
                {"lease_id": str(document.lease.id), "ledger": ledger}, sort_keys=True
            ).encode()
            document.private_content = content
            document.sha256 = hashlib.sha256(content).hexdigest()
            document.storage_key = (
                f"rental-documents/{document.lease.id}/{document.id}/{document.sha256}"
            )
            document.status = RentalDocument.Status.READY
            document.revision += 1
            document.save()
            generated += 1
    for lease in Lease.objects.all().iterator():
        evaluate_financial_closure(lease)
        evaluated += 1
        for participant in (lease.owner, lease.tenant):
            if not participant.is_active:
                _, created = PrivateAccessRevocation.objects.get_or_create(
                    lease=lease, user=participant, defaults={"reason": "account_closed"}
                )
                revoked += int(created)
    return {
        "refunds": refunded,
        "documents": generated,
        "leases": evaluated,
        "access_revocations": revoked,
    }
