"""Synthetic account-provisioning and assigned-approval integration. No real delivery."""

import uuid
from datetime import timedelta
import pytest
from django.core import mail
from django.db import connection
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from core_apps.features.company_models import (
    Company,
    CompanyMembership,
    CompanyApproval,
)
from core_apps.features.company_staff_models import (
    CompanyStaffRecord,
    CompanyAccountProvisioning,
)
from core_apps.features.models import StudentProfile, IdempotencyRecord, PaymentAttempt
from core_apps.features.services.company import (
    staff,
    activation_delivery,
    approval_routing,
    bookings,
    membership,
)
from core_apps.features.services.company.contexts import account_contexts
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_company_housing import (
    company_setup,
    rental_participants,
    policy,
    authenticated,
    command,
    proposed,
    API,
)
from core_apps.features.tests.test_cycle_concurrency import parallel_calls


def staff_data(email="person@example.invalid", **kwargs):
    return {
        "display_name": "Synthetic colleague",
        "work_email": email,
        "employee_code": "STAFF-01",
        "roles": ["employee"],
        **kwargs,
    }


def prepare(setup, settings, user=None):
    settings.COMPANY_ACTIVATION_EMAIL_ENABLED = True
    actor, company = setup[1], setup[3]
    user = user or User.objects.create_user(
        email="new@example.invalid",
        password="synthetic-only",
        first_name="Synthetic",
        last_name="Employee",
        is_verified=True,
    )
    person = staff.create_staff(actor, company, staff_data(user.email))
    person = staff.request_activation(
        actor, company.id, person.id, {"expected_revision": person.revision}
    )
    provision = person.provisionings.get()
    return person, provision, user


@pytest.mark.django_db
@pytest.mark.parametrize("loss", ["admin", "active", "verified"])
def test_legacy_and_prepared_invites_recheck_issuer_authority(
    company_setup, settings, loss
):
    person, provision, recipient = prepare(company_setup, settings)
    issuer, company = company_setup[1], company_setup[3]
    _, legacy_token = membership.invite(
        issuer, company.id, recipient.email, ["employee"]
    )
    if loss == "admin":
        CompanyMembership.objects.filter(company=company, user=issuer).update(
            is_admin=False
        )
    else:
        User.objects.filter(pk=issuer.pk).update(**{"is_" + loss: False})
    with pytest.raises(PermissionDenied):
        membership.accept_invitation(recipient, legacy_token)
    with pytest.raises(RentalConflict):
        staff.respond(
            recipient,
            {
                "token": staff.activation_token(provision),
                "expected_revision": 1,
                "proposal_revision": person.proposal_revision,
            },
        )
    assert not CompanyMembership.objects.filter(
        company=company, user=recipient
    ).exists()


@pytest.mark.django_db
def test_pending_approval_rechecks_approver_account_verification(company_setup):
    item = proposed(company_setup)
    approver = company_setup[2]
    User.objects.filter(pk=approver.pk).update(is_verified=False)
    item.refresh_from_db()
    assert not approval_routing.eligible(item.assigned_approver, item)


@pytest.mark.django_db
def test_preparation_creates_no_login_and_forbids_privilege_injection(company_setup):
    actor, company = company_setup[1], company_setup[3]
    client = authenticated(actor)
    count = User.objects.count()
    body = command(**staff_data())
    endpoint = f"{API}companies/{company.id}/staff/"
    bad = client.post(
        endpoint, {**body, "password": "forbidden", "is_staff": True}, format="json"
    )
    assert bad.status_code == 400
    first = client.post(endpoint, body, format="json")
    assert first.status_code == 201, first.data
    repeated = client.post(endpoint, body, format="json")
    assert repeated.status_code == 201
    assert first.data == repeated.data
    assert set(first.json()) == {"message", "data"}
    resource = first.json()["data"]["resource"]
    assert resource["company_id"] == str(company.id)
    assert resource["access_status"] == "prepared"
    assert "user_id" not in resource and "token" not in resource
    assert User.objects.count() == count
    assert CompanyStaffRecord.objects.count() == 1


@pytest.mark.django_db
def test_existing_student_explicitly_links_without_changing_credentials(
    company_setup, settings
):
    user = User.objects.create_user(
        email="student@example.invalid",
        password="original-secret",
        first_name="Student",
        is_verified=True,
    )
    academic = StudentProfile.objects.create(
        user=user, institution_name="Synthetic University"
    )
    person, provisioning, _ = prepare(company_setup, settings, user)
    assert not CompanyMembership.objects.filter(user=user).exists()
    token = staff.activation_token(provisioning)
    client = authenticated(user)
    preview = client.post(
        API + "company-access/preview/", {"token": token}, format="json"
    )
    assert preview.status_code == 200 and preview.json()["data"]["can_accept"]
    body = command(token=token, expected_revision=1, proposal_revision=1)
    accepted = client.post(API + "company-access/accept/", body, format="json")
    assert accepted.status_code == 200, accepted.data
    assert (
        client.post(API + "company-access/accept/", body, format="json").data
        == accepted.data
    )
    assert (
        client.post(
            API + "company-access/accept/",
            {**body, "request_key": str(uuid.uuid4())},
            format="json",
        ).status_code
        == 200
    )
    person.refresh_from_db()
    user.refresh_from_db()
    assert person.membership.user == user and user.check_password("original-secret")
    assert StudentProfile.objects.get(user=user) == academic
    contexts = account_contexts(user)["contexts"]
    assert {row["type"] for row in contexts} == {"user", "student", "company"}
    assert person.membership.can_execute_payments is False
    assert not user.is_staff and not user.is_superuser
    assert all(
        "token" not in record.response_data.get("resource", {})
        for record in IdempotencyRecord.objects.all()
    )


@pytest.mark.django_db
def test_new_identity_can_register_after_roster_preparation(company_setup, settings):
    person = staff.create_staff(
        company_setup[1], company_setup[3], staff_data("fresh@example.invalid")
    )
    # Same canonical user manager used by personal signup; no reserved auth row.
    user = User.objects.create_user(
        email=person.work_email,
        password="individual-secret",
        first_name="New",
        last_name="Person",
        is_verified=True,
    )
    settings.COMPANY_ACTIVATION_EMAIL_ENABLED = True
    person = staff.request_activation(
        company_setup[1], company_setup[3].id, person.id, {"expected_revision": 1}
    )
    provision = person.provisionings.get()
    response = staff.respond(
        user,
        {
            "token": staff.activation_token(provision),
            "expected_revision": 1,
            "proposal_revision": 1,
        },
    )
    assert response.status == "accepted"
    assert CompanyMembership.objects.get(user=user).company == company_setup[3]


@pytest.mark.django_db
def test_wrong_unverified_expired_and_changed_grants_cannot_activate(
    company_setup, settings
):
    person, provisioning, user = prepare(company_setup, settings)
    token = staff.activation_token(provisioning)
    data = {"token": token, "expected_revision": 1, "proposal_revision": 1}
    with pytest.raises(PermissionDenied):
        staff.respond(company_setup[2], data)
    user.is_verified = False
    with pytest.raises(PermissionDenied):
        staff.respond(user, data)
    user.is_verified = True
    provisioning.expires_at = timezone.now() - timedelta(seconds=1)
    provisioning.save()
    with pytest.raises(RentalConflict):
        staff.respond(user, data)
    provisioning.expires_at = timezone.now() + timedelta(days=1)
    provisioning.save()
    staff.update_pending(
        company_setup[1],
        company_setup[3].id,
        person.id,
        {
            **staff_data(user.email, roles=["coordinator"]),
            "expected_revision": person.revision,
        },
    )
    with pytest.raises(RentalConflict):
        staff.respond(user, data)
    assert not CompanyMembership.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_decline_and_offboarding_preserve_personal_account(company_setup, settings):
    person, provisioning, user = prepare(company_setup, settings)
    data = {
        "token": staff.activation_token(provisioning),
        "expected_revision": 1,
        "proposal_revision": 1,
    }
    staff.respond(user, data, accept=False)
    user.refresh_from_db()
    assert user.is_active and not CompanyMembership.objects.filter(user=user).exists()
    with pytest.raises(RentalConflict):
        staff.respond(user, data)


@pytest.mark.django_db
def test_delivery_is_separate_durable_and_never_retries_unknown(
    company_setup, settings, monkeypatch
):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    person, provisioning, user = prepare(company_setup, settings)
    assert provisioning.delivery_status == "queued"
    assert activation_delivery.deliver(provisioning.pk)
    assert len(mail.outbox) == 1
    assert staff.activation_token(provisioning) in mail.outbox[0].body
    assert not activation_delivery.deliver(provisioning.pk)
    assert not CompanyMembership.objects.filter(user=user).exists()
    CompanyAccountProvisioning.objects.filter(pk=provisioning.pk).update(
        created_at=timezone.now() - timedelta(minutes=2)
    )
    person.refresh_from_db()
    staff.request_activation(
        company_setup[1],
        company_setup[3].id,
        person.id,
        {"expected_revision": person.revision},
    )
    fresh = person.provisionings.order_by("-created_at").first()

    def timeout(**kwargs):
        raise TimeoutError("synthetic uncertain delivery")

    monkeypatch.setattr(activation_delivery, "send_mail", timeout)
    assert not activation_delivery.deliver(fresh.pk)
    fresh.refresh_from_db()
    assert fresh.delivery_status == "unknown"
    assert activation_delivery.drain() == 0
    with pytest.raises(RentalConflict):
        staff.preview(user, staff.activation_token(provisioning))


@pytest.mark.django_db
def test_queued_delivery_rechecks_grant_and_unconfigured_delivery_is_truthful(
    company_setup, settings
):
    person, provisioning, _ = prepare(company_setup, settings)
    CompanyMembership.objects.filter(
        company=company_setup[3], user=company_setup[1]
    ).update(is_admin=False)
    assert not activation_delivery.deliver(provisioning.pk)
    provisioning.refresh_from_db()
    assert provisioning.delivery_status == "cancelled"
    assert staff.staff_payload(person)["access_status"] == "pending_activation"


@pytest.mark.django_db
def test_partial_batch_retry_cannot_duplicate_or_change_rows(company_setup):
    actor, company = company_setup[1], company_setup[3]
    staff.create_staff(actor, company, staff_data())
    data = {
        "batch_key": uuid.uuid4(),
        "expected_revision": 0,
        "rows": [
            {
                "row_key": uuid.uuid4(),
                **staff_data("another@example.invalid", employee_code="STAFF-02"),
            },
            {"row_key": uuid.uuid4(), **staff_data()},
        ],
    }
    batch = staff.create_batch(actor, company.id, data)
    result = staff.batch_payload(batch)
    assert [row["status"] for row in result["results"]] == ["created", "rejected"]
    assert not result["complete"]
    data["expected_revision"] = batch.revision
    retried = staff.create_batch(actor, company.id, data)
    assert CompanyStaffRecord.objects.count() == 2
    assert staff.batch_payload(retried)["results"] == result["results"]
    data["rows"][0]["display_name"] = "Changed"
    data["expected_revision"] = retried.revision
    with pytest.raises(RentalConflict):
        staff.create_batch(actor, company.id, data)


@pytest.mark.django_db
def test_roster_and_contexts_do_not_union_roles_across_companies(company_setup):
    other = Company.objects.create(
        name="Other", registration_number="OTHER", contact_email="other@example.invalid"
    )
    actor = company_setup[1]
    CompanyMembership.objects.create(company=other, user=actor, is_employee=True)
    client = authenticated(actor)
    assert client.get(f"{API}companies/{other.id}/staff/").status_code == 403
    assert (
        client.post(
            f"{API}companies/{other.id}/staff/", command(**staff_data()), format="json"
        ).status_code
        == 403
    )
    company_contexts = [
        row for row in account_contexts(actor)["contexts"] if row["type"] == "company"
    ]
    assert next(row for row in company_contexts if row["company_id"] == str(other.id))[
        "roles"
    ] == ["employee"]


@pytest.mark.django_db
def test_explicit_submit_assigned_work_changes_and_reassignment(company_setup):
    actor, approver, company = company_setup[1], company_setup[2], company_setup[3]
    item = proposed(company_setup)
    assert item.status == "approval_pending" and item.assigned_approver.user == approver
    digest = item.snapshot_digest
    assert approval_routing.work_items(approver, company).count() == 1
    backup = User.objects.create_user(
        email="backup@example.invalid", password="test", is_verified=True
    )
    membership = CompanyMembership.objects.create(
        company=company, user=backup, is_approver=True
    )
    assert (
        authenticated(backup)
        .get(f"{API}company-housing-requests/{item.request.id}/")
        .status_code
        == 403
    )
    item = approval_routing.reassign(
        actor,
        item.id,
        {
            "expected_revision": item.revision,
            "approver_id": membership.id,
            "reason": "Synthetic absence",
        },
    )
    with pytest.raises(PermissionDenied):
        bookings.decide(
            approver,
            item.id,
            {
                "expected_revision": item.revision,
                "snapshot_digest": digest,
                "decision": "approved",
            },
        )
    assert not approval_routing.work_items(approver, company).exists()
    result = bookings.decide(
        backup,
        item.id,
        {
            "expected_revision": item.revision,
            "snapshot_digest": digest,
            "decision": "changes_requested",
            "reason": "Clarify utilities",
        },
    )
    assert result.status == "changes_requested" and result.snapshot_digest == digest
    assert CompanyApproval.objects.get(item=item).reason == "Clarify utilities"
    assert not PaymentAttempt.objects.exists()
    assert not company.budget_reservations.exists()
    assert approval_routing.work_items(actor, company).filter(pk=item.pk).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_activation_consumes_once(company_setup, settings):
    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL locks required")
    person, provision, user = prepare(company_setup, settings)
    data = {
        "token": staff.activation_token(provision),
        "expected_revision": 1,
        "proposal_revision": 1,
    }
    results = parallel_calls(
        lambda _: staff.respond(User.objects.get(pk=user.pk), data).status,
    )
    assert results == ["accepted", "accepted"]
    assert (
        CompanyMembership.objects.filter(company=company_setup[3], user=user).count()
        == 1
    )


@pytest.mark.django_db
def test_pending_staff_can_be_planned_without_identity_or_acknowledgment(company_setup):
    actor, company, offer, request = (
        company_setup[1],
        company_setup[3],
        company_setup[6],
        company_setup[7],
    )
    person = staff.create_staff(actor, company, staff_data())
    result = authenticated(actor).get(f"{API}companies/{company.id}/planning-staff/")
    assert result.status_code == 200
    assert "work_email" not in str(result.json())
    item = bookings.select_offer(
        actor,
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": offer.id,
            "offer_revision": offer.revision,
            "occupant_ids": [],
            "staff_ids": [person.id],
        },
    )
    assert item.snapshot["planned_staff"][0]["activation_required"] is True
    assert item.snapshot["reserve_places"] == 7
    assert item.occupants.count() == 0 and item.assignments.count() == 0
    staff.update_pending(
        actor,
        company.id,
        person.id,
        {**staff_data("changed@example.invalid"), "expected_revision": person.revision},
    )
    with pytest.raises(RentalConflict) as error:
        approval_routing.submit(actor, item.id, {"expected_revision": item.revision})
    assert error.value.get_codes() == "staff_plan_changed"


@pytest.mark.django_db
def test_pending_staff_email_cannot_hide_a_funded_approver(company_setup):
    actor, company, offer, request = (
        company_setup[1],
        company_setup[3],
        company_setup[6],
        company_setup[7],
    )
    person = staff.create_staff(actor, company, staff_data(company_setup[2].email))
    item = bookings.select_offer(
        actor,
        request.id,
        {
            "expected_revision": request.revision,
            "offer_id": offer.id,
            "offer_revision": offer.revision,
            "occupant_ids": [],
            "staff_ids": [person.id],
        },
    )
    with pytest.raises(RentalConflict):
        approval_routing.submit(actor, item.id, {"expected_revision": item.revision})
    assert not CompanyApproval.objects.exists()


@pytest.mark.django_db
def test_route_and_reassignment_api_are_uuid_scoped_and_financially_minimal(
    company_setup,
):
    actor, company = company_setup[1], company_setup[3]
    item = proposed(company_setup)
    backup = User.objects.create_user(
        email="route@example.invalid", password="test", is_verified=True
    )
    member = CompanyMembership.objects.create(
        company=company, user=backup, is_approver=True
    )
    client = authenticated(actor)
    route = client.post(
        f"{API}companies/{company.id}/approval-route/",
        command(
            expected_revision=company.revision,
            default_approver_id=str(company.default_approver.id),
            backup_approver_id=str(member.id),
            reason="Synthetic backup",
        ),
        format="json",
    )
    assert route.status_code == 200, route.json()
    work = client.get(f"{API}companies/{company.id}/work-items/")
    assert work.status_code == 200
    assert "snapshot" not in str(work.json()) and "full_term_rent_minor" not in str(
        work.json()
    )
    response = client.post(
        f"{API}company-booking-items/{item.id}/reassign/",
        command(
            expected_revision=item.revision,
            approver_id=str(member.id),
            reason="Synthetic reassignment",
        ),
        format="json",
    )
    assert response.status_code == 200, response.json()
    resource = response.json()["data"]["resource"]
    assert resource["company_id"] == str(company.id) and resource["request_id"] == str(
        item.request.id
    )
    assert "snapshot" not in resource


@pytest.mark.django_db
def test_notifications_are_deduplicated_and_recheck_revoked_assignments(
    company_setup, monkeypatch
):
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.planning_notifications import (
        deliver_planning_events,
    )
    from core_apps.notifications.services.fcm_service import FCMService

    monkeypatch.setattr(FCMService, "send_push_to_user", lambda **kwargs: 0)
    monkeypatch.setattr(FCMService, "should_send_to_user", lambda *args: False)
    item = proposed(company_setup)
    approval_routing.notify(item, company_setup[2])
    assert PlanningEvent.objects.filter(recipient=company_setup[2]).count() == 1
    CompanyMembership.objects.filter(
        company=company_setup[3], user=company_setup[2]
    ).update(is_active=False)
    deliver_planning_events()
    event = PlanningEvent.objects.get(recipient=company_setup[2])
    assert event.delivered_at and not event.notification_id
    assert item.request.items.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_approval_decisions_resolve_once(company_setup):
    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL locks required")
    item = proposed(company_setup)

    def decide(index):
        try:
            bookings.decide(
                company_setup[2],
                item.id,
                {
                    "expected_revision": item.revision,
                    "snapshot_digest": item.snapshot_digest,
                    "decision": "approved" if index == 0 else "rejected",
                    "reason": "Synthetic decision",
                },
            )
            return "decided"
        except RentalConflict:
            return "conflict"

    assert sorted(parallel_calls(decide)) == ["conflict", "decided"]
    assert CompanyApproval.objects.filter(item=item).count() == 1
