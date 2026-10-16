"""Independent accommodation commitments for explicitly consenting group members."""

import json
from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from ...models import (
    GroupBookingProposal,
    GroupBookingParticipant,
    RentalInterest,
    TermsProposal,
    TenancyInvitation,
)
from ...planning_models import GroupMembership
from ..rental_phase2 import RentalConflict, fingerprint, assert_owner_ready
from ..tenancy_invitations import resolve_offer_snapshot
from .common import audit, lifecycle_policy, require_revision
from .consents import record_consent
from .inventory import unit_keys, assert_available, expire_property_holds
from .notifications import record_rental_event


def current_roster(proposal):
    from ..student_housing.groups import process_current

    proposal.group.refresh_from_db()
    proposal.application.refresh_from_db()
    roster = set(
        str(value)
        for value in proposal.group.memberships.filter(status="active").values_list(
            "user__id", flat=True
        )
    )
    participants = set(
        str(value)
        for value in proposal.participants.values_list("tenant__id", flat=True)
    )
    return (
        proposal.group.status == "active"
        and process_current(proposal.application)
        and proposal.group.roster_revision == proposal.roster_revision
        and participants <= roster
        and proposal.application.status
        not in {"withdrawn", "cancelled", "declined", "expired"}
    )


def create_booking(application, actor, data):
    from ..student_housing.groups import process_current

    if not process_current(application):
        raise RentalConflict(
            "Review changed academic requirements.", code="source_changed"
        )
    policy, rules = lifecycle_policy("independent_group_booking")
    if data["booking_model"] != "independent":
        raise RentalConflict(
            "Conditional bundles require approved joint terms and provider compensation support.",
            code="capability_unavailable",
        )
    if application.property.owner_id != actor.pk or application.kind != "application":
        raise NotFound()
    require_revision(application, data["application_revision"])
    if (
        data["expected_revision"] != 0
        or application.roster_revision != data["roster_revision"]
        or application.group.roster_revision != data["roster_revision"]
    ):
        raise RentalConflict("Review the current group roster.", code="stale_revision")
    if application.status not in {
        "submitted",
        "under_review",
        "approved",
        "accepted",
        "approved_to_proceed",
    }:
        raise RentalConflict(
            "The group application is not ready for booking.", code="source_changed"
        )
    if GroupBookingProposal.objects.filter(
        application=application,
        status__in=["draft", "submitted", "awaiting_participants"],
    ).exists():
        raise RentalConflict(
            "Review the existing booking proposal.", code="proposal_exists"
        )
    if not timezone.now() < data["deadline"] <= timezone.now() + timedelta(days=7):
        raise ValidationError({"deadline": "Choose a deadline within seven days."})
    roster = {
        str(item.user.id): item.user
        for item in application.group.memberships.select_related("user").filter(
            status="active"
        )
    }
    proposed = [str(item["tenant_id"]) for item in data["participants"]]
    if (
        len(proposed) != len(set(proposed))
        or not set(proposed) <= set(roster)
        or set(proposed) != set(map(str, application.participant_ids))
    ):
        raise ValidationError(
            {
                "participants": "Allocate each current application participant exactly once."
            }
        )
    if len(proposed) > 20:
        raise ValidationError(
            {"participants": "At most 20 participants are supported."}
        )
    expire_property_holds(application.property)
    used, rows, periods = set(), [], set()
    for value in data["participants"]:
        tenant = roster[str(value["tenant_id"])]
        if not tenant.is_active or not tenant.is_verified or tenant == actor:
            raise RentalConflict("Every participant needs a verified active account.")
        offer_id, selection = resolve_offer_snapshot(
            application.property, value["offer_id"], value["offer_revision"]
        )
        if selection["rental_scope"] not in {"room", "bed", "room_group"}:
            raise ValidationError(
                {
                    "participants": "Independent agreements require distinct rooms or beds."
                }
            )
        keys = set(unit_keys(application.property, selection))
        if used & keys:
            raise RentalConflict(
                "Participant allocations overlap.", code="inventory_conflict"
            )
        used.update(keys)
        terms = json.loads(json.dumps(value["terms"], default=str))
        from .terms import validate_terms_offer

        validate_terms_offer(terms, selection)
        start, end = value["terms"]["starts_on"], value["terms"]["ends_on_exclusive"]
        from ..student_housing.policies import validate_occupants

        validate_occupants(
            application.property,
            selection,
            [tenant],
            start,
            end,
            occupant_count=value["terms"].get("occupants", 1),
        )
        if (
            start < timezone.localdate()
            or (end - start).days > rules["max_booking_days"]
        ):
            raise ValidationError(
                {"participants": "Choose a supported future rental period."}
            )
        assert_available(application.property, selection, start, end)
        periods.add((start, end))
        rows.append(
            {
                "tenant": tenant,
                "offer_id": offer_id,
                "offer_revision": value["offer_revision"],
                "selection_snapshot": selection,
                "rent_amount_minor": terms["monthly_rent"]["amount_minor"],
                "terms": terms,
            }
        )
    if len(periods) != 1:
        raise ValidationError(
            {"participants": "This proposal requires a common start and end date."}
        )
    start, end = periods.pop()
    digest = fingerprint(
        {
            "roster_revision": data["roster_revision"],
            "booking_model": "independent",
            "participants": [
                {
                    **{key: value for key, value in row.items() if key != "tenant"},
                    "tenant_id": str(row["tenant"].id),
                }
                for row in rows
            ],
        }
    )
    proposal = GroupBookingProposal.objects.create(
        application=application,
        group=application.group,
        property=application.property,
        owner=actor,
        booking_model="independent",
        roster_revision=data["roster_revision"],
        policy_version=policy.version,
        terms_digest=digest,
        starts_on=start,
        ends_on_exclusive=end,
        deadline=data["deadline"],
        total_rent_minor=sum(row["rent_amount_minor"] for row in rows),
    )
    for row in rows:
        GroupBookingParticipant.objects.create(proposal=proposal, **row)
    audit(proposal, actor, "group_booking.created")
    return proposal


def booking_payload(proposal, actor):
    rows = list(proposal.participants.select_related("tenant", "invitation", "lease"))
    own = next((row for row in rows if row.tenant_id == actor.pk), None)
    current = current_roster(proposal) and proposal.deadline > timezone.now()
    actions = []
    if current and proposal.owner_id == actor.pk and proposal.status == "draft":
        actions.append("submit_group_booking")
    if (
        current
        and own
        and own.consent_status == "pending"
        and proposal.status == "awaiting_participants"
    ):
        actions.append("consent_group_booking")
    if (
        own
        and own.consent_status in {"pending", "accepted"}
        and not own.lease_id
        and proposal.status in {"awaiting_participants", "submitted"}
    ):
        actions.append("withdraw_group_booking")
    return {
        "id": str(proposal.id),
        "revision": proposal.revision,
        "group_id": str(proposal.group.id),
        "application_id": str(proposal.application.id),
        "property_id": str(proposal.property.id),
        "booking_model": proposal.booking_model,
        "status": proposal.status,
        "terms_digest": proposal.terms_digest,
        "roster_revision": proposal.roster_revision,
        "deadline": proposal.deadline.isoformat(),
        "currency": proposal.currency,
        "exponent": proposal.exponent,
        "total_rent_minor": proposal.total_rent_minor,
        "participants": [
            {
                "tenant_id": str(row.tenant.id),
                "is_current_user": row.tenant_id == actor.pk,
                "consent_status": row.consent_status,
                "rent_amount_minor": row.rent_amount_minor,
                "selection": row.selection_snapshot,
                "agreement_status": row.lease.status if row.lease else "not_created",
                "invitation_id": (
                    str(row.invitation.id)
                    if row.invitation
                    and (row.tenant_id == actor.pk or proposal.owner_id == actor.pk)
                    else None
                ),
                "lease_id": (
                    str(row.lease.id)
                    if row.lease
                    and (row.tenant_id == actor.pk or proposal.owner_id == actor.pk)
                    else None
                ),
                "terms": (
                    row.terms
                    if row.tenant_id == actor.pk or proposal.owner_id == actor.pk
                    else {}
                ),
            }
            for row in rows
        ],
        "incomplete_policy": proposal.incomplete_policy,
        "allowed_actions": actions,
        "blocking_reasons": [] if current else ["roster_or_deadline_changed"],
    }


def booking_action(proposal, actor, data, action):
    require_revision(proposal, data["expected_revision"])
    if action not in booking_payload(proposal, actor)["allowed_actions"]:
        raise RentalConflict(
            "Review the current roster and proposal.", code="stale_revision"
        )
    if action == "submit_group_booking":
        lifecycle_policy("independent_group_booking")
        assert_owner_ready(actor, proposal.property)
        proposal.status = "awaiting_participants"
        record_consent(
            proposal,
            actor,
            "submit",
            {
                "terms_digest": proposal.terms_digest,
                "roster_revision": proposal.roster_revision,
            },
        )
    else:
        participant = get_object_or_404(
            GroupBookingParticipant.objects.select_for_update(),
            proposal=proposal,
            tenant=actor,
        )
        if action == "withdraw_group_booking":
            if participant.invitation and participant.invitation.lease_id:
                raise RentalConflict(
                    "Use the agreement change process after draft creation.",
                    code="invalid_state",
                )
            participant.consent_status, participant.withdrawn_at = (
                "withdrawn",
                timezone.now(),
            )
            if participant.invitation:
                participant.invitation.status = "revoked"
                participant.invitation.revision += 1
                participant.invitation.revoked_at = timezone.now()
                participant.invitation.save()
        else:
            lifecycle_policy("independent_group_booking")
            if data["terms_digest"] != proposal.terms_digest:
                raise RentalConflict(
                    "Review the exact participant allocation and terms.",
                    code="document_changed",
                )
            participant.consent_status = (
                "accepted" if data["decision"] == "accept" else "declined"
            )
            participant.consent_revision = proposal.revision
            record_consent(
                proposal,
                actor,
                data["decision"],
                {
                    "terms_digest": proposal.terms_digest,
                    "selection": participant.selection_snapshot,
                    "terms": participant.terms,
                    "roster_revision": proposal.roster_revision,
                },
            )
            if data["decision"] == "accept":
                _, current = resolve_offer_snapshot(
                    proposal.property, participant.offer_id, participant.offer_revision
                )
                if current != participant.selection_snapshot:
                    raise RentalConflict(
                        "The offered accommodation changed.", code="offer_changed"
                    )
                assert_available(
                    proposal.property,
                    current,
                    proposal.starts_on,
                    proposal.ends_on_exclusive,
                )
                interest = RentalInterest.objects.create(
                    academic_plan=proposal.application.academic_plan,
                    academic_revision=proposal.application.academic_revision,
                    academic_snapshot=proposal.application.academic_snapshot,
                    desired_end=proposal.ends_on_exclusive,
                    property=proposal.property,
                    tenant=actor,
                    offer_id=participant.offer_id,
                    offer_revision=participant.offer_revision,
                    offer_snapshot=current,
                    desired_start=proposal.starts_on,
                    months=max(
                        1,
                        (proposal.ends_on_exclusive.year - proposal.starts_on.year) * 12
                        + proposal.ends_on_exclusive.month
                        - proposal.starts_on.month,
                    ),
                    occupants=participant.terms["occupants"],
                    status="invited",
                    waiting_for="tenant",
                )
                terms = TermsProposal.objects.create(
                    interest=interest,
                    owner=proposal.owner,
                    terms=participant.terms,
                    offer_snapshot=current,
                    accepted_by=[str(actor.id), str(proposal.owner.id)],
                    status="accepted",
                )
                participant.invitation = TenancyInvitation.objects.create(
                    property=proposal.property,
                    owner=proposal.owner,
                    tenant=actor,
                    initiated_by=proposal.owner,
                    interest=interest,
                    terms_proposal=terms,
                    offer_id=participant.offer_id,
                    offer_snapshot=current,
                    expires_at=proposal.deadline,
                    provenance_version="group_booking_v1",
                    eligibility_snapshot={
                        "group_booking_id": str(proposal.id),
                        "terms_digest": proposal.terms_digest,
                    },
                )
        participant.save()
    proposal.revision += 1
    if (
        action != "submit_group_booking"
        and not proposal.participants.filter(consent_status="pending").exists()
    ):
        proposal.status = "submitted"
    proposal.save()
    audit(proposal, actor, action)
    record_rental_event(
        proposal,
        {
            proposal.owner,
            *[row.tenant for row in proposal.participants.select_related("tenant")],
        },
        action,
        "open_group_booking",
    )
    return proposal
