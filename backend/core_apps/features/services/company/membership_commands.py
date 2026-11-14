"""Company command steps; typed adapters retain the HTTP boundary."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.features.company_models import CompanyBookingItem, PortfolioOffer
from core_apps.features.services.rental_lifecycle.common import require_revision
from core_apps.features.services.company import membership, offers
from core_apps.features.services.company.access import company_for


def invitations_post_create(_, *, actor, company_id, data, token):
    result, token["value"] = membership.invite(
        actor, company_id, data["email"], data["roles"]
    )
    return result


def item_action_post_authorize(*, action, actor, item_id):
    item = get_object_or_404(CompanyBookingItem, id=item_id)
    company_for(
        actor,
        item.request.company.id,
        "approve" if action == "decide" else "coordinate",
        lock=True,
    )
    item.refresh_from_db()
    if action != "decide" and item.request.coordinator_id != actor.pk:
        raise PermissionDenied("Only the assigned coordinator can manage this request.")
    if action == "decide" and (
        not item.assigned_approver_id or item.assigned_approver.user_id != actor.pk
    ):
        raise PermissionDenied(
            "Only the currently assigned approver can decide this package."
        )
    return item


def portfolio_offer_action_post_authorize(*, actor, offer_id):
    return get_object_or_404(
        PortfolioOffer.objects.select_for_update(), id=offer_id, owner=actor
    )


def portfolio_offer_action_post_execute(offer, *, action, actor, data):
    require_revision(offer, data["expected_revision"])
    previous_status = offer.status
    if action == "publish":
        offers.resolve_scope(offer, lock=True)
    offer.status = "published" if action == "publish" else "paused"
    offer.revision += 1
    offer.save()
    from core_apps.features.services.rental_lifecycle.common import audit

    audit(offer, actor, "portfolio_offer_" + action)
    from core_apps.features.services.company.listing_changes import visibility_changed

    visibility_changed(offer, previous_status)
    return offer
