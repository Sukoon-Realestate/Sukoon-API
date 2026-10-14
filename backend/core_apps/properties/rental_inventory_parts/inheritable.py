"""Rental inventory: inheritable."""

import uuid
from rest_framework.exceptions import ValidationError


SCOPES = {"entire_property", "room", "room_group", "bed"}


AVAILABILITY = {"available", "unavailable", "rented"}


INHERITABLE = {
    "rental_period",
    "deposit",
    "suitable_for",
    "description",
    "smoking_allowed",
    "rules",
}


def _new_id():
    return str(uuid.uuid4())


def _resolve_id(item, old_by_id, client_map):
    supplied_id = str(item.get("id") or "")
    client_key = str(item.get("client_key") or "")
    if supplied_id:
        if supplied_id not in old_by_id:
            raise ValidationError(
                "An existing inventory ID does not belong to this property."
            )
        return supplied_id
    if not client_key:
        raise ValidationError("New inventory entities require client_key.")
    if client_key in client_map:
        raise ValidationError("Duplicate client_key in rental_inventory.")
    assigned = _new_id()
    client_map[client_key] = assigned
    return assigned
