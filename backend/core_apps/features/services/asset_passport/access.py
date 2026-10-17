from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from core_apps.properties.models import Property
from ...asset_passport_models import AssetItem
from ...models import Lease, PrivateAccessRevocation


def leases_for(user):
    return Lease.objects.filter(Q(owner=user) | Q(tenant=user)).exclude(
        pk__in=PrivateAccessRevocation.objects.filter(user=user).values("lease_id")
    )


def lease_covers(period, lease):
    """A property reference alone never grants a room renter the whole inventory."""
    if lease.property_id != period.property_id:
        return False
    scope = lease.offer_snapshot or {}
    if scope.get("rental_scope") == "entire_property":
        return True
    return bool(
        period.room_id
        and period.room_id in [str(value) for value in scope.get("room_ids", [])]
    )


def property_for(user, identifier, *, write=False, lease_id="", lock=False):
    query = Property.objects.select_for_update() if lock else Property.objects
    prop = get_object_or_404(query, id=identifier)
    if prop.owner_id == user.pk:
        return prop
    if (
        not write
        and lease_id
        and leases_for(user).filter(id=lease_id, property=prop).exists()
    ):
        return prop
    raise NotFound()


def periods_for(user, asset, lease_id=""):
    leases = leases_for(user)
    if lease_id:
        leases = leases.filter(id=lease_id)
    periods = []
    for period in asset.locations.select_related("property").order_by(
        "starts_on", "created_at"
    ):
        if period.property.owner_id == user.pk:
            periods.append(period)
            continue
        overlapping = leases.filter(
            property_id=period.property_id, end_date__gt=period.starts_on
        ).filter(
            Q(start_date__lt=period.ends_on_exclusive)
            if period.ends_on_exclusive
            else Q()
        )
        if any(lease_covers(period, lease) for lease in overlapping):
            periods.append(period)
    return periods


def asset_for(user, identifier, *, write=False, lease_id="", lock=False):
    query = AssetItem.objects.select_related("property")
    if lock:
        query = query.select_for_update(of=("self",))
    asset = get_object_or_404(query, id=identifier)
    if asset.property.owner_id != user.pk and (
        write or not periods_for(user, asset, lease_id)
    ):
        raise NotFound()
    return asset


def subject(user, identifier):
    from ...asset_passport_models import (
        AssetAnalysisJob,
        AssetAnalysisSuggestion,
        AssetSharedSystem,
        AssetPatternCase,
        AssetWarrantyReference,
    )
    from . import analysis, investigations

    for model, loader in (
        (AssetAnalysisJob, analysis.job_for),
        (AssetAnalysisSuggestion, analysis.finding_for),
        (AssetSharedSystem, investigations.system_for),
        (AssetPatternCase, investigations.case_for),
        (AssetWarrantyReference, investigations.warranty_for),
    ):
        if model.objects.filter(id=identifier).exists():
            return loader(user, identifier)
    if AssetItem.objects.filter(id=identifier).exists():
        return asset_for(user, identifier)
    return None


def actions(user, capability, subject_id=""):
    if capability not in {"asset_passport", "asset_assisted_analysis"}:
        return []
    if not subject_id:
        return ["read"]
    try:
        from ...asset_passport_models import (
            AssetAnalysisJob,
            AssetAnalysisSuggestion,
            AssetSharedSystem,
            AssetPatternCase,
            AssetWarrantyReference,
        )

        if (
            not AssetItem.objects.filter(id=subject_id).exists()
            and not Property.objects.filter(id=subject_id).exists()
        ):
            item = subject(user, subject_id)
            if isinstance(item, AssetAnalysisJob):
                return ["read", "cancel", "rerun"]
            if isinstance(item, AssetAnalysisSuggestion):
                return ["read", "review"]
            if isinstance(item, AssetSharedSystem):
                return ["read", "investigate"]
            if isinstance(item, AssetPatternCase):
                return ["read", "close_case"]
            if isinstance(item, AssetWarrantyReference):
                return ["read", "claim"]
        if AssetItem.objects.filter(id=subject_id).exists():
            asset = asset_for(user, subject_id)
            result = ["read", "analyze"]
            if asset.status not in {"retired", "replaced"}:
                result += ["observe"]
                if asset.property.owner_id == user.pk:
                    result += [
                        "move",
                        "replace",
                        "retire",
                        "register_system",
                        "warranty",
                        "update",
                    ]
            return result
        property_for(user, subject_id, write=True)
        return ["read", "create"]
    except (NotFound, Http404):
        return []
