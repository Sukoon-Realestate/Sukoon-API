"""Fresh membership checks and exact offer identity for organization lists."""

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.properties.models import Property
from ...company_models import PortfolioOffer
from ...company_saved_models import CompanySavedList, CompanySavedItem
from .access import company_for, member_for
from ..rental_lifecycle.common import require_revision, audit
from ..rental_phase2 import RentalConflict


def authorize(user, company_id, *, write=False, lock=False):
    company = company_for(user, company_id, lock=lock)
    member = member_for(user, company)
    if not (
        member.is_admin or member.is_coordinator or (not write and member.is_approver)
    ):
        raise PermissionDenied(
            "Company lists require an active planning team membership."
        )
    return company


def get_list(user, identity, *, write=False, lock=False):
    item = get_object_or_404(CompanySavedList, id=identity)
    authorize(user, item.company.id, write=write, lock=lock)
    if lock:
        item = CompanySavedList.objects.select_for_update().get(pk=item.pk)
    return item


def payload(item):
    return {
        "id": str(item.id),
        "company_id": str(item.company.id),
        "name": item.name,
        "archived": item.archived,
        "revision": item.revision,
        "item_count": item.items.count(),
    }


def item_payload(item):
    available = False
    title = ""
    if item.portfolio_offer_id:
        offer = item.portfolio_offer
        available = offer.status == "published"
        if available:
            from .offers import resolve_scope
            from rest_framework.exceptions import APIException

            try:
                resolve_scope(offer)
            except APIException:
                available = False
        title = offer.scope if available else ""
    else:
        prop = item.property
        available = prop.status == Property.Status.VERIFIED and prop.retired_at is None
        if item.offer_id:
            available = available and any(
                str(v.get("id")) == item.offer_id and not v.get("archived")
                for v in prop.rental_inventory.get("offers", [])
            )
        title = prop.title if available else ""
    return {
        "id": str(item.id),
        "list_id": str(item.saved_list.id),
        "property_id": str(item.property.id) if item.property_id else "",
        "offer_id": item.offer_id,
        "portfolio_offer_id": (
            str(item.portfolio_offer.id) if item.portfolio_offer_id else ""
        ),
        "available": bool(available),
        "title": title,
    }


def create(user, company, data):
    if data["expected_revision"] != 0:
        raise ValidationError(
            {"expected_revision": "New lists start at revision zero."}
        )
    item = CompanySavedList.objects.create(
        company=company, name=data["name"], created_by=user
    )
    audit(item, user, "company_saved_list_created")
    return item


def update(user, item, data, action):
    require_revision(item, data["expected_revision"])
    if item.archived:
        raise RentalConflict("The list is archived.", code="list_archived")
    if action == "rename":
        item.name = data["name"]
    elif action == "archive":
        item.archived = True
    elif action == "remove":
        get_object_or_404(
            CompanySavedItem, saved_list=item, id=data["item_id"]
        ).delete()
    elif action == "add":
        prop_id, portfolio_id = data.get("property_id"), data.get("portfolio_offer_id")
        if bool(prop_id) == bool(portfolio_id) or (
            portfolio_id and data.get("offer_id")
        ):
            raise ValidationError("Choose one exact property offer or portfolio offer.")
        values = {"saved_list": item}
        if portfolio_id:
            values["portfolio_offer"] = get_object_or_404(
                PortfolioOffer, id=portfolio_id, status="published"
            )
            from .offers import resolve_scope

            resolve_scope(values["portfolio_offer"])
        else:
            prop = get_object_or_404(
                Property, id=prop_id, status=Property.Status.VERIFIED, retired_at=None
            )
            offer_id = data.get("offer_id", "")
            if not offer_id or not any(
                str(v.get("id")) == offer_id and not v.get("archived")
                for v in prop.rental_inventory.get("offers", [])
            ):
                raise ValidationError(
                    {"offer_id": "Choose a current, exact rental offer."}
                )
            values.update(property=prop, offer_id=offer_id)
        CompanySavedItem.objects.get_or_create(**values, defaults={"added_by": user})
    item.revision += 1
    item.save()
    audit(item, user, "company_saved_list_" + action)
    return item
