"""Use the same parent-before-unit order as corporate inventory review."""

from ..models import Property, ResidentialBuilding, ResidentialComplex
from core_apps.features.services.rental_phase2 import RentalConflict


def lock_listing(pk):
    source = Property.objects.select_related("building").get(pk=pk)
    root_id = source.building.complex_id if source.building_id else None
    complex_ids = {identity for identity in (source.complex_id, root_id) if identity}
    list(
        ResidentialComplex.objects.select_for_update()
        .filter(pk__in=complex_ids)
        .order_by("pk")
    )
    building = None
    if source.building_id:
        building = ResidentialBuilding.objects.select_for_update().get(
            pk=source.building_id
        )
        if building.complex_id != root_id:
            raise RentalConflict(
                "The inventory parent changed. Reload before editing.",
                code="stale_revision",
            )
    current = Property.objects.select_for_update().get(pk=pk)
    if (current.building_id, current.complex_id) != (
        source.building_id,
        source.complex_id,
    ):
        raise RentalConflict(
            "The inventory parent changed. Reload before editing.",
            code="stale_revision",
        )
    return current
