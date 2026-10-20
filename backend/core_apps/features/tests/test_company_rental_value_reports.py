"""Canonical reporting and resident privacy. Provider fixtures are simulated."""

import csv
import io
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connection, close_old_connections
from django.utils import timezone

from .test_company_tenancy import (
    active_agreement,
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
    person,
    authenticated,
    API,
)
from core_apps.features.models import CompanyMembership
from core_apps.features.services.company.read_snapshot import consistent_read

pytestmark = pytest.mark.django_db


def get(cycle, role, endpoint, params=None):
    return authenticated(cycle[role]).get(
        API + f"companies/{cycle['company'].id}/{endpoint}/",
        params or {},
    )


def test_summary_resident_sees_only_own_assignment_and_no_capacity(active_agreement):
    data, item = active_agreement
    response = get(data, "employee", "rental-summary")
    assert response.status_code == 200, response.data
    assert response["Cache-Control"] == "private, no-store"
    row = response.data["housing"][0]
    assert len(row["assignments"]) == 1
    assert row["assignments"][0]["employee_id"] == str(data["employee"].id)
    assert not row["commercial_access"]
    assert row["contracted_capacity"] is None and row["unassigned_capacity"] is None
    assert row["cost_center"] == row["project_code"] == ""
    assert not response.data["can_view_costs"]
    coordinator = get(data, "coordinator", "rental-summary").data["housing"][0]
    assert len(coordinator["assignments"]) == 2 and coordinator["commercial_access"]
    assert coordinator["arrival_pending_count"] == 2


def test_arrival_address_requires_activation_consent_and_survives_physical_arrival(
    active_agreement,
):
    data, item = active_agreement
    assignment = item.preparation.booking.assignments.get(employee=data["employee"])
    first = get(data, "employee", "rental-summary").data["housing"][0]["assignments"][0]
    assert first["arrival_address"]
    # Physical confirmation increments the assignment revision without replacing consent.
    assignment.occupancy_status = "occupied"
    assignment.revision += 1
    assignment.save()
    assert get(data, "employee", "rental-summary").data["housing"][0]["assignments"][0][
        "arrival_address"
    ]
    assignment.occupancy_status = "returned"
    assignment.save()
    row = get(data, "employee", "rental-summary").data["housing"][0]
    assert row["assignments"][0]["arrival_address"] is None
    assert row["assigned_count"] == 0


def test_read_time_end_attention_keeps_unreturned_and_unsettled_obligations(
    active_agreement,
):
    data, item = active_agreement
    item.lease.end_date = timezone.localdate() + timedelta(days=10)
    item.lease.save()
    assert get(data, "coordinator", "rental-summary").data["housing"][0][
        "end_attention"
    ]
    item.lease.occupancy_status, item.lease.financial_closure_status = (
        "returned",
        "closed",
    )
    item.lease.save()
    assert not get(data, "coordinator", "rental-summary").data["housing"][0][
        "end_attention"
    ]


def test_report_separates_commitment_invoice_capture_and_deposit(active_agreement):
    data, item = active_agreement
    requirement = item.preparation.booking.request
    requirement.project_code, requirement.cost_center = "PROJECT-A", "SITE-1"
    requirement.save()
    result = get(data, "coordinator", "housing-report")
    assert result.status_code == 200, result.data
    rows = result.data["rows"]
    kinds = {row["kind"] for row in rows}
    assert {"contract_rent", "invoice", "payment", "deposit"} <= kinds
    assert not {"reserved_rent", "reserved_deposit"} & kinds
    assert all(
        row["tenancy_id"] == str(item.id) and row["currency"] == "EGP" for row in rows
    )
    expected = sum(
        item.lease.billing_periods.exclude(status="cancelled").values_list(
            "amount_minor", flat=True
        )
    )
    assert result.data["totals"]["contract_rent"]["amount_minor"] == expected
    payment = next(row for row in rows if row["kind"] == "payment")
    assert payment["allocated_minor"] == payment["amount_minor"]
    assert "grand_total" not in result.data
    assert (
        get(data, "coordinator", "housing-report", {"project_code": "other"}).data[
            "rows"
        ]
        == []
    )
    assert (
        get(data, "coordinator", "housing-report", {"tenancy_id": str(item.id)}).data[
            "rows"
        ]
        == rows
    )
    assert get(data, "employee", "housing-report").data["rows"] == []


def test_report_dates_are_exclusive_no_partial_month_proration(signed_agreement):
    data, item = signed_agreement
    period = item.lease.billing_periods.order_by("sequence").first()
    row = get(
        data,
        "payer",
        "housing-report",
        {
            "from": str(period.start + timedelta(days=1)),
            "until": str(period.end_exclusive),
        },
    )
    assert row.status_code == 200, row.data
    commitments = [r for r in row.data["rows"] if r["kind"] == "contract_rent"]
    assert (
        len(commitments) == 1 and commitments[0]["amount_minor"] == period.amount_minor
    )
    assert commitments[0]["basis"] == "whole_billing_period_overlapping_filter"
    excluded = get(data, "payer", "housing-report", {"from": str(period.end_exclusive)})
    assert str(period.id) not in {r["id"] for r in excluded.data["rows"]}
    assert (
        get(data, "payer", "housing-report", {"from": "2026-02-30"}).status_code == 400
    )


def test_report_absent_deposit_not_zero_and_csv_has_exact_ids(signed_agreement):
    data, item = signed_agreement
    deposit = getattr(item.lease, "deposit_agreement", None)
    if deposit:
        deposit.delete()
    requirement = item.preparation.booking.request
    requirement.title = "=unsafe spreadsheet formula"
    requirement.save()
    result = get(data, "coordinator", "housing-report")
    row = next(r for r in result.data["rows"] if r["kind"] == "deposit")
    assert row["amount_minor"] is None and row["collected_minor"] is None
    assert row["state"] == "not_established"
    exported = get(data, "coordinator", "housing-report", {"export": "csv"})
    assert (
        exported.status_code == 200 and exported["Cache-Control"] == "private, no-store"
    )
    rows = list(csv.DictReader(io.StringIO(exported.content.decode("utf-8-sig"))))
    assert rows and all(
        r["title"].startswith("'=") and r["tenancy_id"] == str(item.id) for r in rows
    )


def test_current_membership_rechecked_for_summary_and_export(active_agreement):
    data, item = active_agreement
    CompanyMembership.objects.filter(
        company=data["company"], user=data["coordinator"]
    ).update(is_active=False)
    assert get(data, "coordinator", "rental-summary").status_code in {403, 404}
    assert get(
        data, "coordinator", "housing-report", {"export": "csv"}
    ).status_code in {403, 404}
    stranger = person("unrelated-company-reader")
    assert authenticated(stranger).get(
        API + f"companies/{data['company'].id}/housing-report/"
    ).status_code in {403, 404}


@pytest.mark.django_db(transaction=True)
def test_management_snapshot_keeps_concurrent_updates_out_of_same_report(company_setup):
    company = company_setup[3]
    old = company.name
    model = type(company)

    def update():
        close_old_connections()
        try:
            model.objects.filter(pk=company.pk).update(
                name="Changed while report was read"
            )
        finally:
            close_old_connections()

    with consistent_read():
        assert model.objects.get(pk=company.pk).name == old
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(update).result(timeout=10)
        assert model.objects.get(pk=company.pk).name == old
        with connection.cursor() as cursor:
            cursor.execute("SHOW transaction_read_only")
            assert cursor.fetchone()[0] == "on"
    assert model.objects.get(pk=company.pk).name != old
