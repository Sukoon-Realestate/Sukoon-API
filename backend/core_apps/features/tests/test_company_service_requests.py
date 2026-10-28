"""Real HTTP/PostgreSQL case preparation; provider facts are fixture simulations."""

import uuid
from unittest.mock import patch
import pytest
from django.test import Client
from django.urls import reverse
from core_apps.users.models import User
from core_apps.features.tests.test_company_tenancy import (
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
    handover,
)
from core_apps.features.tests.test_company_continuations import reviews, signatures
from core_apps.features.tests.test_rental_lifecycle_safety import operator
from core_apps.features.models import (
    RentalOperationalCase,
    FinalSettlement,
    SettlementAdjustment,
)

pytestmark = pytest.mark.django_db


def request(cycle, item, kind="ownership_change", user=None):
    item.lease.refresh_from_db()
    reviewed = item.lease.revision
    result = act(
        item,
        user or cycle["owner"],
        "request_service",
        kind=kind,
        reason="Please prepare the supported correction.",
    )
    assert result.status_code == 200, result.data
    assert result.data["resource"]["revision"] > reviewed
    return RentalOperationalCase.objects.get(
        lease=item.lease, kind="company_service_request"
    )


def case_action(case, user, action, **data):
    case.refresh_from_db()
    return authenticated(user).post(
        API + f"rental-cases/{case.id}/actions/",
        command(
            expected_revision=case.revision,
            action=action,
            reason="Reviewed current evidence",
            **data,
        ),
        format="json",
    )


def assign(case, user):
    response = case_action(case, user, "assign", assignee_id=str(user.id))
    assert response.status_code == 200, response.data
    case.refresh_from_db()


def incoming(cycle):
    owner = person("incoming-service-owner")
    for prop in cycle["units"]:
        prop.owner, prop.is_ownership_verified = owner, True
        prop.save()
    return owner


def prepare(case, item, user, **proposal):
    item.lease.refresh_from_db()
    return case_action(
        case,
        user,
        "prepare_company_change",
        tenancy_revision=item.lease.revision,
        company_proposal=proposal,
    )


def test_reason_only_request_deduplicates_and_withdraws_without_domain_effect(
    active_agreement,
):
    cycle, item = active_agreement
    original = item.lease.owner_id
    case = request(cycle, item)
    request(cycle, item, user=cycle["signer"])
    assert (
        RentalOperationalCase.objects.filter(kind="company_service_request").count()
        == 1
    )
    assert not item.changes.exists()
    assert (
        case_action(case, cycle["signer"], "withdraw_company_request").status_code
        == 404  # An owner's discussion is not disclosed to the company signer.
    )
    result = case_action(case, cycle["owner"], "withdraw_company_request")
    assert result.status_code == 200, result.data
    item.lease.refresh_from_db()
    assert item.lease.owner_id == original and not item.changes.exists()
    case.refresh_from_db()
    assert case.status == "resolved" and case.resolution_code == "no_action_required"


def test_operator_prepares_named_review_without_proxy_consent_or_early_closure(
    active_agreement,
):
    cycle, item = active_agreement
    case = request(cycle, item)
    agent, new_owner = operator("support"), incoming(cycle)
    assert prepare(case, item, agent, new_owner_id=str(new_owner.id)).status_code == 403
    assign(case, agent)
    result = prepare(case, item, agent, new_owner_id=str(new_owner.id))
    assert result.status_code == 200, result.data
    change = item.changes.get(kind="ownership")
    assert change.proposed_by == agent and change.decisions == {}
    assert change.snapshot["required"]["owner"] == str(cycle["owner"].id)
    assert prepare(case, item, agent, new_owner_id=str(new_owner.id)).status_code == 409
    assert (
        case_action(case, agent, "resolve", resolution_code="corrected").status_code
        == 409
    )
    assert (
        act(
            item,
            agent,
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role="owner",
            decision="accept",
        ).status_code
        == 404
    )
    result = act(
        item,
        cycle["owner"],
        "withdraw_change",
        change_id=str(change.id),
        reason="Do not proceed",
    )
    assert result.status_code == 200, result.data
    assert (
        case_action(case, agent, "resolve", resolution_code="corrected").status_code
        == 409
    )
    assert (
        case_action(
            case, agent, "resolve", resolution_code="no_action_required"
        ).status_code
        == 200
    )


def test_operator_web_form_to_ownership_completion_preserves_original_creditor(
    active_agreement, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    cycle, item = active_agreement
    case = request(cycle, item)
    agent, new_owner = operator("support"), incoming(cycle)
    assign(case, agent)
    client = Client()
    client.force_login(agent)
    url = reverse("admin:features_rentaloperationalcase_change", args=[case.pk])
    page = client.get(url)
    assert page.status_code == 200 and b"incoming_owner" in page.content
    item.lease.refresh_from_db()
    data = {
        "command_action": "prepare_company_change",
        "decision_reason": "Prepare independently verified property transfer",
        "incoming_owner": str(new_owner.pk),
        "tenancy_revision": item.lease.revision,
        "expected_revision": case.revision,
        "request_key": str(uuid.uuid4()),
        "_save": "Save",
    }
    invalid = client.post(url, {**data, "decision_reason": "x" * 2001})
    assert invalid.status_code == 200
    assert "decision_reason" in invalid.context["adminform"].form.errors
    assert invalid.context["adminform"].form["incoming_owner"].value() == str(
        new_owner.pk
    )
    assert not item.changes.exists()
    assert client.post(url, data).status_code == 302
    assert client.post(url, data).status_code == 302
    assert item.changes.filter(kind="ownership").count() == 1
    change = item.changes.get(kind="ownership")
    reviews(item, change)
    assert (
        case_action(case, agent, "resolve", resolution_code="corrected").status_code
        == 409
    )
    signatures(item, change)  # Synthetic provider adapter, not a live signature.
    assert (
        case_action(case, agent, "resolve", resolution_code="corrected").status_code
        == 200
    )
    item.lease.refresh_from_db()
    assert item.lease.owner == new_owner
    assert item.lease.invoices.first().beneficiary == cycle["owner"]
    view = authenticated(cycle["owner"]).get(API + f"rental-cases/{case.id}/")
    assert view.data["company_service"]["can_open_tenancy"] is False


def test_preparation_rechecks_requester_authority_and_tenancy_revision(
    active_agreement,
):
    cycle, item = active_agreement
    case = request(cycle, item, user=cycle["signer"])
    agent, new_owner = operator("support"), incoming(cycle)
    assign(case, agent)
    stale = case_action(
        case,
        agent,
        "prepare_company_change",
        tenancy_revision=1,
        company_proposal={"new_owner_id": str(new_owner.id)},
    )
    assert stale.status_code == 409, stale.data
    cycle["company"].memberships.filter(user=cycle["signer"]).update(is_active=False)
    denied = prepare(case, item, agent, new_owner_id=str(new_owner.id))
    assert denied.status_code == 403, denied.data
    assert not item.changes.exists()


def test_invalid_customer_kind_and_employee_authority_do_not_create_cases(
    active_agreement,
):
    cycle, item = active_agreement
    for user, kind, status in [
        (cycle["owner"], "refund_anything", 400),
        (cycle["employee"], "ownership_change", 403),
        (cycle["owner"], "settlement_adjustment", 409),
    ]:
        response = act(item, user, "request_service", kind=kind, reason="Request")
        assert response.status_code == status, response.data
    assert not RentalOperationalCase.objects.filter(
        kind="company_service_request"
    ).exists()


def test_incoming_owner_cannot_prepare_their_own_transfer_as_operator(active_agreement):
    cycle, item = active_agreement
    case = request(cycle, item)
    agent = operator("support")
    for prop in cycle["units"]:
        prop.owner, prop.is_ownership_verified = agent, True
        prop.save()
    assign(case, agent)
    result = prepare(case, item, agent, new_owner_id=str(agent.id))
    assert result.status_code == 403, result.data
    assert not item.changes.exists()


def test_correction_operator_and_independent_review_preserve_executed_settlement(
    active_agreement,
):
    from core_apps.features.services.refunds import execute_refund

    cycle, item = active_agreement
    with patch("django.utils.timezone.localdate", return_value=item.lease.start_date):
        assert (
            act(
                item,
                cycle["owner"],
                "terminate",
                effective_on=str(item.lease.start_date),
                reason="End before possession",
            ).status_code
            == 200
        )
        reviews(item, item.changes.get(kind="termination"))
        handover(cycle, item, "move_out", item.lease.start_date)
        assert (
            act(
                item, cycle["payer"], "settlement", reason="Return deposit", lines=[]
            ).status_code
            == 200
        )
        reviews(item, item.changes.get(kind="settlement"))
        for refund in item.lease.refund_requests.all():
            execute_refund(refund)
        original = FinalSettlement.objects.get(lease=item.lease)
        frozen = dict(FinalSettlement.objects.filter(pk=original.pk).values().get())
        case = request(cycle, item, "settlement_adjustment", cycle["payer"])
        finance = operator("financial_approver")
        support = operator("support")
        assert (
            case_action(
                case, support, "assign", assignee_id=str(support.id)
            ).status_code
            == 404
        )
        assign(case, finance)
        reviewer = User.objects.get(email="execution-reviewer@company-test.invalid")
        proposal = {
            "financial_reviewer_id": str(finance.id),
            "lines": [
                {
                    "id": "utility-correction",
                    "type": "utility",
                    "description": "Supported additive utility adjustment",
                    "amount": {"amount_minor": 500, "currency": "EGP", "exponent": 2},
                }
            ],
        }
        assert prepare(case, item, finance, **proposal).status_code == 403
        proposal["financial_reviewer_id"] = str(reviewer.id)
        result = prepare(case, item, finance, **proposal)
        assert result.status_code == 200, result.data
        change = item.changes.get(kind="settlement_adjustment")
        assert change.decisions == {}
        reviews(item, change)
        assert change.state == "applied"
        assert (
            case_action(
                case, finance, "resolve", resolution_code="corrected"
            ).status_code
            == 200
        )
        assert (
            SettlementAdjustment.objects.get(original=original).execution_status
            == "executed"
        )
        assert (
            dict(FinalSettlement.objects.filter(pk=original.pk).values().get())
            == frozen
        )


@pytest.mark.django_db(transaction=True)
def test_concurrent_original_operator_command_creates_one_proposal(active_agreement):
    from concurrent.futures import ThreadPoolExecutor
    from django.db import close_old_connections

    cycle, item = active_agreement
    case = request(cycle, item)
    agent, new_owner = operator("support"), incoming(cycle)
    assign(case, agent)
    item.lease.refresh_from_db()
    body = command(
        expected_revision=case.revision,
        action="prepare_company_change",
        reason="Same original operator operation",
        tenancy_revision=item.lease.revision,
        company_proposal={"new_owner_id": str(new_owner.id)},
    )

    def send():
        close_old_connections()
        try:
            result = authenticated(User.objects.get(pk=agent.pk)).post(
                API + f"rental-cases/{case.id}/actions/", body, format="json"
            )
            return (
                result.status_code,
                result.data["resource"]["company_service"]["proposal_id"],
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: send(), range(2)))
    assert [status for status, _ in results] == [200, 200]
    assert results[0][1] == results[1][1]
    assert item.changes.filter(kind="ownership").count() == 1
    agent.staff_profile.is_active = False
    agent.staff_profile.save()
    response = authenticated(agent).post(
        API + f"rental-cases/{case.id}/actions/", body, format="json"
    )
    assert response.status_code in {403, 404}
