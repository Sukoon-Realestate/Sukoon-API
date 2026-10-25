"""Public, current property cards. Stored chat references never grant access."""

import re
from uuid import UUID

from rest_framework.exceptions import APIException, ValidationError
from django.utils.translation import gettext_lazy as _
from core_apps.properties.services.public_access import public_properties


class ChatPropertyUnavailable(APIException):
    status_code = 422
    default_code = "chat_property_unavailable"
    default_detail = _("This property or offer is no longer available.")


def normalize_reference(value):
    if not isinstance(value, dict) or set(value) - {"property_id", "offer_id"}:
        raise ValidationError({"property": "Supply a property reference."})
    try:
        identity = str(UUID(str(value["property_id"])))
    except (KeyError, ValueError, TypeError):
        raise ValidationError({"property": "Supply a valid property identity."})
    offer = value.get("offer_id") or None
    if offer is not None and (
        not isinstance(offer, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,128}", offer)
    ):
        raise ValidationError({"property": "Supply a valid offer identity."})
    return {"property_id": identity, "offer_id": offer}


def load_properties(references):
    """One publication query and one restrictions query per history page."""
    from core_apps.features.models import HabitabilityRestriction

    ids = {r["property_id"] for r in references if r}
    if not ids:
        return {}
    rows = list(public_properties().filter(id__in=ids).select_related("city"))
    restrictions = {row.pk: set() for row in rows if row.rental_inventory}
    if restrictions:
        for prop_id, key in HabitabilityRestriction.objects.filter(
            unit__property_id__in=restrictions, cleared_at__isnull=True
        ).values_list("unit__property_id", "unit__physical_key"):
            restrictions[prop_id].add(key)
    for row in rows:
        row._listing_restricted_keys = restrictions.get(row.pk, set())
    return {str(row.id): row for row in rows}


def properties_for_messages(messages):
    refs = []
    for message in messages:
        if not message.deleted_at:
            refs.append(message.property_reference)
            if message.reply_to_id and not message.reply_to.deleted_at:
                refs.append(message.reply_to.property_reference)
    return load_properties(refs)


def property_card(reference, properties=None):
    if not reference:
        return None
    from core_apps.profiles.serializers import CloudinarySerializerField
    from core_apps.properties.serializers.property_parts.property_list_serializer import (
        build_rental_summary,
    )
    from core_apps.features.services.rental_lifecycle.habitability import (
        offer_restricted,
    )

    if properties is None:
        properties = load_properties([reference])
    prop = properties.get(reference["property_id"])
    unavailable = {**reference, "availability": "unavailable"}
    if prop is None:
        return unavailable
    offer_id = reference.get("offer_id")
    offer = None
    if offer_id:
        offer = next(
            (
                o
                for o in (prop.rental_inventory or {}).get("offers", [])
                if str(o.get("id")) == offer_id
            ),
            None,
        )
        if (
            not offer
            or offer.get("archived")
            or offer.get("availability") != "available"
            or offer_restricted(prop, offer, prop._listing_restricted_keys)
        ):
            return unavailable
    rental = build_rental_summary(prop)
    terms = offer.get("terms", {}) if offer else rental or {}
    return {
        **reference,
        "availability": "available",
        "title": prop.title,
        "image_url": CloudinarySerializerField().to_representation(prop.main_image)
        or "",
        "location": " · ".join(
            filter(None, [prop.city.name if prop.city else "", prop.district])
        ),
        "price": (
            str(terms.get("price") or "") if prop.rental_inventory else str(prop.price)
        ),
        "price_period": (
            terms.get("price_period") or ""
            if prop.rental_inventory
            else prop.price_period
        ),
        "starting_from": not offer and bool(rental and rental.get("starting_from")),
        "offer_label": offer.get("name", "") if offer else "",
    }


def require_shareable(reference):
    if property_card(reference)["availability"] != "available":
        raise ChatPropertyUnavailable()
