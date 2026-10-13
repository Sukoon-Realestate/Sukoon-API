"""Shared planning service names and deployment selection."""

from django.core.exceptions import ImproperlyConfigured


SERVICES = (
    "lifestyle",
    "roommates",
    "housing_groups",
    "group_visits",
    "group_applications",
    "housing_requests",
    "housing_offers",
    "condition_reports",
    "move_out_notices",
    "replacements",
    "commute",
    "tenant_assistant",
)


def enabled_services_from_env(value):
    value = (value or "").strip()
    # Empty hosting-dashboard fields should not silently disable the product.
    if not value or value.lower() == "all":
        return list(SERVICES)
    if value.lower() == "none":
        return []
    selected = {name.strip() for name in value.split(",") if name.strip()}
    if not selected or selected - set(SERVICES):
        raise ImproperlyConfigured(
            "PLANNING_ENABLED_SERVICES must be all, none, or a comma-separated "
            "list of supported planning services."
        )
    return [name for name in SERVICES if name in selected]
