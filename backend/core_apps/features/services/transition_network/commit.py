"""Lock selected sources in canonical order, then independently revalidate proposals."""

from rest_framework.exceptions import APIException
from django.utils import timezone

from core_apps.users.models import User
from core_apps.properties.models import Property
from ...models import Lease
from ...planning_models import TenancyTransition
from ...transition_network_models import MoveIntent
from .solver import source_snapshot, validate_cycle
from .vacancies import vacancy_snapshot

RELATED = (
    "user",
    "lease__property__owner",
    "lease__property__city",
    "lease__property__property_type",
    "source_transition",
)


def locked_inputs(run, options):
    ids = {run.intent_id, *(item.pk for chain, _ in options for item in chain)}
    hints = list(
        MoveIntent.objects.filter(pk__in=ids).values(
            "pk", "user_id", "lease_id", "source_transition_id", "lease__property_id"
        )
    )
    property_ids = {row["lease__property_id"] for row in hints}
    endpoint_ids = [
        snapshot["endpoint"]["selection"]["property_id"] for _, snapshot in options if snapshot.get("endpoint")
    ]
    properties = Property.objects.filter(pk__in=property_ids) | Property.objects.filter(id__in=endpoint_ids)
    owner_ids = properties.values_list("owner_id", flat=True)
    user_ids = {row["user_id"] for row in hints}
    list(User.objects.select_for_update(no_key=True).filter(pk__in=user_ids | set(owner_ids)).order_by("pk"))
    list(properties.select_for_update(no_key=True).order_by("pk"))
    list(Lease.objects.select_for_update(no_key=True).filter(pk__in=[row["lease_id"] for row in hints]).order_by("pk"))
    list(
        TenancyTransition.objects.select_for_update(no_key=True)
        .filter(pk__in=[row["source_transition_id"] for row in hints])
        .order_by("pk")
    )
    return {
        row.pk: row
        for row in MoveIntent.objects.select_for_update(of=("self",))
        .filter(pk__in=ids)
        .select_related(*RELATED)
        .order_by("pk")
    }


def revalidate(run, options, current):
    origin = current.get(run.intent_id)
    if not origin or origin.revision != run.input_revision:
        return None
    selected = {item.pk for chain, _ in options for item in chain} | {run.intent_id}
    for identity in selected:
        item = current.get(identity)
        if (
            not item
            or item.status != "matching"
            or not item.matching_consent
            or item.expires_at <= timezone.now()
            or not item.user.is_active
            or not item.user.is_verified
        ):
            return None
    checked = []
    try:
        for chain, expected in options:
            fresh = [current[row.pk] for row in chain]
            requirements = run.input_snapshot["requirements"]
            if any(item.revision != requirements[str(item.id)]["revision"] for item in fresh):
                return None
            sources = {str(item.id): source_snapshot(item) for item in fresh}
            if sources != expected["source_manifest"]:
                return None
            endpoint = expected.get("endpoint")
            if endpoint:
                prop = Property.objects.select_related("owner", "city", "property_type").get(
                    id=endpoint["selection"]["property_id"]
                )
                if vacancy_snapshot(prop, endpoint["selection"]["offer_id"]) != endpoint:
                    return None
            if validate_cycle(fresh, sources, endpoint=endpoint) != expected:
                return None
            checked.append((fresh, expected))
    except (APIException, Property.DoesNotExist, MoveIntent.DoesNotExist):
        return None
    return checked
