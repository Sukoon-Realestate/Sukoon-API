"""Current corporate continuation capability and synthetic-completion boundary."""

from datetime import timedelta
import uuid
import pytest
from django.db import connection
from django.utils import timezone
from core_apps.features.models import IdempotencyRecord
from core_apps.features.rental_phase5_views_parts.change_signing_session import (
    complete_change_signature,
)
from core_apps.features.tests.test_company_continuations import (
    cycle,
    person,
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
    agreement,
    signed_agreement,
    active_agreement,
    act,
    expose_unexpected_exceptions,
    proposal,
    reviews,
)


@pytest.fixture
def pending_continuation(active_agreement):
    actors, item = active_agreement
    change = proposal(actors, item)
    reviews(item, change)
    response = act(
        item,
        actors["owner"],
        "submit_continuation",
        change_id=str(change.id),
        digest=change.snapshot_digest,
    )
    assert response.status_code == 200
    for role in ("owner", "signer"):
        response = act(
            item,
            actors[role],
            "sign_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
        )
        assert response.status_code == 200
    change.refresh_from_db()
    change.rental_change.refresh_from_db()
    return actors, item, change


def capability(client, event):
    def read_only(execute, sql, params, many, context):
        statement = sql.strip().upper()
        assert statement.startswith("SELECT"), "Capability GET attempted a write"
        assert "FOR UPDATE" not in statement and "PG_ADVISORY" not in statement
        return execute(sql, params, many, context)

    with connection.execute_wrapper(read_only):
        return client.get(
            API + "rental-capabilities/",
            {"subject_id": str(event.id), "action": "sign"},
        )


def completion_path(session):
    return API + f"mock-provider/change-signing-sessions/{session.id}/complete/"


def session_state(event):
    # Keep hosted/provider URLs out of assertion output, including failures.
    return list(
        event.signing_sessions.order_by("id").values(
            "id",
            "signer_id",
            "status",
            "change_revision",
            "document_id",
            "document_hash",
            "expires_at",
            "completed_at",
        )
    )


def assert_blocked_without_completion(
    client, actor, item, change, session, *, language=None
):
    event = change.rental_change
    event.refresh_from_db()
    item.lease.refresh_from_db()
    before = session_state(event)
    revision, signed_by = event.revision, list(event.signed_by)
    lease_revision = item.lease.revision
    grant = capability(client, event)
    assert grant.status_code in {200, 403, 404}
    if grant.status_code == 200:
        assert "sign" not in grant.data["allowed_actions"]
        if language:
            message = (
                "هذا الإجراء غير متاح للعقد حاليًا. حدّث الحالة وراجع المتطلبات قبل المتابعة."
                if language == "ar"
                else "The requested rental action is not available yet."
            )
            assert grant.json()["data"]["blocking_reasons"] == [message]
    body = command(expected_revision=event.revision)
    result = client.post(completion_path(session), body, format="json")
    assert result.status_code in {403, 404, 409}, result.status_code
    if language:
        assert result.json()["message"] == message
    event.refresh_from_db()
    item.lease.refresh_from_db()
    assert session_state(event) == before
    assert event.revision == revision and event.signed_by == signed_by
    assert item.lease.revision == lease_revision
    assert not IdempotencyRecord.objects.filter(
        user=actor, request_key=body["request_key"]
    ).exists()


@pytest.mark.django_db
def test_company_continuation_current_signatories_can_read_completion_capability(
    pending_continuation,
):
    actors, item, change = pending_continuation
    event = change.rental_change
    for role in ("owner", "signer"):
        client = authenticated(actors[role])
        response = capability(client, event)
        assert response.status_code == 200
        assert response.data["enabled_capabilities"] == ["rental_changes"]
        assert response.data["allowed_actions"] == ["sign"], response.data
        assert response.data["blocking_reasons"] == []
        assert response["Cache-Control"] == "private, no-store"
    event.refresh_from_db()
    assert event.status == "pending_signatures" and event.revision == 2
    assert not event.signing_sessions.exclude(status="pending").exists()


@pytest.mark.django_db
def test_company_mock_completion_preserves_owned_receipt_recovery_and_replay(
    pending_continuation,
):
    actors, item, change = pending_continuation
    event = change.rental_change
    completions = []
    for role in ("owner", "signer"):
        client = authenticated(actors[role])
        session = event.signing_sessions.get(signer=actors[role])
        grant = capability(client, event)
        assert grant.status_code == 200 and grant.data["allowed_actions"] == ["sign"]
        event.refresh_from_db()
        body = command(expected_revision=event.revision)
        result = client.post(completion_path(session), body, format="json")
        assert result.status_code == 200, result.status_code
        receipt = result.data["operation_receipt"]
        assert receipt["subject_id"] == str(event.id)
        assert receipt["request_key"] == body["request_key"]
        assert receipt["status"] == "confirmed"
        completions.append((client, session, body, receipt))
    change.refresh_from_db()
    event.refresh_from_db()
    assert change.state == "applied" and event.status == "applied"
    assert event.revision == 3 and event.signing_sessions.count() == 2
    assert set(event.signed_by) == {str(actors[r].id) for r in ("owner", "signer")}
    for client, session, body, receipt in completions:
        assert "sign" not in capability(client, event).data["allowed_actions"]
        recovered = client.get(
            API + f"rental-operations/{body['request_key']}/",
            {"subject_id": str(event.id)},
        )
        assert recovered.status_code == 200
        assert recovered.data["operation_receipt"] == receipt
        replay = client.post(completion_path(session), body, format="json")
        assert replay.status_code == 200
        assert replay.data["operation_receipt"] == receipt
        fresh = client.post(
            completion_path(session),
            command(expected_revision=event.revision),
            format="json",
        )
        assert fresh.status_code == 409
    event.refresh_from_db()
    assert event.revision == 3 and event.signing_sessions.count() == 2


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role", ["payer", "coordinator", "reviewer", "employee", "colleague", "approver"]
)
def test_other_company_responsibilities_cannot_complete_a_signing_session(
    pending_continuation, role
):
    actors, item, change = pending_continuation
    session = change.rental_change.signing_sessions.get(signer=actors["owner"])
    assert_blocked_without_completion(
        authenticated(actors[role]), actors[role], item, change, session
    )


@pytest.mark.django_db
@pytest.mark.parametrize("context", ["missing", "employee", "other-company"])
def test_current_signer_needs_the_exact_selected_company_role(
    pending_continuation, context
):
    actors, item, change = pending_continuation
    actor = actors["signer"]
    client = authenticated(actor)
    if context == "missing":
        client.credentials()
    elif context == "employee":
        client.credentials(
            HTTP_X_SUKOON_COMPANY_ID=str(actors["company"].id),
            HTTP_X_SUKOON_COMPANY_ROLE="employee",
        )
    else:
        from core_apps.features.services.company.membership import create_company

        other = create_company(
            actor,
            {
                "name": "Independent context",
                "registration_number": "TEST-OTHER",
                "contact_email": "other@example.test",
            },
        )
        client.credentials(
            HTTP_X_SUKOON_COMPANY_ID=str(other.id), HTTP_X_SUKOON_COMPANY_ROLE="admin"
        )
    session = change.rental_change.signing_sessions.get(signer=actor)
    assert_blocked_without_completion(client, actor, item, change, session)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "revocation",
    ["membership", "mandate", "execution", "epoch", "frozen", "unverified"],
)
def test_new_mock_completion_rechecks_signer_authority(
    pending_continuation, revocation
):
    actors, item, change = pending_continuation
    actor = actors["signer"]
    session = change.rental_change.signing_sessions.get(signer=actor)
    mandate = item.signer_mandate
    if revocation == "membership":
        member = mandate.membership
        member.is_active = False
        member.save(update_fields=["is_active"])
    elif revocation == "mandate":
        mandate.state = "revoked"
        mandate.save(update_fields=["state"])
    elif revocation == "execution":
        mandate.execution_verified_until = timezone.now() - timedelta(minutes=1)
        mandate.save(update_fields=["execution_verified_until"])
    else:
        field, value = {
            "epoch": ("security_epoch", actor.security_epoch + 1),
            "frozen": ("sensitive_actions_frozen", True),
            "unverified": ("is_verified", False),
        }[revocation]
        setattr(actor, field, value)
        actor.save(update_fields=[field])
    assert_blocked_without_completion(
        authenticated(actor), actor, item, change, session
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "invalid",
    [
        "missing-own",
        "completed",
        "expired",
        "unknown",
        "document-id",
        "document-hash",
        "revision",
        "event-state",
        "review-state",
        "unlinked",
    ],
)
def test_completion_requires_the_existing_current_own_pending_session(
    pending_continuation, invalid
):
    actors, item, change = pending_continuation
    actor = actors["owner"]
    event = change.rental_change
    session = event.signing_sessions.get(signer=actor)
    if invalid == "missing-own":
        # The other signatory's session cannot supply this actor's capability.
        event.signing_sessions.filter(pk=session.pk).delete()
    elif invalid in {"completed", "unknown"}:
        session.status = invalid
        session.save(update_fields=["status"])
    elif invalid == "expired":
        session.expires_at = timezone.now() - timedelta(minutes=1)
        session.save(update_fields=["expires_at"])
    elif invalid in {"document-id", "document-hash", "revision"}:
        field, value = {
            "document-id": ("document_id", uuid.uuid4()),
            "document-hash": ("document_hash", "f" * 64),
            "revision": ("change_revision", event.revision - 1),
        }[invalid]
        setattr(session, field, value)
        session.save(update_fields=[field])
    elif invalid == "event-state":
        event.status = "accepted"
        event.save(update_fields=["status"])
    elif invalid == "review-state":
        change.state = "review_required"
        change.save(update_fields=["state"])
    else:
        change.rental_change = None
        change.save(update_fields=["rental_change"])
        # Retain the canonical event for the negative assertion helper.
        change.rental_change = event
    client = authenticated(actor)
    language = "ar" if invalid == "expired" else "en" if invalid == "unknown" else None
    if language:
        client.credentials(HTTP_ACCEPT_LANGUAGE=language)
    assert_blocked_without_completion(
        client, actor, item, change, session, language=language
    )


@pytest.mark.django_db
def test_authoritative_late_signature_is_retained_after_mock_eligibility_is_lost(
    pending_continuation,
):
    actors, item, change = pending_continuation
    actor = actors["signer"]
    event = change.rental_change
    session = event.signing_sessions.get(signer=actor)
    original_end = item.lease.end_date
    session.expires_at = timezone.now() - timedelta(minutes=1)
    session.save(update_fields=["expires_at"])
    mandate = item.signer_mandate
    mandate.state = "revoked"
    mandate.save(update_fields=["state"])
    assert_blocked_without_completion(
        authenticated(actor), actor, item, change, session
    )
    # This is the existing authoritative provider callback, not a new HTTP intent.
    complete_change_signature(session.provider_session_id)
    session.refresh_from_db()
    event.refresh_from_db()
    change.refresh_from_db()
    item.lease.refresh_from_db()
    assert session.status == "completed" and str(actor.id) in event.signed_by
    assert change.state == "review_required"
    assert (
        item.lease.end_date == original_end and item.lease.billing_periods.count() == 1
    )
