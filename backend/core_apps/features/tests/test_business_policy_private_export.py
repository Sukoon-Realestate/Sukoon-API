"""D26 normal publication uses the existing first-party action-bound consumer.

Isolated DB fixtures and locmem email only; no live policy/mail/export evidence.
"""

import uuid
from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient

from core_apps.common.contract_testing import api_json
from core_apps.features.models import (
    IdempotencyRecord, PolicyDecision, PolicyDecisionHead, RentalAuditEvent, RentalDocument,
)
from core_apps.features.services import business_policies as policies
from core_apps.features.services.business_policy_catalog import CATALOG, SOURCES
from core_apps.features.services.policy_registry import approved_policy
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.users.models import SensitiveAuthorization, SecurityEvent, TotpFactor
from core_apps.users.services import assurance, sensitive_actions, totp
from core_apps.users.services.sessions import issue_refresh
from .test_business_policies import API, body, client, policy_admin
from .test_rental_phase6 import phase6_lease


pytestmark = pytest.mark.django_db
PROVIDER = "core_apps.users.services.assurance.AccountAssuranceProvider"


@pytest.fixture
def first_party(settings):
    settings.DEBUG = False
    settings.SECURITY_TEST_BYPASS = False
    settings.SECURITY_ASSURANCE_PROVIDER = ""  # Exercise the actual first-party fallback.
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


def actor_request(user):
    return SimpleNamespace(user=user, auth=issue_refresh(user).access_token, data={}, headers={})


def action_data(**changes):
    return {
        "action": "private.export", "resource_id": str(uuid.uuid4()), "resource_revision": 3,
        "payload": {"request_key": str(uuid.uuid4()), "starts_on": None, "ends_on_exclusive": None},
        **changes,
    }


def consume(request, data, **changes):
    parameters = {
        "action": data["action"], "resource_id": data["resource_id"],
        "revision": data["resource_revision"], "payload": data["payload"], **changes,
    }
    with transaction.atomic():
        sensitive_actions.consume(request, **parameters)


def test_normal_operator_template_has_only_reviewed_export_contract(policy_admin):
    response = client(policy_admin).get(API + "operator/business-policies/")
    assert response.status_code == 200
    row = next(row for row in api_json(response)["data"]["items"] if row["code"] == "D26")
    assert row["scope"] == ["private.export"] and row["head_revision"] == 0
    assert row["rules"] == {"provider": PROVIDER, "assurance": "email_otp_or_totp", "proof_lifetime_seconds": 300}
    assert row["choices"] == {"provider": [PROVIDER], "assurance": ["email_otp_or_totp"]}
    assert row["bounds"] == {"proof_lifetime_seconds": [1, 300]}
    assert row["source"] == SOURCES["D26"]
    assert not PolicyDecision.objects.exists()  # Reading defaults is not approval.


@pytest.mark.parametrize("field,value", [
    ("provider", "os.system"), ("provider", "builtins.eval"),
    ("provider", "core_apps.users.tests.test_security_recovery.TestAssuranceAdapter"),
    ("provider", PROVIDER + " "), ("provider", None), ("provider", {"path": PROVIDER}),
    ("assurance", "test-strong"), ("assurance", "email_only"), ("assurance", True),
    ("proof_lifetime_seconds", 0), ("proof_lifetime_seconds", -1),
    ("proof_lifetime_seconds", 301), ("proof_lifetime_seconds", True),
    ("proof_lifetime_seconds", "300"), ("proof_lifetime_seconds", 300.0),
])
def test_unsupported_provider_assurance_and_lifetime_never_publish(policy_admin, field, value):
    response = client(policy_admin).post(API + "operator/business-policies/", body("D26", **{field: value}), format="json")
    assert response.status_code == 400
    assert not PolicyDecision.objects.exists() and not PolicyDecisionHead.objects.exists()
    assert not RentalAuditEvent.objects.filter(action="policy.published").exists()


@pytest.mark.parametrize("extra", [
    {"scope": ["refund.execute"]}, {"scope": ["private.export", "payout.execute"]},
    {"action": "account.closure.review"}, {"effective_at": "2000-01-01T00:00:00Z"},
])
def test_client_cannot_expand_scope_or_backdate_publication(policy_admin, extra):
    response = client(policy_admin).post(API + "operator/business-policies/", {**body("D26"), **extra}, format="json")
    assert response.status_code == 400 and not PolicyDecision.objects.exists()


def test_unknown_scope_inside_rules_is_rejected(policy_admin):
    response = client(policy_admin).post(API + "operator/business-policies/", body("D26", scope=["payout.execute"]), format="json")
    assert response.status_code == 400 and not PolicyDecision.objects.exists()


def test_private_export_publication_does_not_enable_any_other_sensitive_action(policy_admin):
    policies.publish(policy_admin, body("D26"))
    for action in sensitive_actions.ACTIONS - {"private.export"}:
        with pytest.raises(RentalConflict):
            approved_policy("D26", action)


def test_publication_keeps_expected_head_receipt_audit_and_immutable_history(policy_admin):
    command = body("D26")
    first = client(policy_admin).post(API + "operator/business-policies/", command, format="json")
    replay = client(policy_admin).post(API + "operator/business-policies/", command, format="json")
    assert first.status_code == replay.status_code == 201
    assert api_json(first)["data"] == api_json(replay)["data"]
    policy = approved_policy("D26", "private.export")
    original = policies.snapshot(policy)
    assert policy.scope == ["private.export"] and policy.rules == command["rules"]
    assert policy.approver == policy_admin
    head = PolicyDecisionHead.objects.get(code="D26")
    assert head.current == policy and head.revision == 1
    assert IdempotencyRecord.objects.filter(operation="business_policy.publish", request_key=command["request_key"]).count() == 1
    audit = RentalAuditEvent.objects.get(subject_id=policy.id, action="policy.published")
    assert audit.actor == policy_admin and audit.metadata["head_revision"] == 1
    assert audit.metadata["digest"] == original["digest"]
    with pytest.raises(RentalConflict):
        policies.publish(policy_admin, {**command, "rules": {**command["rules"], "proof_lifetime_seconds": 120}})
    with pytest.raises(RentalConflict):
        policies.publish(policy_admin, body("D26", proof_lifetime_seconds=120))
    policies.publish(policy_admin, body("D26", revision=1, proof_lifetime_seconds=120))
    policy.refresh_from_db()
    assert policies.snapshot(policy) == original
    assert PolicyDecisionHead.objects.get(code="D26").revision == 2
    public = client().get(API + "business-policies/").json()["data"]["items"][0]
    assert {value["name"] for value in public["values"]} == {"proof_lifetime_seconds"}
    assert PROVIDER not in str(public)
    assert not {"approver", "rules", "audit_reason", "evidence_reference"} & set(public)


@pytest.mark.parametrize("restriction", ["not_staff", "no_policy_permission", "inactive", "frozen"])
def test_current_policy_authority_is_required_for_d26(policy_admin, restriction):
    if restriction == "not_staff":
        policy_admin.is_staff = False
    elif restriction == "no_policy_permission":
        policy_admin.is_superuser = False
    elif restriction == "inactive":
        policy_admin.is_active = False
    else:
        policy_admin.sensitive_actions_frozen = True
    policy_admin.save()
    with pytest.raises(PermissionDenied):
        policies.publish(policy_admin, body("D26"))
    assert not PolicyDecision.objects.exists()


@pytest.mark.parametrize("ttl", [1, 120, 300])
def test_published_contract_is_consumed_by_real_first_party_email_adapter(
    policy_admin, another_user, first_party, monkeypatch, mailoutbox, ttl,
):
    policies.publish(policy_admin, body("D26", proof_lifetime_seconds=ttl))
    another_user.is_email_verified = True
    another_user.save(update_fields=["is_email_verified"])
    request = actor_request(another_user)
    now = timezone.now()
    monkeypatch.setattr(timezone, "now", lambda: now)
    monkeypatch.setattr(assurance, "generate_otp", lambda: "739251")
    data = action_data()
    challenge = sensitive_actions.begin(request, data)
    item = SensitiveAuthorization.objects.get(id=challenge["id"])
    assert item.expires_at == now + timedelta(seconds=ttl)
    assert item.policy_id == approved_policy("D26", "private.export").pk
    assert challenge["verification"]["type"] == "code" and len(mailoutbox) == 1
    cairo_deadline = item.expires_at.astimezone(ZoneInfo("Africa/Cairo"))
    assert cairo_deadline.strftime("%Y-%m-%d %H:%M:%S") in mailoutbox[0].body
    assert "10 minutes" not in mailoutbox[0].body and "10 دقائق" not in mailoutbox[0].body
    assert "five minutes" not in challenge["verification"]["instructions"]
    proof = sensitive_actions.verify(request, item.id, "739251")
    request.headers["X-Sokoun-Authorization"] = proof["proof"]
    consume(request, data)
    with pytest.raises(PermissionDenied):
        consume(request, data)
    item.refresh_from_db()
    assert item.assurance == "email_otp_or_totp" and item.consumed_at == now
    assert SecurityEvent.objects.filter(user=another_user, action="private.export", policy_version=item.policy.version).count() == 1


def test_unverified_email_and_staff_without_totp_are_not_authorized(policy_admin, another_user, first_party, mailoutbox):
    policies.publish(policy_admin, body("D26"))
    with pytest.raises(PermissionDenied):
        sensitive_actions.begin(actor_request(another_user), action_data())
    with pytest.raises(PermissionDenied):
        sensitive_actions.begin(actor_request(policy_admin), action_data())
    assert not SensitiveAuthorization.objects.exists() and len(mailoutbox) == 0


def test_real_staff_totp_matches_published_assurance_without_email(policy_admin, first_party, mailoutbox):
    policies.publish(policy_admin, body("D26"))
    factor = TotpFactor.objects.create(user=policy_admin, secret_ciphertext=totp.seal(totp.new_secret()), confirmed_at=timezone.now())
    request = actor_request(policy_admin)
    data = action_data()
    challenge = sensitive_actions.begin(request, data)
    code = totp.code_at(totp.unseal(factor.secret_ciphertext), int(timezone.now().timestamp()) // 30)
    proof = sensitive_actions.verify(request, challenge["id"], code)
    request.headers["X-Sokoun-Authorization"] = proof["proof"]
    consume(request, data)
    assert len(mailoutbox) == 0
    assert SensitiveAuthorization.objects.get(id=challenge["id"]).factor_revision == factor.revision


def test_new_export_policy_preserves_other_legacy_scopes_and_requires_fresh_export_proof(
    policy_admin, another_user, first_party, monkeypatch,
):
    legacy = PolicyDecision.objects.create(
        code="D26", version="legacy-internal", status="approved", owner="fixture", approver=policy_admin,
        source="isolated historical fixture", evidence_reference="fixture", scope=["private.export", "refund.execute"],
        effective_at=timezone.now() - timedelta(seconds=1), rules=deepcopy(CATALOG["D26"]["rules"]),
        evidence_requirements={"fixture": True}, actions_and_consequences={"fixture": True},
        historical_treatment="Preserve original", audit_reason="Isolated legacy compatibility", disclosure="Fixture",
    )
    original = policies.snapshot(legacy)
    another_user.is_email_verified = True
    another_user.save(update_fields=["is_email_verified"])
    request = actor_request(another_user)
    monkeypatch.setattr(assurance, "generate_otp", lambda: "739251")
    challenge = sensitive_actions.begin(request, action_data())
    policies.publish(policy_admin, body("D26"))
    current = policies.current("D26")
    assert approved_policy("D26", "private.export") == current and current != legacy
    assert approved_policy("D26", "refund.execute") == legacy
    with pytest.raises(RentalConflict):
        approved_policy("D26", "payout.execute")
    with pytest.raises(PermissionDenied):
        sensitive_actions.verify(request, challenge["id"], "739251")
    legacy.refresh_from_db()
    assert policies.snapshot(legacy) == original and legacy.status == "approved"


def test_configured_provider_mismatch_does_not_import_an_arbitrary_path(policy_admin, another_user, first_party, settings, monkeypatch):
    policies.publish(policy_admin, body("D26"))
    settings.SECURITY_ASSURANCE_PROVIDER = "unapproved.module.Provider"
    calls = []
    monkeypatch.setattr(sensitive_actions, "import_string", lambda path: calls.append(path))
    with pytest.raises(RentalConflict):
        sensitive_actions.begin(actor_request(another_user), action_data())
    assert calls == [] and not SensitiveAuthorization.objects.exists()


def test_published_policy_drives_bound_statement_and_original_receipt_replay(
    policy_admin, phase6_lease, first_party, monkeypatch, mailoutbox,
):
    _, tenant, lease = phase6_lease
    tenant.is_email_verified = True
    tenant.save(update_fields=["is_email_verified"])
    policies.publish(policy_admin, body("D26"))
    monkeypatch.setattr(assurance, "generate_otp", lambda: "739251")
    api = APIClient()
    api.force_authenticate(tenant, token=issue_refresh(tenant).access_token)
    command = {"lease_id": str(lease.id), "expected_revision": lease.revision,
               "starts_on": None, "ends_on_exclusive": None, "request_key": str(uuid.uuid4())}
    payload = {"lease_id": str(lease.id), "lease_revision": lease.revision,
               "starts_on": None, "ends_on_exclusive": None, "request_key": command["request_key"]}
    challenge = api.post("/api/v1/auth/security/challenges/", action_data(resource_id=str(lease.id), resource_revision=lease.revision, payload=payload), format="json")
    assert challenge.status_code == 201 and len(mailoutbox) == 1
    challenge_id = api_json(challenge)["data"]["id"]
    verification = api.post(f"/api/v1/auth/security/challenges/{challenge_id}/verify/", {"assertion": "739251"}, format="json")
    assert verification.status_code == 200
    proof = api_json(verification)["data"]["proof"]
    changed = {**command, "starts_on": "2025-02-01"}
    rejected = api.post(API + "rental-statements/", changed, format="json", HTTP_X_SOKOUN_AUTHORIZATION=proof)
    assert rejected.status_code == 403 and not RentalDocument.objects.exists()
    response = api.post(API + "rental-statements/", command, format="json", HTTP_X_SOKOUN_AUTHORIZATION=proof)
    replay = api.post(API + "rental-statements/", command, format="json", HTTP_X_SOKOUN_AUTHORIZATION=proof)
    assert response.status_code == replay.status_code == 201
    assert api_json(response)["data"] == api_json(replay)["data"]
    document = RentalDocument.objects.get(lease=lease, document_type="statement")
    assert document.requested_by == tenant and document.status == "queued"
    assert document.starts_on is None and document.ends_on_exclusive is None
    assert SensitiveAuthorization.objects.get(id=challenge_id).consumed_at is not None
    assert IdempotencyRecord.objects.filter(operation=f"statement.create.{lease.id}", request_key=command["request_key"]).count() == 1
