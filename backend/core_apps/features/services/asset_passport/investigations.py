"""Explicit shared-system hypotheses and recorded warranty workflows."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from config.advanced_housing import require_mock_mode
from core_apps.properties.models import ResidentialBuilding
from ...asset_passport_models import (
    AssetItem,
    AssetSharedSystem,
    AssetPatternCase,
    AssetWarrantyReference,
)
from ..planning import text_field, civil_date, check_revision
from ..rental_phase2 import fingerprint, RentalConflict
from ..rental_lifecycle.common import audit
from . import access, analysis, evidence

SYMPTOMS = {
    "water_pressure",
    "leak",
    "power_loss",
    "cooling_failure",
    "drainage",
    "other_reported_fault",
}


def system_for(user, identifier, *, lock=False):
    query = AssetSharedSystem.objects.select_related("building")
    if lock:
        query = query.select_for_update(of=("self",))
    system = get_object_or_404(query, id=identifier, building__manager=user)
    if system.assets.exclude(property__owner=user).exists():
        raise NotFound()
    return system


def create_system(user, asset, data):
    access.asset_for(user, asset.id, write=True)
    building = get_object_or_404(
        ResidentialBuilding, id=data.get("building_id"), manager=user
    )
    ids = data.get("asset_ids", [])
    if (
        not isinstance(ids, list)
        or not 2 <= len(ids) <= 20
        or str(asset.id) not in ids
        or len(set(ids)) != len(ids)
    ):
        raise ValidationError(
            {
                "asset_ids": "Choose two to twenty distinct items in the documented shared system."
            }
        )
    items = list(
        AssetItem.objects.filter(
            id__in=ids, property__building=building, property__owner=user
        )
    )
    if len(items) != len(ids):
        raise NotFound()
    kind = data.get("kind")
    if kind not in SYMPTOMS:
        raise ValidationError({"kind": "Choose a supported documented system type."})
    system = AssetSharedSystem.objects.create(
        building=building,
        created_by=user,
        name=text_field(data, "name", required=True, limit=160),
        kind=kind,
        authority_reference=text_field(
            data, "authority_reference", required=True, limit=200
        ),
    )
    system.assets.set(items)
    audit(system, user, "asset_shared_system_documented")
    return system


def system_payload(system):
    return {
        "id": str(system.id),
        "building_id": str(system.building.id),
        "revision": system.revision,
        "name": system.name,
        "kind": system.kind,
        "authority_reference": system.authority_reference,
        "asset_ids": [str(row.id) for row in system.assets.all()],
        "allowed_actions": ["read", "investigate"],
    }


def create_case(user, system, data):
    require_mock_mode()
    system_for(user, system.id)
    observations = analysis.observations_for(user, data.get("observation_ids"))
    asset_ids = set(system.assets.values_list("pk", flat=True))
    if any(
        row.asset_id not in asset_ids
        or row.property.building_id != system.building_id
        or len(row.note.strip()) < 12
        for row in observations
    ):
        raise ValidationError(
            {
                "observation_ids": "Use documented observations from this registered shared system."
            }
        )
    dates = [row.observed_on for row in observations]
    if (max(dates) - min(dates)).days > 30 or len(
        {row.property_id for row in observations}
    ) < 2:
        raise ValidationError(
            {
                "observation_ids": "A common-fault hypothesis requires reports from two units within thirty days."
            }
        )
    symptom = data.get("symptom")
    if symptom not in SYMPTOMS:
        raise ValidationError(
            {
                "symptom": "Choose a reported fault category without attributing responsibility."
            }
        )
    sources = analysis.manifest(user, observations)
    case = AssetPatternCase.objects.create(
        system=system,
        created_by=user,
        symptom=symptom,
        source_manifest=sources,
        source_digest=fingerprint(sources),
        hypothesis={
            "provider": "mock_pattern_rules",
            "version": "shared-system-v2",
            "simulated": True,
            "kind": "possible_shared_source",
            "report_count": len(observations),
            "unit_count": len({row.property_id for row in observations}),
            "window_days": (max(dates) - min(dates)).days,
            "common_system_documented": True,
            "cause_confirmed": False,
            "responsibility_determined": False,
            "suggested_action": "authorized_common_system_inspection",
        },
    )
    audit(case, user, "asset_pattern_case_opened")
    return case


def case_for(user, identifier, *, lock=False):
    query = AssetPatternCase.objects.select_related("system__building")
    if lock:
        query = query.select_for_update(of=("self",))
    case = get_object_or_404(query, id=identifier)
    system_for(user, case.system.id)
    analysis.observations_for(
        user, [row["observation_id"] for row in case.source_manifest]
    )
    return case


def close_case(user, case, data):
    if case.state.startswith("closed"):
        raise RentalConflict(
            "This investigation has a preserved closure decision.", code="case_closed"
        )
    decision = data.get("decision")
    if decision not in {"common_issue_inspected", "separate_issues", "inconclusive"}:
        raise ValidationError(
            {
                "decision": "Record an inspected common issue, separate issues, or an inconclusive outcome."
            }
        )
    kind = data.get("source_kind")
    source = evidence.source_for(user, kind, data.get("source_id"))
    check_revision(source.revision, data.get("source_revision"))
    if (
        source.lease.property.building_id != case.system.building_id
        or source.status not in {"resolved", "acknowledged", "completed", "agreed"}
    ):
        raise ValidationError(
            {
                "source_id": "Link an acknowledged inspection or resolved maintenance record in this building."
            }
        )
    case.review_note = text_field(data, "reason", required=True, limit=1200)
    case.state = "closed_" + decision
    (
        case.resolution_source_kind,
        case.resolution_source_id,
        case.resolution_source_revision,
    ) = (kind, source.id, source.revision)
    case.closed_at = timezone.now()
    case.revision += 1
    case.save()
    audit(case, user, "asset_pattern_case_closed", case.review_note)
    return case


def case_payload(case):
    return {
        "id": str(case.id),
        "system_id": str(case.system.id),
        "revision": case.revision,
        "state": case.state,
        "symptom": case.symptom,
        "source_manifest": case.source_manifest,
        "hypothesis": case.hypothesis,
        "review_note": case.review_note,
        "resolution_source_kind": case.resolution_source_kind,
        "resolution_source_id": (
            str(case.resolution_source_id) if case.resolution_source_id else ""
        ),
        "allowed_actions": ["read"] if case.closed_at else ["read", "close_case"],
    }


def warranty(user, asset, data):
    source = evidence.source_for(user, data.get("source_kind"), data.get("source_id"))
    check_revision(source.revision, data.get("source_revision"))
    if source.lease.property_id != asset.property_id:
        raise ValidationError(
            {"source_id": "Choose a document source for this item's property."}
        )
    start, end = civil_date(data.get("starts_on"), "starts_on"), civil_date(
        data.get("ends_on_exclusive"), "ends_on_exclusive"
    )
    if end <= start:
        raise ValidationError(
            {"ends_on_exclusive": "The recorded warranty end must follow its start."}
        )
    row = AssetWarrantyReference.objects.create(
        asset=asset,
        created_by=user,
        issuer=text_field(data, "issuer", required=True, limit=160),
        reference=text_field(data, "reference", required=True, limit=160),
        starts_on=start,
        ends_on_exclusive=end,
        source_kind=data["source_kind"],
        source_id=source.id,
        source_revision=source.revision,
    )
    audit(row, user, "asset_warranty_recorded")
    return row


def warranty_for(user, identifier, *, lock=False):
    query = AssetWarrantyReference.objects.select_related("asset")
    if lock:
        query = query.select_for_update(of=("self",))
    row = get_object_or_404(query, id=identifier)
    access.asset_for(user, row.asset.id, write=True)
    evidence.source_for(user, row.source_kind, row.source_id)
    return row


def claim(user, row, data):
    require_mock_mode()
    row.claim_note = text_field(data, "reason", required=True, limit=1200)
    source = evidence.source_for(user, row.source_kind, row.source_id)
    if source.revision != row.source_revision:
        raise RentalConflict(
            "The warranty document source changed. Record a new reference.",
            code="stale_revision",
        )
    row.status = "mock_claim_received"
    row.mock_result = {
        "provider": "mock_warranty_v2",
        "simulated": True,
        "reference": "mock:" + str(row.id),
        "coverage_confirmed": False,
        "claim_accepted": False,
        "money_transferred": False,
    }
    row.revision += 1
    row.save()
    audit(row, user, "asset_mock_warranty_claim")
    return row


def warranty_payload(row):
    return {
        "id": str(row.id),
        "asset_id": str(row.asset.id),
        "revision": row.revision,
        "issuer": row.issuer,
        "reference": row.reference,
        "starts_on": str(row.starts_on),
        "ends_on_exclusive": str(row.ends_on_exclusive),
        "status": row.status,
        "source_kind": row.source_kind,
        "source_id": str(row.source_id),
        "source_revision": row.source_revision,
        "claim_note": row.claim_note,
        "mock_result": row.mock_result,
        "allowed_actions": ["read", "claim"],
    }
