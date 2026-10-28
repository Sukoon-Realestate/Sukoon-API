"""Initial agreement recovery over real HTTP/SQL; signatures are synthetic.

The isolated fake adapter establishes test-only provider facts. Review, expiry,
operator notes and reconcile never stand in for an authenticated signature.
"""

from copy import deepcopy
from datetime import timedelta
import uuid
import pytest
from django.db import transaction
from django.utils import timezone
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
    act,
    expose_unexpected_exceptions,
    reviews,
    signatures,
)
from core_apps.features.models import (
    CompanyBudgetReservation,
    DepositAgreement,
    PolicyDecisionHead,
    RentalOperationalCase,
    RentInvoice,
)
from core_apps.features.services import business_policies
from core_apps.features.services.business_policy_catalog import CATALOG
from core_apps.features.services.company import (
    tenancy_initial_recovery as recovery,
    tenancy_projection,
)
from core_apps.features.services.rental_lifecycle.cases import agreement_case_blocker
from core_apps.features.tests.test_cycle_concurrency import parallel_calls
from core_apps.features.rental_phase2_views_parts.apply_fake_rental_event import (
    apply_fake_rental_event,
)
from core_apps.features.rental_phase5_views_parts.change_signing_session import (
    complete_change_signature,
)


def publish_release_policy():
    operator = person("release-policy-" + uuid.uuid4().hex[:12])
    operator.is_staff = operator.is_superuser = True
    operator.save()
    head = PolicyDecisionHead.objects.filter(code="D02").first()
    result = authenticated(operator).post(
        API + "operator/business-policies/",
        {
            "code": "D02",
            "version": "isolated-initial-release-" + uuid.uuid4().hex,
            "expected_head_revision": head.revision if head else 0,
            "rules": deepcopy(CATALOG["D02"]["rules"]),
            "reason": "Synthetic prospective initial release policy publication",
            "evidence_reference": "test_company_initial_recovery; isolated only",
            "request_key": str(uuid.uuid4()),
        },
        format="json",
    )
    assert result.status_code == 201, result.data
    return business_policies.current("D02")


@pytest.fixture
def release_policy():
    return publish_release_policy()


@pytest.fixture
def pending_agreement(agreement):
    cycle, item, _, _ = agreement
    for role in ["owner", "signer"]:
        result = act(item, cycle[role], "review", role=role, digest=item.terms_digest)
        assert result.status_code == 200, result.data
    result = act(item, cycle["owner"], "submit_signature")
    assert result.status_code == 200, result.data
    item.lease.refresh_from_db()
    for role in ["owner", "signer"]:
        result = act(item, cycle[role], "sign", digest=item.lease.document_hash)
        assert result.status_code == 200, result.data
    item.lease.refresh_from_db()
    return cycle, item


def propose(cycle, item, **extra):
    result = act(
        item,
        cycle["owner"],
        "release_agreement",
        digest=item.lease.document_hash,
        reason="Mutual release before any possession or financial instruction",
        **extra,
    )
    assert result.status_code == 200, result.data
    return item.changes.get(kind="agreement_release", state="pending")


def original_event(session):
    with transaction.atomic():
        apply_fake_rental_event(
            {
                "type": "signature.completed",
                "provider_session_id": session.provider_session_id,
            }
        )


def original_sessions(item):
    return list(
        item.lease.signing_sessions.order_by("id").values(
            "id", "provider_session_id", "signer_id", "document_id", "document_hash"
        )
    )


@pytest.mark.django_db
def test_old_d02_remains_visible_but_does_not_authorize_new_scope(monkeypatch):
    with monkeypatch.context() as scoped:
        scoped.setitem(CATALOG["D02"], "scope", ["company.continuation.release"])
        old = publish_release_policy()
    old_snapshot = business_policies.snapshot(old)
    assert business_policies.current("D02").id == old.id
    assert recovery.policy() is None
    new = publish_release_policy()
    assert new.id != old.id and recovery.SCOPE in new.scope
    assert recovery.policy().id == new.id
    old.refresh_from_db()
    assert business_policies.snapshot(old) == old_snapshot
    assert old.scope == ["company.continuation.release"]


@pytest.mark.django_db
def test_initial_release_requires_published_scope(pending_agreement):
    cycle, item = pending_agreement
    assert (
        "release_agreement"
        not in tenancy_projection.payload(item, cycle["owner"])["actions"]
    )
    result = act(
        item,
        cycle["owner"],
        "release_agreement",
        digest=item.lease.document_hash,
        reason="Missing prospective policy",
    )
    assert result.status_code == 409, result.data
    assert not item.changes.exists()
    assert item.lease.inventory_day_locks.exists()


@pytest.mark.django_db
def test_generated_document_without_any_session_can_be_cancelled(agreement):
    cycle, item, _, _ = agreement
    for role in ["owner", "signer"]:
        assert (
            act(
                item, cycle[role], "review", role=role, digest=item.terms_digest
            ).status_code
            == 200
        )
    assert act(item, cycle["owner"], "submit_signature").status_code == 200
    assert "cancel" in tenancy_projection.payload(item, cycle["coordinator"])["actions"]
    result = act(
        item, cycle["coordinator"], "cancel", reason="No provider session was started"
    )
    assert result.status_code == 200, result.data
    item.lease.refresh_from_db()
    assert item.lease.status == "cancelled"
    assert not item.lease.inventory_day_locks.exists()
    assert item.lease.document_id and item.lease.document_hash


@pytest.mark.django_db
@pytest.mark.parametrize(
    "state", ["pending", "completed", "review_required", "unrecognized"]
)
def test_any_original_session_prevents_discarding_pending_agreement(
    pending_agreement, state
):
    cycle, item = pending_agreement
    item.lease.signing_sessions.update(status=state)
    assert "cancel" not in tenancy_projection.payload(item, cycle["owner"])["actions"]
    result = act(
        item,
        cycle["owner"],
        "cancel",
        reason="Do not infer unsigned from unknown status",
    )
    assert result.status_code == 409, result.data
    assert item.lease.inventory_day_locks.exists()


@pytest.mark.django_db
def test_reconcile_only_applies_retained_authenticated_fact(pending_agreement):
    cycle, item = pending_agreement
    first = item.lease.signing_sessions.get(signer=cycle["owner"])
    cycle["company"].review_status = "pending"
    cycle["company"].save(update_fields=["review_status"])
    original_event(first)
    first.refresh_from_db()
    received = first.completed_at
    assert first.status == "review_required" and received
    cycle["company"].review_status = "verified"
    cycle["company"].save(update_fields=["review_status"])
    result = act(item, cycle["coordinator"], "reconcile")
    assert result.status_code == 200, result.data
    first.refresh_from_db()
    assert first.status == "completed" and first.completed_at == received
    untouched = item.lease.signing_sessions.get(signer=cycle["signer"])
    assert untouched.status == "pending" and untouched.completed_at is None
    assert not item.lease.invoices.exists()
    original_event(untouched)
    item.lease.refresh_from_db()
    assert item.lease.status == "signed" and item.lease.invoices.count() == 1


@pytest.mark.django_db
def test_expired_authenticated_fact_is_retained_and_reconcile_cannot_extend_it(
    pending_agreement,
):
    cycle, item = pending_agreement
    first = item.lease.signing_sessions.get(signer=cycle["owner"])
    first.expires_at = timezone.now() - timedelta(seconds=1)
    first.save(update_fields=["expires_at"])
    original_event(first)
    first.refresh_from_db()
    before = (first.completed_at, first.expires_at, first.provider_session_id)
    result = act(item, cycle["coordinator"], "reconcile")
    assert result.status_code == 200, result.data
    first.refresh_from_db()
    assert first.status == "review_required"
    assert (first.completed_at, first.expires_at, first.provider_session_id) == before
    assert not item.lease.invoices.exists()


@pytest.mark.django_db
def test_release_requires_current_named_actors_and_exact_document(
    pending_agreement, release_policy
):
    cycle, item = pending_agreement
    for role in ["payer", "employee", "coordinator"]:
        result = act(
            item,
            cycle[role],
            "release_agreement",
            digest=item.lease.document_hash,
            reason="Wrong responsibility",
        )
        assert result.status_code == 403, (role, result.data)
        assert (
            "release_agreement"
            not in tenancy_projection.payload(item, cycle[role])["actions"]
        )
    result = act(
        item,
        cycle["owner"],
        "release_agreement",
        digest="a" * 64,
        reason="Wrong document",
    )
    assert result.status_code == 409, result.data
    change = propose(cycle, item)
    assert set(change.snapshot["required"]) == {"owner", "signer", "payer"}
    assert change.snapshot["content"]["policy"]["id"] == str(release_policy.id)
    assert "sign" not in tenancy_projection.payload(item, cycle["owner"])["actions"]
    result = act(item, cycle["owner"], "sign", digest=item.lease.document_hash)
    assert result.status_code == 409, result.data
    wrong = act(
        item,
        cycle["coordinator"],
        "respond_change",
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="signer",
        decision="accept",
    )
    assert wrong.status_code == 404, wrong.data  # The forged role has no resource.
    employee = tenancy_projection.payload(item, cycle["employee"])
    assert employee["changes"] == []


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["decline", "withdraw"])
def test_release_nonacceptance_preserves_original_obligations(
    pending_agreement, release_policy, action
):
    cycle, item = pending_agreement
    held = set(item.lease.inventory_day_locks.values_list("pk", flat=True))
    original = original_sessions(item)
    change = propose(cycle, item)
    result = (
        act(
            item,
            cycle["payer"],
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="payer",
            decision="decline",
            reason="Do not accept",
        )
        if action == "decline"
        else act(
            item,
            cycle["owner"],
            "withdraw_change",
            change_id=str(change.id),
            reason="Withdraw only the new proposal",
        )
    )
    assert result.status_code == 200, result.data
    change.refresh_from_db()
    assert change.state == ("declined" if action == "decline" else "withdrawn")
    assert original_sessions(item) == original
    assert set(item.lease.inventory_day_locks.values_list("pk", flat=True)) == held
    assert item.lease.status == "pending_signatures"
    assert (
        "release_agreement"
        in tenancy_projection.payload(item, cycle["owner"])["actions"]
    )


@pytest.mark.django_db
def test_reviews_without_provider_do_not_cancel_or_release(
    pending_agreement, release_policy, settings
):
    cycle, item = pending_agreement
    change = propose(cycle, item)
    reviews(item, change)
    assert change.state == "accepted"
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    result = act(
        item,
        cycle["owner"],
        "submit_continuation",
        change_id=str(change.id),
        digest=change.snapshot_digest,
    )
    assert result.status_code == 409, result.data
    assert item.lease.status == "pending_signatures"
    assert item.lease.inventory_day_locks.exists()
    assert not change.rental_change.signing_sessions.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("late_after_release", [False, True])
def test_mutual_signed_initial_release_retains_exact_late_provider_facts(
    pending_agreement, release_policy, late_after_release
):
    cycle, item = pending_agreement
    original = original_sessions(item)
    original_terms = deepcopy(item.lease.terms)
    original_document = (item.lease.document_id, item.lease.document_hash)
    first = item.lease.signing_sessions.get(signer=cycle["owner"])
    first.expires_at = timezone.now() - timedelta(seconds=1)
    first.save(update_fields=["expires_at"])
    original_event(first)
    case = RentalOperationalCase.objects.get(source_key=f"company-signature:{first.id}")
    assert agreement_case_blocker(case)
    change = propose(cycle, item)
    late = item.lease.signing_sessions.get(signer=cycle["signer"])
    if not late_after_release:
        original_event(late)
    reviews(item, change)
    assert change.state == "accepted" and item.lease.inventory_day_locks.exists()
    signatures(item, change)
    assert change.state == "applied"
    if late_after_release:
        original_event(late)
    late.refresh_from_db()
    received = late.completed_at
    original_event(late)
    late.refresh_from_db()
    item.lease.refresh_from_db()
    case.refresh_from_db()
    assert (
        received and late.completed_at == received and late.status == "review_required"
    )
    assert original_sessions(item) == original
    assert (item.lease.document_id, item.lease.document_hash) == original_document
    assert item.lease.terms == original_terms
    assert (
        item.lease.status == "cancelled"
        and item.lease.financial_closure_status == "closed"
    )
    assert not item.lease.inventory_day_locks.exists()
    assert (
        not item.lease.invoices.exists() and not item.lease.ledger_transactions.exists()
    )
    assert (
        not item.lease.owner_payables.exists()
        and not item.lease.refund_requests.exists()
    )
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).status
        == "released"
    )
    assert not item.preparation.booking.assignments.exclude(
        occupancy_status="cancelled"
    ).exists()
    assert agreement_case_blocker(case) is None


def add_financial_or_possession(item, kind):
    if kind == "invoice":
        from core_apps.features.services.rental_phase3 import generate_billing_schedule

        generate_billing_schedule(item.lease)
        assert RentInvoice.objects.filter(lease=item.lease).exists()
    elif kind == "deposit":
        DepositAgreement.objects.create(lease=item.lease, collected_minor=10)
    else:
        item.lease.occupancy_status = "occupied"
        item.lease.save(update_fields=["occupancy_status"])


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["invoice", "deposit", "occupancy"])
def test_financial_or_possession_boundary_checked_at_proposal(
    pending_agreement, release_policy, kind
):
    cycle, item = pending_agreement
    add_financial_or_possession(item, kind)
    result = act(
        item,
        cycle["owner"],
        "release_agreement",
        digest=item.lease.document_hash,
        reason="Outside pre-financial scope",
    )
    assert result.status_code == 409, result.data
    assert not item.changes.exists() and item.lease.inventory_day_locks.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ["invoice", "deposit", "occupancy"])
def test_race_before_final_signature_retains_fact_without_release(
    pending_agreement, release_policy, kind
):
    cycle, item = pending_agreement
    change = propose(cycle, item)
    reviews(item, change)
    result = act(
        item,
        cycle["owner"],
        "submit_continuation",
        change_id=str(change.id),
        digest=change.snapshot_digest,
    )
    assert result.status_code == 200, result.data
    for role in ["owner", "signer"]:
        result = act(
            item,
            cycle[role],
            "sign_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
        )
        assert result.status_code == 200, result.data
    first = change.rental_change.signing_sessions.get(signer=cycle["owner"])
    complete_change_signature(first.provider_session_id)
    add_financial_or_possession(item, kind)
    last = change.rental_change.signing_sessions.get(signer=cycle["signer"])
    complete_change_signature(last.provider_session_id)
    change.refresh_from_db()
    last.refresh_from_db()
    item.lease.refresh_from_db()
    assert last.status == "completed" and last.completed_at
    assert change.state == "review_required" and change.applied_at is None
    assert (
        item.lease.status == "pending_signatures"
        and item.lease.inventory_day_locks.exists()
    )
    case = RentalOperationalCase.objects.get(
        source_key=f"company-continuation:{change.id}"
    )
    assert agreement_case_blocker(case)


@pytest.mark.django_db
def test_release_session_prevents_unilateral_withdrawal(
    pending_agreement, release_policy
):
    cycle, item = pending_agreement
    change = propose(cycle, item)
    reviews(item, change)
    assert (
        act(
            item,
            cycle["owner"],
            "submit_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
        ).status_code
        == 200
    )
    assert (
        act(
            item,
            cycle["owner"],
            "sign_continuation",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="owner",
        ).status_code
        == 200
    )
    result = act(
        item,
        cycle["owner"],
        "withdraw_change",
        change_id=str(change.id),
        reason="Unknown release signature",
    )
    assert result.status_code == 409, result.data
    assert item.lease.inventory_day_locks.exists()


@pytest.mark.django_db
def test_original_identity_change_invalidates_final_review(
    pending_agreement, release_policy
):
    cycle, item = pending_agreement
    change = propose(cycle, item)
    for role in ["owner", "signer"]:
        result = act(
            item,
            cycle[role],
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
        assert result.status_code == 200, result.data
    session = item.lease.signing_sessions.get(signer=cycle["owner"])
    session.provider_session_id = "different-source-session"
    session.save(update_fields=["provider_session_id"])
    result = act(
        item,
        cycle["payer"],
        "respond_change",
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="payer",
        decision="accept",
    )
    assert result.status_code == 409, result.data
    change.refresh_from_db()
    assert change.state == "pending" and "payer" not in change.decisions


@pytest.mark.django_db
def test_mandate_revision_change_cannot_reuse_release_reviews(
    pending_agreement, release_policy
):
    cycle, item = pending_agreement
    change = propose(cycle, item)
    reviews(item, change)
    mandate = item.signer_mandate
    mandate.revision += 1
    mandate.save(update_fields=["revision"])
    result = act(
        item,
        cycle["owner"],
        "submit_continuation",
        change_id=str(change.id),
        digest=change.snapshot_digest,
    )
    assert result.status_code == 409, result.data
    assert not change.rental_change.signing_sessions.exists()
    result = act(
        item,
        cycle["owner"],
        "withdraw_change",
        change_id=str(change.id),
        reason="Fresh authority requires fresh consent",
    )
    assert result.status_code == 200, result.data
    replacement = propose(cycle, item)
    assert (
        replacement.snapshot["content"]["release_authority"]["signer"]["revision"]
        == mandate.revision
    )
    assert replacement.decisions == {}


@pytest.mark.django_db
def test_release_replay_preserves_original_receipt_and_single_proposal(
    pending_agreement, release_policy
):
    cycle, item = pending_agreement
    data = command(
        expected_revision=item.lease.revision,
        digest=item.lease.document_hash,
        reason="One logical release proposal",
    )
    path = API + f"company-tenancies/{item.id}/release_agreement/"
    first = authenticated(cycle["owner"]).post(path, data, format="json")
    second = authenticated(cycle["owner"]).post(path, data, format="json")
    assert first.status_code == second.status_code == 200, (first.data, second.data)
    assert first.data == second.data
    assert item.changes.filter(kind="agreement_release").count() == 1


@pytest.mark.django_db(transaction=True)
def test_original_completion_and_release_proposal_serialize(
    pending_agreement, release_policy
):
    cycle, item = pending_agreement
    original_event(item.lease.signing_sessions.get(signer=cycle["owner"]))
    item.lease.refresh_from_db()
    pending = item.lease.signing_sessions.get(signer=cycle["signer"])
    data = command(
        expected_revision=item.lease.revision,
        digest=item.lease.document_hash,
        reason="Race with authentic original completion",
    )
    path = API + f"company-tenancies/{item.id}/release_agreement/"

    def execute(index):
        if index:
            original_event(pending)
            return None
        return authenticated(cycle["owner"]).post(path, data, format="json")

    results = parallel_calls(execute)
    response = results[0]
    item.lease.refresh_from_db()
    pending.refresh_from_db()
    if response.status_code == 200:
        assert item.lease.status == "pending_signatures"
        assert pending.status == "review_required" and pending.completed_at
        assert (
            item.changes.filter(kind="agreement_release", state="pending").count() == 1
        )
        assert not item.lease.invoices.exists()
    else:
        assert response.status_code == 409, response.data
        assert item.lease.status == "signed"
        assert item.lease.invoices.count() == 1
        assert not item.changes.filter(kind="agreement_release").exists()
    assert item.lease.inventory_day_locks.exists()
