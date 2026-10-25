"""The same housing requirements govern discovery and final submission."""


def property_requirements(queryset, criteria):
    if criteria.get("property_type"):
        queryset = queryset.filter(property_type__slug=criteria["property_type"])
    if criteria.get("furnished") is not None:
        queryset = queryset.filter(is_furnished=criteria["furnished"])
    for name in criteria.get("amenities", []):
        queryset = queryset.filter(
            **{name if name == "near_metro" else f"has_{name}": True}
        )
    return queryset


def offer_problem(item, prop, snapshot, rent):
    requirements = item.criteria
    if (
        requirements.get("rental_scope")
        and requirements["rental_scope"] != snapshot["rental_scope"]
    ):
        return "The accommodation type must match the housing request."
    capacity = 1 if snapshot["rental_scope"] == "bed" else snapshot.get("capacity")
    if capacity is None or requirements["people"] > capacity:
        return "The accommodation cannot hold the requested party."
    if (
        requirements.get("property_type")
        and prop.property_type.slug != requirements["property_type"]
    ):
        return "The property type does not match the request."
    if (
        requirements.get("furnished") is not None
        and prop.is_furnished != requirements["furnished"]
    ):
        return "The furnishing requirement is not met."
    if any(
        not getattr(prop, name if name == "near_metro" else f"has_{name}", False)
        for name in requirements.get("amenities", [])
    ):
        return "The requested amenities are not available."
    if snapshot["terms"].get("price_period") != requirements["price_period"]:
        return "The offer must use the requested price period."
    per_person_group = bool(
        item.academic_plan_id
        and item.academic_snapshot.get("budget_basis") == "per_person"
        and requirements["people"] > 1
    )
    if not per_person_group and (
        rent < (requirements.get("budget_min") or {}).get("amount_minor", 0)
        or rent > (requirements.get("budget_max") or {}).get("amount_minor", 10**12)
    ):
        return "The rent is outside the requested budget."
    return None
