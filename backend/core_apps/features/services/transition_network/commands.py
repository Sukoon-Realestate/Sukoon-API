from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ...models import Lease
from ...planning_models import TenancyTransition
from ...transition_network_models import MoveIntent, TransitionMatchRun
from ..planning import criteria
from ..rental_phase2 import RentalConflict


def own_lease(user, identifier, *, lock=False):
    rows = Lease.objects.select_related(
        "property__city", "property__owner", "property__property_type"
    )
    if lock:
        rows = rows.select_for_update(of=("self",))
    return get_object_or_404(rows, id=identifier, tenant=user, legacy_read_only=False)


def source_for(user, lease, identifier, *, lock=False):
    rows = TenancyTransition.objects.filter(lease=lease, kind="replacement")
    if lock:
        rows = rows.select_for_update()
    return get_object_or_404(rows, id=identifier)


def check_source(item, *, publishing=False):
    lease, source = item.lease, item.source_transition
    if (
        lease.tenant_id != item.user_id
        or lease.owner_id != lease.property.owner_id
        or lease.legacy_read_only
        or not lease.offer_id
        or lease.status not in {"active", "termination_pending", "ended"}
        or source.lease_id != lease.pk
        or source.status in {"withdrawn", "declined", "cancelled", "expired"}
    ):
        raise RentalConflict(
            "The outgoing relationship needs a new review.", code="snapshot_stale"
        )
    if source.requested_on < lease.end_date:
        raise RentalConflict(
            "A supported contract change is needed before an earlier move.",
            code="outgoing_change_required",
        )
    occupants = (lease.terms or {}).get("occupants")
    if type(occupants) is not int or occupants != 1:
        raise RentalConflict(
            "Additional or unconfirmed occupants require assisted review.",
            code="source_occupants_review_required",
        )
    if publishing and not source.availability_approved:
        raise RentalConflict(
            "The owner must approve the existing replacement availability first.",
            code="owner_review_required",
        )


def bounded_integer(data, key, low, high):
    value = data.get(key)
    if type(value) is not int or not low <= value <= high:
        raise ValidationError({key: "Use an integer within the supported range."})
    return value


def apply_requirements(item, data):
    if str(data.get("lease_id")) != str(item.lease.id) or str(
        data.get("source_transition_id")
    ) != str(item.source_transition.id):
        raise ValidationError(
            {"lease_id": "The reviewed outgoing relationship must match."}
        )
    parsed = criteria(data.get("criteria"))
    if (
        not parsed["end_on"]
        or not parsed["rental_scope"]
        or parsed["people"] != 1
        or parsed["price_period"] != "monthly"
        or parsed["budget_max"] is None
    ):
        raise ValidationError(
            {
                "criteria": "Choose one person, exact scope, dates, monthly rent and a budget."
            }
        )
    item.criteria = parsed
    item.max_deposit_minor = bounded_integer(data, "max_deposit_minor", 0, 10**12)
    item.max_gap_days = bounded_integer(data, "max_gap_days", 0, 30)
    item.turnover_days = bounded_integer(data, "turnover_days", 1, 7)
    check_source(item)


def create(request):
    data = request.data
    lease = own_lease(request.user, data.get("lease_id"), lock=True)
    source = source_for(
        request.user, lease, data.get("source_transition_id"), lock=True
    )
    MoveIntent.objects.filter(
        lease=lease, user=request.user, expires_at__lte=timezone.now()
    ).exclude(status__in=["withdrawn", "expired"]).update(
        status="expired", matching_consent=False
    )
    if (
        MoveIntent.objects.filter(lease=lease, user=request.user)
        .exclude(status__in=["withdrawn", "expired"])
        .exists()
    ):
        raise RentalConflict("Open your existing move plan.", code="move_intent_exists")
    item = MoveIntent(
        user=request.user,
        lease=lease,
        source_transition=source,
        expires_at=timezone.now() + timedelta(days=30),
    )
    apply_requirements(item, data)
    item.save()
    return item


def change(request, item, action):
    from .access import intent_actions

    if action not in intent_actions(item):
        raise RentalConflict(
            "This action is not available for the move plan.", code="invalid_state"
        )
    if action == "update":
        apply_requirements(item, request.data)
    elif action == "publish":
        check_source(item, publishing=True)
        if request.data.get("matching_consent") is not True:
            raise ValidationError(
                {"matching_consent": "Explicit matching consent is required."}
            )
        item.status, item.matching_consent = "matching", True
    elif action == "pause":
        item.status, item.matching_consent = "paused", False
    elif action == "withdraw":
        item.status, item.matching_consent = "withdrawn", False
    elif action == "match":
        check_source(item, publishing=True)
        recent = item.runs.filter(
            created_at__gte=timezone.now() - timedelta(minutes=10)
        ).count()
        if recent >= 3:
            from rest_framework.exceptions import Throttled

            raise Throttled(wait=600)
        run = TransitionMatchRun.objects.create(
            intent=item, user=request.user, input_revision=item.revision
        )
        # A durable row is the job receipt; the worker can recover missed dispatch.
        from .jobs import enqueue

        transaction.on_commit(lambda: enqueue(str(run.id)))
        return run
    item.revision += 1
    item.save()
    return item


def respond(request, candidate):
    from .projections import candidate_stale

    if request.data.get(
        "snapshot_digest"
    ) != candidate.snapshot_digest or candidate_stale(candidate):
        raise RentalConflict(
            "Refresh the changed move proposal.", code="snapshot_stale"
        )
    if any(key in request.data for key in ("participant_id", "user_id", "signer_id")):
        raise ValidationError({"decision": "Respond only for your own account."})
    decision = request.data.get("decision")
    if decision not in {"interested", "declined"}:
        raise ValidationError({"decision": "Choose interested or declined."})
    participant = candidate.participants.select_for_update().get(user=request.user)
    participant.decision = decision
    participant.save(update_fields=["decision", "updated_at"])
    candidate.revision += 1
    candidate.save(update_fields=["revision", "updated_at"])
    return candidate
