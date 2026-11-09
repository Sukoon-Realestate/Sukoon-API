"""Strict shape contract for ``rental_inventory`` commands (Sprint 02, A2-05).

``normalize_inventory`` used to assume shapes and coerce with ``int(...)``, so
``expected_revision: "oops"``, ``rooms: [null]``, ``shared_defaults: []`` or a
``"Infinity"`` price became 500s or reached projections. This module checks
the complete command first and raises field-level ``ValidationError``s only.

Unknown keys: documented fields are strictly typed. Other keys on the
inventory, rooms, beds and offers are client extensions (Flutter sends
``media_ids``/``shared_media_ids``/``bathroom_access``); they are preserved as
before but must be bounded JSON. Stored values keep their original form.
"""

from rest_framework.exceptions import ValidationError

from core_apps.common.command_fields import check_json_bounds, finite_decimal, strict_int

MAX_ROOMS = 50
MAX_BEDS_PER_ROOM = 20
MAX_OFFERS = 100
MAX_NAME = 200
MAX_TEXT = 4000
MAX_INVENTORY_BYTES = 256 * 1024
PRICE_PERIODS = {"daily", "weekly", "monthly", "yearly"}


def _fail(message):
    raise ValidationError({"rental_inventory": message})


def _object(value, label):
    if not isinstance(value, dict):
        _fail(f"{label} must be an object.")
    return value


def _list(value, label, maximum):
    if value is None:
        return []
    if not isinstance(value, list):
        _fail(f"{label} must be an array.")
    if len(value) > maximum:
        _fail(f"{label} supports at most {maximum} items.")
    return value


def _text(container, key, label, *, maximum=MAX_NAME, required=False, nullable=True):
    if key not in container:
        if required:
            _fail(f"{label} is required.")
        return
    value = container[key]
    if value is None and nullable and not required:
        return
    if not isinstance(value, str) or len(value) > maximum or "\x00" in value:
        _fail(f"{label} must be text of at most {maximum} characters.")


def _identity(container, label):
    _text(container, "id", f"{label} id", maximum=64)
    _text(container, "client_key", f"{label} client_key", maximum=100)


def _check_unique(items, label):
    seen = set()
    for item in items:
        identity = item.get("id")
        if identity:
            if identity in seen:
                _fail(f"Duplicate {label} id in rental_inventory.")
            seen.add(identity)


def _terms(terms, label):
    _object(terms, label)
    if "price" in terms:
        try:
            finite_decimal(terms["price"], field="price", max_digits=12, decimal_places=2)
        except ValidationError:
            _fail(
                "Every offer requires a non-negative, finite decimal price with at most "
                "10 whole digits and 2 decimal places."
            )
    if "price_period" in terms and terms["price_period"] not in PRICE_PERIODS:
        _fail("Every offer requires a valid price_period.")
    if terms.get("rental_period") is not None:
        try:
            strict_int(terms["rental_period"], field="rental_period", maximum=120)
        except ValidationError:
            _fail("rental_period must be a whole number of months (0-120).")
    deposit = terms.get("deposit")
    if deposit is not None and (
        isinstance(deposit, bool)
        or not isinstance(deposit, (str, int))
        or isinstance(deposit, str) and len(deposit) > MAX_NAME
    ):
        _fail("deposit must be a deposit code or amount.")
    _text(terms, "suitable_for", f"{label} suitable_for", maximum=MAX_NAME)
    _text(terms, "description", f"{label} description", maximum=MAX_TEXT)
    if terms.get("smoking_allowed") is not None and not isinstance(
        terms["smoking_allowed"], bool
    ):
        _fail("smoking_allowed must be true, false or null.")
    if terms.get("rules") is not None:
        rules = _list(terms["rules"], f"{label} rules", 50)
        if not all(isinstance(rule, str) and len(rule) <= MAX_NAME for rule in rules):
            _fail("rules must be text items.")


def validate_inventory_command(value):
    """Validate the full inventory command shape; return the revision as int."""
    _object(value, "rental_inventory")
    schema = value.get("schema_version")
    if type(schema) is not int or schema != 1:
        _fail("schema_version 1 is required.")
    if value.get("mode") not in {"whole", "partial"}:
        _fail("mode must be whole or partial.")
    try:
        check_json_bounds(value, max_depth=8, max_bytes=MAX_INVENTORY_BYTES, max_items=MAX_OFFERS)
    except ValidationError as error:
        _fail(f"Inventory is too large or malformed: {error.detail[0]}")
    try:
        expected = strict_int(value.get("expected_revision", 0), field="expected_revision")
    except ValidationError:
        _fail("expected_revision must be a non-negative integer.")

    rooms = _list(value.get("rooms"), "rooms", MAX_ROOMS)
    for room in rooms:
        _object(room, "Every room")
        _identity(room, "Room")
        if room.get("capacity") is not None and (
            type(room["capacity"]) is not int or not 1 <= room["capacity"] <= 50
        ):
            _fail("Room capacity must be a positive integer or null.")
        _text(room, "name", "Room name")
        _text(room, "description", "Room description", maximum=MAX_TEXT)
        for bed in _list(room.get("beds"), "beds", MAX_BEDS_PER_ROOM):
            _object(bed, "Every bed")
            _identity(bed, "Bed")
            _text(bed, "name", "Bed name")
    _check_unique(rooms, "room")
    _check_unique([bed for room in rooms for bed in room.get("beds") or []], "bed")

    shared = value.get("shared_defaults")
    if shared is not None:
        _terms(shared, "shared_defaults")

    offers = _list(value.get("offers"), "offers", MAX_OFFERS)
    for offer in offers:
        _object(offer, "Every offer")
        _identity(offer, "Offer")
        _text(offer, "name", "Offer name")
        if not isinstance(offer.get("rental_scope"), str):
            _fail("Unsupported rental_scope.")
        if not isinstance(offer.get("availability", "available"), str):
            _fail("Unsupported availability.")
        if not isinstance(offer.get("archived", False), bool):
            _fail("archived must be true or false.")
        room_ids = _list(offer.get("room_ids"), "room_ids", MAX_ROOMS)
        if not all(isinstance(item, str) and 0 < len(item) <= 100 for item in room_ids):
            _fail("room_ids must be room identifiers.")
        if offer.get("bed_id") not in (None, "") and (
            not isinstance(offer["bed_id"], str) or len(offer["bed_id"]) > 100
        ):
            _fail("bed_id must be a bed identifier.")
        inherited = _list(offer.get("inherited_fields"), "inherited_fields", 20)
        if not all(isinstance(item, str) for item in inherited):
            _fail("Invalid or conflicting inherited_fields.")
        for key in ("term_overrides", "terms"):
            if offer.get(key) is not None:
                _terms(offer[key], f"Offer {key}")
    _check_unique(offers, "offer")
    return expected
