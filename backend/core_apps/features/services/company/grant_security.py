"""Keep privileged onboarding out of unverified invitation/activation paths."""

from django.conf import settings
from ..rental_phase2 import RentalConflict


def require_nonprivileged_onboarding(roles):
    if getattr(
        settings, "RENTAL_RUNTIME_ENVIRONMENT", "production"
    ) == "test" and getattr(settings, "SECURITY_TEST_BYPASS", False):
        return
    if set(roles) & {"admin", "approver"}:
        raise RentalConflict(
            "Activate ordinary membership first. Grant administrative or financial authority through the separately verified membership action.",
            code="verified_role_grant_required",
        )
