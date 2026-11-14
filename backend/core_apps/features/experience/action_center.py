"""Current authorized projections, sorted before pagination. Never replay work."""

from core_apps.features.http import ActionPolicy, FeatureAPIView

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from ..pagination import FeaturePagination
from ..renderers import FeatureJsonRenderer
from .access import require, scope_for, enabled


def deadline(value):
    if not value:
        return None
    if isinstance(value, datetime):
        result = value
    else:
        result = parse_datetime(str(value))
        if result is None:
            date = parse_date(str(value))
            result = (
                datetime.combine(date, time.max, ZoneInfo("Africa/Cairo"))
                if date
                else None
            )
    return (
        timezone.make_aware(result) if result and timezone.is_naive(result) else result
    )


def ordering(item, now):
    due = deadline(item.get("due_at"))
    rank = (
        3
        if due is None
        else 0 if due < now else 1 if due <= now + timedelta(hours=24) else 2
    )
    return rank, due or datetime.max.replace(tzinfo=ZoneInfo("UTC")), item["id"]


def rows(request):
    scope = scope_for(request)
    user = request.user
    result = []

    def add(
        kind,
        identity,
        *,
        title="",
        revision=0,
        actor="",
        actionable=False,
        due=None,
        target=None,
        reason="",
        status="",
        **fields,
    ):
        result.append(
            {
                "id": f"{kind}:{identity}",
                "kind": kind,
                "resource_id": str(identity),
                "target_id": str(target or identity),
                "revision": revision,
                "title": title,
                "next_actor": actor,
                "reason": reason,
                "status": status,
                "bucket": "required" if actionable else "waiting",
                "due_at": deadline(due).isoformat() if deadline(due) else None,
                **fields,
            }
        )

    from core_apps.profiles.services.profile_service import ProfileService

    if ProfileService.calculate_profile_completion(user) < 100:
        add(
            "profile", user.id, actor="self", actionable=True, reason="complete_profile"
        )

    if scope.startswith("company/"):
        from ..services.company.access import company_for
        from ..services.company.role_work import rows as company_rows, SECTIONS

        company = company_for(user, scope.split("/")[1])
        role = scope.split("/")[2]
        from ..services.company.approval_routing import work_items, work_payload

        for item in work_items(user, company):
            work = work_payload(item, user)
            add(
                "company_work",
                item.id,
                title=work["title"],
                revision=work["revision"],
                actionable=work["actionable"],
                actor=role,
                target=work["request_id"],
                due=work["due_at"],
                reason=work["blocking_reason"] or work["action"],
                status=work["status"],
                target_kind="request",
                company_id=str(company.id),
                company_role=role,
            )
        from ..services.company import tenancy_access, tenancy_projection

        for tenancy in tenancy_access.visible(user, company_id=company.id).filter(
            lease__status__in=["draft", "pending_signatures"]
        ):
            value = tenancy_projection.payload(tenancy, user)
            primary = next(
                (
                    action
                    for action in ("submit_signature", "sign")
                    if action in value["actions"]
                ),
                "",
            )
            if (
                not primary
                and "review" in value["actions"]
                and role not in value.get("reviewed_roles", [])
            ):
                primary = "review"
            add(
                "company_work",
                tenancy.id,
                title=value["title"],
                revision=value["revision"],
                actionable=bool(primary),
                actor=role if primary else "other",
                target=tenancy.id,
                reason=primary
                or ((value.get("blocking_reasons") or ["waiting_for_contract"])[0]),
                status=value["state"],
                target_kind="tenancy",
                company_id=str(company.id),
                company_role=role,
            )
        seen = set()
        for section in sorted(
            SECTIONS.get(role, set()) - {"history", "decisions"},
            key=lambda value: (value != "tasks", value),
        ):
            for row in company_rows(user, company, section):
                identity = (row["target_kind"], row["id"])
                if identity in seen:
                    continue
                actionable, due, revision = section == "tasks", None, 0
                reason = row.get("action", "")
                if row["target_kind"] == "invoice":
                    from ..models import RentInvoice
                    from ..services.rental_phase3 import (
                        invoice_balance_minor,
                        invoice_payment_allowed,
                    )

                    invoice = (
                        RentInvoice.objects.select_related("lease")
                        .filter(id=row["target_id"], lease__renter_company=company)
                        .first()
                    )
                    if (
                        not invoice
                        or invoice.status in {"paid", "cancelled", "void"}
                        or invoice_balance_minor(invoice) <= 0
                    ):
                        continue
                    actionable = invoice_payment_allowed(user, invoice)
                    due, revision = invoice.due_date, invoice.revision
                    reason = "pay_invoice" if actionable else "payment_not_ready"
                elif section != "tasks" and row["state"] in {
                    "completed",
                    "cancelled",
                    "canceled",
                    "rejected",
                    "withdrawn",
                    "applied",
                }:
                    continue
                seen.add(identity)
                add(
                    "company_work",
                    row["id"],
                    title=row["title"],
                    actionable=actionable,
                    actor=role,
                    due=due,
                    revision=revision,
                    target=row["target_id"],
                    reason=reason,
                    status=row["state"],
                    target_kind=row["target_kind"],
                    company_id=str(company.id),
                    company_role=role,
                )
    else:
        from ..models import Lease, PrivateAccessRevocation, MaintenanceRequest
        from ..services.rental_lifecycle.journey import lease_journey
        from ..services.cycle_permissions import cycle_actions
        from core_apps.properties.models import PropertyVisit, Property

        role = "owner" if scope == "owner" else "tenant"
        leases = (
            Lease.objects.filter(
                **{role: user},
                **({} if role == "owner" else {"renter_company__isnull": True}),
            )
            .exclude(
                pk__in=PrivateAccessRevocation.objects.filter(user=user).values(
                    "lease_id"
                )
            )
            .select_related("owner", "tenant", "property")
        )
        for lease in leases:
            journey = lease_journey(lease, user)
            action = journey["next_action"]
            if not journey["complete"] and action:
                actor = journey["next_actor"]
                add(
                    "rental",
                    lease.id,
                    title=lease.property.title,
                    revision=lease.revision,
                    actor=actor,
                    actionable=actor in {role, "both"},
                    due=journey["deadline"],
                    reason=action["action"],
                    status=lease.status,
                )
        for item in (
            MaintenanceRequest.objects.filter(lease__in=leases)
            .exclude(status__in=["resolved", "cancelled"])
            .select_related("lease")
        ):
            actions = cycle_actions(user, item)
            add(
                "maintenance",
                item.id,
                title=item.title,
                revision=item.revision,
                target=item.lease.id,
                actionable=bool(actions),
                actor=role if actions else "other",
                status=item.status,
            )
        visits = PropertyVisit.objects.filter(
            status__in=["pending", "confirmed"]
        ).select_related("property")
        visits = (
            visits.filter(property__owner=user)
            if role == "owner"
            else visits.filter(
                tenant=user, company__isnull=True, renter_workspace=scope
            )
        )
        for visit in visits:
            due = (
                datetime.combine(
                    visit.visit_date, visit.visit_time, ZoneInfo("Africa/Cairo")
                )
                if visit.visit_date and visit.visit_time
                else None
            )
            if visit.status == "confirmed" and due and due < timezone.now():
                continue
            add(
                "visit",
                visit.id,
                title=visit.property.title,
                revision=visit.revision,
                actor="owner" if visit.status == "pending" else "both",
                actionable=role == "owner" or visit.status == "confirmed",
                due=due,
                reason="confirm_visit" if visit.status == "pending" else "attend_visit",
                status=visit.status,
            )
        if scope == "owner":
            for item in Property.objects.filter(
                owner=user, status__in=["under_review", "needs_revision"]
            ):
                add(
                    "property",
                    item.id,
                    title=item.title,
                    actionable=item.status == "needs_revision",
                    actor="owner" if item.status == "needs_revision" else "reviewer",
                    status=item.status,
                    revision=getattr(item, "revision", 0),
                )
        if scope == "student":
            from ..services.student_housing.access import plans_for
            from ..services.student_housing.plans import payload

            for plan in plans_for(user).filter(status="planning"):
                value = payload(plan, user)
                step = value["next_step"]
                add(
                    "student_plan",
                    plan.id,
                    title=value.get("label", value.get("title", "")),
                    revision=plan.revision,
                    actor=step["waiting_for"],
                    actionable=step["waiting_for"] == "self",
                    reason=step["reason"],
                    status=plan.status,
                )
    if enabled("preparation"):
        from .models import PreparationTask

        if scope == "student":
            tasks = PreparationTask.objects.filter(
                group__status="active",
                group__memberships__user=user,
                group__memberships__status="active",
                assignee=user,
            ).distinct()
            tasks = [
                t
                for t in tasks
                if t.group.memberships.filter(
                    user=user, status="active", joined_revision=t.membership_period
                ).exists()
            ]
        elif scope.startswith("company/"):
            tasks = PreparationTask.objects.filter(
                company_request__company__id=scope.split("/")[1], assignee=user
            )
        else:
            tasks = []
        for task in tasks:
            if task.status in {"completed", "cancelled"}:
                continue
            add(
                "preparation",
                task.id,
                title=task.title,
                revision=task.revision,
                actor="self",
                actionable=True,
                due=task.due_at,
                status=task.status,
                group_id=str(task.group.id) if task.group_id else "",
                request_id=(
                    str(task.company_request.id) if task.company_request_id else ""
                ),
            )
    return sorted(result, key=lambda item: ordering(item, timezone.now()))


class ActionCenterView(FeatureAPIView):
    name = "Action Center"
    http_method_names = ["get", "options"]
    permission_classes = [IsAuthenticated]
    renderer_classes = [FeatureJsonRenderer]
    action_policies = {
        "get": ActionPolicy(
            "action_center",
            "action_center",
            boundary="standard",
            capability=None,
            typed=False,
        ),
    }

    def get(self, request):
        require("action_center")
        items = rows(request)
        bucket = request.query_params.get("bucket", "required")
        if bucket not in {"required", "waiting", "all"}:
            raise ValidationError("Unknown action center tab.")
        counts = {
            key: sum(row["bucket"] == key for row in items)
            for key in ("required", "waiting")
        }
        page = FeaturePagination()
        values = (
            items
            if bucket == "all"
            else [item for item in items if item["bucket"] == bucket]
        )
        response = page.get_paginated_response(page.paginate_queryset(values, request))
        response.data["counts"] = counts
        response.data["generated_at"] = timezone.now().isoformat()
        return response


# Stable callable import for integrations; URLs use the explicit class.
action_center = ActionCenterView.as_view()
