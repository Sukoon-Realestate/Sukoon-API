"""Revision-scoped links use inventory identities, never inferred prices."""
from .errors import TourError, require


def binding(offer):
    return {
        "offer_id": str(offer.get("id", "")),
        "rental_scope": offer.get("rental_scope", ""),
        "room_ids": sorted(map(str, offer.get("room_ids", []))),
        "bed_id": str(offer.get("bed_id") or ""),
    }


def validate_link(prop, space):
    link = space.get("offer_link")
    if link is None:
        return None
    require(space["space_kind"] in ("room", "bed"), "shared_offer_link",
            "Common places cannot be linked to an exclusive offer.")
    inventory = getattr(prop, "rental_inventory", None) or {}
    offer = next((o for o in inventory.get("offers", [])
                  if str(o.get("id")) == link["offer_id"]), None)
    require(offer and not offer.get("archived")
            and offer.get("availability", "available") == "available",
            "offer_unavailable", "This offer is unavailable. Review the link.", 409)
    require(binding(offer) == link, "offer_link_changed",
            "The offer accommodation changed. Review its link in a new revision.", 409)
    room, bed = space.get("room_id"), space.get("bed_id")
    entire = offer.get("rental_scope") == "entire_property"
    require((entire or room in offer.get("room_ids", []))
            and (not bed or bed == offer.get("bed_id"))
            and (offer.get("rental_scope") != "bed" or bed == offer.get("bed_id")),
            "offer_link_scope", "Link the exact room or bed in this property.", 403)
    return offer


def resolve(session, place_id):
    manifest = session.variant.manifest
    places = (manifest.get("scenes", []) + manifest.get("spawns", [])
              + manifest.get("stations", []) + manifest.get("components", []))
    place = next((p for p in places if p["id"] == place_id), None)
    require(place, "place_unavailable", "This place is no longer in this tour.", 404)
    # Multi-room components have no exclusive accommodation identity.
    space_id = place.get("space_id")
    space = next((s for s in manifest["spaces"] if s["id"] == space_id), None)
    result = {"revision_id": str(session.variant.revision.id),
              "variant_id": str(session.variant.id), "place_id": place_id}
    if not space or not space.get("offer_link"):
        return {**result, "status": "shared" if not space or space["space_kind"] in
                ("shared", "corridor", "entrance") else "unlinked"}
    # Preview stays passive, including when the owner follows a scene link.
    if session.preview:
        return {**result, "status": "preview"}
    try:
        offer = validate_link(session.variant.revision.tour.target, space)
    except TourError:
        return {**result, "status": "unavailable"}
    return {**result, "status": "available",
            "property_id": str(session.variant.revision.tour.property.id),
            "offer_id": str(offer["id"])}
