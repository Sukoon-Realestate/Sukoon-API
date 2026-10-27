"""Planning condition views: condition report context."""

import re
import uuid
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import get_language
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from core_apps.common.translation import translate_message
from ..models import Lease, PrivateAccessRevocation
from ..planning_models import ConditionReport
from ..rental_phase4_views import evidence_payload
from ..services.planning import display_name, planning_api, selection_payload
from ..services.rental_phase2 import RentalConflict


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
    if report.status == "final":
        return ["addendum"]
    return []


def report_history_label(value):
    # Localize generated audit text on read; preserve stored history and names.
    if (get_language() or "en").startswith("ar"):
        match = re.fullmatch(
            r"(submit|object|acknowledge|finalize) by (.+) at revision ([0-9]+)\.",
            value,
            flags=re.DOTALL,
        )
        if match:
            action, name, revision = match.groups()
            labels = {
                "submit": "إرسال التقرير",
                "object": "تسجيل اعتراض",
                "acknowledge": "قبول التقرير",
                "finalize": "اعتماد التقرير النهائي",
            }
            return f"{labels[action]} بواسطة {name} في النسخة {revision}."
    return translate_message(value)


def report_payload(item, user):
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "kind": item.kind,
        "status": item.status,
        "revision": item.revision,
        "content_revision": item.content_revision,
        "inspected_on": str(item.inspected_on),
        "selection": item.selection,
        "items": item.items,
        "evidence": [evidence_payload(x) for x in item.evidence.all()],
        "acknowledgements": item.acknowledgements,
        "baseline_id": str(item.baseline.id) if item.baseline_id else "",
        "baseline_revision": item.baseline_revision,
        "baseline_items": item.baseline_snapshot.get(
            "items", item.baseline.items if item.baseline_id else []
        ),
        "versions": item.versions,
        "objections": item.objections,
        "supersedes_id": str(item.supersedes.id) if item.supersedes_id else "",
        "history": [report_history_label(value) for value in item.history],
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
            "label": translate_message("Walls and floors"),
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
            {
                **x,
                "condition": "notInspected",
                "note": "",
                "reading": "",
                "quantity": None,
                "evidence_ids": [],
            }
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


def _acknowledgement(user, revision, status="accepted", note=""):
    return {
        "user_id": str(user.id),
        "name": display_name(user),
        "status": status,
        "revision": revision,
        "note": note,
        "at": timezone.now().isoformat(),
    }
