"""Named employees cannot enter new packages while deletion is under review."""

# flake8: noqa: F401,F811
import pytest
from core_apps.features.company_models import CompanyBookingItem
from core_apps.features.company_staff_models import CompanyStaffRecord
from core_apps.features.services.company import bookings
from core_apps.users.models import AccountClosureRequest
from core_apps.users.tests.test_account_closure import submit
from .test_cycle_concurrency import parallel_calls
from .test_company_preparation_account_closure import close
from .test_company_contract_preparation import (
    cycle,
    company_setup,
    rental_participants,
    policy,
    authenticated,
    API,
    command,
)

pytestmark = pytest.mark.django_db


def selection(cycle, via_staff=False):
    item = cycle["item"]
    request = item.request
    request.refresh_from_db()
    employee = cycle["employee"]
    staff = None
    if via_staff:
        staff = CompanyStaffRecord.objects.create(
            company=cycle["company"],
            display_name="Named employee",
            work_email=employee.email,
            proposed_roles=["employee"],
            membership=cycle["company"].memberships.get(user=employee),
            created_by=cycle["coordinator"],
        )
    body = command(
        expected_revision=request.revision,
        offer_id=str(item.offer.id),
        offer_revision=item.offer.revision,
        occupant_ids=[] if via_staff else [str(employee.id)],
        staff_ids=[str(staff.id)] if staff else [],
    )
    return request, body


def select(cycle, request, body):
    return authenticated(cycle["coordinator"]).post(
        API + f"company-housing-requests/{request.id}/items/", body, format="json"
    )


@pytest.mark.parametrize("via_staff", [False, True])
def test_pending_employee_cannot_be_selected_through_either_identity(cycle, via_staff):
    request, body = selection(cycle, via_staff)
    before = CompanyBookingItem.objects.count()
    close(cycle["employee"])
    response = select(cycle, request, body)
    assert response.status_code == 403, response.data
    assert CompanyBookingItem.objects.count() == before
    people = authenticated(cycle["coordinator"]).get(
        API + f"companies/{cycle['company'].id}/occupants/"
    )
    assert people.status_code == 200, people.data
    employee = next(
        row
        for row in people.data["results"]
        if row["user_id"] == str(cycle["employee"].id)
    )
    assert employee["account_closure_blocked"]


def test_completed_selection_receipt_survives_employee_closure(cycle):
    request, body = selection(cycle)
    first = select(cycle, request, body)
    assert first.status_code == 201, first.data
    close(cycle["employee"])
    replay = select(cycle, request, body)
    assert replay.status_code == 201 and replay.data == first.data
    item = CompanyBookingItem.objects.get(id=first.data["resource"]["id"])
    result = bookings.item_payload(item)
    assert result["account_closure_blocked"]
    assert not result["can_negotiate"]


@pytest.mark.django_db(transaction=True)
def test_selection_serializes_with_employee_closure(cycle):
    request, body = selection(cycle)
    selected, _ = parallel_calls(
        lambda index: (
            select(cycle, request, body) if index == 0 else submit(cycle["employee"])
        )
    )
    closure = AccountClosureRequest.objects.get(user=cycle["employee"], active=True)
    if selected.status_code == 201:
        item = CompanyBookingItem.objects.get(id=selected.data["resource"]["id"])
        assert item.created_at <= closure.created_at
    else:
        assert selected.status_code == 403, selected.data
