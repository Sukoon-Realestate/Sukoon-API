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
    from ..services.rental_lifecycle.jobs import reconcile_lifecycle_deadlines

    deadlines = reconcile_lifecycle_deadlines()
    from ..services.company.activation_delivery import drain

    return {
        **deadlines,
        "company_activation_emails": drain(),
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
    from core_apps.properties.models import Property
    from ..services.rental_lifecycle.inventory import expire_property_holds
    from ..models import ReservationHold

    roots = set(
        RentalInventoryDayLock.objects.filter(
            kind="hold", expires_at__lte=now
        ).values_list("property_id", flat=True)
    )
    roots.update(
        ReservationHold.objects.filter(
            status="active", expires_at__lte=now
        ).values_list("property_id", flat=True)
    )
    expired_holds, expired_agreements = 0, 0
    for root in sorted(roots):
        with transaction.atomic():
            prop = Property.objects.select_for_update().get(pk=root)
            before = Lease.objects.filter(property=prop, status="expired").count()
            expired_holds += expire_property_holds(prop, now)
            expired_agreements += (
                Lease.objects.filter(property=prop, status="expired").count() - before
            )
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
    from ..services.rental_lifecycle.cases import open_system_case

    unresolved = PaymentAttempt.objects.filter(
        invoice__purpose="rent",
        payment_status__in=["created", "pending", "authorized"],
        checkout_session__expires_at__lte=timezone.now(),
    ).select_related("invoice__lease")[:100]
    cases = 0
    for attempt in unresolved:
        # A URL timeout says nothing about whether the provider took money.
        open_system_case(
            kind="payment_unknown",
            source_key=f"payment-unknown:{attempt.id}",
            attempt=attempt,
            lease=attempt.invoice.lease,
            reason="Checkout expired without an authoritative financial outcome.",
            next_action="Query the original provider reference; do not start another charge.",
        )
        cases += 1
    return {
        "events_processed": processed,
        "attempts_expired": 0,
        "reconciliation_cases": cases,
    }
