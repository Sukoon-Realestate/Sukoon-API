"""Irrecoverable source expiry must lead to a new package, not a dead editor."""

from datetime import timedelta

import pytest
from django.utils import timezone

from core_apps.features.services.company import contract_preparation as prep
from core_apps.features.services.company import contract_projection
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_company_contract_preparation import (
    API,
    authenticated,
    command,
    company_setup,
    create,
    cycle,
    policy,
    rental_participants,
    respond,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "reason", ["quote_expired", "dates_expired", "offer_changed", "hold_expired"]
)
def test_package_requiring_new_quote_does_not_offer_unusable_revision(
    cycle, reason, monkeypatch
):
    item = create(cycle)
    if reason == "hold_expired":
        for role in ["owner", "signer", "payer", "employee", "colleague"]:
            response = respond(cycle, item, role)
            assert response.status_code == 200
        item.refresh_from_db()
        response = authenticated(cycle["coordinator"]).post(
            API + f"company-contract-preparations/{item.id}/reserve/",
            command(expected_revision=item.revision),
            format="json",
        )
        assert response.status_code == 200
        item.refresh_from_db()
        hold = item.booking.hold
        hold.expires_at = timezone.now() - timedelta(seconds=1)
        hold.save(update_fields=["expires_at"])
    elif reason == "quote_expired":
        booking = item.booking
        booking.quote_expires_at = timezone.now() - timedelta(seconds=1)
        booking.save(update_fields=["quote_expires_at"])
    elif reason == "dates_expired":
        # The reviewed package's interval is immutable when the need changes.
        # Advance the clock past that interval instead of rewriting the need.
        monkeypatch.setattr(
            "core_apps.features.services.company.contract_snapshot.timezone.localdate",
            lambda: item.booking.request.starts_on + timedelta(days=1),
        )
    else:
        offer = item.booking.offer
        # Publication pauses are reversible without changing reviewed terms.
        # This case is an actual commercial change requiring a new quote.
        offer.monthly_rent_minor += 100
        offer.save(update_fields=["monthly_rent_minor"])

    current = prep.access.get(cycle["coordinator"], item.id)
    before = (current.revision, current.snapshot_digest, current.state)
    view = contract_projection.payload(current, cycle["coordinator"])
    assert view["effective_state"] == "review_required"
    assert reason in view["blocking_reasons"]
    # The editor cannot change this original package's expired quote/hold,
    # arrival period or commercially approved source. Direct writes already fail.
    with pytest.raises(RentalConflict) as error:
        prep.prepare(
            cycle["coordinator"],
            current.booking.id,
            {**cycle["body"], "expected_revision": current.revision},
        )
    assert error.value.get_codes() == reason
    current.refresh_from_db()
    assert (current.revision, current.snapshot_digest, current.state) == before
    assert not view["can_revise"]
    assert not view["can_reserve"] and not view["can_create_agreement"]
    assert view["can_withdraw"]
    closed = prep.withdraw(
        cycle["coordinator"], item.id, command(expected_revision=current.revision)
    )
    assert closed.state == "withdrawn" and closed.booking.status == "withdrawn"


def test_current_source_keeps_editing_available_and_employee_cannot_edit(cycle):
    item = create(cycle)
    current = prep.access.get(cycle["coordinator"], item.id)
    view = contract_projection.payload(current, cycle["coordinator"])
    assert view["can_revise"] and view["can_withdraw"]
    employee = contract_projection.payload(current, cycle["employee"])
    assert not employee["can_revise"] and not employee["can_withdraw"]


def test_replaceable_expired_mandate_keeps_preparation_editor_available(cycle):
    item = create(cycle)
    mandate = item.signer_mandate
    mandate.valid_until = timezone.now() - timedelta(seconds=1)
    mandate.save(update_fields=["valid_until"])
    current = prep.access.get(cycle["coordinator"], item.id)
    view = contract_projection.payload(current, cycle["coordinator"])
    assert "mandate_unavailable" in view["blocking_reasons"]
    assert view["can_revise"] and view["can_withdraw"]
