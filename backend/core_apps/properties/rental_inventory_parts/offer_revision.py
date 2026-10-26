"""An offer revision tracks its own reviewed content and physical accommodation."""

from copy import deepcopy


def reviewed_content(inventory, offer):
    if offer is None:
        return None
    content = {
        key: deepcopy(value)
        for key, value in offer.items()
        if key
        not in {"revision", "client_key", "actions", "offer_link", "inherited_fields"}
    }
    selected = set(str(identity) for identity in offer.get("room_ids", []))
    rooms = []
    for source in inventory.get("rooms", []):
        if (
            offer.get("rental_scope") != "entire_property"
            and str(source["id"]) not in selected
        ):
            continue
        room = {
            key: deepcopy(value)
            for key, value in source.items()
            if key not in {"client_key", "beds", "actions"}
        }
        room["beds"] = sorted(
            (
                {
                    key: deepcopy(value)
                    for key, value in bed.items()
                    if key not in {"client_key", "actions"}
                }
                for bed in source.get("beds", [])
                if offer.get("rental_scope") != "bed"
                or str(bed["id"]) == str(offer.get("bed_id"))
            ),
            key=lambda bed: str(bed["id"]),
        )
        rooms.append(room)
    content["room_ids"] = sorted(offer.get("room_ids", []))
    return {"offer": content, "rooms": sorted(rooms, key=lambda room: str(room["id"]))}
