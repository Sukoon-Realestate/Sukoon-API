"""Corporate-party adapter. Mock documents/payment never turn staff into payers."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from ...company_models import CompanyBookingItem
from ...models import RentalProviderInstruction
from ..company.access import member_for
from ..company import bookings, approval_routing, offers
from ..rental_phase2 import RentalConflict
from ..advanced_execution import create_plan, record_step
from ..advanced_execution.provider import mock_instruction, reconcile_instructions
from . import access, decisions


def authorize(user, source_id):
    decision = decisions.for_user(user, source_id)
    access.scenario_for(user, decision.scenario.id, write=True)
    return decision


def _items(decision):
    return decision.booking_items.select_related(
        "request__company", "offer__owner", "assigned_approver__user", "hold"
    ).order_by("id")


def create(user, decision):
    authorize(user, decision.id)
    if decision.status != "prepared" or not decision.booking_items.exists():
        raise RentalConflict(
            "Prepare and independently approve the canonical company packages first.",
            code="approval_required",
        )
    company = decision.scenario.company
    member_for(user, company, "sign")
    member_for(user, company, "pay")
    legs = []
    for item in _items(decision):
        approval_routing.require_independent(item.assigned_approver, item)
        approval_routing.validate_staff_plan(item)
        if (
            item.status != "approved"
            or item.assigned_approver_id != decision.approver_id
        ):
            raise RentalConflict(
                "Every exact company package needs its independent commercial approval.",
                code="approval_required",
            )
        staff = list(item.planned_staff.select_related("membership__user"))
        if any(
            not row.membership_id
            or not row.membership.is_active
            or not row.membership.user.is_verified
            for row in staff
        ):
            raise RentalConflict(
                "Activate the named employee accounts before requesting personal execution consent.",
                code="employee_activation_required",
            )
        people = [str(row.membership.user.id) for row in staff]
        property_titles = {unit["id"]: unit["title"] for unit in item.snapshot["units"]}
        staff_users = {str(row.id): str(row.membership.user.id) for row in staff}
        placements = [
            {
                "actor_id": staff_users[row["staff_id"]],
                "property_id": row["property_id"],
                "title": property_titles.get(row["property_id"], ""),
            }
            for row in decision.snapshot["plan"]["assignments"]
            if row["staff_id"] in staff_users
        ]
        legs.append(
            {
                "key": str(item.id),
                "canonical_kind": "company",
                "canonical_id": str(item.id),
                "terms": {
                    "actor_ids": sorted(
                        set(
                            [
                                str(user.id),
                                str(item.offer.owner.id),
                                str(decision.approver.user.id),
                                *people,
                            ]
                        )
                    ),
                    "company_id": str(company.id),
                    "company_name": company.name,
                    "payer_kind": "organization",
                    "signer_id": str(user.id),
                    "payer_authorizer_id": str(user.id),
                    "owner_id": str(item.offer.owner.id),
                    "employee_ids": people,
                    "placements": placements,
                    "properties": [
                        {"id": key, "title": title}
                        for key, title in property_titles.items()
                    ],
                    "snapshot_digest": item.snapshot_digest,
                    "full_term_rent_minor": item.full_term_rent_minor,
                    "monthly_rent_minor": item.offer.monthly_rent_minor,
                    "deposit_minor": item.deposit_minor,
                    "currency": "EGP",
                    "starts_on": str(item.request.starts_on),
                    "ends_on_exclusive": str(item.request.ends_on_exclusive),
                    "agreement": "mock-corporate-agreement-v2",
                    "actual_occupancy": False,
                },
                "metadata": {
                    "provider_mode": "mock",
                    "staff_are_not_personal_payers": True,
                },
            }
        )
    return create_plan(
        user,
        source_kind="company_scenario",
        source_id=decision.id,
        source_revision=decision.revision,
        source_digest=decision.snapshot_digest,
        mode="conditional_package",
        legs=legs,
        context={
            "company_id": str(company.id),
            "scenario_id": str(decision.scenario.id),
            "provider_mode": "mock",
            "actual_occupancy": False,
            "policy_version": "corporate-mock-execution-v2",
        },
    )


def revalidate(plan, action="prepare"):
    decision = decisions.for_user(plan.created_by, plan.source_id)
    access.scenario_for(plan.created_by, decision.scenario.id, write=True)
    if (
        decision.snapshot_digest != plan.source_digest
        or decision.revision != plan.source_revision
        or not decisions.independent(decision.approver, decision.scenario)
    ):
        raise RentalConflict(
            "Review the current company authority and exact decision.",
            code="stale_revision",
        )
    member_for(plan.created_by, decision.scenario.company, "sign")
    member_for(plan.created_by, decision.scenario.company, "pay")
    for leg in plan.legs.all():
        item = get_object_or_404(_items(decision), id=leg.canonical_id)
        if item.status == "withdrawn" and leg.state == "withdrawn":
            continue
        props = offers.resolve_scope(item.offer)
        current = offers.scope_snapshot(item.offer, props)
        if any(current[key] != item.snapshot.get(key) for key in current):
            raise RentalConflict(
                "The canonical company package changed.", code="offer_changed"
            )
        approval_routing.require_independent(item.assigned_approver, item)
        approval_routing.validate_staff_plan(item)
        if item.snapshot_digest != leg.specification["terms"][
            "snapshot_digest"
        ] or item.status not in {"approved", "held"}:
            raise RentalConflict(
                "The canonical company package changed.", code="offer_changed"
            )
        if (
            action in {"prepare", "consents"}
            and item.quote_expires_at <= timezone.now()
        ):
            raise RentalConflict(
                "Refresh the expired commercial package before proceeding.",
                code="quote_expired",
            )
        if action == "advance" and (
            not item.hold_id
            or item.hold.status != "active"
            or item.hold.expires_at <= timezone.now()
        ):
            raise RentalConflict(
                "The canonical company hold expired. Reconcile and prepare a current package.",
                code="hold_expired",
            )
    return decision


def prepare(plan, actor):
    decision = authorize(actor, plan.source_id)
    for leg in plan.legs.all():
        item = get_object_or_404(_items(decision), id=leg.canonical_id)
        if not item.hold_id:
            item = bookings.hold_item(
                actor, item.id, {"expected_revision": item.revision}
            )
        leg.state = "mock_contract_ready"
        leg.save(update_fields=["state", "updated_at"])
        record_step(
            plan,
            leg,
            "company_hold",
            "confirmed",
            "reservation_hold",
            item.hold.id,
            {
                "organization_payer": str(decision.scenario.company.id),
                "provider_mode": "mock",
                "actual_occupancy": False,
            },
            actor,
        )


def _signed(leg):
    return {
        str(row.result.get("actor_id"))
        for row in RentalProviderInstruction.objects.filter(
            subject_id=leg.id, kind="advanced_company_sign", status="confirmed"
        )
        if row.result.get("mock_outcome") == "applied"
    }


def leg_actions(plan, leg, actor):
    if str(actor.id) not in leg.actor_ids or leg.state in {
        "mock_confirmed",
        "withdrawn",
    }:
        return []
    terms = leg.specification["terms"]
    signed = _signed(leg)
    if leg.state in {"mock_contract_ready", "mock_signing", "mock_signed"}:
        if (
            str(actor.id) in {terms["owner_id"], terms["signer_id"]}
            and str(actor.id) not in signed
        ):
            return ["company_sign"]
        if {terms["owner_id"], terms["signer_id"]} <= signed and str(actor.id) == terms[
            "payer_authorizer_id"
        ]:
            return ["company_pay"]
    return []


def leg_payload(plan, leg, actor):
    terms = leg.specification["terms"]
    own = str(actor.id)
    role = (
        "company_authorizer"
        if own == terms["signer_id"]
        else (
            "owner"
            if own == terms["owner_id"]
            else "employee" if own in terms["employee_ids"] else "approver"
        )
    )
    own_placement = next(
        (
            {"property_id": row["property_id"], "title": row["title"]}
            for row in terms["placements"]
            if row["actor_id"] == own
        ),
        {},
    )
    safe_terms = {
        key: terms[key]
        for key in (
            "company_id",
            "company_name",
            "payer_kind",
            "snapshot_digest",
            "full_term_rent_minor",
            "monthly_rent_minor",
            "deposit_minor",
            "currency",
            "starts_on",
            "ends_on_exclusive",
            "agreement",
            "actual_occupancy",
        )
    }
    return {
        "role": role,
        "terms": safe_terms,
        "company_name": terms["company_name"],
        "payer_kind": "organization",
        "rent_minor": terms["monthly_rent_minor"],
        "monthly_rent_minor": terms["monthly_rent_minor"],
        "deposit_minor": terms["deposit_minor"],
        "starts_on": terms["starts_on"],
        "ends_on_exclusive": terms["ends_on_exclusive"],
        "document_hash": plan.digest,
        "first_invoice_minor": terms["monthly_rent_minor"] + terms["deposit_minor"],
        "currency": "EGP",
        "provider_mode": "mock",
        "actual_occupancy": False,
        "staff_are_not_personal_payers": True,
        "own_placement": own_placement,
        "properties": terms["properties"] if role != "employee" else [],
        "available_steps": leg_actions(plan, leg, actor),
    }


def advance(plan, actor, data):
    leg = get_object_or_404(plan.legs.select_for_update(), id=data.get("leg_id"))
    if data.get("step") not in leg_actions(plan, leg, actor):
        raise PermissionDenied(
            "Only the current corporate signer or payment authorizer can perform this step."
        )
    terms = leg.specification["terms"]
    decision = decisions.for_user(plan.created_by, plan.source_id)
    step = data["step"]
    if str(actor.id) == terms["signer_id"]:
        member_for(
            actor,
            decision.scenario.company,
            "sign" if step == "company_sign" else "pay",
        )
    if step == "company_pay" and any(
        row.state not in {"mock_signed", "mock_confirmed"} for row in plan.legs.all()
    ):
        raise RentalConflict(
            "Every company agreement must be signed before the first company payment.",
            code="conditional_threshold",
        )

    def perform(instruction):
        return {
            "agreement_digest": plan.digest,
            "company_id": terms["company_id"],
            "payer_kind": "organization",
            "amount_minor": (
                terms["monthly_rent_minor"] + terms["deposit_minor"]
                if step == "company_pay"
                else None
            ),
            "currency": "EGP",
            "mock_document_reference": "mock-corporate:" + str(leg.id),
            "actual_occupancy": False,
            "provider_money_transferred": False,
        }

    mock_instruction(
        plan,
        leg,
        kind=step,
        actor=actor,
        request_key=data["request_key"],
        behavior=data.get("mock_outcome", "confirmed"),
        perform=perform,
    )
    return sync(plan)


def sync(plan):
    states = []
    unknown = False
    for leg in plan.legs.all():
        if leg.state == "withdrawn":
            states.append(leg.state)
            continue
        instructions = RentalProviderInstruction.objects.filter(subject_id=leg.id)
        unknown |= instructions.filter(status="unknown").exists()
        terms = leg.specification["terms"]
        if instructions.filter(
            kind="advanced_company_pay",
            status="confirmed",
            result__mock_outcome="applied",
        ).exists():
            leg.state = "mock_confirmed"
        elif {terms["signer_id"], terms["owner_id"]} <= _signed(leg):
            leg.state = "mock_signed"
        elif _signed(leg):
            leg.state = "mock_signing"
        leg.save(update_fields=["state", "updated_at"])
        states.append(leg.state)
    if unknown:
        plan.state = "unknown"
    elif plan.state == "closed_partial":
        pass
    elif plan.context.get("withdrawal_review_leg_ids"):
        plan.state = "manual_resolution"
    elif states and all(state == "mock_confirmed" for state in states):
        plan.state = "completed"
    elif "withdrawn" in states:
        plan.state = "partial" if "mock_confirmed" in states else "manual_resolution"
    elif plan.state not in {"awaiting_consents", "ready"}:
        plan.state = (
            "executing"
            if any(
                state in {"mock_signed", "mock_signing", "mock_confirmed"}
                for state in states
            )
            else "prepared"
        )
    return plan


def reconcile(plan, actor):
    for leg in plan.legs.all():
        if str(actor.id) in leg.actor_ids:
            reconcile_instructions(plan, leg, actor)
    return sync(plan)


def withdraw(plan, actor, data):
    decision = authorize(actor, plan.source_id)
    leg = get_object_or_404(plan.legs.select_for_update(), id=data.get("leg_id"))
    if RentalProviderInstruction.objects.filter(
        subject_id=leg.id, status="unknown"
    ).exists():
        raise RentalConflict(
            "Reconcile the original uncertain provider instruction first.",
            code="reconciliation_required",
        )
    if _signed(leg) or leg.state == "mock_confirmed":
        plan.state = "manual_resolution"
        plan.context = {
            **plan.context,
            "withdrawal_review_leg_ids": sorted(
                set([*plan.context.get("withdrawal_review_leg_ids", []), str(leg.id)])
            ),
        }
        record_step(
            plan,
            leg,
            "company_withdrawal_review",
            "manual_resolution",
            metadata={
                "provider_mode": "mock",
                "signed_or_funded_mock_record_preserved": True,
            },
            actor=actor,
        )
        return plan
    item = get_object_or_404(_items(decision), id=leg.canonical_id)
    bookings.withdraw_item(
        actor,
        item.id,
        {
            "expected_revision": item.revision,
            "reason": "Explicit withdrawal of uncommitted mock corporate execution.",
        },
    )
    leg.state = "withdrawn"
    leg.save()
    return sync(plan)


def authorize_participant(plan, user):
    """A stored consent actor is not a durable grant after source authority ends."""
    decision = decisions.for_user(plan.created_by, plan.source_id)
    if not user.is_active or not user.is_verified:
        raise PermissionDenied(
            "This execution participant no longer has current authority."
        )
    if user.pk == decision.created_by_id:
        access.scenario_for(user, decision.scenario.id)
        return
    if user.pk == decision.approver.user_id and decisions.independent(
        decision.approver, decision.scenario
    ):
        return
    for item in _items(decision):
        if item.offer.owner_id == user.pk:
            try:
                if all(
                    unit.owner_id == user.pk
                    for unit in offers.resolve_scope(item.offer)
                ):
                    return
            except (RentalConflict, ValidationError):
                continue
        if item.planned_staff.filter(
            membership__user=user,
            membership__is_active=True,
            membership__is_employee=True,
            employment_status="active",
        ).exists():
            return
    raise PermissionDenied(
        "This execution participant no longer has current authority."
    )
