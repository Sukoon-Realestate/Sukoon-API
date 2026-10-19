"""The existing portfolio price contract uses whole calendar months."""

from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..rental_phase2_parts.remember_mutation import add_months


def monthly_periods(starts_on, ends_on_exclusive):
    months = (ends_on_exclusive.year - starts_on.year) * 12 + (
        ends_on_exclusive.month - starts_on.month
    )
    if not 1 <= months <= 120 or add_months(starts_on, months) != ends_on_exclusive:
        raise ValidationError(
            {
                "ends_on_exclusive": "Choose whole monthly billing periods, up to ten years."
            }
        )
    return months


def validate_request_period(data):
    if data["starts_on"] < timezone.localdate():
        raise ValidationError({"starts_on": "Choose today or a future rental date."})
    months = monthly_periods(data["starts_on"], data["ends_on_exclusive"])
    from ..business_policies import current

    policy = current("D05")
    if policy and months > policy.rules["maximum_months"]:
        raise ValidationError(
            {
                "ends_on_exclusive": "This new request exceeds the published maximum monthly duration."
            }
        )

    # A planning request must not promise a period the configured hold engine
    # will reject only after package/authority reviews have been completed.
    from django.conf import settings
    from ...models import RentalCommercialPolicy

    configured = RentalCommercialPolicy.objects.filter(
        version=getattr(settings, "RENTAL_LIFECYCLE_POLICY_VERSION", ""),
        is_active=True,
    ).first()
    limit = (
        (configured.lifecycle_rules or {}).get("max_booking_days")
        if configured
        else None
    )
    if (
        type(limit) is int
        and (data["ends_on_exclusive"] - data["starts_on"]).days > limit
    ):
        raise ValidationError(
            {
                "ends_on_exclusive": "This request exceeds the currently supported reservation period. Choose an earlier end date."
            }
        )
