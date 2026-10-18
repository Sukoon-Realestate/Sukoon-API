"""Read-only aggregate observations for the existing closure queues."""

import json

from django.core.management.base import BaseCommand
from django.db.models import Count, Min
from django.utils import timezone

from core_apps.features.models import (
    PaymentAttempt,
    RentalOperationalCase,
    RentalProviderInstruction,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.models import HabitabilityRestriction, PolicyDecision
from core_apps.features.asset_passport_models import (
    AssetAnalysisSuggestion,
    AssetWarrantyReference,
)
from core_apps.features.company_staff_models import CompanyAccountProvisioning
from core_apps.users.models import User


def summarize(queryset, observed_at):
    values = queryset.aggregate(count=Count("pk"), oldest=Min("created_at"))
    oldest = values["oldest"]
    return {
        "count": values["count"],
        "oldest_created_at": oldest.isoformat() if oldest else None,
        "oldest_age_seconds": (
            max(0, int((observed_at - oldest).total_seconds())) if oldest else None
        ),
    }


class Command(BaseCommand):
    help = (
        "Print counts and ages for existing rental/payment/notification queues. "
        "Does not reconcile, send notifications, or change business state."
    )

    def handle(self, *args, **options):
        observed_at = timezone.now()
        cases = RentalOperationalCase.objects.exclude(status__in=["resolved", "closed"])
        queues = {
            "habitability_restrictions": HabitabilityRestriction.objects.filter(
                cleared_at__isnull=True
            ),
            "habitability_reviews_due": HabitabilityRestriction.objects.filter(
                cleared_at__isnull=True, review_at__lt=observed_at
            ),
            "manual_visual_reviews": AssetAnalysisSuggestion.objects.filter(
                review_status="ready_for_review", job__provider="manual_visual_review"
            ),
            "warranty_handoffs_pending": AssetWarrantyReference.objects.filter(
                status="manual_review_pending"
            ),
            "company_activation_delivery_pending": CompanyAccountProvisioning.objects.filter(
                delivery_status__in=["queued", "unknown"]
            ),
            "pending_rent_payments": PaymentAttempt.objects.filter(
                payment_status__in=["created", "pending", "authorized"]
            ),
            "captured_rent_payments_without_allocation": PaymentAttempt.objects.filter(
                payment_status="captured", invoice_allocation__isnull=True
            ),
            "unresolved_provider_instructions": RentalProviderInstruction.objects.filter(
                status__in=["pending", "unknown"]
            ),
            "unresolved_cases": cases,
            "overdue_cases": cases.filter(due_at__lt=observed_at),
            "unassigned_cases": cases.filter(assigned_to__isnull=True),
            "cases_with_inactive_assignee": cases.filter(assigned_to__is_active=False),
            "undelivered_planning_events": PlanningEvent.objects.filter(
                delivered_at__isnull=True
            ),
        }
        self.stdout.write(
            json.dumps(
                {
                    "schema_version": 2,
                    "observed_at": observed_at.isoformat(),
                    "frozen_sensitive_accounts": User.objects.filter(
                        sensitive_actions_frozen=True
                    ).count(),
                    "policy_decisions_missing": [
                        f"D{number:02}"
                        for number in range(1, 34)
                        if not PolicyDecision.objects.filter(
                            code=f"D{number:02}"
                        ).exists()
                    ],
                    "queues": {
                        name: summarize(queryset, observed_at)
                        for name, queryset in queues.items()
                    },
                },
                sort_keys=True,
            )
        )
