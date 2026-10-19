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
    monthly_periods(data["starts_on"], data["ends_on_exclusive"])
