from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied
from core_apps.properties.models import City
from ..planning import civil_date, selection, offer_money
from ..rental_phase2 import add_months, RentalConflict, validate_interest_capacity
from ..lease_permissions import interest_creation_blocker
from ..rental_lifecycle.inventory import (
    unit_keys,
    assert_available,
    expire_property_holds,
)
from .access import members, member_ids


def criteria(raw, plan):
    if not isinstance(raw, dict):
        raise ValidationError({"criteria": "Supply housing criteria."})
    city = get_object_or_404(City, id=raw.get("city_id"))
    start = civil_date(raw.get("start_on"), "start_on", future=True)
    months = raw.get("months")
    if type(months) is not int or not 1 <= months <= 60:
        raise ValidationError({"months": "Use 1 to 60 whole months."})
    budgets = raw.get("budgets")
    if (
        not isinstance(budgets, dict)
        or set(budgets) != member_ids(plan)
        or any(type(v) is not int or v <= 0 for v in budgets.values())
    ):
        raise ValidationError(
            {
                "budgets": "Supply each participant's positive monthly budget in minor units."
            }
        )
    try:
        end = add_months(start, months)
    except (ValueError, OverflowError):
        raise ValidationError({"start_on": "Use a supported date range."})
    return {
        "city_id": str(city.id),
        "city_name": city.name,
        "start_on": str(start),
        "end_on": str(end),
        "months": months,
        "budgets": budgets,
    }


def validate_pair(request, plan, lines, *, owned=False):
    if (
        not isinstance(lines, list)
        or len(lines) != 2
        or any(not isinstance(row, dict) for row in lines)
    ):
        raise ValidationError(
            {"allocations": "Select one room or bed for each of the two participants."}
        )
    if any(
        not isinstance(row.get("tenant_id"), str)
        or not isinstance(row.get("selection"), dict)
        for row in lines
    ):
        raise ValidationError(
            {
                "allocations": "Supply a participant and a valid selection for each place."
            }
        )
    if {row.get("tenant_id") for row in lines} != member_ids(plan):
        raise ValidationError(
            {"allocations": "The two participants must match the plan."}
        )
    start = civil_date(plan.criteria["start_on"], future=True)
    end = civil_date(plan.criteria["end_on"])
    resolved, prop, used = [], None, set()
    # Reject cross-property requests before taking locks in user-controlled order.
    if (
        len({str((row.get("selection") or {}).get("property_id")) for row in lines})
        != 1
    ):
        raise ValidationError(
            {"allocations": "Select two places in the same property."}
        )
    for row in lines:
        current, snapshot = selection(request, row.get("selection"), owned=owned)
        if prop is None:
            expire_property_holds(current)
        prop = current
        if (
            snapshot["rental_scope"] not in {"room", "bed"}
            or snapshot["terms"]["price_period"] != "monthly"
        ):
            raise ValidationError(
                {"selection": "Select an independently offered monthly room or bed."}
            )
        if str(prop.city.id) != plan.criteria["city_id"]:
            raise ValidationError({"selection": "Use the agreed city."})
        if plan.criteria["months"] < max(
            1, int(snapshot["terms"].get("rental_period") or 1)
        ):
            raise ValidationError(
                {"months": "The selected offer requires a longer stay."}
            )
        rent, deposit = offer_money(snapshot)
        if deposit is None:
            raise ValidationError({"selection": "The owner must specify the deposit."})
        if rent > plan.criteria["budgets"][row["tenant_id"]]:
            raise ValidationError(
                {"selection": "The offer exceeds this participant's agreed budget."}
            )
        validate_interest_capacity(snapshot, 1)
        keys = set(unit_keys(prop, snapshot))
        if keys & used:
            raise RentalConflict(
                "The two allocations overlap.", code="inventory_conflict"
            )
        used |= keys
        assert_available(prop, snapshot, start, end)
        resolved.append({"tenant_id": row["tenant_id"], "selection": snapshot})
    from core_apps.chat.moderation.policy import require_new_business

    for user in members(plan):
        reason = interest_creation_blocker(user, prop)
        if reason:
            raise PermissionDenied(reason)
        require_new_business(user)
    require_new_business(prop.owner)
    if not prop.is_ownership_verified:
        raise PermissionDenied("Verified ownership is required.")
    return prop, resolved
