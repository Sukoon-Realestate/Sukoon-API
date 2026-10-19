"""Company debtor lifecycle through HTTP, canonical ledger and PostgreSQL locks.

People, authority evidence and provider events here are explicitly synthetic.
"""

from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.features.tests.test_company_contract_preparation import (
    cycle,
    person,
    create as prepare,
    respond as preparation_response,
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
)
from core_apps.features.models import CompanyTenancy, Lease, CompanyBudgetReservation


@pytest.fixture(autouse=True)
def expose_unexpected_exceptions(settings):
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "EXCEPTION_HANDLER": "rest_framework.views.exception_handler",
    }


def act(item, user, action, **values):
    item.lease.refresh_from_db()
    return authenticated(user).post(
        API + f"company-tenancies/{item.id}/{action}/",
        command(expected_revision=item.lease.revision, **values),
        format="json",
    )


@pytest.fixture
def agreement(cycle):
    operator = person("execution-reviewer")
    operator.is_staff = operator.is_superuser = True
    operator.save()
    for mandate in cycle["mandates"]:
        response = authenticated(operator).post(
            API + f"company-mandates/{mandate.id}/execution-review/",
            command(
                expected_revision=mandate.revision,
                evidence_reference="synthetic-operator-evidence",
                verified_until=(timezone.now() + timedelta(days=20)).isoformat(),
                reason="Synthetic authority review",
            ),
            format="json",
        )
        assert response.status_code == 200, response.data
    prep = prepare(cycle)
    for role in ["owner", "signer", "payer", "employee", "colleague"]:
        response = preparation_response(cycle, prep, role)
        assert response.status_code == 200, response.data
    prep.refresh_from_db()
    response = authenticated(cycle["coordinator"]).post(
        API + f"company-contract-preparations/{prep.id}/reserve/",
        command(expected_revision=prep.revision),
        format="json",
    )
    assert response.status_code == 200, response.data
    prep.refresh_from_db()
    body = command(expected_revision=prep.revision)
    path = API + f"company-contract-preparations/{prep.id}/agreement/"
    response = authenticated(cycle["coordinator"]).post(path, body, format="json")
    assert response.status_code == 201, response.data
    return cycle, CompanyTenancy.objects.get(preparation=prep), path, body


@pytest.mark.django_db
def test_company_is_canonical_debtor_and_create_replays(agreement):
    cycle, item, path, body = agreement
    assert (
        item.lease.tenant_id is None
        and item.lease.renter_company_id == cycle["company"].pk
    )
    assert item.lease.terms["employees_are_debtors"] is False
    assert item.preparation.booking.assignments.count() == 2
    replay = authenticated(cycle["coordinator"]).post(path, body, format="json")
    assert replay.status_code == 201, replay.data
    assert CompanyTenancy.objects.count() == Lease.objects.count() == 1


@pytest.mark.django_db
def test_company_private_projection_and_preparation_handoff(agreement):
    cycle, item, _, _ = agreement
    employee = authenticated(cycle["employee"]).get(
        API + f"company-tenancies/{item.id}/"
    )
    assert employee.status_code == 200, employee.data
    assert employee.data["terms"] == {} and employee.data["invoices"] == []
    assert len(employee.data["assignments"]) == 1 and employee.data["package"] == {}
    stranger = person("stranger")
    assert (
        authenticated(stranger).get(API + f"company-tenancies/{item.id}/").status_code
        == 404
    )
    prep = (
        authenticated(cycle["coordinator"])
        .get(API + f"company-contract-preparations/{item.preparation.id}/")
        .data
    )
    assert prep["tenancy_id"] == str(item.id) and prep["responses"] == []
    assert not prep["can_withdraw"] and not prep["can_revise"]


@pytest.mark.django_db
def test_unsigned_cancel_releases_all_units_and_budget(agreement):
    cycle, item, _, _ = agreement
    response = act(item, cycle["coordinator"], "cancel", reason="No longer needed")
    assert response.status_code == 200, response.data
    item.lease.refresh_from_db()
    assert item.lease.status == "cancelled"
    assert not item.lease.inventory_day_locks.exists()
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).status
        == "released"
    )
    assert item.lease.financial_closure_status == "closed"


@pytest.mark.django_db
def test_provider_absence_never_marks_review_as_signature(agreement, settings):
    cycle, item, _, _ = agreement
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    for role in ["owner", "signer"]:
        response = act(item, cycle[role], "review", role=role, digest=item.terms_digest)
        assert response.status_code == 200, response.data
    response = act(item, cycle["owner"], "submit_signature")
    assert response.status_code == 403, response.data
    item.lease.refresh_from_db()
    assert item.lease.status == "draft" and not item.lease.signing_sessions.exists()


@pytest.fixture
def signed_agreement(agreement):
    from core_apps.features.rental_phase2_views_parts.apply_fake_rental_event import (
        apply_fake_rental_event,
    )

    cycle, item, _, _ = agreement
    for role in ["owner", "signer"]:
        result = act(item, cycle[role], "review", role=role, digest=item.terms_digest)
        assert result.status_code == 200, result.data
    result = act(item, cycle["owner"], "submit_signature")
    assert result.status_code == 200, result.data
    item.lease.refresh_from_db()
    for role in ["owner", "signer"]:
        result = act(item, cycle[role], "sign", digest=item.lease.document_hash)
        assert result.status_code == 200, result.data
        session = item.lease.signing_sessions.get(signer=cycle[role])
        apply_fake_rental_event(
            {
                "type": "signature.completed",
                "provider_session_id": session.provider_session_id,
            }
        )
    item.lease.refresh_from_db()
    assert item.lease.status == "signed" and item.lease.invoices.count() == 1
    return cycle, item


@pytest.fixture
def active_agreement(signed_agreement):
    from core_apps.features.rental_phase3_views_parts.owner_payables import (
        apply_fake_payment_event,
    )

    cycle, item = signed_agreement
    invoice = item.lease.invoices.get()
    client = authenticated(cycle["payer"])
    result = client.post(
        API + f"rent-invoices/{invoice.id}/quote/",
        command(expected_revision=invoice.revision),
        format="json",
    )
    assert result.status_code == 201, result.data
    quote = result.data["resource"]
    result = client.post(
        API + f"rent-invoices/{invoice.id}/checkout/",
        command(
            expected_revision=invoice.revision,
            invoice_id=str(invoice.id),
            quote_id=quote["quote_id"],
        ),
        format="json",
    )
    assert result.status_code == 201, result.data
    attempt = invoice.payment_attempts.get()
    apply_fake_payment_event(
        {
            "event_id": f"synthetic-capture:{attempt.id}",
            "type": "payment.captured",
            "sequence": 1,
            "payment_attempt_id": str(attempt.id),
            "amount_minor": attempt.amount_minor,
            "currency": "EGP",
        }
    )
    item.lease.refresh_from_db()
    assert item.lease.status == "active"
    return cycle, item


@pytest.mark.django_db
def test_signing_and_capture_activate_exact_company_inventory(active_agreement):
    cycle, item = active_agreement
    assert set(
        item.lease.inventory_day_locks.values_list("property_id", flat=True)
    ) == {p.pk for p in cycle["units"]}
    assert not item.lease.inventory_day_locks.exclude(kind="occupied").exists()
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).status
        == "committed"
    )
    assert (
        item.lease.invoices.get().payment_attempts.get().payer_id == cycle["payer"].pk
    )


@pytest.mark.django_db
def test_employees_and_coordinators_cannot_pay_company_invoice(signed_agreement):
    cycle, item = signed_agreement
    invoice = item.lease.invoices.get()
    for role in ["employee", "coordinator", "signer", "owner"]:
        result = authenticated(cycle[role]).post(
            API + f"rent-invoices/{invoice.id}/quote/",
            command(expected_revision=invoice.revision),
            format="json",
        )
        assert result.status_code in {403, 404}, result.data


def decide_change(cycle, item, change, participants):
    for role, user in participants:
        result = act(
            item,
            user,
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
        assert result.status_code == 200, result.data
    change.refresh_from_db()
    return change


def handover(cycle, item, kind, day):
    result = act(
        item,
        cycle["coordinator"],
        "handover",
        kind=kind,
        possession_on=str(day),
        condition={"summary": "Synthetic inspection"},
        keys={"received": True},
        meters={},
        inventory=[],
        evidence_ids=[],
        reason="Bilateral synthetic possession",
    )
    assert result.status_code == 200, result.data
    change = item.changes.get(kind=kind, state="pending")
    decide_change(
        cycle,
        item,
        change,
        [("owner", cycle["owner"]), ("coordinator", cycle["coordinator"])],
    )


def presence(cycle, item, row, kind, day):
    result = act(
        item,
        row.employee,
        "presence",
        assignment_id=str(row.id),
        kind=kind,
        possession_on=str(day),
    )
    assert result.status_code == 200, result.data
    record = row.occupancy_confirmations.get(kind=kind)
    for role, user in [("employee", row.employee), ("owner", cycle["owner"])]:
        result = act(
            item,
            user,
            "presence_respond",
            confirmation_id=str(record.id),
            role=role,
            decision="accept",
        )
        assert result.status_code == 200, result.data
    row.refresh_from_db()
    return row


@pytest.mark.django_db
def test_possession_employee_departure_and_return_are_independent(active_agreement):
    from unittest.mock import patch

    cycle, item = active_agreement
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        handover(cycle, item, "move_in", day)
        row = item.preparation.booking.assignments.get(employee=cycle["employee"])
        presence(cycle, item, row, "arrival", day)
        assert row.occupancy_status == "occupied"
        result = act(
            item,
            cycle["coordinator"],
            "handover",
            kind="move_out",
            possession_on=str(day),
            condition={},
            keys={},
            meters={},
            inventory=[],
            evidence_ids=[],
            reason="Premises return",
        )
        assert result.status_code == 200
        change = item.changes.get(kind="move_out")
        result = act(
            item,
            cycle["owner"],
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="owner",
            decision="accept",
        )
        assert result.status_code == 200
        result = act(
            item,
            cycle["coordinator"],
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="coordinator",
            decision="accept",
        )
        assert result.status_code == 409, result.data
        assert item.lease.inventory_day_locks.exists()
        presence(cycle, item, row, "departure", day)
        decide_change(cycle, item, change, [("coordinator", cycle["coordinator"])])
    item.lease.refresh_from_db()
    assert item.lease.occupancy_status == "returned" and item.lease.status == "active"
    assert not item.lease.inventory_day_locks.exists()
    assert item.lease.invoices.exists()  # Actual return cannot cancel rent.


@pytest.fixture
def occupied_agreement(active_agreement):
    from unittest.mock import patch

    cycle, item = active_agreement
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        handover(cycle, item, "move_in", day)
        for row in item.preparation.booking.assignments.select_related("employee"):
            presence(cycle, item, row, "arrival", day)
    item.lease.refresh_from_db()
    return cycle, item


@pytest.mark.django_db
def test_replacement_requires_all_people_then_actual_departure(occupied_agreement):
    from unittest.mock import patch
    from core_apps.features.models import CompanyMembership

    cycle, item = occupied_agreement
    newcomer = person("replacement")
    CompanyMembership.objects.create(
        company=cycle["company"], user=newcomer, is_employee=True
    )
    row = item.preparation.booking.assignments.get(employee=cycle["employee"])
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        response = act(
            item,
            cycle["coordinator"],
            "replace_employee",
            assignment_id=str(row.id),
            employee_id=str(newcomer.id),
            effective_on=str(day),
            reason="Consensual replacement",
        )
        assert response.status_code == 200, response.data
        change = item.changes.get(kind="replacement")
        view = authenticated(newcomer).get(API + f"company-tenancies/{item.id}/").data
        assert view["changes"][0]["roles_to_decide"] == ["incoming_employee"]
        assert view["terms"] == {} and view["invoices"] == []
        decide_change(
            cycle,
            item,
            change,
            [
                ("owner", cycle["owner"]),
                ("coordinator", cycle["coordinator"]),
                ("incoming_employee", newcomer),
                ("outgoing_employee", cycle["employee"]),
            ],
        )
        assert change.state == "waiting_departure"
        assert not item.preparation.booking.assignments.filter(
            employee=newcomer
        ).exists()
        presence(cycle, item, row, "departure", day)
        response = act(
            item, cycle["coordinator"], "resume_change", change_id=str(change.id)
        )
        assert response.status_code == 200, response.data
        change.refresh_from_db()
        assert change.state == "applied"
        assert (
            item.preparation.booking.assignments.get(employee=newcomer).occupancy_status
            == "arrival_pending"
        )
        assert item.lease.inventory_day_locks.exists()
        again = act(
            item,
            cycle["coordinator"],
            "replace_employee",
            assignment_id=str(row.id),
            employee_id=str(newcomer.id),
            effective_on=str(day),
            reason="Repeat",
        )
        assert again.status_code == 409


@pytest.mark.django_db
def test_replacement_decline_preserves_existing_stay(occupied_agreement):
    from unittest.mock import patch
    from core_apps.features.models import CompanyMembership

    cycle, item = occupied_agreement
    newcomer = person("declining-replacement")
    CompanyMembership.objects.create(
        company=cycle["company"], user=newcomer, is_employee=True
    )
    row = item.preparation.booking.assignments.get(employee=cycle["employee"])
    with patch("django.utils.timezone.localdate", return_value=item.lease.start_date):
        assert (
            act(
                item,
                cycle["coordinator"],
                "replace_employee",
                assignment_id=str(row.id),
                employee_id=str(newcomer.id),
                effective_on=str(item.lease.start_date),
                reason="Review replacement",
            ).status_code
            == 200
        )
        change = item.changes.get(kind="replacement")
        result = act(
            item,
            newcomer,
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="incoming_employee",
            decision="decline",
            reason="Not accepted",
        )
        assert result.status_code == 200, result.data
    row.refresh_from_db()
    assert (
        row.occupancy_status == "occupied"
        and item.preparation.booking.assignments.count() == 2
    )
    assert (
        authenticated(newcomer).get(API + f"company-tenancies/{item.id}/").status_code
        == 404
    )


def service(item, user, request, action, **data):
    return act(
        item,
        user,
        "maintenance_action",
        maintenance_id=str(request.id),
        maintenance_action=action,
        reason="Synthetic service decision",
        **data,
    )


@pytest.mark.django_db
def test_company_maintenance_unit_privacy_access_cost_and_resolution(
    occupied_agreement,
):
    from unittest.mock import patch

    cycle, item = occupied_agreement
    row = item.preparation.booking.assignments.get(employee=cycle["employee"])
    result = act(
        item,
        cycle["employee"],
        "maintenance",
        property_id=str(row.property.id),
        title="Water leak",
        description="Inspect the assigned unit",
        category="plumbing",
        priority="urgent",
    )
    assert result.status_code == 200, result.data
    request = item.lease.maintenance_requests.get()
    assert (
        authenticated(cycle["colleague"])
        .get(API + f"company-tenancies/{item.id}/")
        .data["maintenance"]
        == []
    )
    assert service(item, cycle["employee"], request, "acknowledge").status_code == 403
    assert service(item, cycle["owner"], request, "acknowledge").status_code == 200
    start, end = timezone.now() + timedelta(hours=1), timezone.now() + timedelta(
        hours=2
    )
    result = service(
        item,
        cycle["owner"],
        request,
        "propose_appointment",
        appointment_at=start.isoformat(),
        appointment_ends_at=end.isoformat(),
    )
    assert result.status_code == 200, result.data
    assert (
        service(item, cycle["coordinator"], request, "accept_appointment").status_code
        == 403
    )
    assert (
        service(item, cycle["employee"], request, "accept_appointment").status_code
        == 200
    )
    assert (
        service(
            item,
            cycle["owner"],
            request,
            "propose_cost",
            cost_minor=5000,
            cost_payer="company",
        ).status_code
        == 200
    )
    assert service(item, cycle["employee"], request, "approve_cost").status_code == 403
    assert service(item, cycle["payer"], request, "approve_cost").status_code == 200
    with patch("django.utils.timezone.now", return_value=start + timedelta(minutes=5)):
        assert (
            service(item, cycle["employee"], request, "revoke_access").status_code
            == 200
        )
        assert service(item, cycle["owner"], request, "start_work").status_code in {
            403,
            409,
        }
        assert (
            service(item, cycle["employee"], request, "accept_appointment").status_code
            == 200
        )
        result = service(item, cycle["owner"], request, "start_work")
        assert result.status_code == 200, result.data
        assert (
            service(item, cycle["owner"], request, "report_resolved").status_code == 200
        )
        assert (
            service(item, cycle["employee"], request, "confirm_resolved").status_code
            == 200
        )
    request.refresh_from_db()
    assert request.status == "resolved"
    assert item.lease.invoices.count() == 1  # Approval is not a second bill or capture.


@pytest.mark.django_db
def test_unsigned_expiry_releases_whole_portfolio_but_signature_uncertainty_does_not(
    agreement,
):
    from core_apps.features.services.company.tenancy_expiry import expire

    cycle, item, _, _ = agreement
    at = item.lease.hold_expires_at + timedelta(seconds=1)
    assert expire(item, at)
    assert not item.lease.inventory_day_locks.exists()
    item.lease.refresh_from_db()
    assert item.lease.status == "expired"
    assert (
        act(
            item, cycle["coordinator"], "cancel", reason="Close expired draft"
        ).status_code
        == 200
    )


@pytest.mark.django_db
def test_late_signature_is_recorded_for_reconciliation_and_duplicate_is_idempotent(
    agreement,
):
    from unittest.mock import patch
    from core_apps.features.services.company.tenancy_expiry import expire
    from core_apps.features.rental_phase2_views_parts.apply_fake_rental_event import (
        apply_fake_rental_event,
    )

    cycle, item, _, _ = agreement
    for role in ["owner", "signer"]:
        assert (
            act(
                item, cycle[role], "review", role=role, digest=item.terms_digest
            ).status_code
            == 200
        )
    assert act(item, cycle["owner"], "submit_signature").status_code == 200
    item.lease.refresh_from_db()
    assert (
        act(item, cycle["signer"], "sign", digest=item.lease.document_hash).status_code
        == 200
    )
    session = item.lease.signing_sessions.get()
    event = {
        "type": "signature.completed",
        "provider_session_id": session.provider_session_id,
    }
    with patch(
        "django.utils.timezone.now",
        return_value=item.lease.hold_expires_at + timedelta(minutes=1),
    ):
        assert not expire(item)
        apply_fake_rental_event(event)
        apply_fake_rental_event(event)
    session.refresh_from_db()
    item.lease.refresh_from_db()
    assert (
        session.status == "review_required"
        and item.lease.status == "pending_signatures"
    )
    assert item.lease.inventory_day_locks.exists() and not item.lease.invoices.exists()
    assert (
        act(item, cycle["coordinator"], "cancel", reason="Unsafe discard").status_code
        == 409
    )


@pytest.mark.django_db
def test_company_receipt_has_no_historical_private_projection_and_revocation_blocks_replay(
    agreement,
):
    from core_apps.features.models import PrivateAccessRevocation

    cycle, item, path, body = agreement
    replay = authenticated(cycle["coordinator"]).post(path, body, format="json")
    assert set(replay.data["resource"]) == {"id", "revision"}
    PrivateAccessRevocation.objects.create(
        lease=item.lease, user=cycle["employee"], reason="Test revocation"
    )
    client = authenticated(cycle["employee"])
    assert client.get(API + f"company-tenancies/{item.id}/").status_code == 404
    assert client.get(API + "company-tenancies/").data["count"] == 0


@pytest.mark.django_db
def test_termination_at_billing_boundary_and_full_original_capture_refund(
    active_agreement,
):
    from unittest.mock import patch
    from core_apps.features.services.refunds import execute_refund
    from core_apps.features.services.rental_phase6 import evaluate_financial_closure
    from core_apps.features.models import FinalSettlement, LedgerEntry

    cycle, item = active_agreement
    day = (
        item.lease.start_date
    )  # No possession took place in this synthetic cancellation.
    with patch("django.utils.timezone.localdate", return_value=day):
        result = act(
            item,
            cycle["owner"],
            "terminate",
            effective_on=str(day),
            reason="Bilateral end before move-in",
        )
        assert result.status_code == 200, result.data
        change = item.changes.get(kind="termination")
        decide_change(
            cycle,
            item,
            change,
            [(role, cycle[role]) for role in ["owner", "signer", "payer"]],
        )
        item.lease.refresh_from_db()
        assert (
            item.lease.status == "ended"
            and item.lease.occupancy_status == "not_started"
        )
        assert (
            item.lease.inventory_day_locks.exists()
        )  # Legal end is not a possession confirmation.
        handover(cycle, item, "move_out", day)
        invoice = item.lease.invoices.get()
        rent = item.lease.owner_payables.get().gross_minor
        result = act(
            item,
            cycle["payer"],
            "settlement",
            reason="Bilateral return of original rent and remaining deposit",
            lines=[
                {
                    "id": "rent-return",
                    "type": "refund",
                    "description": "Agreed return",
                    "amount": {"amount_minor": rent, "currency": "EGP", "exponent": 2},
                }
            ],
        )
        assert result.status_code == 200, result.data
        change = item.changes.get(kind="settlement")
        decide_change(
            cycle,
            item,
            change,
            [(role, cycle[role]) for role in ["owner", "signer", "payer"]],
        )
        settlement = FinalSettlement.objects.get(lease=item.lease)
        assert settlement.execution_status == "executed"
        item.lease.refresh_from_db()
        assert item.lease.financial_closure_status == "open"
        refund = item.lease.refund_requests.get()
        assert refund.status == "approved" and refund.requester_id == cycle["payer"].pk
        execute_refund(refund)
        assert act(item, cycle["payer"], "reconcile").status_code == 200
    item.lease.refresh_from_db()
    assert item.lease.financial_closure_status == "closed"
    assert (
        item.preparation.booking.__class__.objects.get(
            pk=item.preparation.booking_id
        ).status
        == "closed"
    )
    assert not item.lease.inventory_day_locks.exists()
    refund.refresh_from_db()
    assert refund.status == "succeeded"


@pytest.mark.django_db
def test_company_can_replace_absent_coordinator_without_rewriting_contract(
    active_agreement,
):
    from core_apps.features.models import CompanyMembership

    cycle, item = active_agreement
    newcomer = person("successor-coordinator")
    member = CompanyMembership.objects.create(
        company=cycle["company"], user=newcomer, is_coordinator=True
    )
    old = cycle["company"].memberships.get(user=cycle["coordinator"])
    old.is_coordinator = False
    old.save()
    original_signatures = list(
        item.lease.signing_sessions.values_list("signer_id", "document_hash")
    )
    response = act(
        item,
        cycle["coordinator"],
        "replace_authority",
        signer_mandate_id=str(item.signer_mandate.id),
        payer_mandate_id=str(item.payer_mandate.id),
        reviewer_membership_id=str(
            cycle["company"].memberships.get(user=cycle["reviewer"]).id
        ),
        coordinator_membership_id=str(member.id),
        reason="Assign a current servicing coordinator",
    )
    assert response.status_code == 200, response.data
    change = item.changes.get(kind="authority")
    assert (
        authenticated(newcomer).get(API + f"company-tenancies/{item.id}/").status_code
        == 200
    )
    decide_change(
        cycle,
        item,
        change,
        [
            ("administrator", cycle["reviewer"]),
            ("new_signer", cycle["signer"]),
            ("new_payer", cycle["payer"]),
            ("new_coordinator", newcomer),
        ],
    )
    item.refresh_from_db()
    assert item.coordinator_id == newcomer.pk
    assert item.preparation.booking.request.coordinator_id == cycle["coordinator"].pk
    assert (
        list(item.lease.signing_sessions.values_list("signer_id", "document_hash"))
        == original_signatures
    )
    assert act(item, cycle["coordinator"], "reconcile").status_code == 403
    assert act(item, newcomer, "reconcile").status_code == 200


@pytest.mark.django_db
def test_revoked_payer_cannot_replay_quote_or_checkout(signed_agreement):
    cycle, item = signed_agreement
    invoice = item.lease.invoices.get()
    client = authenticated(cycle["payer"])
    body = command(expected_revision=invoice.revision)
    path = API + f"rent-invoices/{invoice.id}/quote/"
    response = client.post(path, body, format="json")
    assert response.status_code == 201
    item.payer_mandate.state = "revoked"
    item.payer_mandate.save()
    assert client.post(path, body, format="json").status_code == 403
    result = client.post(
        API + f"rent-invoices/{invoice.id}/checkout/",
        command(
            expected_revision=invoice.revision,
            invoice_id=str(invoice.id),
            quote_id=response.data["resource"]["quote_id"],
        ),
        format="json",
    )
    assert result.status_code == 403
    assert not invoice.payment_attempts.exists()


@pytest.mark.django_db
def test_checkout_recovery_requires_current_company_payer(signed_agreement):
    cycle, item = signed_agreement
    invoice = item.lease.invoices.get()
    path = API + "payment-attempts/"
    body = command(action="resolve_checkout", invoice_id=str(invoice.id))
    for role in ["employee", "coordinator", "owner"]:
        assert authenticated(cycle[role]).post(
            path, body, format="json"
        ).status_code in {403, 404}
    result = authenticated(cycle["payer"]).post(path, body, format="json")
    assert result.status_code == 200 and result.data["absence_confirmed"] is True
    item.payer_mandate.state = "revoked"
    item.payer_mandate.save()
    assert (
        authenticated(cycle["payer"])
        .post(
            path,
            command(action="resolve_checkout", invoice_id=str(invoice.id)),
            format="json",
        )
        .status_code
        == 403
    )
    assert not invoice.payment_attempts.exists()


@pytest.mark.django_db
def test_operator_authority_review_is_independent_and_admin_form_uses_same_command(
    cycle, client, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    import uuid
    from django.urls import reverse
    from core_apps.features.models import CompanyMandate

    item = cycle["mandates"][0]
    internal = cycle["coordinator"]
    internal.is_staff = internal.is_superuser = True
    internal.save()
    path = reverse("admin:company-execution-review", args=[item.pk])
    client.force_login(internal)
    body = {
        "request_key": str(uuid.uuid4()),
        "revision": item.revision,
        "verified_until": (timezone.now() + timedelta(days=10)).isoformat(),
        "evidence_reference": "synthetic-reviewed-document",
        "reason": "Independent test",
    }
    response = client.post(path, body)
    assert response.status_code == 200  # Form remains with independent-review error.
    item.refresh_from_db()
    assert item.execution_reviewed_by_id is None
    operator = person("independent-admin-operator")
    operator.is_staff = operator.is_superuser = True
    operator.save()
    client.force_login(operator)
    assert client.get(path).status_code == 200
    response = client.post(path, {**body, "request_key": str(uuid.uuid4())})
    assert response.status_code == 302
    item.refresh_from_db()
    assert item.execution_reviewed_by_id == operator.pk
    assert item.execution_reference == body["evidence_reference"]


@pytest.mark.django_db
def test_company_new_business_off_keeps_existing_obligation_servicing(
    active_agreement, settings
):
    cycle, item = active_agreement
    settings.COMPANY_HOUSING_ENABLED = False
    assert act(item, cycle["coordinator"], "reconcile").status_code == 200
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_CONTROL_FILE = ""
    assert (
        authenticated(cycle["coordinator"])
        .get(API + f"company-tenancies/{item.id}/")
        .status_code
        == 200
    )
    assert act(item, cycle["coordinator"], "reconcile").status_code == 200


@pytest.mark.django_db(transaction=True)
def test_duplicate_company_create_and_cancel_serialize_without_double_effect(agreement):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from core_apps.features.models import RentalAuditEvent

    cycle, item, path, body = agreement
    results = parallel_calls(
        lambda _: authenticated(cycle["coordinator"]).post(path, body, format="json")
    )
    assert [r.status_code for r in results] == [201, 201]
    assert results[0].data == results[1].data
    body = command(expected_revision=item.lease.revision, reason="Concurrent retry")
    path = API + f"company-tenancies/{item.id}/cancel/"
    results = parallel_calls(
        lambda _: authenticated(cycle["coordinator"]).post(path, body, format="json")
    )
    assert [r.status_code for r in results] == [200, 200]
    assert results[0].data == results[1].data
    assert (
        RentalAuditEvent.objects.filter(
            subject_id=item.lease.id, action="company_unsigned_agreement_cancelled"
        ).count()
        == 1
    )
    assert not item.lease.inventory_day_locks.exists()


@pytest.mark.django_db(transaction=True)
def test_final_approval_and_payer_revocation_share_company_lock(active_agreement):
    from unittest.mock import patch
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    cycle, item = active_agreement
    day = item.lease.start_date
    with patch("django.utils.timezone.localdate", return_value=day):
        assert (
            act(
                item,
                cycle["owner"],
                "terminate",
                effective_on=str(day),
                reason="Concurrent review",
            ).status_code
            == 200
        )
        change = item.changes.get(kind="termination")
        decide_change(
            cycle,
            item,
            change,
            [("owner", cycle["owner"]), ("signer", cycle["signer"])],
        )
        item.lease.refresh_from_db()
        mandate = item.payer_mandate

        def call(index):
            if index:
                return authenticated(cycle["reviewer"]).post(
                    API + f"company-mandates/{mandate.id}/revoke/",
                    command(
                        expected_revision=mandate.revision, reason="Authority revoked"
                    ),
                    format="json",
                )
            return act(
                item,
                cycle["payer"],
                "respond_change",
                change_id=str(change.id),
                digest=change.snapshot_digest,
                role="payer",
                decision="accept",
            )

        results = parallel_calls(call)
    assert results[1].status_code == 200, results[1].data
    assert results[0].status_code in {200, 403, 409}, results[0].data
    change.refresh_from_db()
    item.lease.refresh_from_db()
    assert (change.state == "applied") == (results[0].status_code == 200)
    assert item.lease.status == ("ended" if change.state == "applied" else "active")


@pytest.mark.django_db
def test_habitability_restriction_after_capture_blocks_company_move_in(
    active_agreement,
):
    import uuid
    from unittest.mock import patch
    from core_apps.features.models import RentalEvidence
    from core_apps.features.services.rental_lifecycle.cases import open_system_case
    from core_apps.features.services.rental_lifecycle.habitability import report, assess
    from core_apps.features.tests.test_habitability_closure import (
        authorize,
        command as assessment_command,
    )

    cycle, item = active_agreement
    case = open_system_case(
        kind="habitability",
        source_key=str(uuid.uuid4()),
        lease=item.lease,
        actor=cycle["owner"],
        reason="Synthetic restriction after capture",
        next_action="Assess",
    )
    report(case, {"reported_severity": "urgent"})
    media = RentalEvidence.objects.create(
        lease=item.lease,
        uploader=cycle["owner"],
        request_key=uuid.uuid4(),
        original_name="inspection.png",
        content_type="image/png",
        size_bytes=10,
        sha256="b" * 64,
        storage_key="synthetic",
        malware_status="safe",
    )
    case.evidence.add(media)
    operator = authorize(case)
    assess(operator, case, assessment_command(case, media))
    before = item.lease.inventory_day_locks.count()
    with patch("django.utils.timezone.localdate", return_value=item.lease.start_date):
        response = act(
            item,
            cycle["coordinator"],
            "handover",
            kind="move_in",
            possession_on=str(item.lease.start_date),
            condition={},
            keys={},
            meters={},
            inventory=[],
            evidence_ids=[],
            reason="Try unsafe move-in",
        )
    assert response.status_code == 409, response.data
    assert item.lease.inventory_day_locks.count() == before
    assert not item.lease.handovers.exists()


@pytest.mark.django_db
def test_settlement_rejects_malformed_evidence_without_500(active_agreement):
    cycle, item = active_agreement
    response = act(
        item,
        cycle["payer"],
        "settlement",
        reason="Review invalid evidence",
        lines=[
            {
                "type": "damage",
                "description": "Review",
                "amount": {"amount_minor": 100, "currency": "EGP", "exponent": 2},
                "evidence_ids": ["not-a-file-id"],
            }
        ],
    )
    assert response.status_code == 400, response.data
    assert not item.changes.filter(kind="settlement").exists()


@pytest.mark.django_db(transaction=True)
def test_global_employee_assignment_guard_serializes_competing_writes(agreement):
    from django.db import transaction
    from core_apps.features.models import EmployeeAssignment
    from core_apps.features.services.company.assignment_locks import (
        lock_people,
        require_available,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls

    cycle, item, _, _ = agreement
    incoming = person("concurrent-employee")

    def place(index):
        try:
            with transaction.atomic():
                lock_people([incoming.id])
                require_available(incoming, item.lease.start_date, item.lease.end_date)
                EmployeeAssignment.objects.create(
                    item=item.preparation.booking,
                    employee=incoming,
                    property=cycle["units"][index],
                    starts_on=item.lease.start_date,
                    ends_on_exclusive=item.lease.end_date,
                )
            return "placed"
        except RentalConflict:
            return "conflict"

    assert sorted(parallel_calls(place)) == ["conflict", "placed"]
    assert EmployeeAssignment.objects.filter(employee=incoming).count() == 1


@pytest.mark.django_db
def test_expired_source_hides_commit_controls_but_keeps_recovery(agreement):
    cycle, item, _, _ = agreement
    Lease.objects.filter(pk=item.lease_id).update(
        hold_expires_at=timezone.now() - timedelta(seconds=1)
    )
    response = authenticated(cycle["owner"]).get(API + f"company-tenancies/{item.id}/")
    assert response.status_code == 200, response.data
    assert "hold_expired" in response.data["blocking_reasons"]
    assert not {"review", "submit_signature", "sign"} & set(response.data["actions"])
    assert {"cancel", "reconcile", "open_case"}.issubset(response.data["actions"])


@pytest.mark.django_db
def test_signed_unpaid_company_can_end_bilaterally_without_automatic_debt_erasure(
    signed_agreement,
):
    from unittest.mock import patch
    from core_apps.features.services.rental_phase3 import invoice_balance_minor

    cycle, item = signed_agreement
    invoice = item.lease.invoices.get()
    original_balance = invoice_balance_minor(invoice)
    with patch("django.utils.timezone.localdate", return_value=item.lease.start_date):
        response = act(
            item,
            cycle["owner"],
            "terminate",
            effective_on=str(item.lease.start_date),
            reason="Agreed end before payment and arrival",
        )
        assert response.status_code == 200, response.data
        change = item.changes.get(kind="termination")
        decide_change(
            cycle, item, change, [(r, cycle[r]) for r in ["owner", "signer", "payer"]]
        )
    item.lease.refresh_from_db()
    invoice.refresh_from_db()
    assert item.lease.status == "ended"
    assert invoice_balance_minor(invoice) == original_balance > 0
    assert item.lease.inventory_day_locks.exists()
    assert item.lease.financial_closure_status != "closed"


@pytest.mark.django_db
def test_chargeback_reopens_company_projection_and_original_budget_without_inventory_reallocation(
    active_agreement,
):
    from core_apps.features.models import FinalSettlement, OwnerPayable
    from core_apps.features.rental_phase3_views_parts.owner_payables import (
        apply_fake_payment_event,
    )
    from core_apps.features.services.rental_lifecycle.locks import lock_financial_lease
    from core_apps.features.services.rental_phase6 import evaluate_financial_closure
    from django.db import transaction

    cycle, item = active_agreement
    # Construct a closed historical financial state; the bilateral full closure is
    # independently exercised above. This case isolates a late authenticated event.
    invoice = item.lease.invoices.get()
    attempt = invoice.payment_attempts.get()
    Lease.objects.filter(pk=item.lease_id).update(
        status="ended", occupancy_status="returned"
    )
    item.lease.inventory_day_locks.all().delete()
    item.lease.deposit_agreement.delete()
    OwnerPayable.objects.filter(lease=item.lease).update(payout_status="succeeded")
    FinalSettlement.objects.create(
        lease=item.lease, status="accepted", execution_status="executed"
    )
    with transaction.atomic():
        lease = lock_financial_lease(item.lease)
        assert evaluate_financial_closure(lease) == []
    booking = item.preparation.booking
    booking.refresh_from_db()
    assert booking.status == "closed"
    reservation = CompanyBudgetReservation.objects.get(item=booking)
    approved_exposure = (reservation.rent_minor, reservation.deposit_minor)
    assert reservation.status == "released"
    apply_fake_payment_event(
        {
            "event_id": f"synthetic-chargeback:{attempt.id}",
            "type": "payment.chargeback",
            "sequence": 2,
            "payment_attempt_id": str(attempt.id),
            "amount_minor": attempt.amount_minor,
            "currency": "EGP",
        }
    )
    item.lease.refresh_from_db()
    booking.refresh_from_db()
    reservation.refresh_from_db()
    assert item.lease.financial_closure_status == "open"
    assert booking.status == "financial_review" and reservation.status == "committed"
    assert (reservation.rent_minor, reservation.deposit_minor) == approved_exposure
    assert not item.lease.inventory_day_locks.exists()
    assert item.lease.status == "ended" and item.lease.tenant_id is None


@pytest.mark.django_db
def test_company_statements_keep_actual_debtor_and_revoke_old_private_links(
    active_agreement,
):
    import json
    from urllib.parse import urlsplit
    from django.urls import reverse
    from rest_framework.test import APIClient
    from core_apps.features.models import RentalDocument, CompanyMembership
    from core_apps.features.services.private_rental_documents import generate

    cycle, item = active_agreement
    lease_id = item.lease.id
    response = authenticated(cycle["payer"]).post(
        API + "rental-statements/",
        command(
            expected_revision=item.lease.revision,
            lease_id=str(lease_id),
            starts_on="",
            ends_on_exclusive="",
        ),
        format="json",
    )
    assert response.status_code == 201, response.data
    document = RentalDocument.objects.get(id=response.data["resource"]["id"])
    assert generate(document)
    assert json.loads(bytes(document.private_content))["renter"] == {
        "kind": "company",
        "company_id": str(cycle["company"].id),
        "name": cycle["company"].name,
        "employees_are_debtors": False,
    }
    path = reverse("rental-document-download", args=[document.id])
    link = authenticated(cycle["payer"]).get(path)
    assert link.status_code == 200, link.data
    url = urlsplit(link.data["url"])
    target = url.path + "?" + url.query
    assert APIClient().get(target).status_code == 200
    assert authenticated(cycle["employee"]).get(path).status_code == 404
    assert (
        authenticated(cycle["employee"])
        .get(API + f"leases/{lease_id}/documents/")
        .status_code
        == 404
    )
    CompanyMembership.objects.filter(
        company=cycle["company"], user=cycle["payer"]
    ).update(is_active=False)
    assert authenticated(cycle["payer"]).get(path).status_code == 404
    assert APIClient().get(target).status_code == 404


@pytest.mark.django_db
def test_expired_pending_signature_cannot_be_replaced_with_new_unknown_operation(
    agreement,
):
    cycle, item, _, _ = agreement
    for role in ["owner", "signer"]:
        assert (
            act(
                item, cycle[role], "review", role=role, digest=item.terms_digest
            ).status_code
            == 200
        )
    assert act(item, cycle["owner"], "submit_signature").status_code == 200
    item.lease.refresh_from_db()
    assert (
        act(item, cycle["owner"], "sign", digest=item.lease.document_hash).status_code
        == 200
    )
    item.lease.signing_sessions.update(expires_at=timezone.now() - timedelta(seconds=1))
    from core_apps.features.tasks_parts.expire_rental_sources_and_holds import (
        reconcile_rental_provider_sessions,
    )

    reconcile_rental_provider_sessions()
    assert item.lease.signing_sessions.get().status == "pending"
    result = act(item, cycle["owner"], "sign", digest=item.lease.document_hash)
    assert result.status_code == 409, result.data
    assert item.lease.signing_sessions.count() == 1


@pytest.mark.parametrize("role", ["signer", "payer", "coordinator"])
@pytest.mark.django_db
def test_authority_succession_cannot_make_owner_a_company_counterparty(
    active_agreement, role
):
    from core_apps.features.models import CompanyMembership

    cycle, item = active_agreement
    owner_member = CompanyMembership.objects.create(
        company=cycle["company"], user=cycle["owner"], is_coordinator=True
    )
    if role in {"signer", "payer"}:
        mandate = getattr(item, role + "_mandate")
        mandate.membership = owner_member
        mandate.membership_revision = owner_member.revision
        mandate.save()
    response = act(
        item,
        cycle["coordinator"],
        "replace_authority",
        signer_mandate_id=str(item.signer_mandate.id),
        payer_mandate_id=str(item.payer_mandate.id),
        reviewer_membership_id=str(
            cycle["company"].memberships.get(user=cycle["reviewer"]).id
        ),
        coordinator_membership_id=str(
            owner_member.id
            if role == "coordinator"
            else cycle["company"].memberships.get(user=cycle["coordinator"]).id
        ),
        reason="Attempt to make opposing parties the same person",
    )
    assert response.status_code == 403, response.data
    assert not item.changes.filter(kind="authority").exists()
