import pytest
from core_apps.admin_api.models import StaffProfile
from core_apps.features.tests.test_rental_phase3 import phase3_lease
from core_apps.features.tests.test_rental_lifecycle_safety import (
    operator,
    post,
    command,
    PREFIX,
)
from core_apps.features.services.rental_lifecycle.cases import (
    open_system_case,
    case_payload,
)
from core_apps.features.tests.test_rental_lifecycle import (
    rental_participants,
    policy,
    confirm,
    proposal_for,
    hold_body,
)

pytestmark = pytest.mark.django_db


def test_conflicted_operator_retains_participant_read_but_cannot_decide(phase3_lease):
    owner, tenant, lease = phase3_lease
    StaffProfile.objects.create(user=owner, role_name="support")
    item = open_system_case(
        kind="access_failure",
        source_key="closure-authority",
        lease=lease,
        actor=tenant,
        reason="Cannot enter",
        next_action="Independent support review",
    )
    assert case_payload(item, owner)["allowed_actions"] == ["reply"]
    response = post(
        owner,
        f"rental-cases/{item.id}/actions/",
        command(
            1, action="assign", assignee_id=str(owner.id), reason="Self assignment"
        ),
    )
    assert response.status_code == 403
    item.refresh_from_db()
    assert item.assigned_to_id is None and item.status == "open"


def test_suspended_assignee_requires_explicit_current_reassignment(phase3_lease):
    owner, tenant, lease = phase3_lease
    first, next_operator = operator("support"), operator("dispute_resolver")
    item = open_system_case(
        kind="maintenance",
        source_key="closure-reassignment",
        lease=lease,
        actor=tenant,
        reason="Needs assistance",
        next_action="Independent support review",
    )
    item.assigned_to = first
    item.save()
    first.is_active = False
    first.save()
    assert case_payload(item, next_operator)["assignment_current"] is False
    denied = post(
        next_operator,
        f"rental-cases/{item.id}/actions/",
        command(
            1,
            action="resolve",
            resolution_code="no_action_required",
            reason="Review complete",
        ),
    )
    assert denied.status_code == 409
    assigned = post(
        next_operator,
        f"rental-cases/{item.id}/actions/",
        command(
            1,
            action="assign",
            assignee_id=str(next_operator.id),
            reason="Take over the queue",
        ),
    )
    assert assigned.status_code == 200
    assert assigned.data["resource"]["assignment_current"] is True


def test_support_operator_cannot_execute_refund_or_payout_and_denial_is_audited():
    import uuid
    from core_apps.features.models import RentalAuditEvent, RefundRequest, RentalPayout

    support = operator("support")
    refund = post(support, f"refund-requests/{uuid.uuid4()}/execute/", command(1))
    payout = post(
        support,
        "operations/payouts/execute/",
        {"payable_ids": [], "request_key": str(uuid.uuid4())},
    )
    assert refund.status_code == payout.status_code == 403
    assert set(
        RentalAuditEvent.objects.filter(actor=support).values_list("action", flat=True)
    ) == {"refund.execute.denied", "payout.execute.denied"}
    assert not RefundRequest.objects.exists() and not RentalPayout.objects.exists()


def test_finance_permission_is_refreshed_even_for_a_cached_user_object():
    from rest_framework.exceptions import PermissionDenied
    from core_apps.features.services.financial_authority import require_financial_actor

    actor = operator("refund_operator")
    assert actor.staff_profile.is_active
    StaffProfile.objects.filter(user=actor).update(is_active=False)
    with pytest.raises(PermissionDenied):
        require_financial_actor(actor, {"refund_operator"}, "refund.execute")


def test_case_target_preserves_original_hold_deadline_and_its_policy_source(
    rental_participants, policy
):
    from datetime import timedelta
    from django.utils import timezone
    from core_apps.features.models import ReservationHold

    _, tenant, _, prop, offer = rental_participants
    confirm(prop)
    proposal = proposal_for(tenant, prop, offer)
    response = post(tenant, "reservation-holds/", hold_body(proposal))
    assert response.status_code == 201, response.data
    hold = ReservationHold.objects.get(id=response.data["resource"]["id"])
    original_deadline = timezone.now() + timedelta(minutes=20)
    hold.reconciliation_deadline = original_deadline
    hold.save()
    item = open_system_case(
        kind="payment_unknown",
        source_key="hold-deadline-proof",
        hold=hold,
        actor=tenant,
        reason="Recover original payment",
        next_action="Reconcile",
    )
    target = case_payload(item, tenant)["response_target"]
    assert item.due_at == original_deadline
    assert target["source"] == "reservation_hold"
    assert target["version"] == hold.policy_version
    assert target["hold_id"] == str(hold.id)
    assert target["due_at"] == original_deadline.isoformat()
    assert "case_hours" not in target
    hold.reconciliation_deadline += timedelta(hours=2)
    hold.save()
    again = open_system_case(
        kind="payment_unknown",
        source_key="hold-deadline-proof",
        hold=hold,
        actor=tenant,
        reason="Repeated observation",
        next_action="Reconcile",
    )
    assert again.pk == item.pk and again.due_at == original_deadline
    assert case_payload(again, tenant)["response_target"] == target
