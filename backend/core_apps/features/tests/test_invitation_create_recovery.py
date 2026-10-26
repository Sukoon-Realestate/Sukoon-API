"""Creation recovery uses the same property lock and never repeats the invitation."""

# flake8: noqa: F401,F811
import uuid
import pytest
from core_apps.features.models import IdempotencyRecord, TenancyInvitation
from core_apps.notifications.models import Notification
from .test_tenancy_invitations import (
    participants,
    owned_property,
    authenticated,
    create_payload,
)
from .test_cycle_concurrency import parallel_calls

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/tenancy-invitations/"


def resolve(owner, property_obj, key):
    return authenticated(owner).post(
        f"{API}create/resolve/",
        {"property_id": str(property_obj.id), "request_key": key},
        format="json",
    )


def create(owner, body):
    return authenticated(owner).post(API, body, format="json")


def test_confirmed_creation_returns_current_exact_invitation_without_effects(
    participants, owned_property
):
    owner, tenant, _ = participants
    body = create_payload(owned_property, tenant)
    result = create(owner, body)
    assert result.status_code == 201, result.data
    item = TenancyInvitation.objects.get(id=result.data["id"])
    TenancyInvitation.objects.filter(pk=item.pk).update(status="revoked", revision=2)
    count = Notification.objects.count()
    response = resolve(owner, owned_property, body["request_key"])
    assert response.status_code == 200 and response.data["status"] == "confirmed"
    assert response.data["invitation"]["id"] == str(item.id)
    assert response.data["invitation"]["status"] == "revoked"
    assert response["Cache-Control"] == "private, no-store"
    assert resolve(owner, owned_property, body["request_key"]).data == response.data
    assert (
        Notification.objects.count() == count and TenancyInvitation.objects.count() == 1
    )


def test_fenced_absence_prevents_late_creation_but_allows_new_explicit_attempt(
    participants, owned_property
):
    owner, tenant, _ = participants
    body = create_payload(owned_property, tenant)
    recovered = resolve(owner, owned_property, body["request_key"])
    assert (
        recovered.data["status"] == "absent_final"
        and recovered.data["invitation"] is None
    )
    assert create(owner, body).status_code == 409
    assert not TenancyInvitation.objects.exists()
    assert create(owner, {**body, "request_key": str(uuid.uuid4())}).status_code == 201
    assert (
        resolve(owner, owned_property, body["request_key"]).data["status"]
        == "absent_final"
    )


def test_recovery_requires_current_owner_and_same_property(
    participants, owned_property
):
    owner, tenant, stranger = participants
    key = str(uuid.uuid4())
    assert resolve(tenant, owned_property, key).status_code == 404
    assert resolve(stranger, owned_property, key).status_code == 404
    assert not IdempotencyRecord.objects.filter(request_key=key).exists()
    IdempotencyRecord.objects.create(
        user=owner,
        operation="tenancy_invitation.create",
        request_key=key,
        fingerprint="different",
        request_subject_id=uuid.uuid4(),
        response_data={},
    )
    assert resolve(owner, owned_property, key).status_code == 400


@pytest.mark.django_db(transaction=True)
def test_create_and_recovery_race_commits_one_result(participants, owned_property):
    owner, tenant, _ = participants
    body = create_payload(owned_property, tenant)
    command, recovery = parallel_calls(
        lambda i: (
            create(owner, body)
            if i == 0
            else resolve(owner, owned_property, body["request_key"])
        )
    )
    assert recovery.status_code == 200
    if recovery.data["status"] == "confirmed":
        assert command.status_code == 201 and TenancyInvitation.objects.count() == 1
        assert recovery.data["invitation"]["id"] == command.data["id"]
    else:
        assert recovery.data["status"] == "absent_final"
        assert command.status_code == 409 and not TenancyInvitation.objects.exists()
    assert (
        IdempotencyRecord.objects.filter(
            user=owner, request_key=body["request_key"]
        ).count()
        == 1
    )
