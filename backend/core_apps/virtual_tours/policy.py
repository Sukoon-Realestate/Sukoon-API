import hashlib
import json
import uuid
from urllib.parse import urlsplit
from django.conf import settings
from django.shortcuts import get_object_or_404
from core_apps.properties.models import (
    Property,
    ResidentialBuilding,
    ResidentialComplex,
)
from .errors import require

KINDS = ("panorama_360", "model_3d")
PART_SIZE = 8 * 1024 * 1024
LIMITS = {
    "panorama_bytes": 30 * 1024**2,
    "model_bytes": 250 * 1024**2,
    "collision_bytes": 5 * 1024**2,
    "walk_bytes": 1024**2,
    "part_bytes": PART_SIZE,
    "parallel_uploads": 2,
    "local_bytes": 512 * 1024**2,
    "min_scenes": 2,
    "max_scenes": 40,
}


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def enabled(kind, write=False):
    switches = settings.VIRTUAL_TOUR_KINDS.get(kind, {})
    url = urlsplit(settings.VIRTUAL_TOUR_VIEWER_URL)
    configured = (
        url.scheme == "https"
        and bool(url.netloc)
        and not url.query
        and not url.fragment
        and not url.username
        and not url.password
        and url.path == "/tours/"
    )
    if kind == "model_3d" and write:
        configured = configured and bool(
            settings.VIRTUAL_TOUR_GLTF_VALIDATOR
            and settings.VIRTUAL_TOUR_SPAWN_VALIDATOR
        )
    return configured and bool(switches.get("write" if write else "read", False))


def uuid_value(value):
    try:
        return uuid.UUID(value) if isinstance(value, str) else None
    except (ValueError, AttributeError):
        return None


def target_model(kind):
    require(
        kind in {"property", "building", "complex"},
        "invalid_asset",
        "Choose a supported residential asset.",
        404,
    )
    return {
        "property": Property,
        "building": ResidentialBuilding,
        "complex": ResidentialComplex,
    }[kind]


def owner_property(user, property_id, kind="property"):
    require(
        user.is_authenticated,
        "authentication_required",
        "Sign in to manage tours.",
        401,
    )
    return get_object_or_404(
        target_model(kind),
        id=property_id,
        **(
            {"owner": user, "retired_at": None}
            if kind == "property"
            else {"manager": user, "archived": False}
        ),
    )


def writable(revision):
    require(
        enabled(revision.tour.kind, True),
        "tour_disabled",
        "Tour preparation is unavailable.",
        503,
    )
    require(not revision.tour.deleted, "tour_deleted", "This tour was deleted.", 410)
    require(
        revision.review_state == "not_submitted",
        "revision_immutable",
        "Create a new revision to edit submitted content.",
        409,
    )
    require(
        revision.processing_state not in ("queued", "processing"),
        "processing_in_progress",
        "Wait for processing to finish.",
        409,
    )


def match_version(revision, etag):
    require(
        etag == f'"draft-{revision.draft_version}"',
        "draft_version_conflict",
        "Refresh the draft before editing.",
        412,
    )


def public_property(prop):
    from core_apps.chat.models import AccountRestriction

    owner_id = prop.owner_id if isinstance(prop, Property) else prop.manager_id
    if AccountRestriction.objects.filter(
        user_id=owner_id, state__in=["pending_review", "permanent"]
    ).exists():
        return False
    if not isinstance(prop, Property):
        return (
            not prop.archived
            and prop.authority_status == "verified"
            and bool(prop.authority_reviewed_by_id and prop.authority_reference)
        )
    return prop.retired_at is None and prop.status == Property.Status.VERIFIED


def scope_policy(prop, context, spaces):
    """Exclude prices/revision counters. Include persisted spatial identities only."""
    if not isinstance(prop, Property):
        require(
            context == "overview"
            and all(
                s.get("space_kind") in {"shared", "corridor", "entrance"}
                and not s.get("room_id")
                and not s.get("bed_id")
                for s in spaces
            ),
            "scope_violation",
            "Container tours show common areas only. Prepare unit interiors on their canonical unit.",
            403,
        )
        return digest(
            {
                "policy": 1,
                "asset_id": str(prop.id),
                "kind": prop._meta.model_name,
                "topology_revision": prop.topology_revision,
                "spaces": sorted(spaces, key=lambda s: s["id"]),
            }
        )
    inventory = prop.rental_inventory or {}
    rooms = {str(r["id"]): r for r in inventory.get("rooms", []) if r.get("id")}
    beds = {
        str(b["id"]): rid
        for rid, r in rooms.items()
        for b in r.get("beds", [])
        if b.get("id")
    }
    partial = inventory.get("mode") == "partial"
    offer = None
    if context != "overview":
        offer = next(
            (o for o in inventory.get("offers", []) if str(o.get("id")) == context),
            None,
        )
        require(
            offer
            and not offer.get("archived")
            and offer.get("availability", "available") == "available",
            "scope_unavailable",
            "The offer is no longer available.",
            409,
        )
    selected = set(map(str, offer.get("room_ids", []))) if offer else set()
    entire = (offer and offer.get("rental_scope") == "entire_property") or (
        not offer and not partial
    )
    permitted = []
    for space in spaces:
        rid, bid = space.get("room_id"), space.get("bed_id")
        require(
            not rid or rid in rooms,
            "invalid_inventory_mapping",
            "A room is missing from this property.",
        )
        require(
            not bid or (bid in beds and beds[bid] == rid),
            "invalid_inventory_mapping",
            "A bed is missing from this room.",
        )
        shared = (
            space["space_kind"] in ("shared", "corridor", "entrance")
            and not rid
            and not bid
        )
        allowed = (
            entire
            or shared
            or (offer and rid in selected and (not bid or bid == offer.get("bed_id")))
        )
        require(
            allowed,
            "scope_violation",
            "This package contains a space outside its viewing scope.",
            403,
        )
        permitted.append(
            {
                k: space.get(k)
                for k in ("id", "space_kind", "room_id", "bed_id", "floor_id")
            }
        )
    return digest(
        {
            "policy": 1,
            "mode": inventory.get("mode", "whole"),
            "context": context,
            "scope": offer.get("rental_scope") if offer else "overview",
            "rooms": sorted(selected),
            "inventory_geometry": [
                {
                    "id": rid,
                    "beds": sorted(
                        str(b["id"]) for b in rooms[rid].get("beds", []) if b.get("id")
                    ),
                }
                for rid in sorted(rooms if entire else selected)
                if rid in rooms
            ],
            "bed": offer.get("bed_id") if offer else None,
            "spaces": sorted(permitted, key=lambda s: s["id"]),
        }
    )
