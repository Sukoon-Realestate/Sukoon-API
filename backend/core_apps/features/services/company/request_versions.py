"""Version the need without rewriting a reviewed package or an agreement."""

import json
from datetime import date

from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.utils import timezone

from ...company_models import CompanyRequestVersion, CompanyBudgetReservation
from ...company_contract_models import CompanyContractPreparation
from ...planning_models import PlanningEvent
from ..rental_lifecycle.common import audit
from ..rental_phase2 import RentalConflict


MATERIAL_FIELDS = {
    "purpose",
    "cost_center",
    "location",
    "project_code",
    "worksite_latitude",
    "worksite_longitude",
    "requirements",
    "starts_on",
    "ends_on_exclusive",
    "headcount",
}
TERMINAL_PACKAGES = {"withdrawn", "replaced", "rejected"}


def content(request):
    from .bookings import REQUEST_FIELDS

    return json.loads(
        json.dumps(
            {key: getattr(request, key) for key in REQUEST_FIELDS},
            cls=DjangoJSONEncoder,
        )
    )


def record_initial(request, actor, *, baseline=False):
    # A baseline records only the current source, never invented past revisions.
    return CompanyRequestVersion.objects.get_or_create(
        request=request,
        version=request.commercial_revision,
        defaults={"actor": actor, "content": content(request), "baseline": baseline},
    )[0]


def period(item):
    try:
        return (
            date.fromisoformat(item.snapshot["starts_on"]),
            date.fromisoformat(item.snapshot["ends_on_exclusive"]),
        )
    except (KeyError, ValueError, TypeError):
        raise RentalConflict(
            "Review a package with a complete rental interval.", code="package_changed"
        )


def require_current(item):
    if item.request_review_version is not None:
        raise RentalConflict(
            "The housing need changed. Review and replace this affected package.",
            code="company_request_changed",
        )


def notify(request, user, version):
    PlanningEvent.objects.get_or_create(
        recipient=user,
        event_key=f"company.request:{request.id}:{version}",
        defaults={
            "destination": {
                "action_type": "open_company_request",
                "target_id": str(request.id),
                "company_id": str(request.company.id),
                "company_role": (
                    "coordinator" if user.pk == request.coordinator_id else "approver"
                ),
                "revision": request.revision,
                "content_version": version,
                "schema_version": "1",
                "workspace": "company",
            }
        },
    )


def apply(request, actor, before):
    after = content(request)
    changes = {
        key: {"from": before[key], "to": value}
        for key, value in after.items()
        if before[key] != value
    }
    if not changes:
        return None
    request.commercial_revision += 1
    request.revision += 1
    request.save()
    packages = list(
        request.items.select_for_update(of=("self",)).select_related("hold", "lease")
    )
    # Budget history is retained. Expired, uncommitted approvals do not consume
    # the new ceiling; a live inventory hold is released only by its lifecycle.
    reservations = CompanyBudgetReservation.objects.filter(
        item__request=request,
        status__in=["reserved", "committed"],
    ).exclude(
        status="reserved",
        approval__expires_at__lte=timezone.now(),
        item__lease__isnull=True,
    )
    from .listing_changes import live_budget

    totals = live_budget(reservations).aggregate(
        rent=Sum("rent_minor"), deposit=Sum("deposit_minor")
    )
    rent_exceeded = (totals["rent"] or 0) > request.commitment_ceiling_minor
    deposit_exceeded = (totals["deposit"] or 0) > request.deposit_limit_minor
    affected, preserved = [], []
    recipients = {
        request.requester_id: request.requester,
        request.coordinator_id: request.coordinator,
    }
    for item in packages:
        if (
            item.lease_id
            or item.invitation_id
            or (
                item.hold_id
                and (
                    item.hold.lease_id
                    or item.hold.status in {"committed", "reconciliation_pending"}
                )
            )
        ):
            preserved.append(str(item.id))
            continue
        if item.status in TERMINAL_PACKAGES:
            continue
        material = bool(MATERIAL_FIELDS.intersection(changes))
        budget = (
            "commitment_ceiling_minor" in changes
            and (
                rent_exceeded
                or item.full_term_rent_minor > request.commitment_ceiling_minor
            )
        ) or (
            "deposit_limit_minor" in changes
            and (deposit_exceeded or item.deposit_minor > request.deposit_limit_minor)
        )
        if not material and not budget:
            continue
        item.status = "request_changed"
        item.request_review_version = request.commercial_revision
        item.revision += 1
        item.save(
            update_fields=["status", "request_review_version", "revision", "updated_at"]
        )
        CompanyBudgetReservation.objects.filter(item=item, status="reserved").update(
            status="released"
        )
        affected.append(str(item.id))
        if item.assigned_approver_id:
            recipients[item.assigned_approver.user_id] = item.assigned_approver.user
        preparation = (
            CompanyContractPreparation.objects.select_for_update()
            .filter(booking=item)
            .first()
        )
        if preparation and preparation.state != "withdrawn":
            preparation.state = "changes_requested"
            preparation.revision += 1
            preparation.save(update_fields=["state", "revision", "updated_at"])
            from .contract_preparation import notify as notify_preparation

            notify_preparation(preparation)
        audit(
            item,
            actor,
            "company_package_request_changed",
            metadata={
                "request_version": request.commercial_revision,
                "changed_fields": sorted(changes),
            },
        )
    version = CompanyRequestVersion.objects.create(
        request=request,
        version=request.commercial_revision,
        actor=actor,
        content=after,
        changes=changes,
        affected_item_ids=affected,
        preserved_item_ids=preserved,
    )
    audit(
        request,
        actor,
        "company_housing_request_updated",
        metadata={
            "content_version": version.version,
            "changes": changes,
            "affected_item_ids": affected,
            "preserved_item_ids": preserved,
        },
    )
    for recipient in recipients.values():
        notify(request, recipient, version.version)
    return version


def history(request, visible_item_ids=None):
    def visible(values):
        return (
            values
            if visible_item_ids is None
            else [value for value in values if value in visible_item_ids]
        )

    return [
        {
            "version": row.version,
            "created_at": row.created_at.isoformat(),
            "actor_name": row.actor.get_full_name,
            "baseline": row.baseline,
            "changes": row.changes,
            "affected_item_ids": visible(row.affected_item_ids),
            "preserved_item_ids": visible(row.preserved_item_ids),
        }
        for row in request.versions.select_related("actor").order_by("-version")
    ]
