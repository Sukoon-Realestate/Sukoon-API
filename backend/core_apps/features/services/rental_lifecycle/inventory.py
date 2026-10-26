"""One physical-unit/day allocation store. Lock property before lease/hold/units."""

from datetime import timedelta
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.properties.models import Property
from ...models import (
    Lease,
    PaymentAttempt,
    RentalInventoryDayLock,
    RentalInventoryUnit,
    ReservationHold,
)
from ..rental_phase2_parts.remember_mutation import (
    RentalConflict,
    _overlapping_accommodation,
    fingerprint,
)


def topology(inventory):
    rooms = (inventory or {}).get("rooms", [])
    return sorted(
        (str(room["id"]), tuple(sorted(str(bed["id"]) for bed in room.get("beds", []))))
        for room in rooms
    )


def topology_digest(inventory):
    return fingerprint(
        {"rooms": topology(inventory), "mode": (inventory or {}).get("mode", "whole")}
    )


def unit_keys(prop, snapshot):
    inventory = prop.rental_inventory or {}
    rooms = {str(room["id"]): room for room in inventory.get("rooms", [])}
    scope = (snapshot or {}).get("rental_scope", "entire_property")
    if scope == "entire_property":
        selected = list(rooms)
        if not selected:
            return [f"property:{prop.id}"]
    else:
        selected = [str(value) for value in (snapshot or {}).get("room_ids", [])]
        if not selected or any(value not in rooms for value in selected):
            raise RentalConflict(
                "The physical accommodation map needs review.",
                code="inventory_mapping_required",
            )
    keys = []
    for room_id in selected:
        beds = [str(bed["id"]) for bed in rooms[room_id].get("beds", [])]
        if scope == "bed":
            bed_id = str(snapshot.get("bed_id", ""))
            if len(selected) != 1 or bed_id not in beds:
                raise RentalConflict(
                    "The selected bed no longer belongs to this room.",
                    code="offer_changed",
                )
            keys.append(f"bed:{bed_id}")
        else:
            keys.extend([f"bed:{value}" for value in beds] or [f"room:{room_id}"])
    return sorted(set(keys))


def ensure_units(prop, snapshot):
    digest = topology_digest(prop.rental_inventory)
    units = []
    for key in unit_keys(prop, snapshot):
        unit, _ = RentalInventoryUnit.objects.get_or_create(
            property=prop, physical_key=key, defaults={"topology_digest": digest}
        )
        if unit.topology_digest != digest:
            if prop.rental_day_locks.exists():
                raise RentalConflict(
                    "Resolve existing allocations before changing physical inventory.",
                    code="inventory_conflict",
                )
            unit.topology_digest = digest
            unit.save(update_fields=["topology_digest", "updated_at"])
        units.append(unit)
    return units


def unresolved_payment(lease):
    return (
        PaymentAttempt.objects.filter(invoice__lease=lease)
        .filter(payment_status__in=["created", "pending", "authorized"])
        .exists()
        or PaymentAttempt.objects.filter(
            invoice__lease=lease,
            payment_status="captured",
            failure_code="activation_review_required",
        ).exists()
    )


def hold_coverage(lease, *, require_live=True):
    """Unit count is not day count: each selected bed consumes every stay date."""
    rows = lease.inventory_day_locks.filter(kind="hold")
    if require_live:
        rows = rows.filter(expires_at__gt=timezone.now())
    reservation = ReservationHold.objects.filter(lease=lease).first()
    end = reservation.blocked_until_exclusive if reservation else lease.end_date
    expected_days = (end - lease.start_date).days
    if lease.renter_company_id:
        from ..company.tenancy_access import properties

        expected = {
            (prop.pk, key, lease.start_date + timedelta(days=i))
            for prop in properties(lease.company_tenancy)
            for key in unit_keys(prop, {"rental_scope": "entire_property"})
            for i in range(expected_days)
        }
        actual = set(rows.values_list("property_id", "unit__physical_key", "stay_on"))
        return bool(expected and rows.count() == len(expected) and actual == expected)
    keys = unit_keys(lease.property, lease.offer_snapshot)
    return bool(
        expected_days > 0
        and rows.count() == expected_days * len(keys)
        and set(rows.values_list("stay_on", flat=True))
        == {lease.start_date + timedelta(days=i) for i in range(expected_days)}
        and set(rows.values_list("unit__physical_key", flat=True)) == set(keys)
    )


def expire_property_holds(prop, now=None):
    """Caller owns the property lock. Workers and synchronous commands share this rule."""
    from .cases import open_system_case

    now = now or timezone.now()
    released = 0
    lease_ids = list(
        prop.rental_day_locks.filter(
            kind="hold",
            expires_at__lte=now,
            lease__isnull=False,
            lease__renter_company__isnull=True,
        )
        .values_list("lease_id", flat=True)
        .distinct()
    )
    for lease in (
        Lease.objects.select_for_update().filter(pk__in=lease_ids).order_by("pk")
    ):
        from ..signing_documents import unresolved

        if unresolved(lease):
            open_system_case(
                kind="agreement_terms_review",
                source_key=f"hold-signature:{lease.id}",
                lease=lease,
                reason="The original signature result requires reconciliation before this allocation can expire.",
                next_action="Query the original signing document and review its outcome before releasing accommodation.",
            )
            continue
        if unresolved_payment(lease):
            hold = ReservationHold.objects.filter(lease=lease).first()
            if hold and hold.status != "reconciliation_pending":
                hold.status = "reconciliation_pending"
                hold.reconciliation_deadline = now + timedelta(
                    minutes=hold.policy_snapshot["reconciliation_minutes"]
                )
                hold.revision += 1
                hold.save()
            open_system_case(
                kind="payment_unknown",
                source_key=f"hold-payment:{lease.id}",
                lease=lease,
                hold=hold,
                reason="An unresolved payment protects this allocation from automatic expiry.",
                next_action="Reconcile the original provider instruction before releasing accommodation.",
            )
            continue
        released += prop.rental_day_locks.filter(
            lease=lease, kind="hold", expires_at__lte=now
        ).delete()[0]
        if lease.status in {"draft", "pending_signatures", "signed"}:
            lease.status = "expired"
            lease.revision += 1
            lease.save(update_fields=["status", "revision", "updated_at"])
        ReservationHold.objects.filter(
            lease=lease, status__in=["active", "reconciliation_pending"]
        ).update(
            status="expired",
            released_at=now,
            revision=F("revision") + 1,
            updated_at=now,
        )
    # Aggregate holds have one anchor property but own day locks on all units.
    # Visiting any included unit must observe the same authoritative expiry.
    expiring_hold_ids = ReservationHold.objects.filter(
        day_locks__property=prop,
        lease__isnull=True,
        status="active",
        expires_at__lte=now,
    ).values_list("pk", flat=True)
    for hold in (
        ReservationHold.objects.select_for_update()
        .filter(pk__in=expiring_hold_ids)
        .order_by("pk")
    ):
        released += hold.day_locks.all().delete()[0]
        hold.status = "expired"
        hold.released_at = now
        hold.revision += 1
        hold.save()
    return released


def assert_available(
    prop, snapshot, starts_on, ends_on, *, exclude_lease=None, exclude_hold=None
):

    from .habitability import assert_habitable

    assert_habitable(prop, snapshot)
    if prop.retired_at:
        raise RentalConflict(
            "This inventory identity has been retired.", code="inventory_retired"
        )
    keys = unit_keys(prop, snapshot)
    rows = prop.rental_day_locks.filter(stay_on__gte=starts_on, stay_on__lt=ends_on)
    if exclude_lease is not None:
        rows = rows.exclude(lease=exclude_lease)
    if exclude_hold is not None:
        rows = rows.exclude(hold=exclude_hold)
    if rows.filter(unit__physical_key__in=keys).exists():
        raise RentalConflict(
            "The accommodation is no longer available for those dates.",
            code="offer_unavailable",
        )
    for row in rows.filter(unit__isnull=True).select_related("lease"):
        if not row.lease or _overlapping_accommodation(
            snapshot, row.lease.offer_snapshot
        ):
            raise RentalConflict(
                "Historical accommodation allocations require review.",
                code="inventory_conflict",
            )
    # Physical return is independent of contractual end. A known overstay blocks a new promise.
    occupied = Lease.objects.filter(
        Q(property=prop) | Q(inventory_day_locks__property=prop),
        end_date__lte=timezone.localdate(),
        occupancy_status__in=["occupied", "move_out_pending", "handover_disputed"],
    ).distinct()
    from ...models import RentalChange

    continued = RentalChange.objects.filter(
        kind="renewal",
        status="applied",
        result_lease__isnull=False,
        result_lease__tenancy_root_id=F("lease__tenancy_root_id"),
    ).values_list("lease_id", flat=True)
    occupied = occupied.exclude(pk__in=continued)
    if exclude_lease is not None:
        occupied = occupied.exclude(pk=exclude_lease.pk)
    if exclude_lease is not None:
        from ...models import RentalChange

        continuation_ids = RentalChange.objects.filter(
            result_lease=exclude_lease,
            kind="renewal",
            status__in=["signed", "applied"],
            lease__tenant=exclude_lease.tenant,
            lease__owner=exclude_lease.owner,
            lease__tenancy_root_id=exclude_lease.tenancy_root_id,
            lease__end_date=exclude_lease.start_date,
        )
        continuation_ids = (
            continuation_ids.filter(lease__offer_snapshot__isnull=True)
            if exclude_lease.offer_snapshot is None
            else continuation_ids.filter(
                lease__offer_snapshot=exclude_lease.offer_snapshot
            )
        )
        continuation_ids = continuation_ids.values_list("lease_id", flat=True)
        occupied = occupied.exclude(pk__in=continuation_ids)
    if any(
        _overlapping_accommodation(snapshot, item.offer_snapshot) for item in occupied
    ):
        raise RentalConflict(
            "Possession has not been returned for this accommodation.",
            code="occupancy_unresolved",
        )


def allocate_days(
    *, prop, snapshot, offer_id, starts_on, ends_on, expires_at, lease=None, hold=None
):
    if ends_on <= starts_on or (ends_on - starts_on).days > 3660:
        raise ValidationError(
            {"ends_on_exclusive": "A nonempty supported date range is required."}
        )
    assert_available(
        prop, snapshot, starts_on, ends_on, exclude_lease=lease, exclude_hold=hold
    )
    units = ensure_units(prop, snapshot)
    rows = [
        RentalInventoryDayLock(
            property=prop,
            offer_id=offer_id,
            unit=unit,
            stay_on=starts_on + timedelta(days=offset),
            kind="hold" if expires_at else "occupied",
            lease=lease,
            hold=hold,
            expires_at=expires_at,
        )
        for unit in units
        for offset in range((ends_on - starts_on).days)
    ]
    try:
        with transaction.atomic():
            RentalInventoryDayLock.objects.bulk_create(rows, batch_size=500)
    except IntegrityError as error:
        raise RentalConflict(
            "The accommodation is no longer available for those dates.",
            code="offer_unavailable",
        ) from error
    return rows


@transaction.atomic
def reserve_lease(lease, starts_on, ends_on_exclusive, expires_at):
    prop = Property.objects.select_for_update().get(pk=lease.property_id)
    expire_property_holds(prop)
    return allocate_days(
        prop=prop,
        snapshot=lease.offer_snapshot,
        offer_id=lease.offer_id,
        starts_on=starts_on,
        ends_on=ends_on_exclusive,
        expires_at=expires_at,
        lease=lease,
    )


def guard_topology_update(prop, replacement):
    from .habitability import restricted_keys

    if topology_digest(prop.rental_inventory) != topology_digest(
        replacement
    ) and restricted_keys(prop):
        raise RentalConflict(
            "Inspect and clear restricted physical accommodation before changing its identity.",
            code="habitability_restricted",
        )
    if (
        topology_digest(prop.rental_inventory) != topology_digest(replacement)
        and prop.rental_day_locks.exists()
    ):
        raise RentalConflict(
            "Physical inventory cannot change while accommodation is allocated.",
            code="inventory_conflict",
        )
