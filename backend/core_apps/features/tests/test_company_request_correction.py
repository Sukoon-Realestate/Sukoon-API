"""Recover planning inputs without rewriting a selected commercial package."""

from datetime import date, timedelta
import pytest
from core_apps.features.company_models import CompanyMembership
from core_apps.features.services.company import bookings
from core_apps.features.services.company.request_period import monthly_periods
from .test_company_housing import company_setup, command, API, proposed
from .test_rental_phase2 import rental_participants, authenticated
from .test_rental_lifecycle import policy


def body(item, **changes):
    return command(
        **{
            **{k: getattr(item, k) for k in bookings.REQUEST_FIELDS},
            "expected_revision": item.revision,
            **changes,
        }
    )


@pytest.mark.parametrize(
    "start,end,count",
    [
        (date(2028, 1, 31), date(2028, 2, 29), 1),
        (date(2027, 1, 31), date(2027, 2, 28), 1),
        (date(2028, 2, 29), date(2029, 2, 28), 12),
    ],
)
def test_existing_month_end_contract(start, end, count):
    assert monthly_periods(start, end) == count


@pytest.mark.django_db
def test_create_rejects_unsupported_period_before_creating(company_setup):
    _, user, _, company, *_, item = company_setup
    before = company.housing_requests.count()
    response = authenticated(user).post(
        API + f"companies/{company.id}/housing-requests/",
        body(item, ends_on_exclusive=item.ends_on_exclusive + timedelta(days=1)),
        format="json",
    )
    assert response.status_code == 400
    assert company.housing_requests.count() == before


@pytest.mark.django_db
def test_correction_receipt_replay_and_stale_revision(company_setup, monkeypatch):
    _, user, _, company, *_, item = company_setup
    client = authenticated(user)
    url = API + f"company-housing-requests/{item.id}/"
    data = body(item, title="Corrected request", commitment_ceiling_minor=1234567)
    response = client.post(url, data, format="json")
    assert response.status_code == 200
    assert client.post(url, data, format="json").data == response.data
    item.refresh_from_db()
    assert item.title == "Corrected request"
    assert item.commitment_ceiling_minor == 1234567
    assert item.revision == data["expected_revision"] + 1
    assert (
        client.post(url, body(item, expected_revision=0), format="json").status_code
        == 409
    )
    assert bookings.request_payload(item, user)["can_edit"] is True
    monkeypatch.setattr(
        "core_apps.features.services.company.request_period.timezone.localdate",
        lambda: item.ends_on_exclusive + timedelta(days=1),
    )
    assert client.post(url, data, format="json").data == response.data


@pytest.mark.django_db
def test_current_assigned_coordinator_required(company_setup):
    owner, user, approver, company, *_, item = company_setup
    url = API + f"company-housing-requests/{item.id}/"
    assert (
        authenticated(approver).post(url, body(item), format="json").status_code == 403
    )
    CompanyMembership.objects.create(company=company, user=owner, is_coordinator=True)
    assert authenticated(owner).post(url, body(item), format="json").status_code == 403
    assert bookings.request_payload(item, owner)["can_edit"] is False
    CompanyMembership.objects.filter(company=company, user=user).update(is_active=False)
    assert authenticated(user).post(url, body(item), format="json").status_code == 404
    assert bookings.request_payload(item, user)["can_edit"] is False


@pytest.mark.django_db
def test_selected_and_withdrawn_packages_keep_original_terms(company_setup):
    _, user, _, _, *_, request = company_setup
    package = proposed(company_setup)
    request.refresh_from_db()
    url = API + f"company-housing-requests/{request.id}/"
    original_package = package.snapshot.copy()
    for withdrawn in (False, True):
        if withdrawn:
            bookings.withdraw_item(
                user, package.id, {"expected_revision": package.revision}
            )
            request.refresh_from_db()
        result = authenticated(user).post(
            url, body(request, title="Changed"), format="json"
        )
        assert result.status_code == 200
        request.refresh_from_db()
        package.refresh_from_db()
        assert request.title == "Changed"
        assert package.snapshot == original_package
        assert bookings.request_payload(request, user)["can_edit"] is True
