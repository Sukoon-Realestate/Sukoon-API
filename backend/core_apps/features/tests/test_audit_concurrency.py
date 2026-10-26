# Pytest imports fixtures for injection by name.
# flake8: noqa: F401,F811

import uuid
import pytest
from django.db import connection
from django.urls import reverse
from rest_framework.exceptions import APIException
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from core_apps.features.tests.test_rental_phase6 import phase6_lease, client_for
from core_apps.features.models import (
    SearchAlert,
    BoostCampaign,
    IdempotencyRecord,
    RentalDispute,
    RentInvoice,
)
from core_apps.features.catalog_models import PromotionOption
from core_apps.chat.services.message_service_parts.get_or_create_direct_conversation import (
    get_or_create_direct_conversation,
)
from core_apps.chat.models import Conversation, ConversationParticipant
from core_apps.common.idempotency import execute_idempotent, resolve_or_close
from core_apps.users.models import User

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def postgres_only():
    if connection.vendor != "postgresql":
        pytest.skip("Controlled row-lock races require PostgreSQL")


def test_first_chat_pair_is_canonical_under_opposite_direction_race(phase6_lease):
    owner, tenant, _ = phase6_lease
    results = parallel_calls(
        lambda i: str(
            get_or_create_direct_conversation(
                user=owner if i else tenant, other_user=tenant if i else owner
            ).id
        )
    )
    assert results[0] == results[1]
    assert Conversation.objects.count() == 1
    assert ConversationParticipant.objects.count() == 2


def test_unscoped_legacy_chats_are_not_reassigned_to_a_new_workspace(phase6_lease):
    owner, tenant, _ = phase6_lease
    originals = []
    for _ in range(2):
        item = Conversation.objects.create()
        ConversationParticipant.objects.create(conversation=item, user=owner)
        ConversationParticipant.objects.create(conversation=item, user=tenant)
        originals.append(item)
    current = get_or_create_direct_conversation(user=owner, other_user=tenant)
    assert current.pk not in {item.pk for item in originals}
    assert get_or_create_direct_conversation(user=tenant, other_user=owner) == current
    assert Conversation.objects.count() == 3
    assert (
        Conversation.objects.filter(pk__in=[item.pk for item in originals]).count() == 2
    )
    assert all(not item.workspace_contexts.exists() for item in originals)
    assert set(current.workspace_contexts.values_list("workspace", flat=True)) == {
        "individual"
    }
    assert Conversation.objects.exclude(direct_context_key=None).count() == 1


def test_same_revision_alert_edits_have_one_winner(phase6_lease):
    _, tenant, _ = phase6_lease
    item = SearchAlert.objects.create(user=tenant, name="Saved search", filters={})
    responses = parallel_calls(
        lambda i: client_for(tenant).patch(
            f"/api/v1/features/v1/search-alerts/{item.id}/",
            {"revision": 1, "enabled": bool(i), "request_key": str(uuid.uuid4())},
            format="json",
        )
    )
    assert sorted(r.status_code for r in responses) == [200, 409]
    item.refresh_from_db()
    assert item.revision == 2


def test_delete_alert_receipt_replays_after_tombstone(phase6_lease):
    _, tenant, _ = phase6_lease
    item = SearchAlert.objects.create(user=tenant, name="Saved search", filters={})
    payload = {"revision": 1, "request_key": str(uuid.uuid4())}
    responses = parallel_calls(
        lambda _: client_for(tenant).delete(
            f"/api/v1/features/v1/search-alerts/{item.id}/", payload, format="json"
        )
    )
    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].data == responses[1].data
    item.refresh_from_db()
    assert item.deleted_at and item.revision == 2


def test_distinct_promotion_commands_cannot_overlap(phase6_lease):
    owner, _, lease = phase6_lease
    option = PromotionOption.objects.create(
        id="audit-free", title_en="Test", title_ar="Test", duration_days=3
    )
    responses = parallel_calls(
        lambda _: client_for(owner).post(
            "/api/v1/features/v1/boost-campaigns/",
            {
                "property_id": str(lease.property.id),
                "option_id": option.id,
                "option_revision": option.revision,
                "request_key": str(uuid.uuid4()),
            },
            format="json",
        )
    )
    assert sorted(r.status_code for r in responses) == [201, 400]
    assert BoostCampaign.objects.filter(property=lease.property).count() == 1


def test_recovery_fence_racing_original_has_one_durable_outcome(phase6_lease):
    _, tenant, lease = phase6_lease
    key = str(uuid.uuid4())

    def action():
        item = RentalDispute.objects.create(
            lease=lease,
            opened_by=tenant,
            subject_kind="invoice",
            subject_id=uuid.uuid4(),
        )
        return {"id": str(item.id)}, 201, item.id

    def call(index):
        if index:
            return resolve_or_close(
                user=tenant, operation="support.ticket.create:tenant", key=key
            ).recovery_status
        try:
            return execute_idempotent(
                user=tenant,
                operation="support.ticket.create:tenant",
                key=key,
                payload={"intent": "one"},
                action=action,
            )[1]
        except APIException as exc:
            return exc.status_code

    outcomes = parallel_calls(call)
    record = IdempotencyRecord.objects.get(user=tenant, request_key=key)
    assert (record.recovery_status, RentalDispute.objects.count()) in {
        ("confirmed", 1),
        ("absent_final", 0),
    }
    if record.recovery_status == "absent_final":
        assert outcomes[0] == 409
    else:
        assert outcomes[0] == 201


def test_dispute_same_request_race_creates_one_case(phase6_lease):
    _, tenant, lease = phase6_lease
    invoice = RentInvoice.objects.create(
        lease=lease, reference="AUDIT-RACE", due_date=lease.start_date, amount_minor=100
    )
    body = {
        "lease_id": str(lease.id),
        "subject_kind": "invoice",
        "subject_id": str(invoice.id),
        "request_key": str(uuid.uuid4()),
        "reason": "Review charge",
    }
    responses = parallel_calls(
        lambda _: client_for(tenant).post(
            reverse("rental-disputes"), body, format="json"
        )
    )
    assert [r.status_code for r in responses] == [201, 201]
    assert responses[0].data == responses[1].data
    assert RentalDispute.objects.count() == 1


def test_revoked_financial_role_cannot_finish_an_already_started_review(phase6_lease):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from unittest.mock import patch
    from django.db import connections
    from core_apps.admin_api.models import StaffProfile
    from core_apps.features.models import RentalChange
    from core_apps.features.services.financial_authority import require_financial_actor

    owner, tenant, lease = phase6_lease
    operator = User.objects.create_user(
        email="role-race@example.test", password="test", is_verified=True
    )
    profile = StaffProfile.objects.create(user=operator, role_name="financial_approver")
    item = RentalChange.objects.create(
        lease=lease, requester=tenant, kind="external_payment"
    )
    started, revoked = Event(), Event()

    def gate(user, roles, action, *, lock=False):
        result = require_financial_actor(user, roles, action, lock=lock)
        if not lock:
            started.set()
            assert revoked.wait(5)
        return result

    def review():
        try:
            return client_for(operator).post(
                reverse("external-claim-respond", args=[item.id]),
                {
                    "action": "reject",
                    "expected_revision": 1,
                    "request_key": str(uuid.uuid4()),
                    "note": "Review",
                },
                format="json",
            )
        finally:
            connections.close_all()

    with patch(
        "core_apps.features.services.financial_authority.require_financial_actor",
        side_effect=gate,
    ):
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(review)
            assert started.wait(5)
            StaffProfile.objects.filter(pk=profile.pk).update(is_active=False)
            revoked.set()
            response = future.result(timeout=10)
    assert response.status_code == 403
    item.refresh_from_db()
    assert item.status == "proposed" and item.revision == 1
    assert not IdempotencyRecord.objects.filter(result_subject_id=item.id).exists()
