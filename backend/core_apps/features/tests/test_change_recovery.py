"""Agreement-change recovery must survive its own completed state transition."""

import json
import os
from pathlib import Path

import pytest
from django.db import connection
from django.utils import timezone

from core_apps.features.models import ChangeSigningSession, RentalChange
from core_apps.features.models import SigningSession
from .test_funded_settlement import command
from .test_rental_phase5 import client_for, phase5_lease
from .test_cycle_concurrency import parallel_calls
from .test_current_cycle_contract import awaiting_signatures
from .test_rental_phase2 import rental_participants

API = "/api/v1/features/v1/"


def pending_change(phase5_lease, kind="amendments"):
    owner, tenant, lease = phase5_lease
    created = client_for(owner).post(
        API + f"leases/{lease.id}/{kind}/",
        command(
            reason="Explicitly accepted change",
            effective_on=str(timezone.localdate()),
            terms=lease.terms,
            evidence_ids=[],
            lease_revision=lease.revision,
        ),
        format="json",
    )
    assert created.status_code == 201, created.data
    change = created.data["resource"]
    accepted = client_for(tenant).post(
        API + f"{kind}/{change['id']}/respond/",
        command(
            change["revision"],
            action="accept",
        ),
        format="json",
    )
    assert accepted.status_code == 200, accepted.data
    change = accepted.data["resource"]
    path = API + f"{kind}/{change['id']}/submit-for-signature/"
    body = command(change["revision"], action="submit_for_signature")
    submitted = client_for(owner).post(path, body, format="json")
    assert submitted.status_code == 200, submitted.data
    return submitted, path, body


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["amendments", "renewals"])
def test_submit_change_replays_after_entering_pending_signatures(phase5_lease, kind):
    submitted, path, body = pending_change(phase5_lease, kind)
    replay = client_for(phase5_lease[0]).post(path, body, format="json")
    assert replay.status_code == 200, replay.data
    assert replay.data == submitted.data
    assert RentalChange.objects.get().revision == submitted.data["resource"]["revision"]


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["amendments", "renewals"])
def test_change_signing_session_replays_after_both_mock_signatures(phase5_lease, kind):
    owner, tenant, _ = phase5_lease
    submitted, _, _ = pending_change(phase5_lease, kind)
    change = submitted.data["resource"]
    sessions = []
    completions = []
    completion_grants = []
    path = API + f"{kind}/{change['id']}/signing-session/"
    for actor in (owner, tenant):
        body = command(
            change["revision"],
            document_id=change["document_id"],
            document_hash=change["document_hash"],
        )
        response = client_for(actor).post(path, body, format="json")
        assert response.status_code == 201, response.data
        sessions.append((actor, body, response))
    for actor, _, response in sessions:
        descriptor = response.data["resource"]["mock_completion"]
        grant = client_for(actor).get(
            API + f"rental-capabilities/?subject_id={change['id']}&action=sign"
        )
        assert grant.status_code == 200 and "sign" in grant.data["allowed_actions"]
        completion_grants.append(grant.json()["data"])
        body = command(descriptor["expected_revision"])
        completed = client_for(actor).post(descriptor["path"], body, format="json")
        assert completed.status_code == 200, completed.data
        assert (
            client_for(actor).post(descriptor["path"], body, format="json").data
            == completed.data
        )
        completions.append(completed.json())
    assert RentalChange.objects.get().status == RentalChange.Status.SIGNED
    for actor, body, response in sessions:
        replay = client_for(actor).post(path, body, format="json")
        assert replay.status_code == 201, replay.data
        assert replay.data == response.data
        recovered = client_for(actor).get(
            API + f"rental-operations/{body['request_key']}/",
            {"subject_id": change["id"]},
        )
        assert recovered.status_code == 200
        assert recovered.data["operation_receipt"] == response.data["operation_receipt"]
    assert ChangeSigningSession.objects.count() == 2
    if output := os.environ.get("SOKOUN_CONTRACT_ARTIFACT_DIR"):
        folder = Path(output)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"django-{kind}-signing-contract.json").write_text(
            json.dumps(
                {
                    "environment": "local-test-fake-provider",
                    "submitted": submitted.json(),
                    "sessions": [response.json() for _, _, response in sessions],
                    "completions": completions,
                    "completion_grants": completion_grants,
                },
                indent=2,
            )
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_key_change_signing_creates_one_session(phase5_lease):
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent signing-session creation requires PostgreSQL row locks")
    submitted, _, _ = pending_change(phase5_lease)
    change = submitted.data["resource"]
    body = command(
        change["revision"],
        document_id=change["document_id"],
        document_hash=change["document_hash"],
    )
    path = API + f"amendments/{change['id']}/signing-session/"
    responses = parallel_calls(
        lambda _: client_for(phase5_lease[0]).post(path, body, format="json")
    )
    assert [response.status_code for response in responses] == [201, 201]
    assert responses[0].data == responses[1].data
    assert ChangeSigningSession.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_key_agreement_signing_creates_one_session(awaiting_signatures):
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent signing-session creation requires PostgreSQL row locks")
    owner, _, _, lease, _ = awaiting_signatures
    body = command(
        lease.revision,
        document_id=str(lease.document_id),
        document_hash=lease.document_hash,
    )
    path = API + f"leases/{lease.id}/signing-session/"
    responses = parallel_calls(
        lambda _: client_for(owner).post(path, body, format="json")
    )
    assert [response.status_code for response in responses] == [201, 201]
    assert responses[0].data == responses[1].data
    assert SigningSession.objects.filter(request_key=body["request_key"]).count() == 1


@pytest.mark.django_db
def test_completed_agreement_signer_replays_but_cannot_start_another_session(
    awaiting_signatures,
):
    owner, _, _, lease, sessions = awaiting_signatures
    session = sessions[0]
    body = {
        **command(
            lease.revision,
            document_id=str(lease.document_id),
            document_hash=lease.document_hash,
        ),
        "request_key": str(session.request_key),
    }
    path = API + f"leases/{lease.id}/signing-session/"
    initial = client_for(owner).post(path, body, format="json")
    descriptor = initial.data["mock_completion"]
    completed = client_for(owner).post(
        descriptor["path"], command(descriptor["expected_revision"]), format="json"
    )
    assert completed.status_code == 200
    assert "sign" not in completed.data["resource"]["allowed_actions"]
    replay = client_for(owner).post(path, body, format="json")
    assert replay.status_code == 201 and replay.data == initial.data
    fresh = client_for(owner).post(
        path, {**body, "request_key": command()["request_key"]}, format="json"
    )
    assert fresh.status_code == 409, fresh.data
    assert SigningSession.objects.filter(lease=lease, signer=owner).count() == 1


@pytest.mark.django_db
def test_completed_change_signer_replays_but_cannot_start_another_session(phase5_lease):
    owner, _, _ = phase5_lease
    submitted, _, _ = pending_change(phase5_lease)
    change = submitted.data["resource"]
    body = command(
        change["revision"],
        document_id=change["document_id"],
        document_hash=change["document_hash"],
    )
    path = API + f"amendments/{change['id']}/signing-session/"
    initial = client_for(owner).post(path, body, format="json")
    descriptor = initial.data["resource"]["mock_completion"]
    completed = client_for(owner).post(
        descriptor["path"], command(descriptor["expected_revision"]), format="json"
    )
    assert completed.status_code == 200
    assert "sign" not in completed.data["resource"]["allowed_actions"]
    replay = client_for(owner).post(path, body, format="json")
    assert replay.status_code == 201 and replay.data == initial.data
    fresh = client_for(owner).post(
        path, {**body, "request_key": command()["request_key"]}, format="json"
    )
    assert fresh.status_code == 409, fresh.data
    assert ChangeSigningSession.objects.count() == 1
