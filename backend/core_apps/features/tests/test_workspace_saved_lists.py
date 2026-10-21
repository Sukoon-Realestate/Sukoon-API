import pytest
from django.utils import timezone
from core_apps.features.tests.test_company_housing import company_setup, command, API
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.features.company_models import CompanyMembership
from core_apps.features.company_saved_models import CompanySavedList, CompanySavedItem
from core_apps.features.services.company import saved_lists

pytestmark = pytest.mark.django_db


def test_lists_are_team_scoped_revisioned_and_idempotent(company_setup):
    owner, coordinator, approver, company, *rest = company_setup
    client = authenticated(coordinator)
    body = command(name="Team candidates")
    url = API + f"companies/{company.id}/saved-lists/"
    response = client.post(url, body, format="json")
    assert response.status_code == 201, response.data
    item = response.data["resource"]
    replay = client.post(url, body, format="json")
    assert replay.data == response.data
    assert CompanySavedList.objects.count() == 1
    detail = API + f"company-saved-lists/{item['id']}/"
    assert authenticated(approver).get(url).status_code == 200
    assert (
        authenticated(approver)
        .post(
            detail + "rename/", command(expected_revision=1, name="No"), format="json"
        )
        .status_code
        == 403
    )
    assert authenticated(owner).get(url).status_code in (403, 404)
    changed = client.post(
        detail + "rename/", command(expected_revision=1, name="Reviewed"), format="json"
    )
    assert changed.status_code == 200, changed.data
    stale = client.post(
        detail + "archive/", command(expected_revision=1), format="json"
    )
    assert stale.status_code == 409
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        is_active=False
    )
    assert client.post(url, body, format="json").status_code in (403, 404)


def test_employee_cannot_read_or_write_team_lists(company_setup):
    owner, coordinator, approver, company, *rest = company_setup
    CompanyMembership.objects.create(company=company, user=owner, is_employee=True)
    client = authenticated(owner)
    url = API + f"companies/{company.id}/saved-lists/"
    assert client.get(url).status_code == 403
    assert client.post(url, command(name="Private"), format="json").status_code == 403


def test_saved_offers_are_exact_no_reservation_and_survive_creator_departure(
    company_setup,
):
    owner, coordinator, approver, company, building, properties, offer, request = (
        company_setup
    )
    client = authenticated(coordinator)
    response = client.post(
        API + f"companies/{company.id}/saved-lists/",
        command(name="Candidates"),
        format="json",
    )
    identity = response.data["resource"]["id"]
    url = API + f"company-saved-lists/{identity}/"
    before = request.items.count()
    body = command(expected_revision=1, portfolio_offer_id=str(offer.id))
    response = client.post(url + "add/", body, format="json")
    assert response.status_code == 200, response.data
    assert client.post(url + "add/", body, format="json").data == response.data
    assert CompanySavedItem.objects.count() == 1
    assert request.items.count() == before
    result = client.get(url + "items/")
    assert result.status_code == 200, result.data
    assert result.data["results"][0]["portfolio_offer_id"] == str(offer.id)
    offer.status = "paused"
    offer.save()
    assert client.get(url + "items/").data["results"][0]["available"] is False
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        is_active=False
    )
    assert authenticated(approver).get(url + "items/").status_code == 200


def test_list_ids_cannot_be_used_by_other_company_members(company_setup):
    owner, coordinator, approver, company, *rest = company_setup
    from core_apps.features.company_models import Company

    other = Company.objects.create(
        name="Other", registration_number="OTHER", contact_email="other@example.com"
    )
    CompanyMembership.objects.create(company=other, user=owner, is_admin=True)
    item = CompanySavedList.objects.create(
        company=company, name="Team only", created_by=coordinator
    )
    client = authenticated(owner)
    url = API + f"company-saved-lists/{item.id}/"
    assert client.get(url).status_code in (403, 404)
    assert client.post(
        url + "rename/", command(expected_revision=1, name="Stolen"), format="json"
    ).status_code in (403, 404)


def test_request_key_cannot_replay_into_another_company(company_setup):
    from core_apps.features.company_models import Company

    owner, coordinator, approver, company, *rest = company_setup
    other = Company.objects.create(
        name="Second", registration_number="SECOND", contact_email="second@example.com"
    )
    CompanyMembership.objects.create(company=other, user=coordinator, is_admin=True)
    client = authenticated(coordinator)
    body = command(name="Same intent key")
    assert (
        client.post(
            API + f"companies/{company.id}/saved-lists/", body, format="json"
        ).status_code
        == 201
    )
    response = client.post(
        API + f"companies/{other.id}/saved-lists/", body, format="json"
    )
    assert response.status_code == 409, response.data
    assert not other.saved_lists.exists()


def test_property_bookmark_requires_live_exact_offer(company_setup):
    owner, coordinator, approver, company, building, props, offer, request = (
        company_setup
    )
    client = authenticated(coordinator)
    prop = props[0]
    item = CompanySavedList.objects.create(
        company=company, name="Units", created_by=coordinator
    )
    url = API + f"company-saved-lists/{item.id}/add/"
    missing = client.post(
        url, command(expected_revision=1, property_id=str(prop.id)), format="json"
    )
    assert missing.status_code == 400, missing.data
    prop.rental_inventory = {"offers": [{"id": "exact", "archived": False}]}
    prop.save(update_fields=["rental_inventory"])
    added = client.post(
        url,
        command(expected_revision=1, property_id=str(prop.id), offer_id="exact"),
        format="json",
    )
    assert added.status_code == 200, added.data
    saved = CompanySavedItem.objects.get(saved_list=item)
    assert saved.property == prop and saved.offer_id == "exact"
    assert saved_lists.item_payload(saved)["property_id"] == str(prop.id)
    prop.retired_at = timezone.now()
    prop.status = prop.Status.HIDDEN
    prop.save(update_fields=["retired_at", "status"])
    saved.refresh_from_db()
    assert saved_lists.item_payload(saved)["available"] is False


@pytest.mark.django_db(transaction=True)
def test_concurrent_list_edits_fence_revision(company_setup):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections, connection

    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    owner, coordinator, approver, company, *rest = company_setup
    item = CompanySavedList.objects.create(
        company=company, name="Before", created_by=coordinator
    )
    barrier = Barrier(2)

    def edit(index):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return (
                authenticated(coordinator)
                .post(
                    API + f"company-saved-lists/{item.id}/rename/",
                    command(expected_revision=1, name=f"After {index}"),
                    format="json",
                )
                .status_code
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(edit, range(2))) == [200, 409]
    item.refresh_from_db()
    assert item.revision == 2
