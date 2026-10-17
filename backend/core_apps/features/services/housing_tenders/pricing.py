"""Integer monthly EGP quotes; never infer a discount from prose."""

from rest_framework.exceptions import ValidationError
from ..rental_phase2 import RentalConflict


def integer(value, field, *, minimum=0, maximum=10**10):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError({field: "Use an integer within the supported range."})
    return value


def validate_tiers(rule, tiers, capacity, base_prices):
    if rule not in {"canonical", "all_units", "marginal"} or not isinstance(
        tiers, list
    ):
        raise ValidationError(
            {"pricing_rule": "Use canonical, all_units or marginal pricing."}
        )
    if rule == "canonical":
        if tiers:
            raise ValidationError(
                {"price_tiers": "Canonical pricing has no quantity tiers."}
            )
        return []
    if len(tiers) > 12 or not tiers or len(set(base_prices)) != 1:
        raise ValidationError(
            {
                "price_tiers": "Quantity tiers require a homogeneous set of monthly units."
            }
        )
    expected = 1
    clean = []
    for tier in tiers:
        if not isinstance(tier, dict) or set(tier) != {
            "from_quantity",
            "to_quantity",
            "rent_minor",
        }:
            raise ValidationError(
                {
                    "price_tiers": "Supply exact from_quantity, to_quantity and rent_minor fields."
                }
            )
        start = integer(
            tier["from_quantity"], "from_quantity", minimum=1, maximum=capacity
        )
        end = integer(
            tier["to_quantity"], "to_quantity", minimum=start, maximum=capacity
        )
        price = integer(
            tier["rent_minor"], "rent_minor", minimum=1, maximum=base_prices[0]
        )
        if start != expected:
            raise ValidationError(
                {
                    "price_tiers": "Tiers must cover all quantities without gaps or overlap."
                }
            )
        clean.append({"from_quantity": start, "to_quantity": end, "rent_minor": price})
        expected = end + 1
    if expected != capacity + 1:
        raise ValidationError({"price_tiers": "Tiers must cover every offered unit."})
    return clean


def quote_allocations(bid, lines):
    """Marginal positions use stable line UUID order, shown in the exact allocation."""
    quantity = len(lines)
    if quantity < bid.minimum_quantity or quantity > bid.lines.count():
        raise RentalConflict(
            "The accepted quantity does not satisfy this bid.",
            code="quantity_threshold",
        )
    ordered = sorted(lines, key=lambda line: str(line.id))
    if bid.pricing_rule == "canonical":
        return {str(line.id): line.offer.rent_minor for line in ordered}
    result = {}
    for position, line in enumerate(ordered, 1):
        basis = quantity if bid.pricing_rule == "all_units" else position
        tier = next(
            (
                t
                for t in bid.price_tiers
                if t["from_quantity"] <= basis <= t["to_quantity"]
            ),
            None,
        )
        if not tier:
            raise RentalConflict(
                "The quantity tier requires review.", code="price_invalid"
            )
        result[str(line.id)] = tier["rent_minor"]
    return result
