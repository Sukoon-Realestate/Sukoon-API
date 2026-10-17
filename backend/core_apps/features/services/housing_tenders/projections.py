from django.utils import timezone
from .access import (
    admin,
    member,
    current,
    tender_actions,
    actions,
    package_quotes_current,
    CAPABILITY,
)
from ..planning import display_name


def latest_requirements(tender):
    result = {}
    for item in tender.requirements.select_related("participant").order_by(
        "-revision", "-pkid"
    ):
        result.setdefault(str(item.participant.id), item)
    return result


def tender_payload(tender, user):
    participant = member(user, tender)
    requirements = latest_requirements(tender) if participant else {}
    own = requirements.get(str(user.id))
    active_ids = set(
        str(x)
        for x in tender.group.memberships.filter(status="active").values_list(
            "user__id", flat=True
        )
    )
    completed = sum(
        x.values.get("disclose", False)
        and x.roster_revision == tender.group.roster_revision
        and x.request_revision == tender.request.revision
        for key, x in requirements.items()
        if key in active_ids
    )
    status = tender.status
    if status not in {"withdrawn", "expired"}:
        if not current(tender):
            status = "review_required"
        elif tender.closes_at <= timezone.now():
            status = "closed_to_bids"
    return {
        "id": str(tender.id),
        "revision": tender.revision,
        "title": tender.title,
        "group_id": str(tender.group.id) if participant else "",
        "request_id": str(tender.request.id) if participant else "",
        "status": status,
        "closes_at": tender.closes_at.isoformat(),
        "execution_mode": "independent_participants",
        "execution_available": False,
        "execution_blocker": "canonical_tiered_handoff_not_verified",
        "roster_revision": tender.roster_revision,
        "request_revision": tender.request_revision,
        "participant_count": (
            len(active_ids)
            if participant
            else (
                tender.active_snapshot.owner_projection.get("participant_count", 0)
                if tender.active_snapshot
                else 0
            )
        ),
        "missing_requirements": (
            max(0, len(active_ids) - completed) if participant else None
        ),
        "own_requirement": own.values if own else None,
        "source_context": tender.source_context if participant else {},
        "participants": (
            [
                {
                    "user_id": str(m.user.id),
                    "name": display_name(m.user),
                    "role": m.role,
                    "status": m.status,
                }
                for m in tender.group.memberships.filter(
                    status="active"
                ).select_related("user")
            ]
            if admin(user, tender)
            else []
        ),
        "snapshot_id": str(tender.active_snapshot.id) if tender.active_snapshot else "",
        "snapshot_digest": (
            tender.active_snapshot.digest
            if tender.active_snapshot and participant
            else ""
        ),
        "demand": (
            tender.active_snapshot.owner_projection if tender.active_snapshot else {}
        ),
        "allowed_actions": tender_actions(user, tender),
    }


def bid_payload(bid, user):
    from rest_framework.exceptions import NotFound

    if bid.owner_id != user.pk and not admin(user, bid.tender):
        raise NotFound()
    state = bid.status
    if state == "submitted":
        if bid.expires_at <= timezone.now():
            state = "expired"
        elif (
            bid.tender.active_snapshot_id != bid.snapshot_id
            or not current(bid.tender)
            or bid.tender.status != "published"
        ):
            state = "review_required"
    return {
        "id": str(bid.id),
        "revision": bid.revision,
        "tender_id": str(bid.tender.id),
        "snapshot_id": str(bid.snapshot.id),
        "status": state,
        "expires_at": bid.expires_at.isoformat(),
        "start_on": str(bid.start_on),
        "end_on": str(bid.end_on),
        "minimum_quantity": bid.minimum_quantity,
        "maximum_quantity": bid.lines.count(),
        "combines": bid.combines,
        "pricing_rule": bid.pricing_rule,
        "price_tiers": bid.price_tiers,
        "supersedes_id": str(bid.supersedes.id) if bid.supersedes_id else "",
        "clarification_count": bid.clarifications.count(),
        "allowed_actions": actions(user, CAPABILITY, str(bid.id))[1:],
        "lines": [
            {
                "id": str(line.id),
                "housing_offer_id": str(line.offer.id),
                "selection": line.offer.selection,
                "rent_minor": line.offer.rent_minor,
                "deposit_minor": line.offer.deposit_minor,
            }
            for line in bid.lines.select_related("offer")
        ],
    }


def package_payload(package, user):
    from ...advanced_execution_models import AdvancedExecution

    execution_actions = actions(user, "collective_tender_execution", str(package.id))[
        1:
    ]
    modes = []
    if "prepare" in execution_actions:
        modes.append("independent_participants")
        if "prepare" in actions(user, "conditional_group_execution", str(package.id)):
            modes.append("conditional_package")
    coordinator = admin(user, package.tender)
    consents = {
        str(c.participant.id): c.decision
        for c in package.consents.select_related("participant")
    }
    allocations = []
    for allocation in package.allocations:
        if coordinator or allocation["participant_id"] == str(user.id):
            allocations.append(
                {
                    **allocation,
                    "decision": consents.get(allocation["participant_id"], "pending"),
                }
            )
    status = package.status
    if (
        not current(package.tender)
        or package.tender.status != "published"
        or package.tender.active_snapshot_id != package.snapshot_id
        or not package_quotes_current(package)
    ):
        status = "review_required"
    elif any(c == "decline" for c in consents.values()):
        status = "review_required"
    elif len(consents) == len(package.allocations) and all(
        c == "accept" for c in consents.values()
    ):
        status = "accepted_for_planning"
    return {
        "id": str(package.id),
        "revision": package.revision,
        "tender_id": str(package.tender.id),
        "digest": package.digest,
        "status": status,
        "execution_mode": package.execution_mode,
        "execution_available": bool(modes),
        "execution_modes": modes,
        "execution_ids": [
            str(x)
            for x in AdvancedExecution.objects.filter(
                source_kind="tender", source_id=package.id, actors=user
            ).values_list("id", flat=True)
        ],
        "allocations": allocations,
        "allocated_count": len(package.allocations),
        "unallocated_count": len(package.unallocated_ids),
        "accepted_count": sum(c == "accept" for c in consents.values()),
        "total_rent_minor": package.total_rent_minor if coordinator else None,
        "total_deposit_minor": package.total_deposit_minor if coordinator else None,
        "allowed_actions": actions(user, CAPABILITY, str(package.id))[1:],
    }
