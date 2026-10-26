"""Versioned corporate bargaining, followed by independent company approval."""

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from ...models import (
    CompanyTermsNegotiation,
    CompanyTermsVersion,
    CompanyBudgetReservation,
)
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict, fingerprint
from . import negotiation_access as access, negotiation_binding as binding

OPEN = {"proposed", "changes_requested"}


def uncommitted(booking):
    if booking.hold_id or booking.invitation_id or booking.lease_id:
        raise RentalConflict(
            "Continue through the existing commitment's rules.", code="followup_started"
        )


def invalidate(booking):
    CompanyBudgetReservation.objects.filter(item=booking, status="reserved").update(
        status="released"
    )
    preparation = getattr(booking, "contract_preparation", None)
    if preparation and preparation.state != "withdrawn":
        preparation.state = "changes_requested"
        preparation.revision += 1
        preparation.save(update_fields=["state", "revision", "updated_at"])
        from .contract_preparation import notify

        notify(preparation)


def version(item):
    item.terms_digest = fingerprint(
        {
            "negotiation_id": str(item.id),
            "booking_id": str(item.booking.id),
            "company_id": str(item.booking.request.company.id),
            "owner_id": str(item.owner.id),
            "coordinator_id": str(item.coordinator.id),
            "version": item.content_revision,
            "terms": item.terms,
            "expires_at": item.expires_at.isoformat(),
            "identity": item.source_snapshot["identity"],
        }
    )
    CompanyTermsVersion.objects.create(
        negotiation=item,
        version=item.content_revision,
        author=item.author,
        terms=item.terms,
        terms_digest=item.terms_digest,
        expires_at=item.expires_at,
    )


def record(item, actor, action, reason=""):
    audit(
        item,
        actor,
        f"company_terms_{action}",
        reason,
        {"content_revision": item.content_revision},
    )
    from .negotiation_projection import notify

    notify(item, action)


def start(booking, user, data):
    from .access import require_new_business
    from .request_versions import require_current
    from . import offers

    require_new_business()
    from core_apps.users.services.new_business import (
        require_new_business as require_account_business,
    )

    from .access import booking_account_parties

    require_account_business(
        user.pk, *booking_account_parties(booking.id, include_preparation=False)
    )
    require_revision(booking, data["expected_revision"])
    require_current(booking)
    uncommitted(booking)
    if hasattr(booking, "negotiation") or booking.status not in {
        "proposed",
        "approval_pending",
        "approved",
        "changes_requested",
        "rejected",
    }:
        raise RentalConflict(
            "Continue the existing negotiation or replace the package.",
            code="negotiation_exists",
        )
    if not timezone.now() < data["expires_at"] <= booking.quote_expires_at:
        raise RentalConflict(
            "Choose an explicit deadline within the current quote.",
            code="invalid_deadline",
        )
    binding.refresh_offer(booking, lock=True)
    binding.require_published(booking)
    props = offers.resolve_scope(booking.offer, lock=True)
    from .listing_changes import require_current as require_source

    require_source(booking)
    current = offers.scope_snapshot(booking.offer, props)
    if booking.offer.status != "published":
        raise RentalConflict(
            "The portfolio offer is unavailable.", code="offer_changed"
        )
    # Start from the exact selected physical scope, even if public prices changed.
    if binding.identity(current, props) != binding.identity(booking.snapshot, props):
        raise RentalConflict(
            "Review the changed physical package.", code="offer_changed"
        )
    terms = binding.validate_terms(booking, data["terms"], current)
    item = CompanyTermsNegotiation.objects.create(
        booking=booking,
        owner=booking.offer.owner,
        coordinator=user,
        author=user,
        terms=terms,
        expires_at=data["expires_at"],
        source_snapshot={
            "inventory": current,
            "identity": binding.identity(current, props),
        },
    )
    version(item)
    item.save(update_fields=["terms_digest", "updated_at"])
    invalidate(booking)
    booking.status = "negotiating"
    booking.revision += 1
    booking.save()
    record(item, user, "proposed")
    return item


def act(item, user, action, data):
    from .access import require_new_business

    role = access.role(item, user)
    if role not in {"owner", "coordinator"}:
        raise PermissionDenied("Only the owner and assigned coordinator negotiate.")
    require_revision(item, data["expected_revision"])
    if data["terms_digest"] != item.terms_digest:
        raise RentalConflict("Review the exact current terms.", code="stale_revision")
    uncommitted(item.booking)
    if item.followed_at or item.expires_at <= timezone.now():
        raise RentalConflict(
            "The agreement expired or its next stage already started.",
            code="negotiation_closed",
        )
    author = user.pk == item.author_id
    if action == "withdraw":
        if item.status not in OPEN | {"accepted"} or not data["reason"].strip():
            raise RentalConflict("Explain withdrawal before a later commitment starts.")
        item.status = "withdrawn"
        item.booking.status = "withdrawn"
        invalidate(item.booking)
    else:
        if item.status not in OPEN:
            raise RentalConflict(
                "This terms version is closed.", code="negotiation_closed"
            )
        require_new_business()
        if action in {"edit", "counter", "accept"}:
            from core_apps.users.services.new_business import (
                require_new_business as require_account_business,
            )

            from .access import booking_account_parties

            require_account_business(
                user.pk,
                *booking_account_parties(item.booking.id, include_preparation=False),
            )
        physical = binding.current(item, lock=True)
        if action in {"edit", "counter"}:
            if (action == "edit") != author:
                raise PermissionDenied(
                    "Edit your version or counter the other party's version."
                )
            item.terms = binding.validate_terms(item.booking, data["terms"], physical)
            item.content_revision += 1
            item.author = user
            item.status = "proposed"
            version(item)
        elif action in {"accept", "reject", "request-changes"}:
            if author:
                raise PermissionDenied("The other party must respond to this version.")
            if action != "accept" and not data["reason"].strip():
                raise RentalConflict("Explain the rejection or requested change.")
            if action == "accept":
                binding.validate_terms(item.booking, item.terms, physical)
                item.status, item.accepted_by, item.accepted_at = (
                    "accepted",
                    user,
                    timezone.now(),
                )
                binding.apply(item)
            elif action == "reject":
                item.status, item.booking.status = "rejected", "rejected"
            else:
                item.status = "changes_requested"
        else:
            raise PermissionDenied("Unsupported negotiation action.")
    item.revision += 1
    item.save()
    item.booking.revision += 1
    item.booking.save()
    record(item, user, action, data.get("reason", ""))
    return item


def expire_due():
    from django.db import transaction
    from ...models import Company, CompanyBookingItem

    count = 0
    for identity in CompanyTermsNegotiation.objects.filter(
        status__in=OPEN | {"accepted"},
        followed_at__isnull=True,
        expires_at__lte=timezone.now(),
    ).values_list("id", flat=True)[:200]:
        with transaction.atomic():
            source = CompanyTermsNegotiation.objects.get(id=identity)
            Company.objects.select_for_update().get(
                pk=source.booking.request.company_id
            )
            CompanyBookingItem.objects.select_for_update().get(pk=source.booking_id)
            item = CompanyTermsNegotiation.objects.select_for_update().get(pk=source.pk)
            if (
                item.status not in OPEN | {"accepted"}
                or item.followed_at
                or item.expires_at > timezone.now()
            ):
                continue
            # Never expire an already-created commitment because of this deadline.
            if (
                item.booking.hold_id
                or item.booking.invitation_id
                or item.booking.lease_id
            ):
                continue
            item.status = "expired"
            item.revision += 1
            item.save()
            if item.booking.status not in {"withdrawn", "replaced", "request_changed"}:
                item.booking.status = "withdrawn"
                item.booking.revision += 1
                item.booking.save()
            invalidate(item.booking)
            record(item, item.author, "expired")
            count += 1
    return count
