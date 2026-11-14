"""Planning condition views: condition report action."""

from core_apps.features.http import ActionPolicy, FeatureAPIView
from rest_framework.permissions import IsAuthenticated
from core_apps.features.renderers import FeatureJsonRenderer


import uuid
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from ..planning_models import ConditionReport
from ..services.planning import (
    check_revision,
    display_name,
    mutate,
    page,
    selection_payload,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from .condition_report_context import (
    participant_lease,
    report_actions,
    report_payload,
    report_for,
    _acknowledgement,
)
from .report_snapshot import _report_values, report_snapshot


class ConditionReportsView(FeatureAPIView):
    name = "Condition Reports"
    http_method_names = ["get", "post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "condition_report_action",
            "condition_reports",
            boundary="planning",
            capability="condition_reports",
            typed=False,
        ),
        "post": ActionPolicy(
            "condition_report_action",
            "condition_reports",
            boundary="planning",
            capability="condition_reports",
            typed=False,
        ),
    }

    def get(self, request, lease_id):
        lease = participant_lease(request.user, lease_id)
        return page(
            request,
            lease.condition_reports.order_by("-created_at", "pkid"),
            lambda x: report_payload(x, request.user),
        )

    def post(self, request, lease_id):
        participant_lease(request.user, lease_id)

        def apply(lease, revision):
            if request.data.get("action") != "submit":
                raise ValidationError({"action": "Use submit to create a report."})
            values, evidence = _report_values(lease, request.data)
            source = None
            if request.data.get("supersedes_id"):
                source = get_object_or_404(
                    ConditionReport.objects.select_for_update(),
                    lease=lease,
                    id=request.data["supersedes_id"],
                    status="final",
                    kind=values["kind"],
                )
                check_revision(source.revision, request.data.get("source_revision"))
                if source.addenda.exists():
                    raise RentalConflict(
                        "Continue the existing addendum before creating another."
                    )
            item = ConditionReport.objects.create(
                lease=lease,
                author=request.user,
                acknowledgements=[_acknowledgement(request.user, 1)],
                history=["Report submitted."],
                supersedes=source,
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


# Stable callable import for integrations; URLs use the explicit class.
condition_reports = ConditionReportsView.as_view()


class ConditionReportDetailView(FeatureAPIView):
    name = "Condition Report Detail"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "condition_report_action",
            "condition_report_detail",
            boundary="planning",
            capability="condition_reports",
            typed=False,
        ),
    }

    def get(self, request, report_id):
        return Response(
            report_payload(report_for(request.user, report_id), request.user)
        )


# Stable callable import for integrations; URLs use the explicit class.
condition_report_detail = ConditionReportDetailView.as_view()


class ConditionReportActionView(FeatureAPIView):
    name = "Condition Report Action"
    http_method_names = ["post", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "post": ActionPolicy(
            "condition_report_action",
            "condition_report_action",
            boundary="planning",
            capability="condition_reports",
            typed=False,
        ),
    }

    def post(self, request, report_id, action):
        def apply(item, revision):
            if action not in report_actions(request.user, item):
                raise PermissionDenied("This report action is not available to you.")
            if request.data.get("action") != action or str(
                request.data.get("lease_id")
            ) != str(item.lease.id):
                raise ValidationError("Action and lease must match the report.")
            if action == "addendum":
                raise ValidationError(
                    "Submit a new report with supersedes_id and source_revision."
                )
            item.versions.append(report_snapshot(item))
            if action == "submit":
                values, evidence = _report_values(item.lease, request.data)
                if values["kind"] != item.kind:
                    raise ValidationError({"kind": "The report kind cannot change."})
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
                item_id = text_field(request.data, "objection_item_id", limit=100)
                if item_id and not any(x["id"] == item_id for x in item.items):
                    raise ValidationError(
                        {
                            "objection_item_id": "Select an item from this report version."
                        }
                    )
                objection = {
                    **_acknowledgement(
                        request.user, item.content_revision, "objected", note
                    ),
                    "id": str(uuid.uuid4()),
                    "item_id": item_id,
                }
                item.objections.append(objection)
                item.acknowledgements = [
                    x
                    for x in item.acknowledgements
                    if x["user_id"] != str(request.user.id)
                ] + [
                    _acknowledgement(
                        request.user, item.content_revision, "objected", note
                    )
                ]
                item.status = "changes_requested"
            elif action == "acknowledge":
                # Full client bodies cannot edit inspected facts while acknowledging.
                expected_selection = selection_payload(item.selection)
                acknowledged_selection = selection_payload(
                    request.data.get("selection") or {}
                )
                # Ancestry is server-owned provenance, absent from the mobile
                # accommodation model. Omission must not invalidate an unchanged
                # report; a supplied conflicting value is still rejected below.
                if "reputation_ancestry" in expected_selection:
                    acknowledged_selection.setdefault(
                        "reputation_ancestry", expected_selection["reputation_ancestry"]
                    )
                if (
                    request.data.get("items") != item.items
                    or sorted(request.data.get("evidence_ids", []))
                    != sorted(
                        str(x) for x in item.evidence.values_list("id", flat=True)
                    )
                    or request.data.get("inspected_on") != str(item.inspected_on)
                    or acknowledged_selection != expected_selection
                ):
                    raise RentalConflict(
                        "Acknowledgement must refer to the persisted report content.",
                        code="report_changed",
                    )
                item.acknowledgements = [
                    x
                    for x in item.acknowledgements
                    if x["user_id"] != str(request.user.id)
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


# Stable callable import for integrations; URLs use the explicit class.
condition_report_action = ConditionReportActionView.as_view()
