"""Personal contract identity, current membership and bounded pagination."""

import uuid
from datetime import date, datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

import pytest
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone

from core_apps.common.contract_testing import api_json
from core_apps.features.models import (
    Company, CompanyMembership, Lease, PrivateAccessRevocation,
    RentalChange, RentalTimelineEvent, SigningSession,
)
from core_apps.profiles.models import Contract
from core_apps.profiles.serializers import TenantContractSerializer
from core_apps.profiles.services import contract_projection
from .test_screen_views import create_test_property


pytestmark = pytest.mark.django_db
DAY = date(2026, 10, 30)
URL = reverse("tenant-contracts-list")


@pytest.fixture(autouse=True)
def fixed_cairo_day():
    with patch("django.utils.timezone.now", return_value=datetime(2026, 10, 30, 10, tzinfo=dt_timezone.utc)):
        yield


@pytest.fixture
def make_lease(user, another_user):
    property_obj = create_test_property(another_user)

    def make(**overrides):
        values = dict(
            tenant=user, owner=another_user, property=property_obj,
            template_id="eg-v1", template_version="1", legacy_read_only=False,
            offer_id=str(uuid.uuid4()), rent_amount_minor=1000,
            start_date=DAY - timedelta(days=3), end_date=DAY + timedelta(days=28),
            status=Lease.Status.ACTIVE,
        )
        values.update(overrides)
        return Lease.objects.create(**values)

    return make


def get_page(client, *, bucket="current", page=1, page_size=20):
    query = {"page": page, "page_size": page_size}
    if bucket is not None:
        query["bucket"] = bucket
    response = client.get(URL, query)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    # Verify the actual old wire shape before api_json adapts pagination.
    body = response.json()
    assert set(body) == {"message", "data"} and isinstance(body["data"], list)
    assert int(response["X-Page"]) == page
    assert int(response["X-Per-Page"]) == page_size
    return {
        **api_json(response)["data"], "page": int(response["X-Page"]),
        "bucket": response["X-Contracts-Bucket"], "as_of": response["X-Contracts-As-Of"],
        "projection_version": int(response["X-Contracts-Projection-Version"]),
    }


def make_legacy(user, **overrides):
    values = dict(tenant=user, property_title="Legacy home", status="active",
                  start_date=date(2001, 1, 1), end_date=date(2002, 1, 1),
                  document_url="https://files.example.test/legacy.pdf")
    values.update(overrides)
    return Contract.objects.create(**values)


def renewal(predecessor, successor, **overrides):
    values = dict(lease=predecessor, result_lease=successor, requester=predecessor.tenant,
                  kind="renewal", status="applied")
    values.update(overrides)
    return RentalChange.objects.create(**values)


def successor(make_lease, predecessor, **overrides):
    return make_lease(**{
        "tenancy_root_id": predecessor.tenancy_root_id, "offer_id": predecessor.offer_id,
        "property": predecessor.property, "owner": predecessor.owner, **overrides,
    })


def test_canonical_profile_count_matches_current_exact_identity(auth_client, user, make_lease):
    lease = make_lease(document_url="https://provider.invalid/private-secret", revision=7,
                       offer_snapshot={"title": "Selected unit"})
    before = (Lease.objects.count(), Contract.objects.count(), SigningSession.objects.count())
    current = get_page(auth_client)
    account = api_json(auth_client.get(reverse("my-account")))["data"]["menu_items"]["contracts"]
    assert account["count"] == current["count"] == 1
    assert account["as_of"] == current["as_of"] == DAY.isoformat()
    assert account["projection_version"] == current["projection_version"] == 1
    row = current["results"][0]
    assert row["id"] == f"lease:{lease.id}"
    assert row["lease_id"] == str(lease.id)
    assert row["source"] == "canonical_lease" and row["party_role"] == "tenant"
    assert row["revision"] == 7 and row["is_current"] is True
    assert row["tenancy_root_id"] == str(lease.tenancy_root_id)
    assert row["end_date_is_exclusive"] is True
    assert row["end_date"] == lease.end_date.isoformat()
    assert row["lease_status"] == row["status"] == "active"
    assert row["offer_id"] == lease.offer_id and row["offer_snapshot"] == lease.offer_snapshot
    assert row["document_url"] == ""
    assert (Lease.objects.count(), Contract.objects.count(), SigningSession.objects.count()) == before


def test_saved_six_period_topology_is_four_current_six_all(auth_client, user, make_lease):
    independent = [make_lease(start_date=date(2026, 10, 27), end_date=date(2026, 11, 27)) for _ in range(2)]
    previous, renewed = [], []
    for _ in range(2):
        old = make_lease(start_date=date(2026, 9, 28), end_date=date(2026, 10, 28))
        new = successor(make_lease, old, start_date=date(2026, 10, 28), end_date=date(2026, 11, 28))
        renewal(old, new)
        previous.append(old)
        renewed.append(new)
    current, all_rows = get_page(auth_client), get_page(auth_client, bucket="all")
    assert current["count"] == contract_projection.count_current(user) == 4
    assert {x["lease_id"] for x in current["results"]} == {str(x.id) for x in independent + renewed}
    assert all_rows["count"] == 6
    prior_rows = [x for x in all_rows["results"] if x["lease_id"] in {str(x.id) for x in previous}]
    assert len(prior_rows) == 2
    assert all(not row["is_current"] and row["lease_status"] == "active" for row in prior_rows)
    for old in previous:
        old.refresh_from_db()
        assert old.status == "active" and old.end_date == date(2026, 10, 28)


@pytest.mark.parametrize("starts,ends,expected", [
    (DAY, DAY + timedelta(days=1), True),
    (DAY - timedelta(days=1), DAY, False),
    (DAY + timedelta(days=1), DAY + timedelta(days=2), False),
])
def test_exclusive_current_date_boundaries(user, make_lease, starts, ends, expected):
    lease = make_lease(start_date=starts, end_date=ends)
    assert contract_projection.count_current(user) == int(expected)
    row = TenantContractSerializer(list(contract_projection.rows(user)), many=True).data[0]
    assert row["is_current"] is expected
    assert row["start_date"] == starts.isoformat() and row["end_date"] == ends.isoformat()
    if ends == DAY:
        assert row["status"] == "expired" and row["lease_status"] == "active"
    lease.refresh_from_db()
    assert lease.start_date == starts and lease.end_date == ends and lease.status == "active"


@pytest.mark.parametrize("instant,expected", [
    (datetime(2026, 10, 29, 21, 59, 59, tzinfo=dt_timezone.utc), date(2026, 10, 29)),
    (datetime(2026, 10, 29, 22, 0, tzinfo=dt_timezone.utc), DAY),
    (datetime(2028, 2, 28, 22, 0, tzinfo=dt_timezone.utc), date(2028, 2, 29)),
    (datetime(2026, 12, 31, 22, 0, tzinfo=dt_timezone.utc), date(2027, 1, 1)),
])
def test_civil_clock_uses_cairo_not_active_timezone(instant, expected):
    with timezone.override("America/Los_Angeles"), patch("django.utils.timezone.now", return_value=instant):
        assert contract_projection.civil_day() == expected


def test_current_ignores_possession_and_financial_closure(user, make_lease):
    make_lease(occupancy_status="returned", financial_closure_status="closed")
    make_lease(status="termination_pending", occupancy_status="move_out_pending")
    make_lease(status="ended", occupancy_status="occupied", financial_closure_status="open")
    assert contract_projection.count_current(user) == 2
    assert contract_projection.rows(user).count() == 3


def test_applied_overlapping_renewal_suppresses_only_predecessor(auth_client, user, make_lease):
    old = make_lease()
    new = successor(make_lease, old)
    unrelated = successor(make_lease, old)  # same root/property alone never deduplicates
    renewal(old, new)
    current = get_page(auth_client)
    assert {x["lease_id"] for x in current["results"]} == {str(new.id), str(unrelated.id)}
    all_rows = get_page(auth_client, bucket="all")
    previous = next(x for x in all_rows["results"] if x["lease_id"] == str(old.id))
    assert previous["is_current"] is False and previous["status"] == "ended"
    assert previous["lease_status"] == "active"
    assert contract_projection.count_current(user) == 2


@pytest.mark.parametrize("change_status", ["proposed", "accepted", "pending_signatures", "signed"])
def test_unapplied_renewal_does_not_replace_current(user, make_lease, change_status):
    old = make_lease()
    new = successor(make_lease, old)
    renewal(old, new, status=change_status)
    assert contract_projection.count_current(user) == 2


@pytest.mark.parametrize("condition", ["future", "signed", "revoked", "wrong_root", "wrong_owner", "wrong_offer"])
def test_ineligible_result_does_not_suppress_original(user, another_user, make_lease, condition):
    old = make_lease()
    overrides = {
        "future": {"start_date": DAY + timedelta(days=1)},
        "signed": {"status": "signed"},
        "wrong_root": {"tenancy_root_id": uuid.uuid4()},
        "wrong_owner": {"owner": user}, "wrong_offer": {"offer_id": "different"},
    }.get(condition, {})
    new = successor(make_lease, old, **overrides)
    renewal(old, new)
    if condition == "revoked":
        PrivateAccessRevocation.objects.create(lease=new, user=user, reason="Test revocation")
    current = TenantContractSerializer(list(contract_projection.rows(user, bucket="current")), many=True).data
    assert str(old.id) in {row["lease_id"] for row in current}


def test_amendment_and_unsigned_proposals_do_not_add_contracts(user, make_lease):
    active = make_lease()
    RentalChange.objects.create(lease=active, requester=user, kind="amendment", status="applied")
    for status in ("draft", "pending_signatures", "pending", "cancelled", "expired"):
        make_lease(status=status)
    signed = make_lease(status="signed", start_date=DAY + timedelta(days=1))
    rows = TenantContractSerializer(list(contract_projection.rows(user)), many=True).data
    assert {row["lease_id"] for row in rows} == {str(active.id), str(signed.id)}
    assert contract_projection.count_current(user) == 1
    assert next(row for row in rows if row["lease_id"] == str(signed.id))["status"] == "signed"


@pytest.mark.parametrize("terminal_status", ["cancelled", "expired"])
def test_terminal_history_requires_bilateral_or_activation_evidence(user, make_lease, terminal_status):
    unsigned = make_lease(status=terminal_status, document_id=uuid.uuid4(), document_hash="a" * 64)
    partial = make_lease(status=terminal_status, document_id=uuid.uuid4(), document_hash="b" * 64)
    signed = make_lease(status=terminal_status, document_id=uuid.uuid4(), document_hash="c" * 64)
    for lease, parties in [(partial, [partial.tenant]), (signed, [signed.tenant, signed.owner])]:
        for signer in parties:
            SigningSession.objects.create(lease=lease, signer=signer, status="completed",
                completed_at=timezone.now(), expires_at=timezone.now() + timedelta(days=1),
                document_id=lease.document_id, document_hash=lease.document_hash)
    historical = make_lease(status=terminal_status)
    RentalTimelineEvent.objects.create(lease=historical, kind="signed", label="Agreement fully signed")
    activated = make_lease(status=terminal_status, activated_at=timezone.now())
    rows = TenantContractSerializer(list(contract_projection.rows(user)), many=True).data
    assert {row["lease_id"] for row in rows} == {str(x.id) for x in (signed, historical, activated)}
    assert all(row["status"] == terminal_status and not row["is_current"] for row in rows)
    assert contract_projection.count_current(user) == 0


def test_personal_revocation_and_other_tenant_are_excluded(auth_client, user, another_user, make_lease):
    own = make_lease()
    revoked = make_lease()
    make_lease(tenant=another_user, owner=user)
    PrivateAccessRevocation.objects.create(lease=revoked, user=user, reason="Revoked")
    for bucket in ("current", "all"):
        rows = get_page(auth_client, bucket=bucket)
        assert rows["count"] == 1 and rows["results"][0]["lease_id"] == str(own.id)


@pytest.mark.parametrize("role", ["is_admin", "is_coordinator", "is_approver", "is_employee", "can_execute_payments", "signer"])
def test_company_role_never_manufactures_personal_contract(user, make_lease, role):
    company = Company.objects.create(name="Contract test company", registration_number="fixture", contact_email="fixture@example.test")
    roles = {role: True} if role != "signer" else {"signing_verified_until": timezone.now() + timedelta(days=30)}
    CompanyMembership.objects.create(company=company, user=user, **roles)
    make_lease(tenant=None, renter_company=company)
    assert contract_projection.rows(user).count() == 0
    assert contract_projection.count_current(user) == 0


def test_legacy_raw_semantics_and_unknown_provenance_are_preserved(auth_client, user, make_lease):
    canonical = make_lease()
    legacy = make_legacy(user, property_title=canonical.property.title,
                         start_date=canonical.start_date, end_date=canonical.end_date)
    old_active = make_legacy(user)  # date alone cannot expire this legacy row
    old_expired = make_legacy(user, status="expired")
    current, all_rows = get_page(auth_client), get_page(auth_client, bucket=None)
    assert current["count"] == 3 and all_rows["count"] == 4
    assert all_rows["bucket"] == "all"
    row = next(x for x in all_rows["results"] if x["id"] == str(old_active.id))
    assert row["source"] == "legacy_registry" and row["party_role"] == "tenant"
    assert row["lease_id"] is None and row["end_date_is_exclusive"] is None
    assert row["end_date"] == "2002-01-01" and row["status"] == "active" and row["is_current"] is True
    assert row["document_url"] == old_active.document_url
    assert {x["id"] for x in current["results"]} >= {str(legacy.id), f"lease:{canonical.id}"}
    assert next(x for x in all_rows["results"] if x["id"] == str(old_expired.id))["is_current"] is False


def test_combined_database_pagination_has_no_omissions_or_n_plus_one(auth_client, user, make_lease, django_assert_num_queries):
    leases = [make_lease() for _ in range(7)]
    legacy = [make_legacy(user, start_date=DAY - timedelta(days=3)) for _ in range(5)]
    expected = {f"lease:{x.id}" for x in leases} | {str(x.id) for x in legacy}
    pages = [get_page(auth_client, page=index, page_size=5) for index in (1, 2, 3)]
    ids = [row["id"] for page in pages for row in page["results"]]
    assert len(ids) == len(set(ids)) == 12 and set(ids) == expected
    assert all(page["count"] == 12 and page["total_pages"] == 3 for page in pages)
    assert [row["id"] for row in get_page(auth_client, page_size=5)["results"]] == ids[:5]
    with django_assert_num_queries(2):
        page = Paginator(contract_projection.rows(user, bucket="current"), 5).page(2)
        serialized = TenantContractSerializer(list(page), many=True).data
        assert len(serialized) == 5


def test_all_orders_current_before_history_and_date_before_stable_identity(auth_client, user, make_lease):
    current = make_lease(start_date=DAY - timedelta(days=10))
    earlier = make_lease(start_date=DAY - timedelta(days=20))
    future_signed = make_lease(status="signed", start_date=DAY + timedelta(days=1))
    historical = make_lease(status="ended", start_date=DAY - timedelta(days=2))
    rows = get_page(auth_client, bucket="all")["results"]
    assert [row["lease_id"] for row in rows] == [str(x.id) for x in (current, earlier, future_signed, historical)]


def test_invalid_bucket_is_validation_error(auth_client):
    response = auth_client.get(URL, {"bucket": "other"})
    assert response.status_code == 400


def test_explicit_day_is_computed_once_for_endpoint(auth_client, make_lease):
    make_lease()
    with patch.object(contract_projection, "civil_day", return_value=DAY) as today:
        page = get_page(auth_client)
    today.assert_called_once_with()
    assert page["as_of"] == DAY.isoformat()
