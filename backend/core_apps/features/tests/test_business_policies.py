"""Real HTTP publication, immutable snapshots and independent policy authority."""

import uuid
from copy import deepcopy
from datetime import timedelta
import pytest
from django.core.exceptions import ValidationError as ModelValidationError
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from core_apps.features.models import (
    PolicyDecision,
    PolicyDecisionHead,
    RentalOperationalCase,
)
from core_apps.features.services import business_policies as policies
from core_apps.features.services.business_policy_catalog import CATALOG
from core_apps.features.services.rental_lifecycle.cases import (
    open_system_case,
    case_payload,
)
from core_apps.features.services.rental_lifecycle.case_commands import act_on_case
from core_apps.features.services.company.request_period import validate_request_period
from core_apps.features.services.rental_phase2 import RentalConflict, add_months

pytestmark = pytest.mark.django_db
API = "/api/v1/features/v1/"


@pytest.fixture
def policy_admin(user):
    user.is_verified = user.is_staff = user.is_superuser = True
    user.save()
    return user


def body(code="D01", revision=0, **rules):
    return {
        "code": code,
        "version": "test-" + uuid.uuid4().hex,
        "expected_head_revision": revision,
        "rules": {**deepcopy(CATALOG[code]["rules"]), **rules},
        "reason": "Synthetic local policy verification",
        "evidence_reference": "isolated-test-only",
        "request_key": str(uuid.uuid4()),
    }


def client(user=None):
    result = APIClient()
    if user:
        result.force_authenticate(user)
    return result


def test_public_endpoint_has_no_unpublished_defaults_or_approval_identity(policy_admin):
    anonymous = client()
    assert anonymous.get(API + "business-policies/").json()["data"]["items"] == []
    data = body()
    response = client(policy_admin).post(
        API + "operator/business-policies/", data, format="json"
    )
    assert response.status_code == 201, response.data
    result = anonymous.get(
        API + "business-policies/", HTTP_ACCEPT_LANGUAGE="en"
    ).json()["data"]["items"][0]
    assert result["version"] == data["version"]
    assert result["values"][0]["value"] == "72"
    assert (
        not {"approver", "evidence_reference", "audit_reason", "owner"} & result.keys()
    )
    localized = anonymous.get(
        API + "business-policies/", HTTP_ACCEPT_LANGUAGE="ar"
    ).json()["data"]["items"][0]
    assert localized["title"] != result["title"]


def test_membership_or_staff_without_policy_authority_cannot_publish(user):
    data = body()
    assert (
        client()
        .post(API + "operator/business-policies/", data, format="json")
        .status_code
        == 401
    )
    assert (
        client(user)
        .post(API + "operator/business-policies/", data, format="json")
        .status_code
        == 403
    )
    user.is_staff = True
    user.save()
    assert (
        client(user)
        .post(API + "operator/business-policies/", data, format="json")
        .status_code
        == 403
    )
    assert not PolicyDecision.objects.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_hours", True),
        ("case_hours", 0),
        ("case_hours", 169),
        ("urgent_case_hours", 73),
    ],
)
def test_invalid_values_do_not_publish(policy_admin, field, value):
    response = client(policy_admin).post(
        API + "operator/business-policies/", body(**{field: value}), format="json"
    )
    assert response.status_code == 400
    assert not PolicyDecision.objects.exists()


@pytest.mark.parametrize(
    "change",
    [
        {"effective_at": "2000-01-01T00:00:00Z"},
        {"code": ["D01"]},
        {"code": "D31"},
        {
            "rules": {
                "case_hours": 72,
                "urgent_case_hours": 24,
                "silence_means_consent": True,
            }
        },
    ],
)
def test_unknown_rules_backdating_and_deferred_recovery_are_rejected(
    policy_admin, change
):
    data = {**body(), **change}
    response = client(policy_admin).post(
        API + "operator/business-policies/", data, format="json"
    )
    assert response.status_code == 400, response.data


def test_replay_stale_head_and_published_record_immutability(policy_admin):
    data = body()
    first = policies.publish(policy_admin, data)
    assert policies.publish(policy_admin, data) == first
    with pytest.raises(RentalConflict):
        policies.publish(policy_admin, body(case_hours=96))
    assert PolicyDecision.objects.count() == 1
    old = policies.current("D01")
    original = policies.snapshot(old)
    policies.publish(policy_admin, body(revision=1, case_hours=96))
    old.refresh_from_db()
    assert policies.snapshot(old) == original
    old.rules["case_hours"] = 100
    with pytest.raises(ModelValidationError):
        old.save()
    assert (
        client()
        .get(API + f"business-policies/D01/versions/{data['version']}/")
        .status_code
        == 200
    )


def test_revoked_or_frozen_admin_cannot_replay_publication(policy_admin):
    data = body()
    policies.publish(policy_admin, data)
    policy_admin.sensitive_actions_frozen = True
    policy_admin.save()
    with pytest.raises(PermissionDenied):
        policies.publish(policy_admin, data)


def test_case_deadlines_use_new_versions_without_rewriting_existing_cases(policy_admin):
    policies.publish(policy_admin, body(case_hours=48))
    first = open_system_case(
        kind="maintenance",
        source_key="policy-first",
        actor=policy_admin,
        reason="Synthetic",
        next_action="Review",
    )
    original_due, original_policy = first.due_at, deepcopy(first.baseline)
    policies.publish(policy_admin, body(revision=1, case_hours=96))
    second = open_system_case(
        kind="maintenance",
        source_key="policy-second",
        actor=policy_admin,
        reason="Synthetic",
        next_action="Review",
    )
    first.refresh_from_db()
    assert (first.due_at, first.baseline) == (original_due, original_policy)
    assert second.baseline["response_target"]["case_hours"] == 96
    assert second.due_at - timezone.now() > timedelta(hours=95)


def test_review_request_is_discoverable_bounded_and_preserves_canonical_effects(
    policy_admin, django_user_model
):
    policies.publish(policy_admin, body("D25", reassessment_hours=48))
    actor = django_user_model.objects.create_user(
        email="case-policy@example.test", password="Synthetic-only", is_verified=True
    )
    case = open_system_case(
        kind="maintenance",
        source_key="policy-review",
        actor=actor,
        reason="Synthetic",
        next_action="Review",
    )
    assert "request_review" not in case_payload(case, actor)["allowed_actions"]
    RentalOperationalCase.objects.filter(pk=case.pk).update(
        due_at=timezone.now() - timedelta(seconds=1)
    )
    case.refresh_from_db()
    assert "request_review" in case_payload(case, actor)["allowed_actions"]
    data = {
        "request_key": str(uuid.uuid4()),
        "expected_revision": case.revision,
        "action": "request_review",
        "reason": "No response",
    }
    result = act_on_case(actor, case.id, data)
    assert act_on_case(actor, case.id, data) == result
    case.refresh_from_db()
    assert case.status == "under_review" and case.baseline["review_pending"]
    assert "request_review" not in case_payload(case, actor)["allowed_actions"]
    assert case.refund_id is None and case.payout_id is None
    with pytest.raises(RentalConflict):
        act_on_case(
            actor,
            case.id,
            {
                **data,
                "request_key": str(uuid.uuid4()),
                "expected_revision": case.revision,
            },
        )


def test_new_period_limit_has_a_real_consumer_and_bound_terms_stay_original(
    policy_admin,
):
    policies.publish(policy_admin, body("D05", maximum_months=12))
    original = policies.freeze(["D05"])
    starts = timezone.localdate() + timedelta(days=10)
    validate_request_period(
        {"starts_on": starts, "ends_on_exclusive": add_months(starts, 12)}
    )
    from rest_framework.exceptions import ValidationError

    with pytest.raises(ValidationError):
        validate_request_period(
            {"starts_on": starts, "ends_on_exclusive": add_months(starts, 13)}
        )
    policies.publish(policy_admin, body("D05", revision=1, maximum_months=6))
    assert (
        policies.bound({"business_policies": original}, "D05")["rules"][
            "maximum_months"
        ]
        == 12
    )
    assert policies.bound({}, "D05") is None


@pytest.mark.django_db(transaction=True)
def test_independent_administrators_cannot_overwrite_the_same_reviewed_head(
    policy_admin, django_user_model
):
    from core_apps.features.tests.test_cycle_concurrency import parallel_calls
    from django.db import close_old_connections

    second = django_user_model.objects.create_user(
        email="policy-second@example.test",
        password="Synthetic-only",
        is_staff=True,
        is_superuser=True,
    )

    def invoke(identity):
        close_old_connections()
        actor = django_user_model.objects.get(pk=identity)
        try:
            policies.publish(actor, body())
            return "published"
        except RentalConflict:
            return "stale"
        finally:
            close_old_connections()

    results = parallel_calls(lambda index: invoke([policy_admin.pk, second.pk][index]))
    assert sorted(results) == ["published", "stale"]
    assert PolicyDecisionHead.objects.get(code="D01").revision == 1
    assert PolicyDecision.objects.filter(code="D01").count() == 1


def test_admin_page_uses_reviewed_head_and_preserves_form_on_conflict(
    policy_admin, client, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    client.force_login(policy_admin)
    path = "/admin/features/policydecision/publish/"
    response = client.get(path)
    assert response.status_code == 200
    assert b"Publish a prospective business policy" in response.content
    data = body()
    import json

    submitted = {**data, "rules": json.dumps(data["rules"])}
    assert client.post(path, submitted).status_code == 302
    conflict = client.post(
        path, {**submitted, "request_key": str(uuid.uuid4()), "version": "second"}
    )
    assert conflict.status_code == 200
    assert b"Another policy version" in conflict.content
    assert PolicyDecision.objects.filter(code="D01").count() == 1


def test_all_supported_families_publish_and_disclose_without_external_dependencies(
    policy_admin, settings
):
    settings.RECOVERY_CONTROL_FILE = ""
    for code in CATALOG:
        policies.publish(policy_admin, body(code=code))
    response = APIClient().get(API + "business-policies/")
    assert response.status_code == 200
    assert {item["code"] for item in response.json()["data"]["items"]} == set(CATALOG)


def test_private_legacy_policy_is_not_exposed_as_public_history(policy_admin):
    policies.publish(policy_admin, body())
    item = policies.current("D01")
    # Represent an older internal approval, without changing the immutable public record.
    PolicyDecision.objects.filter(pk=item.pk).update(
        presentation={}, disclosure="Private operator evidence"
    )
    client = APIClient()
    assert client.get(API + "business-policies/").json()["data"]["items"] == []
    assert (
        client.get(API + f"business-policies/D01/versions/{item.version}/").status_code
        == 404
    )


def test_policy_pack_command_is_dry_by_default_and_idempotent(policy_admin):
    from io import StringIO
    from django.core.management import call_command

    output = StringIO()
    options = {
        "actor_id": str(policy_admin.id),
        "evidence_reference": "Synthetic reviewed instruction",
        "stdout": output,
    }
    call_command("publish_business_policies", **options)
    assert not PolicyDecision.objects.exists()
    call_command("publish_business_policies", apply=True, **options)
    call_command("publish_business_policies", apply=True, **options)
    assert PolicyDecision.objects.count() == len(CATALOG)


from core_apps.features.tests.test_rental_lifecycle import policy, rental_participants


def test_published_hold_policy_changes_new_hold_not_existing_extension(
    policy_admin, policy, rental_participants
):
    from core_apps.features.tests.test_rental_lifecycle import (
        proposal_for,
        hold_body,
        confirm,
        post,
        command,
    )
    from core_apps.features.models import ReservationHold
    from core_apps.features.services.rental_lifecycle.common import lifecycle_policy

    _, tenant, _, prop, offer = rental_participants
    policies.publish(policy_admin, body("D17", hold_minutes=20, max_extensions=1))
    confirm(prop)
    result = post(
        tenant, "reservation-holds/", hold_body(proposal_for(tenant, prop, offer))
    )
    assert result.status_code == 201, result.data
    hold = ReservationHold.objects.get(id=result.data["resource"]["id"])
    old_snapshot = deepcopy(hold.policy_snapshot)
    policies.publish(
        policy_admin, body("D17", revision=1, hold_minutes=5, max_extensions=0)
    )
    assert lifecycle_policy()[1]["hold_minutes"] == 5
    response = post(
        tenant, f"reservation-holds/{hold.id}/extend/", command(hold.revision)
    )
    assert response.status_code == 200, response.data
    hold.refresh_from_db()
    assert hold.policy_snapshot == old_snapshot
    assert hold.policy_snapshot["hold_minutes"] == 20


def test_new_request_cannot_outgrow_configured_reservation_window(policy_admin, policy):
    from rest_framework.exceptions import ValidationError

    policies.publish(policy_admin, body("D05"))
    start = timezone.localdate() + timedelta(days=1)
    with pytest.raises(ValidationError, match="reservation period"):
        validate_request_period(
            {"starts_on": start, "ends_on_exclusive": add_months(start, 13)}
        )
    validate_request_period(
        {"starts_on": start, "ends_on_exclusive": add_months(start, 3)}
    )
