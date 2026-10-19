"""Real PostgreSQL interleavings for company authority and academic consent.

The database and domain services are real. Accounts, supply reviews, authority and
the reservation policy are synthetic fixtures; no signing/payment provider runs.
"""

from concurrent.futures import ThreadPoolExecutor
from time import monotonic, sleep
import uuid

import pytest
from django.db import connection, connections, transaction

from core_apps.features.company_models import (
    Company,
    CompanyApproval,
    CompanyBudgetReservation,
    CompanyMembership,
)
from core_apps.features.models import (
    AcademicHousingPlan,
    HousingRequest,
    Lease,
    RentalConsentRecord,
    RentalInventoryDayLock,
    ReservationHold,
)
from core_apps.features.services.company import administration, membership
from core_apps.features.services.student_housing import access, publication
from .test_company_housing import company_setup, approved, held, proposed
from .test_company_request_correction import body as request_body
from .test_cycle_concurrency import parallel_calls
from .test_rental_lifecycle import command, policy
from .test_rental_phase2 import authenticated, rental_participants
from .test_student_housing import (
    API,
    create_plan,
    group,
    read,
    requirements,
    review,
    student_capabilities,
)


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def real_postgres_without_providers(settings):
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL row locks and independent sessions")
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = False
    settings.RENTAL_CHECKOUT_ENABLED = False
    settings.PLANNING_MOCK_DISCOVERY = False


def post(user, path, body):
    return authenticated(user).post(API + path, body, format="json")


def blocked_command_after_change(company, actor, path, body, change):
    """Prove the command is waiting for our company lock before changing authority.

    PostgreSQL wait-state observation orders two real sessions; no handler or
    permission function is patched to manufacture the interleaving.
    """
    application_name = "sokoun-authority-" + uuid.uuid4().hex

    def pending_command():
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SET application_name = %s", [application_name])
                cursor.execute("SET lock_timeout = '10s'")
            return post(actor, path, body)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Company.objects.select_for_update().get(pk=company.pk)
            pending = pool.submit(pending_command)
            deadline = monotonic() + 8
            while monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_stat_clear_snapshot()")
                    cursor.execute(
                        "SELECT EXISTS (SELECT 1 FROM pg_stat_activity "
                        "WHERE application_name = %s AND wait_event_type = 'Lock')",
                        [application_name],
                    )
                    if cursor.fetchone()[0]:
                        break
                if pending.done():
                    pytest.fail("Command finished before reaching the company lock")
                sleep(0.01)
            else:
                pytest.fail("Command did not reach the observed PostgreSQL lock")
            change()
        return pending.result(timeout=15)


@pytest.mark.parametrize("action", ["hold", "withdraw", "hold_receipt"])
def test_reassigned_coordinator_cannot_finish_an_already_waiting_command(
    company_setup, action
):
    owner, coordinator, _, company, *_, request = company_setup
    item = held(company_setup) if action == "withdraw" else approved(company_setup)
    body = command(item.revision)
    endpoint_action = "hold" if action == "hold_receipt" else action
    if action == "hold_receipt":
        assert (
            post(
                coordinator, f"company-booking-items/{item.id}/hold/", body
            ).status_code
            == 200
        )
        item.refresh_from_db()
    CompanyMembership.objects.create(company=company, user=owner, is_coordinator=True)
    request.refresh_from_db()
    before = (
        item.revision,
        item.status,
        ReservationHold.objects.count(),
        RentalInventoryDayLock.objects.count(),
    )

    def reassign():
        administration.reassign_coordinator(
            coordinator,
            request.id,
            {
                "expected_revision": request.revision,
                "coordinator_id": owner.id,
                "reason": "Synthetic reassignment during an in-flight command",
            },
        )

    response = blocked_command_after_change(
        company,
        coordinator,
        f"company-booking-items/{item.id}/{endpoint_action}/",
        body,
        reassign,
    )
    assert response.status_code == 403, response.data
    item.refresh_from_db()
    request.refresh_from_db()
    assert request.coordinator_id == owner.pk
    assert (
        item.revision,
        item.status,
        ReservationHold.objects.count(),
        RentalInventoryDayLock.objects.count(),
    ) == before
    assert CompanyBudgetReservation.objects.get(item=item).status == "reserved"


def test_revoked_approver_cannot_finish_an_already_waiting_decision(company_setup):
    _, coordinator, approver, company, *_ = company_setup
    item = proposed(company_setup)
    member = CompanyMembership.objects.get(company=company, user=approver)

    def revoke():
        membership.update_member(
            coordinator,
            company.id,
            member.id,
            {
                "expected_revision": member.revision,
                "roles": [],
                "is_active": False,
                "reason": "Synthetic revocation while approval is waiting",
            },
        )

    response = blocked_command_after_change(
        company,
        approver,
        f"company-booking-items/{item.id}/decide/",
        command(
            item.revision, snapshot_digest=item.snapshot_digest, decision="approved"
        ),
        revoke,
    )
    assert response.status_code == 404, response.data
    item.refresh_from_db()
    assert item.status == "approval_pending"
    assert not CompanyApproval.objects.filter(item=item).exists()
    assert not CompanyBudgetReservation.objects.filter(item=item).exists()
    assert not ReservationHold.objects.exists()


def test_concurrent_same_identity_hold_has_one_effect_and_recovers_receipt(
    company_setup,
):
    _, coordinator, _, _, _, props, _, _ = company_setup
    item = approved(company_setup)
    body = command(item.revision)
    responses = parallel_calls(
        lambda _: post(coordinator, f"company-booking-items/{item.id}/hold/", body)
    )
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    item.refresh_from_db()
    assert ReservationHold.objects.count() == 1
    assert item.revision == body["expected_revision"] + 1
    assert set(item.hold.day_locks.values_list("property_id", flat=True)) == {
        prop.pk for prop in props
    }
    receipt = authenticated(coordinator).get(
        API + f"rental-operations/{body['request_key']}/",
        {"subject_id": str(item.id)},
    )
    assert receipt.status_code == 200, receipt.data
    assert receipt.data["operation_receipt"] == responses[0].data["operation_receipt"]
    assert receipt.data["operation_receipt"]["subject_id"] == str(item.id)
    assert receipt.data["operation_receipt"]["revision"] == item.revision


def test_company_decide_and_withdraw_cannot_both_commit_same_revision(company_setup):
    _, coordinator, approver, _, *_ = company_setup
    item = proposed(company_setup)

    def race(index):
        return post(
            approver if index == 0 else coordinator,
            f"company-booking-items/{item.id}/{'decide' if index == 0 else 'withdraw'}/",
            command(
                item.revision,
                **(
                    {"snapshot_digest": item.snapshot_digest, "decision": "approved"}
                    if index == 0
                    else {}
                ),
            ),
        )

    responses = parallel_calls(race)
    assert sorted(r.status_code for r in responses) == [200, 409]
    item.refresh_from_db()
    assert item.status in {"approved", "withdrawn"}
    expected = 1 if item.status == "approved" else 0
    assert CompanyApproval.objects.filter(item=item).count() == expected
    assert CompanyBudgetReservation.objects.filter(item=item).count() == expected
    assert not ReservationHold.objects.exists()


def test_request_correction_and_offer_selection_preserve_one_reviewed_revision(
    company_setup,
):
    _, coordinator, _, _, _, _, offer, request = company_setup

    def race(index):
        if index == 0:
            return post(
                coordinator,
                f"company-housing-requests/{request.id}/",
                request_body(request, title="Corrected before package selection"),
            )
        return post(
            coordinator,
            f"company-housing-requests/{request.id}/items/",
            command(
                request.revision,
                offer_id=str(offer.id),
                offer_revision=offer.revision,
                occupant_ids=[],
            ),
        )

    responses = parallel_calls(race)
    assert sorted(r.status_code for r in responses) in ([200, 409], [201, 409])
    request.refresh_from_db()
    assert request.revision == 2
    if responses[0].status_code == 200:
        assert request.title == "Corrected before package selection"
        assert not request.items.exists()
    else:
        assert request.title == "Synthetic team"
        assert request.items.count() == 1


def test_receipt_does_not_restore_reassigned_coordinator_access(company_setup):
    owner, coordinator, _, company, *_, request = company_setup
    item = approved(company_setup)
    body = command(item.revision)
    path = f"company-booking-items/{item.id}/hold/"
    assert post(coordinator, path, body).status_code == 200
    CompanyMembership.objects.create(company=company, user=owner, is_coordinator=True)
    request.refresh_from_db()
    administration.reassign_coordinator(
        coordinator,
        request.id,
        {
            "expected_revision": request.revision,
            "coordinator_id": owner.id,
            "reason": "Synthetic completed handoff",
        },
    )
    assert post(coordinator, path, body).status_code == 403
    assert ReservationHold.objects.count() == 1


def reviewed_group(tenant, member, prop, group):
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    plan = requirements(tenant, plan, study_space="Shared study room")
    plan = requirements(member, plan, internet="Reliable connection")
    return review(member, review(tenant, plan))


def test_student_withdraw_and_publication_preserve_current_consent(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    plan = reviewed_group(tenant, member, prop, group)
    preview = (
        authenticated(tenant)
        .get(API + f"academic-plans/{plan['id']}/publication-preview/")
        .data["publication_preview"]
    )

    def race(index):
        return post(
            tenant if index == 0 else member,
            f"academic-plans/{plan['id']}/{'publish' if index == 0 else 'withdraw'}/",
            command(
                plan["revision"],
                consent=index == 0,
                digest=preview["preview_digest"] if index == 0 else plan["digest"],
            ),
        )

    responses = parallel_calls(race)
    assert sorted(r.status_code for r in responses) == [200, 409]
    current = read(tenant, plan["id"])
    if responses[1].status_code == 409:
        retry = post(
            member,
            f"academic-plans/{plan['id']}/withdraw/",
            command(current["revision"], consent=False, digest=current["digest"]),
        )
        assert retry.status_code == 200, retry.data
    persisted = AcademicHousingPlan.objects.get(id=plan["id"])
    assert persisted.participants.get(user=member).status == "withdrawn"
    assert "waiting_for_consent" in read(tenant, plan["id"])["blocking_reasons"]
    for demand in HousingRequest.objects.filter(academic_plan=persisted):
        assert not publication.request_current(demand)
    assert not ReservationHold.objects.exists()
    assert not Lease.objects.exists()


def test_student_requirement_change_invalidates_competing_consent(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    plan = create_plan(tenant, prop, group=group, people=[tenant, member])
    plan = requirements(member, requirements(tenant, plan))

    def race(index):
        return post(
            tenant if index == 0 else member,
            f"academic-plans/{plan['id']}/{'review' if index == 0 else 'requirements'}/",
            command(
                plan["revision"],
                **(
                    {"consent": True, "digest": plan["digest"]}
                    if index == 0
                    else {
                        "requirements": {"internet": "Changed requirement"},
                        "budget_min": {"amount_minor": 100000},
                        "budget_max": {"amount_minor": 400000},
                        "owner_disclosures": ["affordability"],
                    }
                ),
            ),
        )

    responses = parallel_calls(race)
    assert sorted(r.status_code for r in responses) == [200, 409]
    current = read(tenant, plan["id"])
    if responses[1].status_code == 409:
        current = requirements(member, current, internet="Changed requirement")
    assert current["requirements_revision"] == plan["requirements_revision"] + 1
    assert "waiting_for_consent" in current["blocking_reasons"]
    assert (
        RentalConsentRecord.objects.filter(
            subject_id=plan["id"],
            subject_revision=current["requirements_revision"],
            decision="accept",
        ).count()
        == 0
    )


def test_withdrawn_student_cannot_repeatedly_invalidate_remaining_consent(
    rental_participants, group
):
    _, tenant, member, prop, _ = rental_participants
    plan = reviewed_group(tenant, member, prop, group)
    body = command(plan["revision"], consent=False, digest=plan["digest"])
    path = f"academic-plans/{plan['id']}/withdraw/"
    first = post(member, path, body)
    assert first.status_code == 200, first.data
    assert post(member, path, body).data == first.data
    current = review(tenant, read(tenant, plan["id"]))
    assert not current["blocking_reasons"]
    assert "withdraw" not in read(member, plan["id"])["allowed_actions"]
    assert access.actions(member, "student_planning", plan["id"]) == ["read"]
    duplicate_with_new_identity = post(
        member,
        path,
        command(current["revision"], consent=False, digest=current["digest"]),
    )
    assert (
        duplicate_with_new_identity.status_code == 403
    ), duplicate_with_new_identity.data
    persisted = AcademicHousingPlan.objects.get(id=plan["id"])
    assert persisted.revision == current["revision"]
    assert persisted.requirements_revision == current["requirements_revision"]
    assert not read(tenant, plan["id"])["blocking_reasons"]
    assert (
        RentalConsentRecord.objects.filter(
            actor=member, subject_id=plan["id"], decision="withdraw"
        ).count()
        == 1
    )


def test_completed_student_plan_rejects_new_consent_or_correction_but_replays_receipt(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    plan = create_plan(tenant, prop)
    body = command(plan["revision"])
    path = f"academic-plans/{plan['id']}/complete/"
    first = post(tenant, path, body)
    assert first.status_code == 200, first.data
    assert post(tenant, path, body).data == first.data
    current = read(tenant, plan["id"])
    assert current["status"] == "completed"
    assert current["allowed_actions"] == []
    rejected = post(
        tenant,
        f"academic-plans/{plan['id']}/requirements/",
        command(
            current["revision"],
            requirements={},
            budget_min={"amount_minor": 1},
            budget_max={"amount_minor": 2},
            owner_disclosures=[],
        ),
    )
    assert rejected.status_code == 409, rejected.data
    assert (
        AcademicHousingPlan.objects.get(id=plan["id"]).revision == current["revision"]
    )
