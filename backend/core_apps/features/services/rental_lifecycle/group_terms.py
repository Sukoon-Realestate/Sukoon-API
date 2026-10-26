"""Group representatives negotiate a version; only individuals start their own booking."""

import copy
from datetime import date
from types import SimpleNamespace

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from ...models import GroupBookingTermsVersion, RentalAuditEvent
from ..negotiation_terms import (
    validate,
    material_selection,
    with_context,
    with_physical_context,
)
from ..rental_phase2 import RentalConflict, fingerprint
from ..tenancy_invitations import resolve_offer_snapshot
from .common import audit, lifecycle_policy
from .consents import record_consent

LIVE = {"draft", "negotiating", "changes_requested", "awaiting_participants"}


def representative(proposal, actor):
    return (
        proposal.application.initiated_by_id == actor.pk
        and proposal.group.memberships.filter(
            user=actor,
            status="active",
            joined_revision__lte=proposal.application.access_group_revision,
        ).exists()
    )


def can_negotiate(proposal, actor):
    return proposal.owner_id == actor.pk or representative(proposal, actor)


def started(proposal):
    return proposal.participants.filter(invitation__isnull=False).exists()


def rows_snapshot(proposal):
    return [
        {
            "tenant_id": str(row.tenant.id),
            "selection": copy.deepcopy(row.selection_snapshot),
            "terms": copy.deepcopy(row.terms),
        }
        for row in proposal.participants.select_related("tenant").order_by("pk")
    ]


def remember(proposal):
    return GroupBookingTermsVersion.objects.get_or_create(
        proposal=proposal,
        version=proposal.terms_revision,
        defaults={
            "author_id": proposal.terms_author_id or proposal.owner_id,
            "participants": rows_snapshot(proposal),
            "terms_digest": proposal.terms_digest,
            "deadline": proposal.deadline,
        },
    )[0]


def selection(proposal, row):
    from ..group_booking_listing_changes import require_current

    require_current(proposal, row)
    current_offer = next(
        (
            v
            for v in (proposal.property.rental_inventory or {}).get("offers", [])
            if str(v.get("id")) == row.offer_id
        ),
        None,
    )
    if current_offer is None:
        raise RentalConflict(
            "The allocated accommodation is unavailable.", code="offer_unavailable"
        )
    current = resolve_offer_snapshot(
        proposal.property, row.offer_id, current_offer["revision"]
    )[1]
    current = with_physical_context(current, proposal.property)
    previous = row.selection_snapshot
    if not previous.get("negotiation_context"):
        previous = with_context(previous, proposal.property)
    # Previously captured contexts retain their meaning. All new independent
    # follow-up captures the exact physical facts, including same-capacity beds.
    comparable = current
    if "physical_source" not in previous.get("negotiation_context", {}):
        comparable = with_context(current, proposal.property)
    if material_selection(previous) != material_selection(comparable):
        raise RentalConflict(
            "Review the changed allocation before continuing.", code="offer_changed"
        )
    return current


def validate_row(proposal, row, terms):
    snapshot = selection(proposal, row)
    result = validate(
        SimpleNamespace(academic_plan_id=None),
        terms,
        snapshot,
        proposal.deadline,
        previous=row,
    )
    start, end = date.fromisoformat(result["starts_on"]), date.fromisoformat(
        result["ends_on_exclusive"]
    )
    _, rules = lifecycle_policy("independent_group_booking")
    if (end - start).days > rules["max_booking_days"]:
        raise ValidationError({"terms": "Choose a supported rental period."})
    from ..student_housing.policies import validate_occupants

    validate_occupants(
        proposal.property,
        snapshot,
        [row.tenant],
        start,
        end,
        occupant_count=result["occupants"],
    )
    plan = proposal.application.academic_plan
    if plan and (
        start != plan.starts_on
        or end != plan.ends_on_exclusive
        or result["occupants"] != 1
        or result["monthly_rent"]["amount_minor"]
        > (plan.criteria.get("budget_max") or {}).get("amount_minor", 0)
    ):
        raise RentalConflict(
            "Review the affected academic requirements first.",
            code="academic_review_required",
        )
    return result


def actions(proposal, actor, current):
    if (
        not current
        or not can_negotiate(proposal, actor)
        or started(proposal)
        or (proposal.status == "draft" and actor.pk != proposal.owner_id)
    ):
        return []
    author_id = proposal.terms_author_id or proposal.owner_id
    result = []
    if proposal.status in {"draft", "negotiating", "changes_requested"}:
        result.append(
            "edit_group_terms" if actor.pk == author_id else "counter_group_terms"
        )
    if proposal.status == "negotiating" and actor.pk != author_id:
        result += [
            "accept_group_terms",
            "reject_group_terms",
            "request_group_terms_changes",
        ]
    if proposal.status in LIVE:
        result.append("withdraw_group_terms")
    return result


def act(proposal, actor, data, action):
    if data["terms_digest"] != proposal.terms_digest:
        raise RentalConflict(
            "Review this exact version first.", code="document_changed"
        )
    if action in {"edit_group_terms", "counter_group_terms"}:
        values = {str(v["tenant_id"]): v["terms"] for v in data["participants"]}
        rows = list(proposal.participants.select_for_update().select_related("tenant"))
        if len(values) != len(data["participants"]) or set(values) != {
            str(v.tenant.id) for v in rows
        }:
            raise ValidationError(
                {"participants": "Keep the exact reviewed participant allocations."}
            )
        reviewed = [
            (row, validate_row(proposal, row, values[str(row.tenant.id)]))
            for row in rows
        ]
        if len({(v["starts_on"], v["ends_on_exclusive"]) for _, v in reviewed}) != 1:
            raise ValidationError({"participants": "Use a common rental interval."})
        if all(row.terms == terms for row, terms in reviewed):
            raise ValidationError({"terms": "The proposal has no changes."})
        remember(proposal)
        for row, terms in reviewed:
            row.terms, row.rent_amount_minor = (
                terms,
                terms["monthly_rent"]["amount_minor"],
            )
            row.consent_status, row.consent_revision, row.withdrawn_at = (
                "pending",
                None,
                None,
            )
            row.save()
        proposal.terms_revision += 1
        proposal.terms_author = actor
        proposal.terms_accepted_by = [str(actor.id)]
        proposal.terms_digest = fingerprint(
            {
                "roster_revision": proposal.roster_revision,
                "booking_model": "independent",
                "deadline": proposal.deadline.isoformat(),
                "participants": rows_snapshot(proposal),
            }
        )
        proposal.total_rent_minor = sum(v.rent_amount_minor for v in rows)
        proposal.starts_on = reviewed[0][1]["starts_on"]
        proposal.ends_on_exclusive = reviewed[0][1]["ends_on_exclusive"]
        proposal.status = "draft" if proposal.status == "draft" else "negotiating"
        remember(proposal)
    elif action == "accept_group_terms":
        for row in proposal.participants.select_related("tenant"):
            validate_row(proposal, row, row.terms)
        proposal.terms_accepted_by = sorted(
            {*proposal.terms_accepted_by, str(actor.id)}
        )
        proposal.status = "awaiting_participants"
    else:
        if not data.get("reason", "").strip():
            raise ValidationError(
                {"reason": "Explain this decision to the other participants."}
            )
        proposal.status = {
            "reject_group_terms": "rejected",
            "request_group_terms_changes": "changes_requested",
            "withdraw_group_terms": "withdrawn",
        }[action]
        proposal.terms_accepted_by = []
    record_consent(
        proposal,
        actor,
        action,
        {
            "terms_revision": proposal.terms_revision,
            "terms_digest": proposal.terms_digest,
            "roster_revision": proposal.roster_revision,
        },
    )
    proposal.revision += 1
    proposal.save()
    audit(
        proposal,
        actor,
        action,
        reason=data.get("reason", ""),
        metadata={"terms_revision": proposal.terms_revision},
    )
    from .group_bookings import notify

    notify(proposal, action)
    return proposal


def history(proposal, actor):
    from ..group_booking_listing_changes import ACTION, visible_allocations

    full = can_negotiate(proposal, actor)
    versions = [
        {
            "version": v.version,
            "author_name": v.author.get_full_name,
            "deadline": v.deadline.isoformat(),
            "terms_digest": v.terms_digest,
            "participants": [
                row
                for row in v.participants
                if full or row["tenant_id"] == str(actor.id)
            ],
        }
        for v in proposal.terms_versions.select_related("author").order_by("version")
    ]
    changes = [
        {
            "action": e.action,
            "revision": e.subject_revision,
            "reason": e.reason,
            "at": e.created_at.isoformat(),
            "terms_revision": e.metadata.get("terms_revision"),
            **(
                {
                    "source_revision": e.metadata.get("source_revision"),
                    "allocations": visible_allocations(e, actor, full),
                }
                if e.action == ACTION
                else {}
            ),
        }
        for e in RentalAuditEvent.objects.filter(
            subject_kind=proposal._meta.model_name,
            subject_id=proposal.id,
        ).order_by("created_at", "pk")
        if e.action != ACTION or visible_allocations(e, actor, full)
    ]
    return versions, changes


def expire_due(now=None):
    from django.db import transaction
    from core_apps.properties.models import Property
    from ...models import GroupBookingProposal
    from ...planning_models import HousingGroup
    from .group_bookings import notify

    now, count = now or timezone.now(), 0
    for identity, group, prop in (
        GroupBookingProposal.objects.filter(
            status__in=LIVE,
            deadline__lte=now,
        )
        .values_list("pk", "group_id", "property_id")
        .iterator()
    ):
        with transaction.atomic():
            HousingGroup.objects.select_for_update().get(pk=group)
            Property.objects.select_for_update().get(pk=prop)
            proposal = GroupBookingProposal.objects.select_for_update().get(pk=identity)
            if proposal.status not in LIVE or proposal.deadline > now:
                continue
            proposal.status, proposal.revision = "expired", proposal.revision + 1
            proposal.save()
            proposal.participants.filter(consent_status="pending").update(
                consent_status="expired"
            )
            audit(
                proposal,
                None,
                "group_terms_expired",
                metadata={"terms_revision": proposal.terms_revision},
            )
            notify(proposal, "group_terms_expired")
            count += 1
    return count


def notification_copy(event):
    from rest_framework.exceptions import NotFound
    from .access import booking_queryset

    proposal = (
        booking_queryset(event.recipient)
        .filter(id=event.destination.get("target_id"))
        .first()
    )
    if not proposal or proposal.owner_id != proposal.property.owner_id:
        raise NotFound()
    owner = proposal.owner_id == event.recipient_id
    if event.destination.get("workspace") != ("owner" if owner else "student") or (
        not owner
        and not proposal.group.memberships.filter(
            user=event.recipient,
            status="active",
            joined_revision__lte=proposal.application.access_group_revision,
        ).exists()
    ):
        raise NotFound()
    from ..group_booking_listing_changes import ACTION, events, visible_allocations

    if event.destination.get("event_kind") == ACTION:
        source = (
            events(proposal).filter(id=event.destination.get("source_event_id")).first()
        )
        if not source or not visible_allocations(
            source, event.recipient, can_negotiate(proposal, event.recipient)
        ):
            raise NotFound()
        return {
            "title": "تغير تخصيص السكن / Accommodation allocation changed",
            "body": "راجع التخصيص المتأثر وسجل التغيير. الدعوات والعقود القائمة محفوظة. / Review the affected allocation and history. Existing invitations and contracts are preserved.",
        }
    return {
        "title": "تحديث شروط سكن الطلاب / Student housing terms updated",
        "body": "راجع النسخة الحالية وتاريخ التغيير وموافقتك المستقلة. / Review the current version, history and your independent consent.",
    }
