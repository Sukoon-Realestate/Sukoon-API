"""Shared lease lock preconditions for competing renewal/departure workflows."""

from ..models import RentalChange
from ..planning_models import TenancyTransition
from .rental_phase2 import RentalConflict

TERMINAL_TRANSITIONS = {"withdrawn", "declined", "cancelled", "expired", "effective"}


def require_no_renewal(lease):
    if (
        lease.rental_changes.filter(kind=RentalChange.Kind.RENEWAL)
        .exclude(status=RentalChange.Status.REJECTED)
        .exists()
    ):
        raise RentalConflict(
            "Resolve the current renewal before starting departure or replacement.",
            code="competing_renewal",
        )


def require_no_departure(lease, *, activating=False):
    if (
        TenancyTransition.objects.filter(lease=lease)
        .exclude(status__in=TERMINAL_TRANSITIONS)
        .exists()
    ):
        raise RentalConflict(
            "Resolve the departure or replacement request before renewing.",
            code="competing_departure",
        )
    states = {"active", "ended"} if activating else {"active"}
    terminated = (
        activating
        and lease.rental_changes.filter(
            kind=RentalChange.Kind.TERMINATION,
            status__in=[RentalChange.Status.ACCEPTED, RentalChange.Status.APPLIED],
        ).exists()
    )
    if lease.status not in states or lease.occupancy_status == "returned" or terminated:
        raise RentalConflict(
            "Renewal requires a current tenancy with retained possession."
        )
