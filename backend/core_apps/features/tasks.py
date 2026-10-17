"""Stable public imports for tasks.

Implementation modules separate domain responsibilities without changing routes.
"""

from celery import shared_task
from .services.transition_network.jobs import process_transition_match
from .services.housing_tenders.jobs import process_tender_packages
from .services.housing_scenarios.jobs import calculate as calculate_housing_scenario
from .services.asset_passport.analysis import process as analyze_asset_observations
from .services.advanced_housing_jobs import recover_jobs, purge_private_inputs
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
from .services.rental_phase2 import RentalConflict
from .services.rental_phase3 import issue_invoice, process_provider_event

from .tasks_parts.expire_rental_sources_and_holds import (
    process_commute_search,
    process_planning_jobs,
    expire_rental_sources_and_holds,
    reconcile_rental_provider_sessions,
    run_rental_billing_cycle,
    reconcile_ambiguous_rental_payments,
)
from .tasks_parts.process_rental_changes import (
    scan_rental_evidence,
    reconcile_approved_payouts,
    process_rental_changes,
)
from .tasks_parts.process_rental_closure import (
    process_rental_closure,
)

@shared_task
def reconcile_reviews():
    from .services.reputation.tasks import reconcile
    return reconcile()
