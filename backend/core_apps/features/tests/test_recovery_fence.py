import json
import uuid
from pathlib import Path
import pytest
from django.test import override_settings
from core_apps.common.recovery import (
    dispatch,
    require_scope,
    RecoveryRequired,
    reconcile_instruction,
    journal,
)
from core_apps.features.models import RentalProviderInstruction
from core_apps.users.services.sessions import issue_refresh, validate_session
from rest_framework_simplejwt.exceptions import AuthenticationFailed

pytestmark = pytest.mark.django_db


@pytest.fixture
def recovery(settings, tmp_path):
    settings.DEBUG = True
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_ENVIRONMENT = "isolated-restore-drill"
    settings.RECOVERY_CONTROL_FILE = str(tmp_path / "independent-control.json")
    settings.RECOVERY_LOCAL_JOURNAL = str(tmp_path / "independent-journal.jsonl")
    settings.RECOVERY_JOURNAL_ADAPTER = "local_drill"
    state = {
        "environment": settings.RECOVERY_ENVIRONMENT,
        "generation": "g1",
        "security_epoch": "s1",
        "mode": "open",
        "scopes": ["provider_outbound", "inventory_commitments"],
        "approval_reference": "synthetic-fixture-only",
        "coverage_reference": "synthetic-fixture-only",
    }
    path = Path(settings.RECOVERY_CONTROL_FILE)
    path.write_text(json.dumps(state))
    return path, state


def instruction():
    return RentalProviderInstruction.objects.create(
        reference="synthetic:" + str(uuid.uuid4()),
        kind="payout",
        provider="synthetic",
        subject_id=uuid.uuid4(),
        subject_revision=1,
        request_fingerprint="a" * 64,
    )


def test_default_outbound_is_closed(settings):
    settings.RECOVERY_TEST_BYPASS = False
    settings.RECOVERY_CONTROL_FILE = ""
    with pytest.raises(RecoveryRequired):
        require_scope("provider_outbound")


def test_prepared_unknown_never_resends(recovery):
    item = instruction()
    calls = []

    def transport():
        calls.append(1)
        raise TimeoutError("synthetic outcome unknown")

    with pytest.raises(TimeoutError):
        dispatch(
            item,
            {"account": "synthetic", "amount_minor": 700, "currency": "EGP"},
            transport,
        )
    with pytest.raises(RecoveryRequired):
        dispatch(item, {"account": "synthetic"}, transport)
    assert len(calls) == 1
    assert reconcile_instruction(item)["status"] == "unknown"


def test_journal_failure_prevents_transport(recovery, monkeypatch):
    item = instruction()
    calls = []
    from core_apps.common.recovery import LocalDrillJournal

    monkeypatch.setattr(
        LocalDrillJournal,
        "append",
        lambda *args: (_ for _ in ()).throw(OSError("synthetic disk error")),
    )
    with pytest.raises(OSError):
        dispatch(item, {}, lambda: calls.append(1))
    assert calls == []


def test_stale_worker_persists_external_fact_but_cannot_apply_local_success(recovery):
    path, state = recovery
    item = instruction()

    def transport():
        path.write_text(
            json.dumps({**state, "generation": "g2", "mode": "reconciling"})
        )
        return "synthetic-external-001"

    with pytest.raises(RecoveryRequired):
        dispatch(item, {"account": "synthetic"}, transport)
    item.refresh_from_db()
    assert item.status == "pending"
    assert reconcile_instruction(item)["domain_reconciliation_required"] is True
    assert reconcile_instruction(item)["domain_reconciliation_required"] is True
    item.refresh_from_db()
    assert item.provider_reference == "synthetic-external-001"


def test_deferred_global_epoch_does_not_replace_account_session_authority(
    recovery, user
):
    path, state = recovery
    token = issue_refresh(user)
    path.write_text(
        json.dumps({**state, "security_epoch": "s2", "mode": "quarantined"})
    )
    validate_session(user, token)
    user.security_epoch += 1
    user.save(update_fields=["security_epoch"])
    with pytest.raises(AuthenticationFailed):
        validate_session(user, token)


def test_journal_corruption_fails_closed(recovery):
    item = instruction()
    dispatch(item, {"account": "synthetic"}, lambda: "synthetic-receipt")
    store = journal()
    store.path.write_text(
        store.path.read_text().replace("synthetic-receipt", "edited-receipt")
    )
    with pytest.raises(RecoveryRequired):
        reconcile_instruction(item)


def test_account_epoch_invalidates_links_and_otp_without_global_recovery(
    recovery, user
):
    from core_apps.users.services.recovery_tokens import recovery_token_generator
    from core_apps.users.services.otp_service import (
        create_and_send_otp,
        verify_email_otp,
    )
    from rest_framework.exceptions import ValidationError

    path, state = recovery
    link = recovery_token_generator.make_token(user)
    code = create_and_send_otp(user)
    path.write_text(
        json.dumps({**state, "security_epoch": "s2", "mode": "quarantined"})
    )
    assert recovery_token_generator.check_token(user, link)
    user.security_epoch += 1
    user.save(update_fields=["security_epoch"])
    assert not recovery_token_generator.check_token(user, link)
    with pytest.raises(ValidationError):
        verify_email_otp(user.email, code)


def test_orphan_callback_is_rejected_by_domain_without_recovery_dependency(
    recovery, user
):
    from core_apps.features.providers import sign_fake_webhook
    from core_apps.features.models import ProviderWebhookEvent
    from rest_framework.test import APIClient

    path, state = recovery
    path.write_text(json.dumps({**state, "mode": "quarantined"}))
    body = {
        "id": "synthetic-quarantine-callback",
        "type": "payment.settled",
        "payment_attempt_id": str(uuid.uuid4()),
        "sequence": 1,
        "amount_minor": 700,
        "currency": "EGP",
    }
    response = APIClient().post(
        "/api/v1/features/v1/provider-webhooks/payments/",
        body,
        format="json",
        HTTP_X_RENTAL_SIGNATURE=sign_fake_webhook(body),
    )
    assert response.status_code == 404
    assert not ProviderWebhookEvent.objects.exists()
