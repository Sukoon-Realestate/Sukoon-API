"""Owner revocation stays available without signing or payment providers."""

import uuid
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace

import pytest
from django.db import connection
from django.utils import timezone

from core_apps.features import rental_phase2_views
from core_apps.features.models import IdempotencyRecord, Lease, TenancyInvitation
from core_apps.features.serializers import TenancyInvitationSerializer
from .test_cycle_concurrency import parallel_calls
from .test_tenancy_invitations import authenticated, owned_property, participants


API = "/api/v1/features/v1/"


@pytest.fixture
def invitation(participants, owned_property):  # noqa: F811 - shared pytest fixtures
    owner, tenant, _ = participants
    return TenancyInvitation.objects.create(
        property=owned_property,
        owner=owner,
        tenant=tenant,
        initiated_by=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )


def revoke_body(invitation):
    return {
        "decision": "revoke_invitation",
        "expected_revision": invitation.revision,
        "request_key": str(uuid.uuid4()),
    }


def readiness_url(invitation):
    return (
        API + f"rental-capabilities/?subject_id={invitation.id}"
        "&action=revoke_invitation"
    )


def serialized_actions(user, invitation):
    return TenancyInvitationSerializer(
        invitation, context={"request": SimpleNamespace(user=user)}
    ).data["allowed_actions"]


@pytest.mark.django_db
@pytest.mark.parametrize("provider", ["disabled", "fake"])
@pytest.mark.parametrize("language", ["en", "ar"])
@pytest.mark.parametrize("invitation_status", ["pending", "accepted"])
def test_owner_can_revoke_without_provider_and_replay_original_receipt(
    invitation, settings, provider, language, invitation_status
):
    settings.RENTAL_PROVIDER_BACKEND = provider
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = provider == "fake"
    invitation.status = invitation_status
    invitation.revision = 4
    invitation.save(update_fields=["status", "revision"])
    client = authenticated(invitation.owner)
    client.defaults["HTTP_ACCEPT_LANGUAGE"] = language
    detail_url = API + f"tenancy-invitations/{invitation.id}/"
    body = revoke_body(invitation)

    readiness = client.get(readiness_url(invitation))
    assert readiness.status_code == 200
    assert readiness["Cache-Control"] == "private, no-store"
    assert "rental_agreements" in readiness.data["enabled_capabilities"]
    assert "revoke_invitation" in readiness.data["allowed_actions"]
    assert readiness.data["blocking_reasons"] == []
    if provider == "disabled":
        assert "create_lease" not in readiness.data["allowed_actions"]
    assert client.get(detail_url).data["allowed_actions"] == ["revoke_invitation"]

    revoked = client.post(detail_url + "revoke/", body, format="json")
    assert revoked.status_code == 200
    resource = revoked.data["resource"]
    assert resource["status"] == "revoked"
    assert resource["revision"] == 5
    assert resource["revoked_at"] is not None
    assert resource["allowed_actions"] == []
    assert resource["eligible_for_lease"] is False
    receipt = revoked.data["operation_receipt"]
    assert receipt["request_key"] == body["request_key"]
    assert receipt["subject_id"] == str(invitation.id)
    assert receipt["revision"] == 5

    for actor, workspace in (
        (invitation.owner, "owner"),
        (invitation.tenant, "tenant"),
    ):
        actor_client = authenticated(actor)
        detail = actor_client.get(detail_url).data
        listed = actor_client.get(
            API + f"tenancy-invitations/?workspace={workspace}"
        ).data["results"][0]
        for item in (detail, listed):
            assert item["status"] == "revoked"
            assert item["revision"] == 5
            assert item["allowed_actions"] == []
        assert (
            "revoke_invitation"
            not in actor_client.get(readiness_url(invitation)).data["allowed_actions"]
        )

    # Replaying a completed command ignores the now terminal state/revision.
    replay = client.post(detail_url + "revoke/", body, format="json")
    assert replay.status_code == 200
    assert replay.data == revoked.data
    operation = client.get(
        API + f"rental-operations/{body['request_key']}/?subject_id={invitation.id}"
    )
    assert operation.data["status"] == "confirmed"
    assert operation.data["operation_receipt"] == receipt
    changed = client.post(
        detail_url + "revoke/", {**body, "note": "changed"}, format="json"
    )
    assert changed.status_code == 409
    assert changed.json()["code"] == "idempotency_conflict"
    invitation.refresh_from_db()
    assert invitation.revision == 5
    assert (
        IdempotencyRecord.objects.filter(
            operation=f"rental_invitation.revoke.{invitation.id}"
        ).count()
        == 1
    )


@pytest.mark.django_db
@pytest.mark.parametrize("actor", ["tenant", "stranger"])
def test_tenant_and_stranger_cannot_revoke(
    invitation, participants, actor
):  # noqa: F811
    client = authenticated(invitation.tenant if actor == "tenant" else participants[2])
    readiness = client.get(readiness_url(invitation))
    if actor == "tenant":
        assert readiness.status_code == 200
        assert "revoke_invitation" not in readiness.data["allowed_actions"]
        assert readiness.data["blocking_reasons"]
    else:
        assert readiness.status_code == 404
    response = client.post(
        API + f"tenancy-invitations/{invitation.id}/revoke/",
        revoke_body(invitation),
        format="json",
    )
    assert response.status_code == 404
    invitation.refresh_from_db()
    assert invitation.status == "pending"
    assert invitation.revision == 1
    assert not IdempotencyRecord.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("account_field", ["is_active", "is_verified"])
def test_revocation_requires_verified_active_owner(invitation, account_field):
    owner = invitation.owner
    setattr(owner, account_field, False)
    owner.save(update_fields=[account_field])
    client = authenticated(owner)
    readiness = client.get(readiness_url(invitation))
    assert readiness.status_code == 200
    assert readiness.data["account_verified"] is False
    assert readiness.data["allowed_actions"] == []
    assert serialized_actions(owner, invitation) == []
    response = client.post(
        API + f"tenancy-invitations/{invitation.id}/revoke/",
        revoke_body(invitation),
        format="json",
    )
    assert response.status_code == 403
    invitation.refresh_from_db()
    assert invitation.status == "pending"
    assert invitation.revision == 1
    assert not IdempotencyRecord.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "state", ["rejected", "revoked", "expired", "past_due", "consumed", "lease"]
)
def test_unavailable_invitation_cannot_be_revoked(invitation, state):
    if state == "past_due":
        invitation.expires_at = timezone.now() - timedelta(seconds=1)
    elif state == "consumed":
        invitation.consumed_at = timezone.now()
    elif state == "lease":
        invitation.lease = Lease.objects.create(
            property=invitation.property,
            owner=invitation.owner,
            tenant=invitation.tenant,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=30),
            rent_amount_minor=500000,
        )
    else:
        invitation.status = state
    invitation.save()
    client = authenticated(invitation.owner)
    readiness = client.get(readiness_url(invitation))
    assert readiness.status_code == 200
    assert "revoke_invitation" not in readiness.data["allowed_actions"]
    assert readiness.data["blocking_reasons"]
    assert serialized_actions(invitation.owner, invitation) == []
    response = client.post(
        API + f"tenancy-invitations/{invitation.id}/revoke/",
        revoke_body(invitation),
        format="json",
    )
    assert response.status_code == 409
    invitation.refresh_from_db()
    assert invitation.revision == 1
    assert not IdempotencyRecord.objects.exists()


@pytest.mark.django_db
def test_revocation_rejects_stale_revision_without_mutation(invitation):
    response = authenticated(invitation.owner).post(
        API + f"tenancy-invitations/{invitation.id}/revoke/",
        {**revoke_body(invitation), "expected_revision": 2},
        format="json",
    )
    assert response.status_code == 409
    assert response.json()["code"] == "stale_revision"
    invitation.refresh_from_db()
    assert invitation.status == "pending"
    assert invitation.revision == 1
    assert not IdempotencyRecord.objects.exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("same_key", [False, True])
def test_concurrent_revocations_increment_once(invitation, same_key, monkeypatch):
    if connection.vendor != "postgresql":
        pytest.skip("Revocation races require PostgreSQL row locks")
    body = revoke_body(invitation)
    bodies = [body, dict(body)]
    if not same_key:
        bodies[1]["request_key"] = str(uuid.uuid4())
    barrier = Barrier(2)
    original = rental_phase2_views._replay_response

    def synchronized_replay(*args):
        result = original(*args)
        if not connection.in_atomic_block:
            # Both requests miss the receipt before either acquires the row lock.
            barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(rental_phase2_views, "_replay_response", synchronized_replay)
    responses = parallel_calls(
        lambda index: authenticated(invitation.owner).post(
            API + f"tenancy-invitations/{invitation.id}/revoke/",
            bodies[index],
            format="json",
        )
    )
    assert sorted(response.status_code for response in responses) == (
        [200, 200] if same_key else [200, 409]
    )
    if same_key:
        assert responses[0].data == responses[1].data
    invitation.refresh_from_db()
    assert invitation.status == "revoked"
    assert invitation.revision == 2
    record = IdempotencyRecord.objects.get()
    assert record.result_revision == 2
