"""Synthetic internship relocation through real domain commands, not status edits."""

import copy
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.utils import timezone
from core_apps.properties.models import Property
from core_apps.features.models import (
    Lease,
    DepositAgreement,
    RentalInventoryDayLock,
    RefundRequest,
)
from core_apps.features.tasks import process_rental_changes, process_rental_closure
from .test_student_housing import (
    student_capabilities,
    API,
    post,
    create_plan,
    command,
    read,
)
from .test_student_journeys import reviewed_plan, response_for, inventory, artifact
from .test_planning_cycles import criteria_for
from .test_rental_phase2 import (
    rental_participants,
    run_interest_to_activation,
    authenticated,
)
from .test_rental_lifecycle_safety import operator


@pytest.mark.django_db
def test_journey_e_internship_booking_formal_departure_and_separate_deposit_settlement(
    rental_participants, monkeypatch
):
    owner, tenant, next_owner, prop, _ = rental_participants
    run_interest_to_activation(
        rental_participants, artifact_name="synthetic-student-previous-tenancy"
    )
    current = Lease.objects.get(tenant=tenant)
    before = (current.status, current.occupancy_status, copy.deepcopy(current.terms))
    previous = create_plan(tenant, prop, current_lease_id=str(current.id))
    ending_day = current.start_date + timedelta(days=20)
    next_start = ending_day + timedelta(days=10)

    next_inventory = copy.deepcopy(prop.rental_inventory)
    next_offer = str(uuid.uuid4())
    next_inventory["offers"][0]["id"] = next_offer
    next_prop = Property.objects.create(
        owner=next_owner,
        title="Synthetic internship accommodation",
        price=10000,
        property_type=prop.property_type,
        governorate=prop.governorate,
        city=prop.city,
        district="Synthetic placement district",
        status=Property.Status.VERIFIED,
        is_verified=True,
        is_ownership_verified=True,
        rental_inventory=next_inventory,
    )
    inventory(next_prop)
    plan = reviewed_plan(
        tenant,
        next_prop,
        [tenant],
        starts_on=str(next_start),
        period_kind="internship",
        previous_plan_id=previous["id"],
        current_lease_id=str(current.id),
        criteria={**criteria_for(next_prop, 1), "rental_scope": "room"},
    )
    current.refresh_from_db()
    assert (current.status, current.occupancy_status, current.terms) == before
    from core_apps.features.services.termination_notice import policy

    change = post(
        owner,
        f"leases/{current.id}/termination-requests/",
        command(
            lease_revision=current.revision,
            effective_on=str(ending_day),
            reason="Reviewed internship relocation",
            evidence_ids=[],
            termination_mode="contract_notice",
            notice_basis_digest=policy(current)["basis_digest"],
        ),
        201,
    ).data["resource"]
    post(
        tenant,
        f"termination-requests/{change['id']}/respond/",
        command(change["revision"], action="accept", termination_notice_digest=change["termination_notice"]["digest"]),
    )
    current.refresh_from_db()
    assert (
        current.status == "termination_pending"
        and current.occupancy_status == "occupied"
    )
    assert RentalInventoryDayLock.objects.filter(lease=current).exists()
    future_now = datetime.combine(
        ending_day, datetime.min.time(), tzinfo=dt_timezone.utc
    ) + timedelta(hours=12)
    monkeypatch.setattr(timezone, "now", lambda: future_now)
    assert process_rental_changes()["applied"] == 1
    current.refresh_from_db()
    assert current.status == "ended" and current.occupancy_status == "move_out_pending"
    assert RentalInventoryDayLock.objects.filter(lease=current).exists()
    handover = post(
        owner,
        f"leases/{current.id}/handovers/",
        command(
            kind="move_out",
            possession_on=str(ending_day),
            condition={"summary": "Reviewed key condition"},
            keys={"count": 2},
            meters={},
            inventory=[],
            evidence_ids=[],
        ),
        201,
    ).data["resource"]
    for actor in [owner, tenant]:
        handover = post(
            actor,
            f"handovers/{handover['id']}/respond/",
            command(handover["revision"], decision="accept"),
        ).data["resource"]
    assert not RentalInventoryDayLock.objects.filter(lease=current).exists()
    current.refresh_from_db()
    assert (
        current.occupancy_status == "returned"
        and current.financial_closure_status == "open"
    )

    plan, response, _ = response_for(
        next_owner, tenant, next_prop, read(tenant, plan["id"]), next_offer
    )
    interest = post(
        tenant,
        "rental-interests/",
        command(
            property_id=str(next_prop.id),
            offer_id=next_offer,
            offer_revision=2,
            desired_start=plan["starts_on"],
            months=1,
            occupants=1,
            academic_plan_id=plan["id"],
            academic_revision=plan["requirements_revision"],
            source_housing_offer_id=response["id"],
            source_housing_offer_revision=response["revision"],
        ),
        201,
    ).data["resource"]
    run_interest_to_activation(
        (next_owner, tenant, owner, next_prop, next_offer),
        existing_interest=interest,
        artifact_name="synthetic-student-internship-tenancy",
    )
    new = Lease.objects.get(tenant=tenant, property=next_prop)
    new_deposit = DepositAgreement.objects.get(lease=new)
    old_deposit = DepositAgreement.objects.get(lease=current)
    assert new.status == "active" and new.owner != current.owner
    assert new_deposit.pk != old_deposit.pk and new_deposit.collected_minor == 1_000_000
    assert old_deposit.returned_minor == 0
    assert new.invoices.get().applied_minor == 2_000_000

    base = f"leases/{current.id}/final-settlement/"
    initial = authenticated(owner).get(API + base).data
    settlement = post(
        owner,
        base + "propose/",
        command(
            initial["revision"],
            lines=[
                {
                    "type": "deposit_deduction",
                    "description": "Reviewed replacement key",
                    "amount": {"amount_minor": 200_000},
                    "evidence_ids": [],
                }
            ],
        ),
    ).data["resource"]
    post(tenant, base + "respond/", command(settlement["revision"], action="accept"))
    old_deposit.refresh_from_db()
    assert old_deposit.returned_minor == 0  # Approval is not repayment.
    assert process_rental_closure()["refunds"] == 1
    assert process_rental_closure()["refunds"] == 0
    old_deposit.refresh_from_db()
    new_deposit.refresh_from_db()
    assert (
        old_deposit.returned_minor == 800_000
        and new_deposit.collected_minor == 1_000_000
    )
    assert RefundRequest.objects.get(lease=current).amount_minor == 800_000
    assert not RefundRequest.objects.filter(lease=new).exists()
    staff = operator("payout_operator")
    payout = post(
        staff,
        "operations/payouts/execute/",
        command(
            payable_ids=[
                str(x) for x in current.owner_payables.values_list("id", flat=True)
            ]
        ),
        201,
    ).data["resource"]
    post(
        staff,
        f"operations/payouts/{payout['id']}/reconcile/",
        command(payout["revision"]),
    )
    process_rental_closure()
    current.refresh_from_db()
    new.refresh_from_db()
    assert current.financial_closure_status == "closed" and current.status == "ended"
    assert new.status == "active" and new.financial_closure_status == "open"
    assert read(tenant, plan["id"])["participants"][0]["lease_id"] == str(new.id)
    for lease in [current, new]:
        for entry in lease.ledger_transactions.all():
            assert sum(
                entry.entries.filter(direction="debit").values_list(
                    "amount_minor", flat=True
                )
            ) == sum(
                entry.entries.filter(direction="credit").values_list(
                    "amount_minor", flat=True
                )
            )
    artifact(
        "relocation-result",
        {
            "old_lease_id": str(current.id),
            "new_lease_id": str(new.id),
            "old_status": current.status,
            "old_financial_closure": current.financial_closure_status,
            "new_status": new.status,
            "old_deposit_returned_minor": old_deposit.returned_minor,
            "new_deposit_collected_minor": new_deposit.collected_minor,
            "deposit_transfer": False,
        },
    )
