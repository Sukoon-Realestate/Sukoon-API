"""Deletion review blocks new company preparation, never erases its reviewed record."""

# flake8: noqa: F401,F811
import pytest
from core_apps.users.models import AccountClosureRequest
from core_apps.features.company_contract_models import CompanyContractPreparation
from .test_company_contract_preparation import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    create,
    respond,
    command,
    authenticated,
    API,
)

pytestmark = pytest.mark.django_db


def close(user):
    return AccountClosureRequest.objects.create(
        user=user, active=True, reason="Local closure review"
    )


@pytest.mark.parametrize("who", ["owner", "coordinator", "employee", "signer", "payer"])
def test_closing_account_cannot_be_bound_by_new_preparation(cycle, who):
    close(cycle[who])
    response = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{cycle['item'].id}/contract-preparation/",
        cycle["body"],
        format="json",
    )
    assert response.status_code == 403, response.data
    assert not CompanyContractPreparation.objects.filter(booking=cycle["item"]).exists()


def test_existing_preparation_blocks_acceptance_but_preserves_history_and_decline(
    cycle,
):
    item = create(cycle)
    original_snapshot = item.snapshot
    close(cycle["employee"])
    result = respond(cycle, item, "owner")
    assert result.status_code == 403, result.data
    item.refresh_from_db()
    assert item.snapshot == original_snapshot
    assert not item.consents.filter(decision="accepted").exists()
    detail = authenticated(cycle["owner"]).get(
        API + f"company-contract-preparations/{item.id}/"
    )
    assert detail.status_code == 200
    assert "account_closure_pending" in detail.data["blocking_reasons"]
    assert {"role": "owner", "decision": "accepted"} in detail.data[
        "available_responses"
    ]
    assert {"role": "owner", "decision": "accepted"} not in detail.data["responses"]
    assert all(row["role"] == "owner" for row in detail.data["available_responses"])
    assert respond(cycle, item, "owner", decision="declined").status_code == 200
