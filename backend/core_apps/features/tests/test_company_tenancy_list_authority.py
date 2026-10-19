"""Collection discovery must enforce the same current grant as detail reads."""

import pytest
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import CompanyMembership, CompanyTenancyChange
from core_apps.features.tests.test_company_continuations import (
    active_agreement,
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
    authenticated,
    API,
    act,
    person,
    proposal,
)


def identities(response):
    assert response.status_code == 200, response.data
    return {row["id"] for row in response.data["results"]}


def assert_hidden(item, user):
    client = authenticated(user)
    assert client.get(API + f"company-tenancies/{item.id}/").status_code == 404
    listed = client.get(API + "company-tenancies/")
    assert str(item.id) not in identities(listed), listed.data
    filtered = client.get(
        API + f"company-tenancies/?company_id={item.lease.renter_company.id}"
    )
    assert str(item.id) not in identities(filtered), filtered.data


@pytest.mark.django_db
def test_removed_approver_role_cannot_keep_discovery_through_an_old_assignment(
    active_agreement,
):
    cycle, item = active_agreement
    proposal(cycle, item)
    actor = cycle["approver"]
    assert str(item.id) in identities(
        authenticated(actor).get(API + "company-tenancies/")
    )
    member = CompanyMembership.objects.get(company=cycle["company"], user=actor)
    member.is_approver = False
    member.save(update_fields=["is_approver"])
    assert_hidden(item, actor)


@pytest.mark.django_db
def test_unrelated_open_change_cannot_reopen_a_former_approvers_closed_review(
    active_agreement,
):
    cycle, item = active_agreement
    change = proposal(cycle, item)
    actor = cycle["approver"]
    result = act(
        item,
        cycle["owner"],
        "withdraw_change",
        change_id=str(change.id),
        reason="Owner withdraws before signatures",
    )
    assert result.status_code == 200, result.data
    result = act(
        item,
        cycle["owner"],
        "terminate",
        effective_on=str(item.lease.start_date),
        reason="Separate mutual termination review",
    )
    assert result.status_code == 200, result.data
    assert_hidden(item, actor)


@pytest.mark.django_db
def test_unverified_incoming_owner_cannot_keep_discovery_after_title_authority_changes(
    active_agreement,
):
    cycle, item = active_agreement
    actor = person("incoming-list-owner")
    for prop in cycle["units"]:
        prop.owner = actor
        prop.is_ownership_verified = True
        prop.save(update_fields=["owner", "is_ownership_verified"])
    result = act(
        item,
        cycle["owner"],
        "ownership_change",
        new_owner_id=str(actor.id),
        reason="Verified proposed transfer",
    )
    assert result.status_code == 200, result.data
    assert str(item.id) in identities(
        authenticated(actor).get(API + "company-tenancies/")
    )
    prop = cycle["units"][0]
    prop.is_ownership_verified = False
    prop.save(update_fields=["is_ownership_verified"])
    assert_hidden(item, actor)


@pytest.mark.django_db
def test_suspended_financial_reviewer_cannot_keep_private_task_discovery(
    active_agreement,
):
    cycle, item = active_agreement
    actor = person("financial-list-reviewer")
    actor.is_staff = True
    actor.save(update_fields=["is_staff"])
    staff = StaffProfile.objects.create(
        user=actor, role_name="financial_approver", is_active=True
    )
    # A pending independent-review assignment is the authentication fixture;
    # this test does not execute or assert a settlement/financial effect.
    CompanyTenancyChange.objects.create(
        tenancy=item,
        proposed_by=cycle["payer"],
        kind="settlement_adjustment",
        snapshot={"required": {"financial_reviewer": str(actor.id)}, "content": {}},
        snapshot_digest="list-authority-fixture",
        state="pending",
        reason="Independent review fixture",
    )
    assert str(item.id) in identities(
        authenticated(actor).get(API + "company-tenancies/")
    )
    staff.is_active = False
    staff.save(update_fields=["is_active"])
    assert_hidden(item, actor)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role", ["owner", "coordinator", "signer", "payer", "employee", "colleague"]
)
def test_existing_contract_participants_keep_authorized_paginated_discovery(
    active_agreement, role
):
    cycle, item = active_agreement
    client = authenticated(cycle[role])
    for query in ["", f"?company_id={item.lease.renter_company.id}&per_page=1"]:
        response = client.get(API + "company-tenancies/" + query)
        assert identities(response) == {str(item.id)}
        assert response.data["count"] == 1
        assert response.data["results"][0]["roles"]
    assert client.get(API + f"company-tenancies/{item.id}/").status_code == 200
