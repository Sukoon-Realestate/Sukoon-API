"""Actual authenticated API persistence, privacy, provenance, recovery and races."""

import uuid
import json
import os
from pathlib import Path
from datetime import datetime, time, timedelta, timezone as dt_timezone

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import (
    IdempotencyRecord,
    Lease,
    RentalInterest,
    RentInvoice,
    TenancyInvitation,
)
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.services.tenancy_invitations import resolve_offer_snapshot
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from core_apps.features.tests.test_rental_phase2 import (
    authenticated,
    agreement_terms,
    complete_owner_onboarding,
    rental_participants,
)
from core_apps.notifications.models import Notification
from core_apps.properties.models import PropertyVisit, PropertyVisitDecision
from core_apps.properties.services.post_visit_decision import DecisionConflict

API = "/api/v1/features/v1/"
PROPERTIES = "/api/v1/properties/"


@pytest.fixture
def visit(rental_participants):
    owner, tenant, _, prop, offer = rental_participants
    _, snapshot = resolve_offer_snapshot(prop, offer, 2)
    yesterday = timezone.localtime() - timedelta(days=1)
    return PropertyVisit.objects.create(
        property=prop,
        tenant=tenant,
        visit_date=yesterday.date(),
        visit_time=yesterday.time().replace(tzinfo=None),
        status="confirmed",
        accepted_at=yesterday - timedelta(days=1),
        offer_id=offer,
        offer_snapshot=snapshot,
    )


def path(visit):
    return PROPERTIES + f"visits/{visit.id}/post-visit-decision/"


def body(visit, **extra):
    return {
        "decision": "proceed",
        "attended": True,
        "expected_revision": visit.revision,
        "request_key": str(uuid.uuid4()),
        **extra,
    }


def decide(visit, **extra):
    response = authenticated(visit.tenant).post(
        path(visit), body(visit, **extra), format="json"
    )
    assert response.status_code == 200, response.data
    visit.refresh_from_db()
    return response.json()["data"]


def invite_body(visit, decision=None, **extra):
    decision = decision or visit.post_visit_decision
    return {
        "property_id": str(visit.property.id),
        "tenant_id": str(visit.tenant.id),
        "offer_id": visit.offer_id,
        "expected_offer_revision": (visit.offer_snapshot or {}).get("offer_revision"),
        "source_visit_id": str(visit.id),
        "source_decision_id": str(decision.id),
        "request_key": str(uuid.uuid4()),
        **extra,
    }


@pytest.mark.django_db
def test_positive_is_persisted_without_reservation_or_automatic_invitation(visit):
    before = authenticated(visit.tenant).get(path(visit)).json()["data"]
    assert before["post_visit_actions"]["can_submit"]
    assert before["rental_continuation"]["next_action"] == "submit_post_visit_decision"
    saved = decide(visit)
    decision = PropertyVisitDecision.objects.get()
    assert decision.attended and decision.attendance_source == "tenant_attestation"
    assert (
        decision.offer_snapshot == visit.offer_snapshot and decision.visit_revision == 1
    )
    assert saved["revision"] == 2 and saved["post_visit_decision"]["id"] == str(
        decision.id
    )
    assert saved["rental_continuation"]["next_actor"] == "owner"
    assert saved["rental_continuation"]["next_action"] is None
    assert (
        not Lease.objects.exists()
        and not TenancyInvitation.objects.exists()
        and not RentalInterest.objects.exists()
    )
    owner = authenticated(visit.property.owner).get(path(visit)).json()["data"]
    assert owner["rental_continuation"]["next_action"] == "create_rental_invitation"
    assert (
        Notification.objects.filter(data__event_kind="visit_post_decision").count() == 1
    )
    assert PlanningEvent.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("state", ["pending", "canceled", "rejected", "future"])
def test_server_eligibility_rejects_unattendable_visits(visit, state):
    if state == "future":
        visit.visit_date += timedelta(days=3)
    else:
        visit.status = state
    visit.save()
    current = authenticated(visit.tenant).get(path(visit)).json()["data"]
    assert current["post_visit_actions"]["can_submit"] is False
    response = authenticated(visit.tenant).post(path(visit), body(visit), format="json")
    assert response.status_code == 409
    assert response.json()["code"] == (
        "visit_not_started" if state == "future" else "visit_not_confirmed"
    )
    assert not PropertyVisitDecision.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("actor", ["owner", "stranger", "anonymous"])
def test_only_visit_tenant_may_submit(visit, rental_participants, actor):
    client = (
        APIClient()
        if actor == "anonymous"
        else authenticated(rental_participants[0 if actor == "owner" else 2])
    )
    response = client.post(path(visit), body(visit), format="json")
    assert response.status_code in {401, 404}
    if actor == "stranger":
        assert client.get(path(visit)).status_code == 404
    assert not PropertyVisitDecision.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "extra,code",
    [
        ({"attended": False}, "attendance_required"),
        ({"decision": "unknown"}, "invalid_decision"),
        ({"decision": "decline", "reason": " \n\t "}, "reason_required"),
        ({"decision": "decline", "reason": "😀" * 1001}, "reason_too_long"),
        ({"reason": "unused"}, "reason_not_allowed"),
    ],
)
def test_input_validation_no_side_effects(visit, extra, code):
    response = authenticated(visit.tenant).post(
        path(visit), body(visit, **extra), format="json"
    )
    assert response.status_code == 400 and response.json()["code"] == code
    assert (
        not PropertyVisitDecision.objects.exists()
        and not PlanningEvent.objects.exists()
    )


@pytest.mark.django_db
def test_decline_preserves_unicode_private_reason_and_blocks_invitation(
    visit, rental_participants
):
    text = "المكان\nnot suitable 😀 " + "x" * (1000 - len("المكان\nnot suitable 😀 "))
    saved = decide(visit, decision="decline", reason="  " + text + "  ")
    assert saved["post_visit_decision"]["reason"] == text
    assert saved["rental_continuation"]["status"] == "declined"
    for endpoint in [
        path(visit),
        PROPERTIES + f"owner/visits/requests/{visit.id}/",
        PROPERTIES + "owner/visits/requests/",
        PROPERTIES + "visits/received/",
        PROPERTIES + f"visits/{visit.id}/",
    ]:
        response = authenticated(visit.property.owner).get(endpoint)
        assert response.status_code == 200, endpoint
        assert (
            text not in response.content.decode()
            and '"reason"' not in response.content.decode()
        )
    for event in PlanningEvent.objects.all():
        assert text not in str(event.destination) and text not in str(
            event.notification.data
        )
    response = authenticated(visit.property.owner).post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert (
        response.status_code == 409 and response.json()["code"] == "decision_conflict"
    )
    assert not TenancyInvitation.objects.exists()
    assert text not in str(IdempotencyRecord.objects.get().response_data)
    staff = rental_participants[2]
    staff.is_staff = True
    staff.save(update_fields=["is_staff"])
    assert authenticated(staff).get(path(visit)).status_code == 404
    StaffProfile.objects.create(user=staff, role_name="support", is_active=True)
    staff.refresh_from_db()
    staff_read = authenticated(staff).get(path(visit))
    assert (
        staff_read.status_code == 200
        and staff_read.json()["data"]["post_visit_decision"]["reason"] == text
    )


@pytest.mark.django_db
def test_recovery_and_replays_return_canonical_without_duplicate_event(visit):
    client = authenticated(visit.tenant)
    data = body(visit)
    before = client.get(path(visit), {"request_key": data["request_key"]}).json()[
        "data"
    ]
    assert before["operation"]["status"] == "absent"
    committed = client.post(path(visit), data, format="json")
    assert (
        committed.status_code == 200
    )  # Discard this response to model transport loss.
    canonical = client.get(path(visit), {"request_key": data["request_key"]}).json()[
        "data"
    ]
    assert canonical["operation"]["status"] == "recorded"
    assert canonical["post_visit_decision"]["value"] == "proceed"
    replay = client.post(path(visit), data, format="json")
    assert (
        replay.status_code == 200 and replay.json()["data"] == committed.json()["data"]
    )
    another_key = {**data, "request_key": str(uuid.uuid4())}
    assert client.post(path(visit), another_key, format="json").status_code == 200
    for changed, expected in [
        (dict(data, decision="decline", reason="changed"), "idempotency_conflict"),
        (
            dict(
                another_key,
                request_key=str(uuid.uuid4()),
                decision="decline",
                reason="changed",
            ),
            "decision_conflict",
        ),
    ]:
        response = client.post(path(visit), changed, format="json")
        assert response.status_code == 409 and response.json()["code"] == expected
    assert PropertyVisitDecision.objects.count() == PlanningEvent.objects.count() == 1


@pytest.mark.django_db
def test_schedule_revision_and_attended_appointment_are_protected(visit):
    stale = body(visit)
    visit.visit_time = (
        (timezone.localtime() - timedelta(hours=2)).time().replace(tzinfo=None)
    )
    visit.save(update_fields=["visit_time"])
    assert visit.revision == stale["expected_revision"] + 1
    response = authenticated(visit.tenant).post(path(visit), stale, format="json")
    assert response.status_code == 409 and response.json()["code"] == "stale_revision"
    decide(visit)
    response = authenticated(visit.tenant).post(
        PROPERTIES + f"visits/{visit.id}/cancel/", {}, format="json"
    )
    assert response.status_code == 409
    visit.refresh_from_db()
    visit.visit_date += timedelta(days=3)
    with pytest.raises(DecisionConflict):
        visit.save(update_fields=["visit_date"])


@pytest.mark.django_db
def test_feedback_survives_unavailable_accommodation(visit):
    visit.property.status = "rented"
    visit.property.save(update_fields=["status"])
    saved = decide(visit)
    assert saved["rental_continuation"]["status"] == "contracting_blocked"
    assert saved["rental_continuation"]["blocked_reason"] == "property_unavailable"
    assert saved["rental_continuation"]["next_action"] is None


@pytest.mark.django_db
def test_direct_invitation_cannot_omit_or_swap_source_or_offer(
    visit, rental_participants
):
    client = authenticated(visit.property.owner)
    without = {
        "property_id": str(visit.property.id),
        "tenant_id": str(visit.tenant.id),
        "request_key": str(uuid.uuid4()),
    }
    response = client.post(API + "tenancy-invitations/", without, format="json")
    assert (
        response.status_code == 400
        and response.json()["code"] == "source_visit_required"
    )
    decide(visit)
    for extra, expected in [
        ({"source_decision_id": str(uuid.uuid4())}, "source_mismatch"),
        ({"offer_id": str(uuid.uuid4())}, "offer_mismatch"),
    ]:
        response = client.post(
            API + "tenancy-invitations/", invite_body(visit, **extra), format="json"
        )
        assert response.status_code == 409 and response.json()["code"] == expected
    response = authenticated(rental_participants[2]).post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_historical_journey_resumes_without_fabricated_decision(visit):
    invitation = TenancyInvitation.objects.create(
        property=visit.property,
        owner=visit.property.owner,
        tenant=visit.tenant,
        initiated_by=visit.property.owner,
        expires_at=timezone.now() + timedelta(days=7),
        offer_id=visit.offer_id,
        offer_snapshot=visit.offer_snapshot,
        provenance_version="historical_v0",
    )
    data = authenticated(visit.tenant).get(path(visit)).json()["data"]
    assert data["post_visit_decision"] is None
    assert data["post_visit_actions"]["blocked_reason"] == "continuation_exists"
    assert data["rental_continuation"]["invitation_id"] == str(invitation.id)
    assert data["rental_continuation"]["compatibility_version"] == "historical_v0"
    response = authenticated(visit.tenant).post(path(visit), body(visit), format="json")
    assert response.status_code == 409 and not PropertyVisitDecision.objects.exists()
    assert invitation.source_visit_id is None


@pytest.mark.django_db
def test_notification_failure_keeps_decision_and_deduplicated_retry(visit, monkeypatch):
    decide(visit)
    monkeypatch.setattr(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user",
        lambda **kw: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    assert deliver_planning_events() == 0
    assert PlanningEvent.objects.get().delivered_at is None
    assert (
        PropertyVisitDecision.objects.count()
        == Notification.objects.filter(data__event_kind="visit_post_decision").count()
        == 1
    )
    monkeypatch.setattr(
        "core_apps.notifications.services.fcm_service.FCMService.send_push_to_user",
        lambda **kw: 1,
    )
    retry_at = timezone.now() + timedelta(minutes=3)
    monkeypatch.setattr(timezone, "now", lambda: retry_at)
    assert deliver_planning_events() == 1
    assert deliver_planning_events() == 0
    assert PlanningEvent.objects.get().attempts == 2
    assert (
        Notification.objects.filter(data__event_kind="visit_post_decision").count() == 1
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("race", ["same", "opposite", "cancel", "reschedule"])
def test_decision_transaction_races(visit, race):
    if connection.vendor != "postgresql":
        pytest.skip("Actual row locking requires PostgreSQL")
    data = body(visit)

    def call(index):
        client = authenticated(visit.tenant)
        if not index or race in {"same", "opposite"}:
            payload = dict(data)
            if index and race == "opposite":
                payload.update(
                    decision="decline",
                    reason="Not suitable",
                    request_key=str(uuid.uuid4()),
                )
            return client.post(path(visit), payload, format="json").status_code
        if race == "cancel":
            return client.post(
                PROPERTIES + f"visits/{visit.id}/cancel/", {}, format="json"
            ).status_code
        item = PropertyVisit.objects.get(pk=visit.pk)
        item.visit_date += timedelta(days=3)
        try:
            item.save(update_fields=["visit_date"])
            return 200
        except DecisionConflict:
            return 409

    codes = parallel_calls(call)
    assert sorted(codes) == ([200, 200] if race == "same" else [200, 409])
    visit.refresh_from_db()
    if PropertyVisitDecision.objects.exists():
        assert visit.status == "confirmed" and visit.visit_date < timezone.localdate()
        assert (
            PropertyVisitDecision.objects.count() == PlanningEvent.objects.count() == 1
        )
    else:
        assert visit.status == "canceled" or visit.visit_date > timezone.localdate()


@pytest.mark.django_db
def test_full_visit_decision_to_signed_agreement_and_initial_invoice(visit):
    decide(visit)
    owner, tenant = authenticated(visit.property.owner), authenticated(visit.tenant)
    response = owner.post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert response.status_code == 201, response.data
    invitation = response.data
    assert invitation["source_visit_id"] == str(visit.id)
    assert invitation["source_decision_id"] == str(visit.post_visit_decision.id)
    assert (
        tenant.get(path(visit)).json()["data"]["rental_continuation"]["next_action"]
        == "open_invitation"
    )
    response = tenant.post(
        API + f"tenancy-invitations/{invitation['id']}/respond/",
        {
            "decision": "accepted",
            "revision": invitation["revision"],
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert response.status_code == 200, response.data
    invitation = response.data
    assert (
        owner.get(path(visit)).json()["data"]["rental_continuation"]["next_action"]
        == "setup_owner_payments"
    )
    complete_owner_onboarding(visit.property.owner)
    start = timezone.localdate() + timedelta(days=1)
    response = owner.post(
        API + "leases/",
        {
            "invitation_id": invitation["id"],
            "invitation_revision": invitation["revision"],
            "property_id": str(visit.property.id),
            "tenant_id": str(visit.tenant.id),
            "offer_id": visit.offer_id,
            "offer_revision": 2,
            "terms": agreement_terms(start, start + timedelta(days=31)),
            "request_key": str(uuid.uuid4()),
            "expected_revision": 0,
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    lease = response.data["resource"]
    assert (
        owner.get(path(visit)).json()["data"]["rental_continuation"]["agreement_id"]
        == lease["id"]
    )
    for client in (owner, tenant):
        response = client.post(
            API + f"leases/{lease['id']}/review/",
            {
                "decision": "accept_review",
                "expected_revision": lease["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert response.status_code == 200, response.data
        lease = response.data["resource"]
    submit_body = {
        "decision": "submit_for_signature",
        "expected_revision": lease["revision"],
        "request_key": str(uuid.uuid4()),
    }
    response = owner.post(
        API + f"leases/{lease['id']}/submit-for-signature/",
        submit_body,
        format="json",
    )
    assert response.status_code == 200, response.data
    lease = response.data["resource"]
    for index, client in enumerate((owner, tenant)):
        session = client.post(
            API + f"leases/{lease['id']}/signing-session/",
            {
                "document_id": lease["document_id"],
                "document_hash": lease["document_hash"],
                "expected_revision": lease["revision"],
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert session.status_code == 201, session.data
        assert session.data["provider_mode"] == "mock"
        completion = session.data["mock_completion"]
        payload = {
            "expected_revision": completion["expected_revision"],
            "request_key": str(uuid.uuid4()),
        }
        completed = client.post(completion["path"], payload, format="json")
        assert completed.status_code == 200, completed.data
        assert (
            client.post(completion["path"], payload, format="json").status_code == 200
        )
        canonical = Lease.objects.get(id=lease["id"])
        assert canonical.status == ("pending_signatures" if index == 0 else "signed")
        if index == 0:
            original_document = (canonical.document_id, canonical.document_hash)
            replay = owner.post(
                API + f"leases/{lease['id']}/submit-for-signature/",
                submit_body,
                format="json",
            )
            assert replay.status_code == 200, replay.data
            assert replay.data["resource"]["document_id"] == lease["document_id"]
            changed = owner.post(
                API + f"leases/{lease['id']}/submit-for-signature/",
                {
                    **submit_body,
                    "expected_revision": canonical.revision,
                    "request_key": str(uuid.uuid4()),
                },
                format="json",
            )
            assert changed.status_code == 409, changed.data
            canonical.refresh_from_db()
            assert (canonical.document_id, canonical.document_hash) == original_document
    assert canonical.invoices.count() == 1 and canonical.activated_at is None
    continuation = tenant.get(path(visit)).json()["data"]["rental_continuation"]
    assert (
        continuation["status"] == "agreement_signed"
        and continuation["next_action"] == "open_invoice"
    )
    assert continuation["invoice_id"] == str(canonical.invoices.get().id)
    assert (
        not RentalInterest.objects.exists()
        and PropertyVisitDecision.objects.count() == 1
    )


@pytest.mark.django_db(transaction=True)
def test_complete_post_visit_journey_over_authenticated_http(
    visit, rental_participants, live_server, monkeypatch
):
    """Same connected journey through loopback HTTP/JWT rather than APIClient."""
    from core_apps.features.tests import test_rental_phase2
    from core_apps.features.tests.test_full_cycle_http import HttpActor
    import sys

    actors = {
        actor.pk: HttpActor(live_server.url, actor) for actor in rental_participants[:3]
    }
    monkeypatch.setattr(
        sys.modules[__name__], "authenticated", lambda actor: actors[actor.pk]
    )
    monkeypatch.setattr(
        test_rental_phase2, "authenticated", lambda actor: actors[actor.pk]
    )
    test_full_visit_decision_to_signed_agreement_and_initial_invoice(visit)
    assert sum(len(actor.calls) for actor in actors.values()) >= 20


@pytest.mark.django_db
@pytest.mark.parametrize("outcome", ["rejected", "expired", "revoked"])
def test_closed_invitation_never_resets_to_waiting(visit, outcome):
    decide(visit)
    client = authenticated(visit.property.owner)
    created = client.post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert created.status_code == 201
    invitation = TenancyInvitation.objects.get(id=created.data["id"])
    if outcome == "rejected":
        response = authenticated(visit.tenant).post(
            API + f"tenancy-invitations/{invitation.id}/respond/",
            {
                "decision": "rejected",
                "revision": invitation.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert response.status_code == 200
    elif outcome == "revoked":
        response = client.post(
            API + f"tenancy-invitations/{invitation.id}/revoke/",
            {
                "decision": "revoke_invitation",
                "expected_revision": invitation.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
        assert response.status_code == 200
    else:
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
        invitation.save(update_fields=["expires_at"])
    for actor in (visit.tenant, visit.property.owner):
        current = authenticated(actor).get(path(visit)).json()["data"]
        assert current["rental_continuation"]["status"] == f"invitation_{outcome}"
        assert current["rental_continuation"]["invitation_id"] == str(invitation.id)
        assert current["post_visit_decision"]["value"] == "proceed"
        assert current["rental_continuation"]["next_action"] == "open_invitation"
    assert TenancyInvitation.objects.count() == 1


@pytest.mark.django_db
def test_legacy_property_visit_preserves_broad_context_and_exact_chosen_offer(visit):
    visit.offer_id, visit.offer_snapshot = "", None
    visit.save(update_fields=["offer_id", "offer_snapshot"])
    decide(visit)
    offer = visit.property.rental_inventory["offers"][0]
    payload = invite_body(
        visit, offer_id=offer["id"], expected_offer_revision=offer["revision"]
    )
    response = authenticated(visit.property.owner).post(
        API + "tenancy-invitations/", payload, format="json"
    )
    assert response.status_code == 201
    assert response.data["offer_id"] == offer["id"]
    assert (
        visit.post_visit_decision.offer_id == ""
        and visit.post_visit_decision.offer_snapshot is None
    )


@pytest.mark.django_db
def test_ambiguous_historical_context_is_not_linked_or_redecided(visit):
    TenancyInvitation.objects.create(
        property=visit.property,
        owner=visit.property.owner,
        tenant=visit.tenant,
        initiated_by=visit.property.owner,
        expires_at=timezone.now() + timedelta(days=7),
        offer_id=visit.offer_id,
        offer_snapshot=visit.offer_snapshot,
        provenance_version="historical_v0",
    )
    PropertyVisit.objects.create(
        property=visit.property,
        tenant=visit.tenant,
        visit_date=visit.visit_date - timedelta(days=1),
        visit_time=visit.visit_time,
        status="confirmed",
        offer_id=visit.offer_id,
    )
    data = authenticated(visit.tenant).get(path(visit)).json()["data"]
    assert data["rental_continuation"]["status"] == "contracting_blocked"
    assert data["rental_continuation"]["invitation_id"] is None
    assert data["post_visit_actions"]["blocked_reason"] == "continuation_exists"
    assert not PropertyVisitDecision.objects.exists()


@pytest.mark.django_db
def test_migrated_legacy_agreement_resumes_without_a_retrospective_decision(visit):
    lease = Lease.objects.create(
        property=visit.property,
        owner=visit.property.owner,
        tenant=visit.tenant,
        offer_id=visit.offer_id,
        template_id="eg-residential-v1",
        template_version="1",
        start_date=timezone.localdate(),
        end_date=timezone.localdate() + timedelta(days=30),
        rent_amount_minor=1000000,
    )
    data = authenticated(visit.tenant).get(path(visit)).json()["data"]
    assert data["rental_continuation"]["agreement_id"] == str(lease.id)
    assert data["rental_continuation"]["compatibility_version"] == "historical_v0"
    assert (
        data["post_visit_decision"] is None
        and not data["post_visit_actions"]["can_submit"]
    )


@pytest.mark.django_db
def test_new_owner_cannot_follow_previous_owners_linked_invitation(
    visit, rental_participants
):
    decide(visit)
    response = authenticated(visit.property.owner).post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert response.status_code == 201
    replacement = rental_participants[2]
    visit.property.owner = replacement
    visit.property.save(update_fields=["owner"])
    result = authenticated(replacement).get(path(visit)).json()["data"]
    assert result["rental_continuation"]["invitation_id"] is None
    assert result["rental_continuation"]["blocked_reason"] == "ownership_changed"


@pytest.mark.django_db(transaction=True)
def test_one_operation_key_cannot_commit_different_visits(visit):
    if connection.vendor != "postgresql":
        pytest.skip("Actual row locking requires PostgreSQL")
    other = PropertyVisit.objects.create(
        property=visit.property,
        tenant=visit.tenant,
        visit_date=visit.visit_date - timedelta(days=1),
        visit_time=visit.visit_time,
        status="confirmed",
    )
    data = body(visit)
    responses = parallel_calls(
        lambda index: authenticated(visit.tenant).post(
            path(visit if index == 0 else other), data, format="json"
        )
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    assert PropertyVisitDecision.objects.count() == PlanningEvent.objects.count() == 1


@pytest.mark.django_db
def test_export_actual_visit_contract_for_flutter(visit, rental_participants):
    owner, tenant = authenticated(visit.property.owner), authenticated(visit.tenant)
    examples = {"eligible_tenant": tenant.get(path(visit)).json()}
    decide(visit)
    examples["proceed_tenant"] = tenant.get(path(visit)).json()
    examples["proceed_owner"] = owner.get(
        PROPERTIES + f"owner/visits/requests/{visit.id}/"
    ).json()
    invitation = owner.post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert invitation.status_code == 201
    examples["invitation"] = invitation.json()
    examples["invitation_tenant_context"] = tenant.get(path(visit)).json()
    declined = PropertyVisit.objects.create(
        property=visit.property,
        tenant=visit.tenant,
        visit_date=visit.visit_date - timedelta(days=1),
        visit_time=visit.visit_time,
        status="confirmed",
    )
    decide(
        declined,
        decision="decline",
        reason="المساحة لا تناسب احتياجاتي.\nThe space does not meet my needs. 😀",
    )
    examples["decline_tenant"] = tenant.get(path(declined)).json()
    examples["decline_owner"] = owner.get(
        PROPERTIES + f"owner/visits/requests/{declined.id}/"
    ).json()
    historical = PropertyVisit.objects.create(
        property=visit.property,
        tenant=rental_participants[2],
        visit_date=visit.visit_date,
        visit_time=visit.visit_time,
        status="confirmed",
        offer_id=visit.offer_id,
    )
    TenancyInvitation.objects.create(
        property=visit.property,
        owner=visit.property.owner,
        tenant=historical.tenant,
        initiated_by=visit.property.owner,
        expires_at=timezone.now() + timedelta(days=7),
        offer_id=visit.offer_id,
        offer_snapshot=visit.offer_snapshot,
        provenance_version="historical_v0",
    )
    examples["historical_tenant"] = (
        authenticated(historical.tenant).get(path(historical)).json()
    )
    assert "reason" not in examples["decline_owner"]["data"]["post_visit_decision"]
    assert (
        examples["historical_tenant"]["data"]["rental_continuation"][
            "compatibility_version"
        ]
        == "historical_v0"
    )
    directory = os.environ.get("SOKOUN_POST_VISIT_ARTIFACT_DIR")
    if directory:
        output = Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        (output / "django-visit-context.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source": "actual_local_django_api_test_responses",
                    "scenarios": examples,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )


@pytest.mark.django_db
def test_cairo_midnight_boundary_is_controlled_by_server_time(visit, monkeypatch):
    visit.visit_date = datetime(2026, 10, 13).date()
    visit.visit_time = time(0, 30)
    visit.save(update_fields=["visit_date", "visit_time"])
    before = datetime(2026, 10, 12, 21, 29, tzinfo=dt_timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: before)
    assert (
        not authenticated(visit.tenant)
        .get(path(visit))
        .json()["data"]["post_visit_actions"]["can_submit"]
    )
    after = before + timedelta(minutes=1)
    monkeypatch.setattr(timezone, "now", lambda: after)
    assert (
        authenticated(visit.tenant)
        .get(path(visit))
        .json()["data"]["post_visit_actions"]["can_submit"]
    )
    decide(visit)


@pytest.mark.django_db
def test_same_offer_id_cannot_silently_change_visited_accommodation(visit):
    decide(visit)
    offer = visit.property.rental_inventory["offers"][0]
    offer.update(rental_scope="room", room_ids=[str(uuid.uuid4())], revision=3)
    visit.property.save(update_fields=["rental_inventory"])
    owner = authenticated(visit.property.owner)
    current = owner.get(path(visit)).json()["data"]
    assert current["rental_continuation"]["blocked_reason"] == "accommodation_changed"
    response = owner.post(
        API + "tenancy-invitations/",
        invite_body(visit, expected_offer_revision=3),
        format="json",
    )
    assert (
        response.status_code == 409
        and response.json()["code"] == "accommodation_changed"
    )
    assert not TenancyInvitation.objects.exists()


@pytest.mark.django_db
def test_draft_edit_cannot_replace_the_accepted_physical_accommodation(visit):
    decide(visit)
    invitation = TenancyInvitation.objects.create(
        property=visit.property,
        owner=visit.property.owner,
        tenant=visit.tenant,
        initiated_by=visit.property.owner,
        status="accepted",
        expires_at=timezone.now() + timedelta(days=7),
        offer_id=visit.offer_id,
        offer_snapshot=visit.offer_snapshot,
        source_visit=visit,
        source_decision=visit.post_visit_decision,
    )
    complete_owner_onboarding(visit.property.owner)
    starts_on = timezone.localdate() + timedelta(days=1)
    data = {
        "invitation_id": str(invitation.id),
        "invitation_revision": invitation.revision,
        "property_id": str(visit.property.id),
        "tenant_id": str(visit.tenant.id),
        "offer_id": visit.offer_id,
        "offer_revision": 2,
        "terms": agreement_terms(starts_on, starts_on + timedelta(days=31)),
        "request_key": str(uuid.uuid4()),
        "expected_revision": 0,
    }
    owner = authenticated(visit.property.owner)
    response = owner.post(API + "leases/", data, format="json")
    assert response.status_code == 201, response.data
    saved = response.data["resource"]
    canonical = Lease.objects.get(id=saved["id"])
    before = (canonical.offer_snapshot, canonical.revision)
    visit.property.rental_inventory["offers"][0].update(
        rental_scope="room", room_ids=[str(uuid.uuid4())], revision=3
    )
    visit.property.save(update_fields=["rental_inventory"])
    response = owner.patch(
        API + f"leases/{canonical.id}/",
        {
            **data,
            "offer_revision": 3,
            "expected_revision": canonical.revision,
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert response.status_code == 409, response.data
    assert response.json()["code"] == "accommodation_changed"
    canonical.refresh_from_db()
    assert (canonical.offer_snapshot, canonical.revision) == before


@pytest.mark.django_db
def test_original_operation_is_recoverable_after_auxiliary_record_retention(visit):
    client = authenticated(visit.tenant)
    payload = body(visit)
    first = client.post(path(visit), payload, format="json")
    assert first.status_code == 200
    IdempotencyRecord.objects.filter(operation="visit.post_visit_decision").delete()
    recovered = client.get(path(visit), {"request_key": payload["request_key"]})
    assert recovered.json()["data"]["operation"]["status"] == "recorded"
    assert client.post(path(visit), payload, format="json").status_code == 200
    other = PropertyVisit.objects.create(
        property=visit.property,
        tenant=visit.tenant,
        visit_date=visit.visit_date - timedelta(days=2),
        visit_time=visit.visit_time,
        status="confirmed",
    )
    response = client.post(path(other), payload, format="json")
    assert (
        response.status_code == 409
        and response.json()["code"] == "idempotency_conflict"
    )
    assert PropertyVisitDecision.objects.count() == PlanningEvent.objects.count() == 1


@pytest.mark.django_db
def test_unexpected_failure_logs_identifiers_without_private_feedback(
    visit, monkeypatch, caplog
):
    from core_apps.notifications.services.notification_service import (
        NotificationService,
    )

    private_text = "Private decline feedback: المكان لا يناسبني"

    def failed_notification(**kwargs):
        raise RuntimeError(private_text)

    monkeypatch.setattr(NotificationService, "create_notification", failed_notification)
    payload = body(visit, decision="decline", reason=private_text)
    client = authenticated(visit.tenant)
    response = client.post(path(visit), payload, format="json")
    assert response.status_code == 500
    assert response.json()["code"] == "decision_request_failed"
    assert (
        private_text not in response.content.decode()
        and private_text not in caplog.text
    )
    assert "post_visit_request_failed" in caplog.text and "RuntimeError" in caplog.text
    assert (
        not PropertyVisitDecision.objects.exists()
        and not PlanningEvent.objects.exists()
    )
    recovered = client.get(path(visit), {"request_key": payload["request_key"]})
    assert recovered.json()["data"]["operation"]["status"] == "absent"


@pytest.mark.django_db
def test_grandfather_migration_preserves_existing_rows_without_fabricating_decisions(
    visit,
):
    from importlib import import_module
    from django.apps import apps

    old = TenancyInvitation.objects.create(
        property=visit.property,
        owner=visit.property.owner,
        tenant=visit.tenant,
        initiated_by=visit.property.owner,
        status="revoked",
        revision=4,
        expires_at=timezone.now() - timedelta(days=1),
    )
    decide(visit)
    current = authenticated(visit.property.owner).post(
        API + "tenancy-invitations/", invite_body(visit), format="json"
    )
    assert current.status_code == 201, current.data
    migration = import_module(
        "core_apps.features.migrations.0015_post_visit_invitation_compatibility"
    )
    migration.grandfather_existing_invitations(apps, None)
    old.refresh_from_db()
    linked = TenancyInvitation.objects.get(id=current.data["id"])
    assert old.provenance_version == "historical_v0" and old.revision == 4
    assert old.status == "revoked" and old.source_decision_id is None
    assert linked.provenance_version == "visit_decision_v1"
    assert linked.source_decision_id == visit.post_visit_decision.pk
    assert PropertyVisitDecision.objects.count() == 1
