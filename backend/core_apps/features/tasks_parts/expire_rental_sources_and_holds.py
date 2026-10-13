"""Tasks: expire rental sources and holds."""

from celery import shared_task
from datetime import timedelta
from django.db import models, transaction
from django.utils import timezone
from ..models import (
    OwnerOnboardingSession,
    RentalInventoryDayLock,
    SigningSession,
    TenancyInvitation,
    BillingPeriod,
    PaymentAttempt,
    ProviderWebhookEvent,
    RentInvoice,
    Lease,
)
from ..services.rental_phase3 import issue_invoice, process_provider_event


@shared_task(acks_late=True)
def process_commute_search(search_id):
    from ..services.commute_jobs import run_commute

    run_commute(search_id)


@shared_task(acks_late=True)
def process_planning_jobs():
    from ..planning_models import CommuteSearch
    from ..services.commute_jobs import run_commute
    from ..services.planning_notifications import (
        deliver_planning_events,
        record_lease_reminders,
    )

    cutoff = timezone.now() - timedelta(minutes=5)
    # A crashed or timed-out worker cannot leave a forever-running search.
    CommuteSearch.objects.filter(status="running", updated_at__lt=cutoff).update(
        status="failed", failure_code="worker_interrupted", coverage="unavailable"
    )
    for identifier in CommuteSearch.objects.filter(
        status="queued", expires_at__gt=timezone.now()
    ).values_list("id", flat=True)[:20]:
        run_commute(identifier)
    return {
        "reminders": record_lease_reminders(),
        "notifications": deliver_planning_events(),
    }


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
        # Capture/signature handlers also lock the lease before its day locks.
        expired_leases = list(
            Lease.objects.select_for_update()
            .filter(
                status=Lease.Status.SIGNED,
                hold_expires_at__lte=now,
            )
            .order_by("pk")
            .values_list("pk", flat=True)
        )
        expired_agreements = Lease.objects.filter(pk__in=expired_leases).update(
            status=Lease.Status.EXPIRED,
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
        "expired_agreements": expired_agreements,
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
            status=BillingPeriod.Status.SCHEDULED,
            issue_at__lte=now,
            lease__status__in=[Lease.Status.ACTIVE, Lease.Status.TERMINATION_PENDING],
        ):
            issue_invoice(period)
            issued += 1
        overdue = (
            RentInvoice.objects.filter(
                purpose="rent",
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
        invoice__purpose="rent",
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
