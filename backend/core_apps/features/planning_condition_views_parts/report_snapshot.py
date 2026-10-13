"""Planning condition views: report snapshot."""

import re
from copy import deepcopy
from rest_framework.exceptions import ValidationError
from ..models import RentalEvidence
from ..services.planning import check_revision, civil_date, text_field
from ..services.rental_phase2 import RentalConflict
from .condition_report_context import baseline_for, lease_selection


def report_snapshot(item):
    return deepcopy(
        {
            "revision": item.revision,
            "content_revision": item.content_revision,
            "status": item.status,
            "inspected_on": str(item.inspected_on),
            "selection": item.selection,
            "items": item.items,
            "evidence_ids": sorted(
                str(x) for x in item.evidence.values_list("id", flat=True)
            ),
            "acknowledgements": item.acknowledgements,
            "objections": item.objections,
        }
    )


def _report_values(lease, data):
    if lease.legacy_read_only or lease.status not in {
        "active",
        "termination_pending",
        "ended",
    }:
        raise RentalConflict("Condition reporting requires a current or ended tenancy.")
    if str(data.get("lease_id")) != str(lease.id):
        raise ValidationError({"lease_id": "Must match the report lease."})
    kind = data.get("kind")
    if kind not in {"move_in", "move_out"}:
        raise ValidationError({"kind": "Use move_in or move_out."})
    expected_selection = lease_selection(lease)
    raw = data.get("selection", {})
    if not isinstance(raw, dict):
        raise ValidationError(
            {"selection": "Supply the signed accommodation snapshot."}
        )
    for field in (
        "property_id",
        "offer_id",
        "offer_revision",
        "rental_scope",
        "room_ids",
        "bed_id",
    ):
        if raw.get(field, [] if field == "room_ids" else "") != expected_selection.get(
            field, [] if field == "room_ids" else ""
        ):
            raise RentalConflict(
                "Inspection accommodation must match the signed lease.",
                code="accommodation_changed",
            )
    baseline = baseline_for(lease, kind)
    if str(data.get("baseline_id") or "") != (str(baseline.id) if baseline else ""):
        raise RentalConflict(
            "Review the current finalized move-in baseline.", code="baseline_changed"
        )
    check_revision(
        baseline.revision if baseline else 0, data.get("baseline_revision", 0)
    )
    evidence_ids = data.get("evidence_ids", [])
    if (
        not isinstance(evidence_ids, list)
        or len(evidence_ids) > 100
        or any(not isinstance(x, str) for x in evidence_ids)
        or len(set(evidence_ids)) != len(evidence_ids)
    ):
        raise ValidationError({"evidence_ids": "Use distinct evidence IDs."})
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=evidence_ids,
            lease=lease,
            malware_status="safe",
            deleted_at__isnull=True,
        )
    )
    if len(evidence) != len(evidence_ids):
        raise ValidationError(
            {"evidence_ids": "All evidence must be safe and belong to this lease."}
        )
    items = data.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 200:
        raise ValidationError({"items": "Supply between 1 and 200 inspection items."})
    ids = set()
    for item in items:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("id"), str)
            or not item["id"]
            or item["id"] in ids
        ):
            raise ValidationError(
                {"items": "Every item needs a distinct stable identifier."}
            )
        ids.add(item["id"])
        if item.get("kind") not in {"surface", "inventory", "meter", "key"} or item.get(
            "condition"
        ) not in {"notInspected", "unknown", "good", "worn", "damaged", "missing"}:
            raise ValidationError(
                {"items": "Unsupported inspection kind or condition."}
            )
        text_field(item, "space", required=True, limit=160)
        text_field(item, "label", required=True, limit=160)
        text_field(item, "note")
        if item["kind"] == "meter" and (
            not isinstance(item.get("reading"), str)
            or not re.fullmatch(r"\d+(?:\.\d+)?", item["reading"])
            or not item.get("unit")
        ):
            raise ValidationError(
                {
                    "reading": "Meter readings must be nonnegative decimal strings with units."
                }
            )
        if item["kind"] == "key" and (
            type(item.get("quantity")) is not int or not 0 <= item["quantity"] <= 10000
        ):
            raise ValidationError(
                {"quantity": "Key quantities must be nonnegative integers."}
            )
        if (
            not isinstance(item.get("evidence_ids", []), list)
            or any(not isinstance(x, str) for x in item.get("evidence_ids", []))
            or not set(item.get("evidence_ids", [])).issubset(evidence_ids)
        ):
            raise ValidationError(
                {
                    "evidence_ids": "Item evidence must be included in the report evidence."
                }
            )
    return {
        "kind": kind,
        "inspected_on": civil_date(data.get("inspected_on"), "inspected_on"),
        "selection": expected_selection,
        "items": items,
        "baseline": baseline,
        "baseline_revision": baseline.revision if baseline else 0,
        "baseline_snapshot": report_snapshot(baseline) if baseline else {},
    }, evidence
