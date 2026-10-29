"""Lease lookup narrows the existing company/role projection, never grants it."""

import uuid

import pytest

from core_apps.features.models import Company, Lease
from core_apps.features.tests import test_company_role_contexts as role_contexts


API = role_contexts.API
client = role_contexts.client
tenancy = role_contexts.tenancy
cycle = role_contexts.cycle
company_setup = role_contexts.company_setup
rental_participants = role_contexts.rental_participants
policy = role_contexts.policy


pytestmark = pytest.mark.django_db


def lookup(actors, item, *, actor="payer", role="payer", **filters):
    return client(actors[actor], actors["company"], role).get(
        API + "company-tenancies/",
        {
            "company_id": str(actors["company"].id),
            "lease_id": str(item.lease.id),
            **filters,
        },
    )


def test_lease_lookup_returns_current_payer_revision_and_projection(tenancy):
    actors, item = tenancy
    item.lease.revision += 7
    item.lease.save(update_fields=["revision"])

    response = lookup(actors, item)

    assert response.status_code == 200, response.data
    assert response.data["count"] == 1
    row = response.data["results"][0]
    assert (row["id"], row["lease_id"], row["company_id"], row["revision"]) == (
        str(item.id),
        str(item.lease.id),
        str(actors["company"].id),
        item.lease.revision,
    )
    assert row["roles"] == ["payer"] and row["active_role"] == "payer"
    assert "invoices" in row and row["role_projection_version"] == 1
    assert (
        not {"terms", "signing_document", "signing_sessions", "assignments", "people"}
        & row.keys()
    )
    unfiltered = client(actors["payer"], actors["company"], "payer").get(
        API + "company-tenancies/", {"company_id": str(actors["company"].id)}
    )
    assert unfiltered.status_code == 200
    assert unfiltered.data["results"] == response.data["results"]


def test_unknown_lease_does_not_return_another_authorized_tenancy(tenancy):
    actors, item = tenancy
    response = lookup(actors, item, lease_id=str(uuid.uuid4()))
    assert response.status_code == 200, response.data
    assert response.data["count"] == 0 and response.data["results"] == []


def test_lease_without_company_tenancy_does_not_fall_back_to_another_row(tenancy):
    actors, item = tenancy
    other = Lease.objects.create(
        property=item.lease.property,
        owner=item.lease.owner,
        renter_company=actors["company"],
        template_id=item.lease.template_id,
        template_version=item.lease.template_version,
        start_date=item.lease.start_date,
        end_date=item.lease.end_date,
        rent_amount_minor=item.lease.rent_amount_minor,
        legacy_read_only=False,
    )
    response = lookup(actors, item, lease_id=str(other.id))
    assert response.status_code == 200, response.data
    assert response.data["count"] == 0 and response.data["results"] == []


@pytest.mark.parametrize("identity", ["not-a-uuid", "123", ""])
def test_invalid_lease_filter_is_rejected(tenancy, identity):
    actors, item = tenancy
    response = lookup(actors, item, lease_id=identity)
    assert response.status_code == 400, response.data


def test_lease_filter_intersects_company_filter_and_selected_company(tenancy):
    actors, item = tenancy
    other = Company.objects.create(
        name="Other synthetic lease lookup company",
        registration_number="LEASE-FILTER-OTHER",
        contact_email="lease-filter-other@example.test",
    )
    response = lookup(actors, item, company_id=str(other.id))
    assert response.status_code == 200, response.data
    assert response.data["count"] == 0 and response.data["results"] == []

    forged = client(actors["payer"], other, "payer").get(
        API + "company-tenancies/",
        {"company_id": str(actors["company"].id), "lease_id": str(item.lease.id)},
    )
    assert forged.status_code == 200, forged.data
    assert forged.data["count"] == 0 and forged.data["results"] == []


@pytest.mark.parametrize(
    ("actor", "role"), [("employee", "payer"), ("payer", "signer"), ("payer", None)]
)
def test_lease_filter_never_grants_a_forged_or_missing_role(tenancy, actor, role):
    actors, item = tenancy
    response = lookup(actors, item, actor=actor, role=role)
    assert response.status_code == 200, response.data
    assert response.data["count"] == 0 and response.data["results"] == []


def test_lease_filter_rechecks_revoked_payer_mandate(tenancy):
    actors, item = tenancy
    assert lookup(actors, item).data["count"] == 1
    item.payer_mandate.state = "revoked"
    item.payer_mandate.save(update_fields=["state"])
    response = lookup(actors, item)
    assert response.status_code == 200, response.data
    assert response.data["count"] == 0 and response.data["results"] == []
