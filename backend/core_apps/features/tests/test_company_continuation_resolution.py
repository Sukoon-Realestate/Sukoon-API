"""Signed mutual resolution preserves late facts without applying released terms."""

import pytest
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
    signatures,
)
from core_apps.features.models import CompanyBudgetReservation
from core_apps.features.rental_phase5_views_parts.change_signing_session import (
    complete_change_signature,
)
from core_apps.features.tests.test_cycle_concurrency import parallel_calls


def open_sessions(cycle, item):
    change = proposal(cycle, item)
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
    change.refresh_from_db()
    return change


def resolution(cycle, item, original):
    result = act(
        item,
        cycle["owner"],
        "release_continuation",
        change_id=str(original.id),
        digest=original.snapshot_digest,
        reason="Mutually release an unapplied renewal",
    )
    assert result.status_code == 200, result.data
    return item.changes.get(kind="continuation_release")


@pytest.mark.django_db
@pytest.mark.parametrize("late_after_release", [False, True])
def test_mutual_release_preserves_original_signatures_and_existing_obligations(
    active_agreement, late_after_release
):
    cycle, item = active_agreement
    end = item.lease.end_date
    original_locks = set(item.lease.inventory_day_locks.values_list("pk", flat=True))
    invoices = list(item.lease.invoices.values())
    original = open_sessions(cycle, item)
    held = original.inventory_locks.count()
    assert held > 0
    resolved = resolution(cycle, item, original)
    late = original.rental_change.signing_sessions.get(signer=cycle["signer"])
    if not late_after_release:
        complete_change_signature(late.provider_session_id)
    original.refresh_from_db()
    assert (
        original.state == "resolution_pending"
        and original.inventory_locks.count() == held
    )
    reviews(item, resolved)
    assert resolved.state == "accepted" and original.inventory_locks.count() == held
    signatures(item, resolved)
    assert resolved.state == "applied"
    if late_after_release:
        complete_change_signature(late.provider_session_id)
    original.refresh_from_db()
    original.rental_change.refresh_from_db()
    item.lease.refresh_from_db()
    assert original.state == "resolved_unapplied" and original.applied_at is None
    assert original.rental_change.status == "superseded"
    assert len(original.rental_change.signed_by) == 2
    assert (
        original.rental_change.signing_sessions.filter(status="completed").count() == 2
    )
    assert item.lease.end_date == end and item.lease.billing_periods.count() == 1
    assert list(item.lease.invoices.values()) == invoices
    assert (
        set(item.lease.inventory_day_locks.values_list("pk", flat=True))
        == original_locks
    )
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 100000
    )
    complete_change_signature(late.provider_session_id)
    assert (
        CompanyBudgetReservation.objects.get(item=item.preparation.booking).rent_minor
        == 100000
    )
    # A new proposal is allowed only after the separately signed resolution.
    result = act(
        item,
        cycle["owner"],
        "commercial_change",
        kind="renewal",
        effective_on=str(end),
        ends_on_exclusive=str(
            resolved.tenancy.lease.end_date.replace(year=end.year + 1)
        ),
        rent_minor=100000,
        reviewer_membership_id=str(cycle["company"].default_approver.id),
        reason="Fresh future proposal",
    )
    assert result.status_code == 200, result.data


@pytest.mark.django_db
@pytest.mark.parametrize("action", ["decline", "withdraw"])
def test_resolution_nonacceptance_returns_to_reconciliation_without_releasing(
    active_agreement, action
):
    cycle, item = active_agreement
    original = open_sessions(cycle, item)
    held = original.inventory_locks.count()
    result = resolution(cycle, item, original)
    if action == "decline":
        response = act(
            item,
            cycle["signer"],
            "respond_change",
            change_id=str(result.id),
            digest=result.snapshot_digest,
            role="signer",
            decision="decline",
            reason="Do not release",
        )
    else:
        response = act(
            item,
            cycle["owner"],
            "withdraw_change",
            change_id=str(result.id),
            reason="Withdraw resolution proposal",
        )
    assert response.status_code == 200, response.data
    original.refresh_from_db()
    assert (
        original.state == "review_required" and original.inventory_locks.count() == held
    )


@pytest.mark.django_db
def test_resolution_does_not_replace_signatures_when_provider_absent(
    active_agreement, settings
):
    cycle, item = active_agreement
    original = open_sessions(cycle, item)
    result = resolution(cycle, item, original)
    denied = act(
        item,
        cycle["employee"],
        "respond_change",
        change_id=str(result.id),
        digest=result.snapshot_digest,
        role="signer",
        decision="accept",
    )
    assert denied.status_code in {403, 404}
    reviews(item, result)
    settings.RENTAL_PROVIDER_BACKEND = "disabled"
    response = act(
        item,
        cycle["owner"],
        "submit_continuation",
        change_id=str(result.id),
        digest=result.snapshot_digest,
    )
    assert response.status_code in {403, 409}, response.data
    original.refresh_from_db()
    assert original.state == "resolution_pending" and original.inventory_locks.exists()


@pytest.mark.django_db(transaction=True)
def test_last_signature_races_resolution_without_double_application(active_agreement):
    cycle, item = active_agreement
    original = open_sessions(cycle, item)
    late = original.rental_change.signing_sessions.get(signer=cycle["signer"])
    item.lease.refresh_from_db()
    body = command(
        expected_revision=item.lease.revision,
        change_id=str(original.id),
        digest=original.snapshot_digest,
        reason="Concurrent mutual resolution proposal",
    )

    def run(index):
        if index == 0:
            return (
                authenticated(cycle["owner"])
                .post(
                    API + f"company-tenancies/{item.id}/release_continuation/",
                    body,
                    format="json",
                )
                .status_code
            )
        complete_change_signature(late.provider_session_id)
        return 200

    results = parallel_calls(run)
    assert results[1] == 200
    original.refresh_from_db()
    item.lease.refresh_from_db()
    if original.state == "applied":
        assert results[0] == 409 and item.lease.billing_periods.count() == 2
        assert not item.changes.filter(kind="continuation_release").exists()
    else:
        assert results[0] == 200 and original.state == "resolution_pending"
        assert item.lease.billing_periods.count() == 1
        assert original.inventory_locks.filter(kind="hold").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "kind", ["company_continuation_review", "company_continuation_signing"]
)
def test_operator_can_close_case_only_after_canonical_resolution(
    active_agreement, kind
):
    from core_apps.features.services.rental_lifecycle.cases import (
        open_system_case,
        case_action,
        case_payload,
    )
    from core_apps.features.services.rental_phase2 import RentalConflict

    cycle, item = active_agreement
    original = open_sessions(cycle, item)
    identity = (
        original.id
        if kind.endswith("review")
        else original.rental_change.signing_sessions.first().id
    )
    case = open_system_case(
        kind=kind,
        source_key=f"continuation-test:{identity}",
        reason="Unapplied continuation",
        next_action="Reconcile exact continuation",
        lease=item.lease,
    )
    operator = person("case-reviewer")
    operator.is_staff = operator.is_superuser = True
    operator.save()
    case.assigned_to = operator
    case.save()
    data = {
        "action": "resolve",
        "expected_revision": case.revision,
        "reason": "Reviewed retained evidence",
        "resolution_code": "mutually_resolved",
    }
    assert case_payload(case, operator)["blocking_reasons"]
    with pytest.raises(RentalConflict):
        case_action(case, operator, data)
    resolved = resolution(cycle, item, original)
    reviews(item, resolved)
    signatures(item, resolved)
    assert case_payload(case, operator)["blocking_reasons"] == []
    case_action(case, operator, data)
    assert case.status == "resolved"


@pytest.mark.django_db
def test_malformed_continuation_case_stays_reviewable_not_server_error(
    active_agreement,
):
    from core_apps.features.services.rental_lifecycle.cases import (
        open_system_case,
        agreement_case_blocker,
    )

    _, item = active_agreement
    case = open_system_case(
        kind="company_continuation_review",
        source_key="invalid-source",
        reason="Legacy source needs repair",
        next_action="Reconcile source",
        lease=item.lease,
    )
    assert agreement_case_blocker(case)


@pytest.mark.django_db
def test_external_original_signer_has_only_resolution_access_and_must_sign(
    active_agreement,
):
    cycle, item = active_agreement
    incoming = person("resolution-prior-owner")
    for prop in cycle["units"]:
        prop.owner = incoming
        prop.is_ownership_verified = True
        prop.save()
    result = act(
        item,
        cycle["owner"],
        "ownership_change",
        new_owner_id=str(incoming.id),
        reason="Verified transfer proposed",
    )
    assert result.status_code == 200, result.data
    original = item.changes.get(kind="ownership")
    reviews(item, original)
    response = act(
        item,
        cycle["owner"],
        "submit_continuation",
        change_id=str(original.id),
        digest=original.snapshot_digest,
    )
    assert response.status_code == 200, response.data
    response = act(
        item,
        incoming,
        "sign_continuation",
        change_id=str(original.id),
        digest=original.snapshot_digest,
        role="new_owner",
    )
    assert response.status_code == 200, response.data
    complete_change_signature(
        original.rental_change.signing_sessions.get(signer=incoming).provider_session_id
    )
    original.refresh_from_db()
    resolved = resolution(cycle, item, original)
    private = authenticated(incoming).get(API + f"company-tenancies/{item.id}/")
    assert private.status_code == 200, private.data
    assert private.data["roles"] == ["prior_signer"]
    assert private.data["assignments"] == [] and private.data["invoices"] == []
    assert set(private.data["actions"]) <= {"open_case", "respond_change"}
    from core_apps.features.services.rental_lifecycle.cases import (
        open_system_case,
        case_queryset,
    )

    private_case = open_system_case(
        kind="company_tenancy_review",
        source_key=f"private-case:{item.id}",
        reason="Private current-company servicing",
        next_action="Current parties only",
        lease=item.lease,
        actor=cycle["owner"],
    )
    assert not case_queryset(incoming).filter(pk=private_case.pk).exists()
    denied = act(
        item,
        incoming,
        "respond_change",
        change_id=str(resolved.id),
        digest=resolved.snapshot_digest,
        role="signer",
        decision="accept",
    )
    assert denied.status_code == 403, denied.data
    reviews(item, resolved)
    signatures(item, resolved)
    assert resolved.state == "pending_signatures"
    role = next(
        k for k, v in resolved.snapshot["required"].items() if v == str(incoming.id)
    )
    response = act(
        item,
        incoming,
        "sign_continuation",
        change_id=str(resolved.id),
        digest=resolved.snapshot_digest,
        role=role,
    )
    assert response.status_code == 200, response.data
    complete_change_signature(
        resolved.rental_change.signing_sessions.get(signer=incoming).provider_session_id
    )
    resolved.refresh_from_db()
    assert resolved.state == "applied"
    assert (
        authenticated(incoming).get(API + f"company-tenancies/{item.id}/").status_code
        == 404
    )
