"""A lost invitation response is queried or durably fenced, never inferred."""

# flake8: noqa: F401,F811
import uuid
import pytest
from core_apps.features.models import IdempotencyRecord, TenancyInvitation
from core_apps.notifications.models import Notification
from .test_tenancy_invitation_revoke import invitation
from .test_tenancy_invitations import participants, owned_property, authenticated
from .test_cycle_concurrency import parallel_calls

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/tenancy-invitations/"


def resolve(item, key, user=None):
    return authenticated(user or item.tenant).post(
        f"{API}{item.id}/respond/resolve/",
        {"request_key": key},
        format="json",
    )


def respond(item, body):
    return authenticated(item.tenant).post(
        f"{API}{item.id}/respond/", body, format="json"
    )


@pytest.mark.parametrize("decision", ["accepted", "rejected"])
def test_confirmed_response_recovers_original_decision_and_current_state(
    invitation, decision
):
    key = str(uuid.uuid4())
    body = {"decision": decision, "revision": invitation.revision, "request_key": key}
    result = respond(invitation, body)
    assert result.status_code == 200, result.data
    count = Notification.objects.count()
    TenancyInvitation.objects.filter(pk=invitation.pk).update(
        status="revoked", revision=3
    )
    recovered = resolve(invitation, key)
    assert recovered.status_code == 200 and recovered.data["status"] == "confirmed"
    assert recovered.data["decision"] == decision
    assert recovered.data["invitation"]["status"] == "revoked"
    assert recovered.data["invitation"]["id"] == str(invitation.id)
    assert recovered["Cache-Control"] == "private, no-store"
    assert resolve(invitation, key).data == recovered.data
    assert Notification.objects.count() == count


def test_absence_fences_late_response_and_allows_only_fresh_explicit_command(
    invitation,
):
    key = str(uuid.uuid4())
    body = {"decision": "accepted", "revision": invitation.revision, "request_key": key}
    recovered = resolve(invitation, key)
    assert recovered.data["status"] == "absent_final"
    assert respond(invitation, body).status_code == 409
    invitation.refresh_from_db()
    assert invitation.status == "pending" and not invitation.accepted_at
    result = respond(invitation, {**body, "request_key": str(uuid.uuid4())})
    assert result.status_code == 200, result.data
    assert resolve(invitation, key).data["status"] == "absent_final"


def test_recovery_is_private_to_the_original_tenant(invitation, participants):
    key = str(uuid.uuid4())
    assert resolve(invitation, key, invitation.owner).status_code == 403
    assert resolve(invitation, key, participants[2]).status_code == 404
    assert not IdempotencyRecord.objects.filter(request_key=key).exists()


@pytest.mark.django_db(transaction=True)
def test_response_and_recovery_race_has_one_definitive_result(invitation):
    key = str(uuid.uuid4())
    body = {"decision": "accepted", "revision": invitation.revision, "request_key": key}
    command, recovery = parallel_calls(
        lambda i: respond(invitation, body) if i == 0 else resolve(invitation, key)
    )
    assert recovery.status_code == 200
    invitation.refresh_from_db()
    if recovery.data["status"] == "confirmed":
        assert command.status_code == 200 and invitation.status == "accepted"
    else:
        assert recovery.data["status"] == "absent_final"
        assert command.status_code == 409 and invitation.status == "pending"
    assert (
        IdempotencyRecord.objects.filter(
            user=invitation.tenant, request_key=key
        ).count()
        == 1
    )
