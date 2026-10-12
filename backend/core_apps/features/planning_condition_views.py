import re
import uuid

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Lease, PrivateAccessRevocation, RentalEvidence
from .planning_models import ConditionReport
from .rental_phase4_views import evidence_payload
from .services.planning import (
    check_revision,
    civil_date,
    display_name,
    mutate,
    page,
    planning_api,
    selection_payload,
    text_field,
)
from .services.rental_phase2 import RentalConflict


def participant_lease(user, identifier, *, lock=False):
    queryset = Lease.objects.filter(Q(owner=user) | Q(tenant=user))
    if lock:
        queryset = queryset.select_for_update()
    lease = get_object_or_404(queryset, id=identifier)
    if PrivateAccessRevocation.objects.filter(lease=lease, user=user).exists():
        raise NotFound()
    return lease


def report_actions(user, report):
    if (
        user.pk not in {report.lease.owner_id, report.lease.tenant_id}
        or report.lease.legacy_read_only
    ):
        return []
    if report.status in {"draft", "changes_requested"}:
        return ["submit"] if report.author_id == user.pk else []
    if report.status == "submitted":
        return ["acknowledge", "object"] if report.author_id != user.pk else []
    if report.status == "acknowledged":
        return ["finalize", "object"]
    return []


def report_payload(item, user):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "kind": item.kind,
        "status": item.status,
        "revision": item.revision,
        "inspected_on": str(item.inspected_on),
        "selection": item.selection,
        "items": item.items,
        "evidence": [evidence_payload(x) for x in item.evidence.all()],
        "acknowledgements": item.acknowledgements,
        "baseline_id": str(item.baseline.id) if item.baseline_id else "",
        "baseline_revision": item.baseline_revision,
        "baseline_items": item.baseline.items if item.baseline_id else [],
        "history": item.history,
        "allowed_actions": report_actions(user, item),
        "blocking_reasons": [],
    }


def report_for(user, identifier, *, lock=False):
    item = get_object_or_404(ConditionReport, id=identifier)
    lease = participant_lease(user, item.lease.id, lock=lock)
    return get_object_or_404(
        (
            ConditionReport.objects.select_for_update()
            if lock
            else ConditionReport.objects.all()
        ),
        pk=item.pk,
        lease=lease,
    )


def baseline_for(lease, kind):
    return (
        lease.condition_reports.filter(kind="move_in", status="final")
        .order_by("-created_at")
        .first()
        if kind == "move_out"
        else None
    )


def lease_selection(lease):
    result = {
        "property_id": str(lease.property.id),
        **(lease.offer_snapshot or {}),
        "offer_id": lease.offer_id,
    }
    result["bed_id"] = result.get("bed_id") or ""
    result["bed_name"] = result.get("bed_name") or ""
    return selection_payload(result)


@planning_api(["GET"], "condition_reports")
def condition_report_context(request, lease_id):
    lease = participant_lease(request.user, lease_id)
    if lease.legacy_read_only or not lease.offer_id:
        raise RentalConflict(
            "Reconcile legacy accommodation before creating condition reports."
        )
    kind = request.query_params.get(
        "kind", "move_out" if lease.occupancy_status == "occupied" else "move_in"
    )
    if kind not in {"move_in", "move_out"}:
        raise ValidationError({"kind": "Use move_in or move_out."})
    selection = lease_selection(lease)
    baseline = baseline_for(lease, kind)
    rooms = list(
        zip(selection.get("room_ids", []), selection.get("room_names", []))
    ) or [(str(lease.property.id), lease.property.title)]
    items = [
        {
            "id": str(uuid.uuid5(lease.id, f"surface:{identifier}")),
            "space": name,
            "label": "Walls and floors",
            "kind": "surface",
            "condition": "notInspected",
            "note": "",
            "reading": "",
            "unit": "",
            "quantity": None,
            "evidence_ids": [],
        }
        for identifier, name in rooms
    ]
    if baseline:
        items = [
            {**x, "condition": "notInspected", "note": "", "evidence_ids": []}
            for x in baseline.items
        ]
    return Response(
        {
            "id": "",
            "lease_id": str(lease.id),
            "kind": kind,
            "status": "draft",
            "revision": 0,
            "inspected_on": str(timezone.localdate()),
            "selection": selection,
            "items": items,
            "evidence": [],
            "acknowledgements": [],
            "baseline_id": str(baseline.id) if baseline else "",
            "baseline_revision": baseline.revision if baseline else 0,
            "baseline_items": baseline.items if baseline else [],
            "history": [],
            "allowed_actions": ["create"],
            "blocking_reasons": [],
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
    }, evidence


def _acknowledgement(user, revision, status="accepted", note=""):
    return {
        "user_id": str(user.id),
        "name": display_name(user),
        "status": status,
        "revision": revision,
        "note": note,
    }


@planning_api(["GET", "POST"], "condition_reports")
def condition_reports(request, lease_id):
    lease = participant_lease(request.user, lease_id)
    if request.method == "GET":
        return page(
            request,
            lease.condition_reports.order_by("-created_at", "pkid"),
            lambda x: report_payload(x, request.user),
        )

    def apply(lease, revision):
        if request.data.get("action") != "submit":
            raise ValidationError({"action": "Use submit to create a report."})
        values, evidence = _report_values(lease, request.data)
        item = ConditionReport.objects.create(
            lease=lease,
            author=request.user,
            acknowledgements=[_acknowledgement(request.user, 1)],
            history=["Report submitted."],
            **values,
        )
        item.evidence.set(evidence)
        return item

    return mutate(
        request,
        f"condition.create.{lease_id}",
        lambda: participant_lease(request.user, lease_id, lock=True),
        apply,
        lambda x: report_payload(x, request.user),
        creating=True,
    )


@planning_api(["GET"], "condition_reports")
def condition_report_detail(request, report_id):
    return Response(report_payload(report_for(request.user, report_id), request.user))


@planning_api(["POST"], "condition_reports")
def condition_report_action(request, report_id, action):
    def apply(item, revision):
        if action not in report_actions(request.user, item):
            raise PermissionDenied("This report action is not available to you.")
        if request.data.get("action") != action or str(
            request.data.get("lease_id")
        ) != str(item.lease.id):
            raise ValidationError("Action and lease must match the report.")
        if action == "submit":
            values, evidence = _report_values(item.lease, request.data)
            if values["kind"] != item.kind:
                raise ValidationError({"kind": "The report kind cannot change."})
            item.versions.append(
                {
                    "revision": item.revision,
                    "content_revision": item.content_revision,
                    "items": item.items,
                    "acknowledgements": item.acknowledgements,
                }
            )
            for key, value in values.items():
                setattr(item, key, value)
            item.evidence.set(evidence)
            item.content_revision += 1
            item.acknowledgements = [
                _acknowledgement(request.user, item.content_revision)
            ]
            item.status = "submitted"
        elif action == "object":
            note = text_field(request.data, "objection", required=True)
            item.acknowledgements = [
                _acknowledgement(request.user, item.content_revision, "objected", note)
            ]
            item.status = "changes_requested"
        elif action == "acknowledge":
            # Full client bodies cannot edit inspected facts while acknowledging.
            if request.data.get("items") != item.items or selection_payload(
                request.data.get("selection") or {}
            ) != selection_payload(item.selection):
                raise RentalConflict(
                    "Acknowledgement must refer to the persisted report content.",
                    code="report_changed",
                )
            item.acknowledgements = [
                x for x in item.acknowledgements if x["user_id"] != str(request.user.id)
            ] + [_acknowledgement(request.user, item.content_revision)]
            if {str(item.lease.owner.id), str(item.lease.tenant.id)}.issubset(
                {
                    x["user_id"]
                    for x in item.acknowledgements
                    if x["status"] == "accepted"
                    and x["revision"] == item.content_revision
                }
            ):
                item.status = "acknowledged"
        elif action == "finalize":
            item.status = "final"
        item.history.append(
            f"{action} by {display_name(request.user)} at revision {item.revision + 1}."
        )
        item.revision += 1
        item.save()
        return item

    return mutate(
        request,
        f"condition.{action}.{report_id}",
        lambda: report_for(request.user, report_id, lock=True),
        apply,
        lambda x: report_payload(x, request.user),
    )
