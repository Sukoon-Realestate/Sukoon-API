"""Keep private commercial terms separate from live physical inventory."""

from datetime import date
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..rental_phase2 import RentalConflict, fingerprint
from .request_period import validate_request_period, monthly_periods
from . import offers


def refresh_offer(booking, *, lock=False):
    from ...company_models import PortfolioOffer

    query = PortfolioOffer.objects.all()
    if lock:
        query = query.select_for_update()
    # Offer before buildings/units, matching selection and owner publication.
    booking.offer = query.get(pk=booking.offer_id)
    return booking.offer


def require_published(booking):
    if booking.offer.status != "published":
        raise RentalConflict(
            "The owner paused this offer. Wait for republication or withdraw the package.",
            code="portfolio_offer_unpublished",
        )


def identity(snapshot, props):
    # Translated labels and prices do not identify the rented accommodation.
    return {
        key: snapshot.get(key)
        for key in (
            "scope",
            "offer_id",
            "owner_id",
            "building_ids",
            "complex_ids",
            "capacity",
            "occupancy_policy",
            "topology_revisions",
        )
    } | {
        "units": [
            {
                k: row.get(k)
                for k in (
                    "id",
                    "floor",
                    "building_id",
                    "complex_id",
                    "capacity",
                    "topology_digest",
                    "physical_keys",
                )
            }
            for row in snapshot["units"]
        ],
        "locations": [
            {
                "id": str(p.id),
                "city": p.city_id,
                "governorate": p.governorate_id,
                "district": p.district_catalog_id or p.district,
                "latitude": str(p.latitude),
                "longitude": str(p.longitude),
            }
            for p in props
        ],
    }


def validate_terms(booking, values, physical):
    data = {
        **values,
        "starts_on": date.fromisoformat(str(values["starts_on"])),
        "ends_on_exclusive": date.fromisoformat(str(values["ends_on_exclusive"])),
    }
    validate_request_period(data)
    named = booking.occupants.count() + booking.planned_staff.count()
    capacity = physical["capacity"]
    if capacity is None or not max(1, named) <= data["occupants"] <= capacity:
        raise ValidationError(
            {"occupants": "Keep the named employees within the accommodation capacity."}
        )
    if (
        physical["occupancy_policy"] != "reserve_capacity_with_notice"
        and data["occupants"] != named
    ):
        raise ValidationError(
            {"occupants": "This offer requires named occupants for every agreed place."}
        )
    return {
        **values,
        "starts_on": str(data["starts_on"]),
        "ends_on_exclusive": str(data["ends_on_exclusive"]),
    }


def current(item, *, lock=False):
    booking = item.booking
    from .request_versions import require_current
    from .approval_routing import validate_staff_plan

    require_current(booking)
    if booking.status in {"withdrawn", "replaced", "request_changed"}:
        raise RentalConflict(
            "This package is no longer open for negotiation.", code="package_closed"
        )
    validate_staff_plan(booking)
    refresh_offer(booking, lock=lock)
    require_published(booking)
    props = offers.resolve_scope(booking.offer, lock=lock)
    from .listing_changes import require_current as require_source

    require_source(booking)
    snapshot = offers.scope_snapshot(booking.offer, props)
    if (
        booking.offer.status != "published"
        or identity(snapshot, props) != item.source_snapshot["identity"]
    ):
        raise RentalConflict(
            "Review the changed accommodation or owner.", code="offer_changed"
        )
    from .negotiation_access import role

    if (
        role(item, item.coordinator) != "coordinator"
        or role(item, item.owner) != "owner"
    ):
        raise RentalConflict(
            "The negotiation parties changed.", code="participants_changed"
        )
    return snapshot


def inventory(booking, current_snapshot, props):
    """Public packages retain their existing checks; negotiated packages bind the agreement."""
    from .listing_changes import require_current as require_source

    require_source(booking)
    require_published(booking)
    item = getattr(booking, "negotiation", None)
    if item is None:

        def comparable(snapshot):
            return {
                **{k: v for k, v in snapshot.items() if k != "offer_revision"},
                "units": [
                    {
                        k: v
                        for k, v in row.items()
                        if k
                        not in {
                            "title",
                            "building_name",
                            "complex_name",
                            "inventory_revision",
                        }
                    }
                    for row in snapshot.get("units", [])
                ],
            }

        reviewed = comparable(booking.snapshot)
        if any(reviewed.get(k) != v for k, v in comparable(current_snapshot).items()):
            raise RentalConflict(
                "Inventory or terms changed. Review a current package.",
                code="offer_changed",
            )
        return {
            **current_snapshot,
            "offer_revision": booking.snapshot.get("offer_revision"),
        }
    if (
        item.status != "accepted"
        or booking.snapshot.get("negotiation")
        != {
            "id": str(item.id),
            "version": item.content_revision,
            "digest": item.terms_digest,
        }
        or identity(current_snapshot, props) != item.source_snapshot["identity"]
    ):
        raise RentalConflict(
            "Review the accepted terms and exact accommodation.",
            code="negotiation_changed",
        )
    if item.followed_at is None and item.expires_at <= timezone.now():
        raise RentalConflict(
            "The negotiated agreement expired.", code="negotiation_expired"
        )
    return {
        **item.source_snapshot["inventory"],
        **{
            k: booking.snapshot[k]
            for k in (
                "monthly_rent",
                "deposit",
                "included_services",
                "excluded_services",
                "capacity",
            )
        },
        "negotiation": booking.snapshot["negotiation"],
    }


def apply(item):
    booking, terms = item.booking, item.terms
    snapshot = dict(booking.snapshot)
    for key in (
        "included_services",
        "excluded_services",
        "starts_on",
        "ends_on_exclusive",
    ):
        snapshot[key] = terms[key]
    snapshot.update(
        monthly_rent={
            "amount_minor": terms["monthly_rent_minor"],
            "currency": "EGP",
            "exponent": 2,
        },
        deposit={
            "amount_minor": terms["deposit_minor"],
            "currency": "EGP",
            "exponent": 2,
        },
        capacity=terms["occupants"],
        reserve_places=terms["occupants"]
        - booking.occupants.count()
        - booking.planned_staff.count(),
        full_term_rent_minor=monthly_periods(
            date.fromisoformat(terms["starts_on"]),
            date.fromisoformat(terms["ends_on_exclusive"]),
        )
        * terms["monthly_rent_minor"],
        negotiation={
            "id": str(item.id),
            "version": item.content_revision,
            "digest": item.terms_digest,
        },
    )
    booking.snapshot, booking.snapshot_digest = snapshot, fingerprint(snapshot)
    booking.full_term_rent_minor, booking.deposit_minor = (
        snapshot["full_term_rent_minor"],
        terms["deposit_minor"],
    )
    booking.quote_expires_at = item.expires_at
    booking.commercial_revision += 1
    booking.status = "proposed"


def require_accepted(booking):
    item = getattr(booking, "negotiation", None)
    if item:
        if item.status != "accepted" or item.expires_at <= timezone.now():
            raise RentalConflict(
                "Review a current accepted version before company approval.",
                code="negotiation_changed",
            )
        physical = current(item, lock=True)
        validate_terms(booking, item.terms, physical)
    else:
        refresh_offer(booking, lock=True)
        require_published(booking)
        props = offers.resolve_scope(booking.offer, lock=True)
        inventory(booking, offers.scope_snapshot(booking.offer, props), props)


def follow(booking):
    item = getattr(booking, "negotiation", None)
    if item and item.status == "accepted" and item.followed_at is None:
        if item.expires_at <= timezone.now():
            raise RentalConflict(
                "The negotiated agreement expired.", code="negotiation_expired"
            )
        item.followed_at = timezone.now()
        item.save(update_fields=["followed_at", "updated_at"])
