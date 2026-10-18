"""Report, independently assess and clear only the affected physical scope."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.properties.models import Property
from ...models import (
    HabitabilityRestriction,
    RentalOperationalCase,
    RentalEvidence,
    Lease,
)
from ..policy_registry import approved_policy
from ..rental_phase2 import RentalConflict
from .common import audit, require_revision, staff_role
from .inventory import unit_keys, ensure_units


def report(case, data):
    keys = unit_keys(case.property, case.lease.offer_snapshot)
    selected = data.get("physical_keys") or keys
    if not set(selected).issubset(keys):
        raise ValidationError(
            {"physical_keys": "Report only accommodation covered by this agreement."}
        )
    started = data.get("reported_started_at")
    if started and started > timezone.now():
        raise ValidationError(
            {"reported_started_at": "The reported onset cannot be in the future."}
        )
    labels = {f"property:{case.property.id}": case.property.title}
    for room in (case.property.rental_inventory or {}).get("rooms", []):
        labels[f"room:{room['id']}"] = room.get("name") or case.property.title
        for bed in room.get("beds", []):
            labels[f"bed:{bed['id']}"] = (
                " · ".join(filter(None, [room.get("name"), bed.get("name")]))
                or case.property.title
            )
    case.baseline = {
        **case.baseline,
        "habitability": {
            "scope_labels": [
                labels.get(key, case.property.title) for key in sorted(set(selected))
            ],
            "status": "reported",
            "reported_started_at": started.isoformat() if started else None,
            "received_at": timezone.now().isoformat(),
            "reported_severity": data.get("reported_severity", "unassessed"),
            "assessed_severity": None,
            "physical_keys": sorted(set(selected)),
            "assessment_policy": None,
            "financial_status": "awaiting_policy",
            "financial_policy": None,
            "alternative_accommodation": "not_committed",
        },
    }
    case.next_action = "Assign a qualified assessor under the approved habitability policy. No financial adjustment has been authorized."
    case.save(update_fields=["baseline", "next_action", "updated_at"])


def authorize_assessment(case, actor, action):
    from core_apps.users.models import User
    from core_apps.admin_api.models import StaffProfile

    current = User.objects.select_for_update().get(pk=actor.pk)
    StaffProfile.objects.select_for_update().filter(user=current).first()
    policy = approved_policy("D29", "habitability." + action)
    roles = policy.rules.get("assessor_roles", [])
    if (
        not roles
        or not staff_role(current, roles)
        or case.assigned_to_id != current.pk
        or current.pk in {case.opened_by_id, case.lease.owner_id, case.lease.tenant_id}
    ):
        raise PermissionDenied(
            "An independent current assessor assigned to this case is required."
        )
    return current, policy


def restricted_keys(prop):
    return set(
        HabitabilityRestriction.objects.filter(
            unit__property=prop, cleared_at__isnull=True
        ).values_list("unit__physical_key", flat=True)
    )


def offer_restricted(prop, snapshot, keys=None):
    keys = restricted_keys(prop) if keys is None else keys
    return bool(keys and set(unit_keys(prop, snapshot)) & keys)


def assert_habitable(prop, snapshot):
    if offer_restricted(prop, snapshot):
        raise RentalConflict(
            "This accommodation requires an authorized habitability clearance.",
            code="habitability_restricted",
        )


@transaction.atomic
def assess(actor, case, data):
    Property.objects.select_for_update().get(pk=case.property_id)
    case = (
        RentalOperationalCase.objects.select_for_update(of=("self",))
        .select_related("lease", "property")
        .get(pk=case.pk)
    )
    require_revision(case, data["expected_revision"])
    state = dict(case.baseline.get("habitability", {}))
    if not state or case.kind != "habitability":
        raise ValidationError("This is not a habitability report.")
    action = data["action"]
    current, policy = authorize_assessment(case, actor, action)
    keys = data["physical_keys"]
    if not keys or not set(keys).issubset(state["physical_keys"]):
        raise ValidationError(
            {"physical_keys": "Inspect only the reported physical scope."}
        )
    evidence = list(
        RentalEvidence.objects.filter(
            id__in=data["evidence_ids"],
            lease=case.lease,
            malware_status="safe",
            deleted_at__isnull=True,
        )
    )
    # An operator must already have a current evidence grant through this case.
    allowed = set(case.evidence.values_list("pk", flat=True))
    if (
        not evidence
        or len(evidence) != len(set(data["evidence_ids"]))
        or any(item.pk not in allowed for item in evidence)
    ):
        raise ValidationError(
            {
                "evidence_ids": "Use clean inspection evidence already authorized for this case."
            }
        )
    now = timezone.now()
    if action == "restrict":
        review_at = data.get("review_at")
        if not review_at or review_at <= now:
            raise ValidationError(
                {
                    "review_at": "An explicit future review appointment is required; it does not reopen inventory."
                }
            )
        for unit in ensure_units(case.property, case.lease.offer_snapshot):
            if unit.physical_key in keys:
                restriction, _ = HabitabilityRestriction.objects.get_or_create(
                    case=case,
                    unit=unit,
                    cleared_at__isnull=True,
                    defaults={
                        "policy": policy,
                        "assessed_by": current,
                        "restricted_at": now,
                        "review_at": review_at,
                    },
                )
                restriction.inspection_evidence.add(*evidence)
        state.update(
            status="restricted_use",
            assessed_severity=data["assessed_severity"],
            assessment_policy=policy.version,
            assessed_at=now.isoformat(),
            review_at=review_at.isoformat(),
        )
        from .cases import open_system_case

        for lease in (
            Lease.objects.filter(property=case.property)
            .exclude(status__in=["expired", "cancelled"])
            .exclude(pk=case.lease_id)
        ):
            if set(unit_keys(case.property, lease.offer_snapshot)) & set(keys):
                impact = open_system_case(
                    kind="habitability_impact",
                    source_key=f"habitability-impact:{case.id}:{lease.id}",
                    lease=lease,
                    reason="An approved restriction affects accommodation in this agreement.",
                    next_action="Review accommodation and existing obligations. No refund or departure has been inferred.",
                )
                impact.baseline = {
                    **impact.baseline,
                    "incident_id": str(case.id),
                    "financial_status": "awaiting_policy",
                }
                impact.save(update_fields=["baseline", "updated_at"])
    elif action == "reopen":
        rows = HabitabilityRestriction.objects.select_for_update().filter(
            case=case, unit__physical_key__in=keys, cleared_at__isnull=True
        )
        if set(rows.values_list("unit__physical_key", flat=True)) != set(keys):
            raise RentalConflict(
                "Review the current restricted scope.", code="stale_revision"
            )
        for row in rows:
            row.cleared_at, row.cleared_by, row.clearance_policy = now, current, policy
            row.save(
                update_fields=[
                    "cleared_at",
                    "cleared_by",
                    "clearance_policy",
                    "updated_at",
                ]
            )
            row.inspection_evidence.add(*evidence)
        state["status"] = (
            "restricted_use"
            if case.habitability_restrictions.filter(cleared_at__isnull=True).exists()
            else "reopened"
        )
        state["clearance_at"] = now.isoformat()
    else:
        raise ValidationError({"action": "Use restrict or reopen."})
    case.baseline = {**case.baseline, "habitability": state}
    case.revision += 1
    case.save(update_fields=["baseline", "revision", "updated_at"])
    audit(
        case,
        current,
        "habitability." + action,
        data["reason"],
        {
            "policy_version": policy.version,
            "physical_keys": keys,
            "evidence_ids": [str(item.id) for item in evidence],
        },
    )
    from .cases import notify_case_participants

    notify_case_participants(case, "habitability." + action)
    return case


def projection(case):
    state = case.baseline.get("habitability")
    if not state:
        return None
    return {
        **state,
        "restricted_keys": list(
            case.habitability_restrictions.filter(cleared_at__isnull=True).values_list(
                "unit__physical_key", flat=True
            )
        ),
    }
