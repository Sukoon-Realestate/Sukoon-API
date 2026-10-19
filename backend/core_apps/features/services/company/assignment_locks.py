"""Serialize one person's placements across different company roots."""

import hashlib
from django.db import connection
from ...models import EmployeeAssignment
from ..rental_phase2 import RentalConflict


def lock_people(identities):
    if not connection.in_atomic_block:
        raise RuntimeError("Employee assignment locks require an atomic command.")
    if connection.vendor == "postgresql":
        with connection.cursor() as cursor:
            for identity in sorted(set(map(str, identities))):
                key = int.from_bytes(
                    hashlib.sha256(
                        ("employee-placement:" + identity).encode()
                    ).digest()[:8],
                    "big",
                    signed=True,
                )
                cursor.execute("SELECT pg_advisory_xact_lock(%s)", [key])


def require_available(employee, start, end):
    if (
        EmployeeAssignment.objects.filter(
            employee=employee, starts_on__lt=end, ends_on_exclusive__gt=start
        )
        .exclude(occupancy_status__in=["returned", "cancelled"])
        .exists()
    ):
        raise RentalConflict(
            "This employee already has an overlapping current assignment.",
            code="occupancy_overlap",
        )
