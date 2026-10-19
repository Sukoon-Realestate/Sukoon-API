"""Real domain/HTTP writes with synthetic people; no signature/payment provider."""

from datetime import timedelta
import uuid
import pytest
from django.utils import timezone
from django.db import connection
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.features.company_models import (
    CompanyMembership,
    CompanyBudgetReservation,
)
from core_apps.features.company_contract_models import (
    CompanyMandate,
    CompanyContractPreparation,
    CompanyPreparationConsent,
)
from core_apps.features.models import Lease, PaymentAttempt, RentalInventoryDayLock
from core_apps.features.services.company import (
    mandates,
    bookings,
    approval_routing,
    contract_preparation as prep,
    contract_projection,
    contract_access,
)
from core_apps.features.tests.test_company_housing import (
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
)
from core_apps.features.tests.test_cycle_concurrency import parallel_calls


def person(name):
    return User.objects.create_user(
        email=f"{name}@company-test.invalid",
        password="synthetic-only",
        first_name=name,
        last_name="Example",
        is_verified=True,
    )


@pytest.fixture
def cycle(company_setup):
    owner, coordinator, approver, company, _, units, offer, request = company_setup
    reviewer, signer, payer, employee, colleague = [
        person(n) for n in ["reviewer", "signer", "payer", "employee", "colleague"]
    ]
    CompanyMembership.objects.create(company=company, user=reviewer, is_admin=True)
    for user in [signer, payer, employee, colleague]:
        CompanyMembership.objects.create(company=company, user=user, is_employee=True)
    made = []
    for user, kind in [(signer, "sign"), (payer, "pay")]:
        m = mandates.propose(
            coordinator,
            company.id,
            command(
                expected_revision=company.revision,
                membership_id=company.memberships.get(user=user).id,
                kind=kind,
                valid_from=timezone.now() - timedelta(minutes=1),
                valid_until=timezone.now() + timedelta(days=30),
                limit_minor=1000000,
                evidence_reference="synthetic-board-delegation",
                reason="Synthetic company test",
            ),
        )
        made.append(
            mandates.decide(
                reviewer,
                m.id,
                "approve",
                command(
                    expected_revision=m.revision, reason="Independent synthetic review"
                ),
            )
        )
    item = bookings.select_offer(
        coordinator,
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": offer.id,
            "offer_revision": offer.revision,
            "occupant_ids": [employee.id, colleague.id],
        },
    )
    item = approval_routing.submit(
        coordinator, item.id, {"expected_revision": item.revision}
    )
    item = bookings.decide(
        approver,
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": item.snapshot_digest,
            "decision": "approved",
        },
    )
    body = command(
        expected_revision=item.revision,
        signer_mandate_id=str(made[0].id),
        payer_mandate_id=str(made[1].id),
        placements=[
            {"employee_id": str(employee.id), "property_id": str(units[0].id)},
            {"employee_id": str(colleague.id), "property_id": str(units[1].id)},
        ],
    )
    return dict(
        owner=owner,
        coordinator=coordinator,
        approver=approver,
        reviewer=reviewer,
        signer=signer,
        payer=payer,
        employee=employee,
        colleague=colleague,
        company=company,
        units=units,
        item=item,
        mandates=made,
        body=body,
    )


def create(cycle):
    response = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{cycle['item'].id}/contract-preparation/",
        cycle["body"],
        format="json",
    )
    assert response.status_code == 201, response.data
    return CompanyContractPreparation.objects.get(booking=cycle["item"])


def respond(cycle, item, role, decision="accepted", **extra):
    actor = cycle[role]
    item.refresh_from_db()
    body = command(
        expected_revision=item.revision,
        snapshot_digest=item.snapshot_digest,
        role="employee" if role == "colleague" else role,
        decision=decision,
        reason="Reviewed" if decision != "accepted" else "",
        **extra,
    )
    return authenticated(actor).post(
        API + f"company-contract-preparations/{item.id}/respond/", body, format="json"
    )


@pytest.mark.django_db
def test_complete_ordinary_review_cycle_stops_before_provider(cycle, settings):
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    item = create(cycle)
    for role in ["owner", "signer", "payer", "employee", "colleague"]:
        result = respond(cycle, item, role)
        assert result.status_code == 200, result.data
    view = contract_projection.payload(
        prep.access.get(cycle["coordinator"], item.id), cycle["coordinator"]
    )
    assert view["effective_state"] == "ready_for_hold" and view["can_reserve"]
    assert not RentalInventoryDayLock.objects.exists()
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-contract-preparations/{item.id}/reserve/",
        command(expected_revision=view["revision"]),
        format="json",
    )
    assert result.status_code == 200, result.data
    view = result.data["resource"]
    assert view["effective_state"] == "ready_for_provider"
    assert view["blocking_reasons"] == ["execution_authority_required"]
    assert not view["can_create_agreement"]
    assert not Lease.objects.exists() and not PaymentAttempt.objects.exists()
    assert RentalInventoryDayLock.objects.exists()
    assert CompanyBudgetReservation.objects.get(item=cycle["item"]).status == "reserved"
    assert not cycle["company"].memberships.filter(can_execute_payments=True).exists()
    assert (
        not cycle["company"].memberships.exclude(signing_verified_until=None).exists()
    )


@pytest.mark.django_db
def test_prepare_response_loss_replays_identical_record_and_receipt(cycle):
    path = API + f"company-booking-items/{cycle['item'].id}/contract-preparation/"
    client = authenticated(cycle["coordinator"])
    first = client.post(path, cycle["body"], format="json")
    second = client.post(path, cycle["body"], format="json")
    assert first.status_code == second.status_code == 201
    assert first.data == second.data
    assert CompanyContractPreparation.objects.count() == 1
    assert CompanyPreparationConsent.objects.count() == 5


@pytest.mark.django_db
def test_employee_privacy_and_no_proxy_consent(cycle):
    item = create(cycle)
    client = authenticated(cycle["employee"])
    view = client.get(API + f"company-contract-preparations/{item.id}/").data
    assert view["full_term_rent_minor"] is None and view["deposit_minor"] is None
    assert len(view["placements"]) == len(view["reviews"]) == 1
    assert view["package"] == {}
    commercial = (
        authenticated(cycle["signer"])
        .get(API + f"company-contract-preparations/{item.id}/")
        .data
    )
    assert (
        commercial["package"]["snapshot"]["included_services"]
        == cycle["item"].snapshot["included_services"]
    )
    assert commercial["package"]["snapshot"]["price_basis"] == "selected_scope"
    assert "planned_staff" not in commercial["package"]["snapshot"]
    assert str(cycle["colleague"].id) not in str(view)
    result = client.post(
        API + f"company-contract-preparations/{item.id}/respond/",
        command(
            expected_revision=item.revision,
            snapshot_digest=item.snapshot_digest,
            role="signer",
            decision="accepted",
        ),
        format="json",
    )
    assert result.status_code == 403
    outsider = person("outsider")
    CompanyMembership.objects.create(
        company=cycle["company"], user=outsider, is_employee=True
    )
    assert (
        authenticated(outsider)
        .get(API + f"company-contract-preparations/{item.id}/")
        .status_code
        == 404
    )


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["signer_mandate_id", "payer_mandate_id"])
def test_mandate_kind_is_not_interchangeable(cycle, field):
    cycle["body"][field] = cycle["body"][
        "payer_mandate_id" if field == "signer_mandate_id" else "signer_mandate_id"
    ]
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{cycle['item'].id}/contract-preparation/",
        cycle["body"],
        format="json",
    )
    assert result.status_code == 409
    assert not CompanyContractPreparation.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "change", ["revoked", "expired", "limit", "membership", "company"]
)
def test_changed_authority_blocks_acceptance_but_allows_decline(cycle, change):
    item = create(cycle)
    mandate = cycle["mandates"][0]
    if change == "revoked":
        mandate.state = "revoked"
    elif change == "expired":
        mandate.valid_until = timezone.now() - timedelta(seconds=1)
    elif change == "limit":
        mandate.limit_minor = 1
    elif change == "membership":
        member = mandate.membership
        member.revision += 1
        member.save()
    else:
        company = cycle["company"]
        company.review_status = "pending"
        company.save()
    mandate.save()
    assert respond(cycle, item, "employee").status_code == 409
    assert respond(cycle, item, "employee", "declined").status_code == 200


@pytest.mark.django_db
def test_decline_and_revise_requires_every_participant_to_review_again(cycle):
    item = create(cycle)
    assert respond(cycle, item, "employee").status_code == 200
    assert respond(cycle, item, "colleague", "declined").status_code == 200
    item.refresh_from_db()
    old = item.snapshot_digest
    revised = prep.prepare(
        cycle["coordinator"],
        cycle["item"].id,
        {**cycle["body"], "expected_revision": item.revision},
    )
    assert revised.snapshot_digest != old and revised.state == "awaiting_reviews"
    assert revised.consents.count() == 10
    assert (
        not revised.consents.filter(snapshot_digest=revised.snapshot_digest)
        .exclude(decision="pending")
        .exists()
    )


@pytest.mark.django_db
def test_withdrawal_releases_canonical_hold_and_budget_even_with_new_business_off(
    cycle, settings
):
    held = bookings.hold_item(
        cycle["coordinator"],
        cycle["item"].id,
        {"expected_revision": cycle["item"].revision},
    )
    cycle["body"]["expected_revision"] = held.revision
    item = create(cycle)
    assert RentalInventoryDayLock.objects.filter(hold=held.hold).exists()
    settings.COMPANY_HOUSING_ENABLED = False
    response = authenticated(cycle["coordinator"]).post(
        API + f"company-contract-preparations/{item.id}/withdraw/",
        command(expected_revision=item.revision),
        format="json",
    )
    assert response.status_code == 200, response.data
    held.hold.refresh_from_db()
    assert held.hold.status == "released" and not held.hold.day_locks.exists()
    assert CompanyBudgetReservation.objects.get(item=held).status == "released"


@pytest.mark.django_db
def test_stale_revision_duplicate_review_and_receipt_recovery(cycle):
    item = create(cycle)
    body = command(
        expected_revision=item.revision,
        snapshot_digest=item.snapshot_digest,
        role="employee",
        decision="accepted",
    )
    client = authenticated(cycle["employee"])
    path = API + f"company-contract-preparations/{item.id}/respond/"
    first = client.post(path, body, format="json")
    assert first.status_code == 200, first.data
    assert client.post(path, body, format="json").data == first.data
    assert (
        client.post(
            path, {**body, "request_key": str(uuid.uuid4())}, format="json"
        ).status_code
        == 409
    )
    item.refresh_from_db()
    assert (
        client.post(
            path,
            {
                **body,
                "request_key": str(uuid.uuid4()),
                "expected_revision": item.revision,
            },
            format="json",
        ).status_code
        == 409
    )


@pytest.mark.django_db
def test_removed_employee_loses_read_write_and_original_receipt(cycle):
    item = create(cycle)
    member = cycle["company"].memberships.get(user=cycle["employee"])
    member.is_active = False
    member.revision += 1
    member.save()
    client = authenticated(cycle["employee"])
    assert (
        client.get(API + f"company-contract-preparations/{item.id}/").status_code == 404
    )
    assert respond(cycle, item, "employee").status_code == 404
    assert respond(cycle, item, "signer").status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind", ["wrong_unit", "missing_person", "duplicate", "capacity"]
)
def test_assignment_requires_exact_people_units_and_capacity(cycle, kind):
    if kind == "wrong_unit":
        cycle["body"]["placements"][0]["property_id"] = str(uuid.uuid4())
    elif kind == "missing_person":
        cycle["body"]["placements"].pop()
    elif kind == "duplicate":
        cycle["body"]["placements"].append(cycle["body"]["placements"][0])
    else:
        cycle["units"][0].occupancy_capacity = 1
        cycle["units"][0].save()
        cycle["body"]["placements"][1]["property_id"] = str(cycle["units"][0].id)
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{cycle['item'].id}/contract-preparation/",
        cycle["body"],
        format="json",
    )
    assert result.status_code in {400, 409}
    assert not CompanyContractPreparation.objects.exists()


@pytest.mark.django_db
def test_self_approval_of_mandate_is_rejected(cycle):
    mandate = cycle["mandates"][0]
    mandate.state = "pending"
    mandate.save()
    for actor in [cycle["coordinator"], cycle["signer"]]:
        cycle["company"].memberships.filter(user=actor).update(is_admin=True)
        with pytest.raises(PermissionDenied):
            mandates.decide(
                actor,
                mandate.id,
                "approve",
                command(expected_revision=mandate.revision, reason="not independent"),
            )


@pytest.mark.django_db
def test_expired_quote_and_hold_have_visible_recovery(cycle):
    item = create(cycle)
    booking = cycle["item"]
    booking.quote_expires_at = timezone.now() - timedelta(seconds=1)
    booking.save()
    item = contract_access.get(cycle["coordinator"], item.id)
    view = contract_projection.payload(item, cycle["coordinator"])
    assert (
        view["effective_state"] == "review_required"
        and "quote_expired" in view["blocking_reasons"]
    )
    assert view["can_withdraw"]
    assert (
        prep.withdraw(
            cycle["coordinator"], item.id, command(expected_revision=item.revision)
        ).state
        == "withdrawn"
    )


@pytest.mark.django_db(transaction=True)
def test_concurrent_reviews_do_not_lose_consent(cycle):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock check")
    item = create(cycle)
    responses = parallel_calls(
        lambda n: authenticated(cycle[["employee", "colleague"][n]]).post(
            API + f"company-contract-preparations/{item.id}/respond/",
            command(
                expected_revision=item.revision,
                snapshot_digest=item.snapshot_digest,
                role="employee",
                decision="accepted",
            ),
            format="json",
        )
    )
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert item.consents.filter(decision="accepted").count() == 1


@pytest.mark.django_db
def test_worklists_exclude_inactive_employment_and_other_company(cycle):
    from core_apps.features.company_staff_models import CompanyStaffRecord

    item = create(cycle)
    member = cycle["company"].memberships.get(user=cycle["employee"])
    staff = CompanyStaffRecord.objects.create(
        company=cycle["company"],
        membership=member,
        display_name="Employee",
        work_email="staff@company-test.invalid",
        created_by=cycle["coordinator"],
    )
    client = authenticated(cycle["employee"])
    path = API + "company-contract-preparations/"
    assert client.get(path).data["count"] == 1
    assert client.get(path, {"company_id": str(uuid.uuid4())}).data["count"] == 0
    assert client.get(path, {"company_id": "invalid"}).status_code == 400
    staff.employment_status = "inactive"
    staff.save()
    result = client.get(path)
    assert result.status_code == 200 and result.data["count"] == 0
    assert client.get(path + str(item.id) + "/").status_code == 404


@pytest.mark.django_db
def test_transfer_does_not_transfer_reviews_or_allow_old_owner_to_approve(cycle):
    item = create(cycle)
    incoming = person("incoming-owner")
    unit = cycle["units"][0]
    unit.owner = incoming
    unit.save()
    old_client = authenticated(cycle["owner"])
    path = API + "company-contract-preparations/"
    # Original counterparty retains history but loses current decision authority.
    assert old_client.get(path).status_code == 200
    view = old_client.get(path + str(item.id) + "/").data
    assert view["effective_state"] == "review_required" and view["responses"] == []
    assert respond(cycle, item, "owner").status_code == 403
    assert authenticated(incoming).get(path + str(item.id) + "/").status_code == 404
    assert authenticated(incoming).get(path).data["count"] == 0


@pytest.mark.django_db
def test_disabled_new_business_keeps_recovery_actions(cycle, settings):
    item = create(cycle)
    assert respond(cycle, item, "employee").status_code == 200
    settings.COMPANY_HOUSING_ENABLED = False
    coordinator = (
        authenticated(cycle["coordinator"])
        .get(API + f"company-contract-preparations/{item.id}/")
        .data
    )
    assert (
        coordinator["can_withdraw"]
        and not coordinator["can_revise"]
        and not coordinator["can_reserve"]
    )
    assert respond(cycle, item, "signer").status_code == 409
    employee = (
        authenticated(cycle["employee"])
        .get(API + f"company-contract-preparations/{item.id}/")
        .data
    )
    assert employee["responses"] == [{"role": "employee", "decision": "withdrawn"}]
    assert respond(cycle, item, "employee", "withdrawn").status_code == 200


@pytest.mark.django_db
def test_booking_withdrawal_cancels_preparation_and_notifies_participants(cycle):
    from core_apps.features.planning_models import PlanningEvent

    item = create(cycle)
    bookings.withdraw_item(
        cycle["coordinator"],
        cycle["item"].id,
        {"expected_revision": cycle["item"].revision},
    )
    item.refresh_from_db()
    assert item.state == "withdrawn"
    events = PlanningEvent.objects.filter(
        event_key=f"company.contract:{item.id}:{item.revision}"
    )
    assert events.count() == 6
    assert all(e.destination["target_id"] == str(item.id) for e in events)
    assert not contract_projection.payload(item, cycle["coordinator"])["can_withdraw"]


@pytest.mark.django_db
def test_reserve_cannot_skip_reviews_and_replay_keeps_one_hold(cycle):
    item = create(cycle)
    path = API + f"company-contract-preparations/{item.id}/reserve/"
    client = authenticated(cycle["coordinator"])
    assert (
        client.post(
            path, command(expected_revision=item.revision), format="json"
        ).status_code
        == 409
    )
    for role in ["owner", "signer", "payer", "employee", "colleague"]:
        assert respond(cycle, item, role).status_code == 200
    item.refresh_from_db()
    body = command(expected_revision=item.revision)
    first = client.post(path, body, format="json")
    replay = client.post(path, body, format="json")
    assert first.status_code == replay.status_code == 200
    assert first.data == replay.data
    item.booking.refresh_from_db()
    assert item.booking.hold_id
    assert item.booking.hold.day_locks.count() == RentalInventoryDayLock.objects.count()


@pytest.mark.django_db
def test_mandate_http_permissions_and_bounded_duration(cycle):
    company = cycle["company"]
    client = authenticated(cycle["coordinator"])
    body = command(
        expected_revision=company.revision,
        membership_id=str(company.memberships.get(user=cycle["employee"]).id),
        kind="sign",
        valid_from=timezone.now().isoformat(),
        valid_until=(timezone.now() + timedelta(days=367)).isoformat(),
        limit_minor=1000000,
        evidence_reference="Synthetic board record",
        reason="Synthetic test",
    )
    path = API + f"companies/{company.id}/mandates/"
    assert client.post(path, body, format="json").status_code == 400
    body["valid_until"] = (timezone.now() + timedelta(days=30)).isoformat()
    result = client.post(path, body, format="json")
    assert result.status_code == 201, result.data
    identity = result.data["resource"]["id"]
    assert (
        client.post(
            API + f"company-mandates/{identity}/approve/",
            command(
                expected_revision=result.data["resource"]["revision"],
                reason="Own approval",
            ),
            format="json",
        ).status_code
        == 403
    )
    approved = authenticated(cycle["reviewer"]).post(
        API + f"company-mandates/{identity}/approve/",
        command(
            expected_revision=result.data["resource"]["revision"],
            reason="Independent review",
        ),
        format="json",
    )
    assert approved.status_code == 200 and approved.data["resource"]["effective"]
    assert not approved.data["resource"]["binding_execution_authorized"]
    revoked = authenticated(cycle["employee"]).post(
        API + f"company-mandates/{identity}/revoke/",
        command(
            expected_revision=approved.data["resource"]["revision"],
            reason="Delegate leaves",
        ),
        format="json",
    )
    assert revoked.status_code == 200 and not revoked.data["resource"]["effective"]
    assert (
        "evidence_reference" in result.data["resource"]
        and revoked.data["resource"]["evidence_reference"] == ""
    )


@pytest.mark.django_db
def test_legacy_reserve_endpoint_cannot_bypass_existing_review_cycle(cycle):
    item = create(cycle)
    assert respond(cycle, item, "employee", "declined").status_code == 200
    result = authenticated(cycle["coordinator"]).post(
        API + f"company-booking-items/{cycle['item'].id}/hold/",
        command(expected_revision=cycle["item"].revision),
        format="json",
    )
    assert result.status_code == 409, result.data
    assert not RentalInventoryDayLock.objects.exists()


@pytest.mark.django_db
def test_recovery_lookup_and_capabilities_follow_current_membership(cycle):
    item = create(cycle)
    client = authenticated(cycle["employee"])
    body = command(
        expected_revision=item.revision,
        snapshot_digest=item.snapshot_digest,
        role="employee",
        decision="accepted",
    )
    assert (
        client.post(
            API + f"company-contract-preparations/{item.id}/respond/",
            body,
            format="json",
        ).status_code
        == 200
    )
    query = {"capability": "company_housing", "subject_id": str(item.id)}
    caps = client.get(API + "planning-capabilities/", query)
    assert "contract_respond" in caps.json()["data"]["allowed_actions"], caps.data
    path = API + f"rental-operations/{body['request_key']}/?subject_id={item.id}"
    assert client.get(path).status_code == 200
    member = cycle["company"].memberships.get(user=cycle["employee"])
    member.is_active = False
    member.save()
    assert client.get(path).status_code == 404
    assert (
        client.post(
            API + f"company-contract-preparations/{item.id}/respond/",
            body,
            format="json",
        ).status_code
        == 404
    )
    delegate = authenticated(cycle["signer"])
    caps = delegate.get(
        API + "planning-capabilities/",
        {"capability": "company_housing", "subject_id": str(cycle["mandates"][0].id)},
    )
    assert "mandate_revoke" in caps.json()["data"]["allowed_actions"], caps.data


@pytest.mark.django_db
def test_frozen_participant_blocks_progression_and_security_epoch_invalidates_consent(
    cycle,
):
    item = create(cycle)
    employee = cycle["employee"]
    employee.sensitive_actions_frozen = True
    employee.security_epoch += 1
    employee.save()
    assert respond(cycle, item, "owner").status_code == 409
    assert respond(cycle, item, "employee", "declined").status_code == 200
    employee.sensitive_actions_frozen = False
    employee.save()
    assert respond(cycle, item, "owner").status_code == 409
    item.refresh_from_db()
    refreshed = prep.prepare(
        cycle["coordinator"],
        cycle["item"].id,
        {**cycle["body"], "expected_revision": item.revision},
    )
    assert refreshed.snapshot_digest != item.snapshot_digest


@pytest.mark.django_db
def test_missing_disaster_recovery_config_preserves_current_company_authority(
    cycle, settings
):
    item = create(cycle)
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_CONTROL_FILE = ""
    client = authenticated(cycle["coordinator"])
    for path in [
        "company-contract-preparations/",
        f"company-contract-preparations/{item.id}/",
        f"companies/{cycle['company'].id}/mandates/",
    ]:
        assert client.get(API + path).status_code == 200
    assert (
        client.post(
            API + f"company-contract-preparations/{item.id}/withdraw/",
            command(expected_revision=item.revision),
            format="json",
        ).status_code
        == 200
    )
    assert authenticated(person("unrelated-policy-viewer")).get(
        API + f"company-contract-preparations/{item.id}/"
    ).status_code in {403, 404}


@pytest.mark.django_db
def test_incoming_owner_never_inherits_predecessor_consent(cycle):
    item = create(cycle)
    incoming = person("new-owner-of-all-units")
    for prop in cycle["units"]:
        prop.owner = incoming
        prop.save()
    offer = cycle["item"].offer
    offer.owner = incoming
    offer.save()
    client = authenticated(incoming)
    assert (
        client.get(API + f"company-contract-preparations/{item.id}/").status_code == 404
    )
    assert (
        client.post(
            API + f"company-contract-preparations/{item.id}/respond/",
            command(
                expected_revision=item.revision,
                snapshot_digest=item.snapshot_digest,
                role="owner",
                decision="accepted",
            ),
            format="json",
        ).status_code
        == 404
    )
    old = authenticated(cycle["owner"]).get(
        API + f"company-contract-preparations/{item.id}/"
    )
    assert old.status_code == 200 and old.data["responses"] == []


@pytest.mark.django_db
def test_notification_rechecks_removed_employee_and_deduplicates(cycle):
    from unittest.mock import patch
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.planning_notifications_parts.deliver_planning_events import (
        deliver_planning_events,
    )

    item = create(cycle)
    member = cycle["company"].memberships.get(user=cycle["employee"])
    member.is_active = False
    member.save()
    event = PlanningEvent.objects.get(
        event_key=f"company.contract:{item.id}:{item.revision}",
        recipient=cycle["employee"],
    )
    # Only external push transport is replaced; records and access checks are real.
    with patch(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user",
        return_value=0,
    ) as sender:
        deliver_planning_events()
        event.refresh_from_db()
        assert (
            event.delivery_status == "stale_or_unauthorized"
            and event.notification_id is None
        )
        assert all(
            call.kwargs["user"].pk != member.user_id for call in sender.call_args_list
        )
        count = sender.call_count
        deliver_planning_events()
        assert sender.call_count == count


@pytest.mark.django_db(transaction=True)
def test_independent_mandate_review_and_delegate_revocation_serialize(cycle):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row-lock check")
    mandate = cycle["mandates"][0]
    mandate.state = "pending"
    mandate.reviewed_by = None
    mandate.save()

    def call(index):
        actor, action = (
            (cycle["reviewer"], "approve")
            if index == 0
            else (cycle["signer"], "revoke")
        )
        return authenticated(actor).post(
            API + f"company-mandates/{mandate.id}/{action}/",
            command(
                expected_revision=mandate.revision,
                reason="Independent concurrent action",
            ),
            format="json",
        )

    results = parallel_calls(call)
    assert sorted(r.status_code for r in results) == [200, 409]
    mandate.refresh_from_db()
    assert mandate.state in {"approved", "revoked"} and mandate.revision == 3


@pytest.mark.django_db
def test_frozen_proposer_is_checked_from_current_database_not_stale_user(cycle):
    coordinator = cycle["coordinator"]
    User.objects.filter(pk=coordinator.pk).update(sensitive_actions_frozen=True)
    with pytest.raises(PermissionDenied):
        mandates.propose(
            coordinator,
            cycle["company"].id,
            command(expected_revision=cycle["company"].revision),
        )
