from .access import periods_for, actions, leases_for
from .evidence import visible_observation, observation_payload


def payload(asset, user, *, detailed=True, lease_id=""):
    from config.advanced_housing import mock_mode_available
    from ..planning import enabled_services

    analysis_ready = (
        mock_mode_available() and "asset_assisted_analysis" in enabled_services()
    )
    owner = asset.property.owner_id == user.pk
    periods = periods_for(user, asset, lease_id)
    allowed_properties = {row.property_id for row in periods}
    successor = getattr(asset, "successor", None)
    # Historical residents receive neither the new location nor later lifecycle
    # status or successor IDs; current property ownership conveys continuity only.
    visible = []
    if detailed:
        leases = list(leases_for(user).filter(property_id__in=allowed_properties))
        for event in asset.events.order_by("effective_on", "created_at"):
            related_property = event.from_property_id or event.to_property_id
            if owner or any(
                lease.property_id == related_property
                and lease.start_date <= event.effective_on < lease.end_date
                for lease in leases
            ):
                visible.append(
                    {
                        "id": str(event.id),
                        "action": event.action,
                        "effective_on": str(event.effective_on),
                        "server_received_at": event.created_at.isoformat(),
                        "from_property_id": (
                            str(event.from_property.id)
                            if event.from_property_id in allowed_properties
                            else ""
                        ),
                        "to_property_id": (
                            str(event.to_property.id)
                            if event.to_property_id in allowed_properties
                            else ""
                        ),
                        "related_asset_id": (
                            str(event.related_asset.id)
                            if owner and event.related_asset_id
                            else ""
                        ),
                    }
                )
    observations = (
        [
            observation_payload(row, user)
            for row in asset.observations.select_related("lease", "author").order_by(
                "-observed_on", "-created_at"
            )
            if (not lease_id or str(row.lease.id) == lease_id)
            and visible_observation(row, user)
        ]
        if detailed
        else []
    )
    return {
        "id": str(asset.id),
        "property_id": (
            str(asset.property.id)
            if owner
            else str(periods[-1].property.id) if periods else ""
        ),
        "label": asset.label,
        "category": asset.category,
        "make_model": asset.make_model,
        "serial_number": asset.serial_number if owner else "",
        "status": asset.status if owner else "tenancy_history",
        "revision": asset.revision,
        "predecessor_id": (
            str(asset.predecessor.id) if owner and asset.predecessor_id else ""
        ),
        "successor_id": str(successor.id) if owner and successor else "",
        "identity_provenance": "owner_recorded",
        "locations": (
            [
                {
                    "property_id": str(row.property.id),
                    "room_id": row.room_id,
                    "space_label": row.space_label,
                    "starts_on": str(row.starts_on),
                    "ends_on_exclusive": (
                        str(row.ends_on_exclusive) if row.ends_on_exclusive else None
                    ),
                }
                for row in periods
            ]
            if detailed and owner
            else []
        ),
        "events": visible,
        "observations": observations,
        "allowed_actions": actions(user, "asset_passport", str(asset.id)),
        "analysis_available": analysis_ready,
        "blocking_reason_codes": (
            [] if analysis_ready else ["assisted_analysis_unavailable"]
        ),
        "private_history_policy": "canonical_source_authorization_required",
    }
