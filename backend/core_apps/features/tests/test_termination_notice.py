"""Personal termination consent is distinct from ordinary proposal approval."""

import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from threading import Barrier

import pytest
from django.db import close_old_connections, connection
from django.utils import timezone

from core_apps.features.models import (
    Lease,
    RentalChange,
    RentalConsentRecord,
    RentInvoice,
)
from core_apps.features.services import termination_notice as notice
from core_apps.features.services.legal_lifecycle import (
    accept_termination,
    end_due_leases,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from .test_rental_phase5 import client_for, phase5_lease

API = "/api/v1/features/v1/"


@pytest.fixture(autouse=True)
def cairo_clock(monkeypatch):
    monkeypatch.setattr(
        timezone, "now", lambda: datetime(2026, 10, 29, 12, tzinfo=dt_timezone.utc)
    )


def create_body(lease, *, day=None, mode="mutual_short_notice", **extra):
    return {
        "expected_revision": 0,
        "lease_revision": lease.revision,
        "request_key": str(uuid.uuid4()),
        "effective_on": str(day or notice.today()),
        "reason": "Reviewed end",
        "evidence_ids": [],
        "termination_mode": mode,
        "notice_basis_digest": notice.policy(lease)["basis_digest"],
        "short_notice_acknowledged": mode == "mutual_short_notice",
        **extra,
    }


def create(user, lease, body=None, **extra):
    return client_for(user).post(
        API + f"leases/{lease.id}/termination-requests/",
        body or create_body(lease, **extra),
        format="json",
    )


def response_body(item, **extra):
    return {
        "expected_revision": item["revision"],
        "request_key": str(uuid.uuid4()),
        "action": "accept",
        "termination_notice_digest": item["termination_notice"]["digest"],
        "short_notice_acknowledged": True,
        **extra,
    }


def respond(user, item, body=None, **extra):
    return client_for(user).post(
        API + f"termination-requests/{item['id']}/respond/",
        body or response_body(item, **extra),
        format="json",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ack,expected", [(None, 409), (False, 409), ("true", 400), (1, 400)]
)
def test_short_notice_requester_must_explicitly_acknowledge(
    phase5_lease, ack, expected
):
    owner, _, lease = phase5_lease
    body = create_body(lease, short_notice_acknowledged=ack)
    if ack is None:
        body.pop("short_notice_acknowledged")
    result = create(owner, lease, body)
    assert result.status_code == expected, result.data
    assert not lease.rental_changes.exists()
    assert not RentalConsentRecord.objects.exists()
    lease.refresh_from_db()
    assert lease.status == "active" and lease.end_date == date(2027, 1, 1)


@pytest.mark.django_db
def test_bilateral_short_notice_preserves_debt_and_separate_possession(phase5_lease):
    owner, tenant, lease = phase5_lease
    invoice = RentInvoice.objects.create(
        lease=lease,
        reference="NOTICE-DEBT",
        due_date=notice.today(),
        amount_minor=1000,
        charges_minor=1000,
        status="due",
    )
    created = create(owner, lease)
    assert created.status_code == 201, created.data
    item = created.data["resource"]
    frozen = copy.deepcopy(
        RentalChange.objects.get(id=item["id"]).termination_notice_snapshot
    )
    assert item["termination_notice"]["acknowledged_by"] == [str(owner.id)]
    assert item["termination_notice"]["financial_obligations_preserved"] is True
    assert item["termination_notice"]["lease_revision"] == lease.revision
    accepted = respond(tenant, item)
    assert accepted.status_code == 200, accepted.data
    assert accepted.data["resource"]["status"] == "applied"
    assert set(accepted.data["resource"]["termination_notice"]["acknowledged_by"]) == {
        str(owner.id),
        str(tenant.id),
    }
    lease.refresh_from_db()
    invoice.refresh_from_db()
    change = RentalChange.objects.get(id=item["id"])
    assert change.termination_notice_snapshot == frozen
    assert change.versions.get().snapshot["termination_notice"] == frozen
    assert change.document_id is None and change.signed_by == []
    assert lease.end_date == notice.today() and lease.status == "ended"
    assert lease.occupancy_status == "move_out_pending"
    assert lease.financial_closure_status != "closed"
    assert invoice.charges_minor == 1000 and invoice.status == "due"
    assert (
        RentalConsentRecord.objects.filter(
            subject_id=change.id, decision__startswith="termination_"
        ).count()
        == 2
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    "ack,expected", [(None, 409), (False, 409), ("true", 400), (1, 400)]
)
def test_responder_needs_independent_explicit_acknowledgement(
    phase5_lease, ack, expected
):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    body = response_body(item, short_notice_acknowledged=ack)
    if ack is None:
        body.pop("short_notice_acknowledged")
    result = respond(tenant, item, body)
    assert result.status_code == expected, result.data
    change = RentalChange.objects.get(id=item["id"])
    assert change.approvals == [str(owner.id)] and change.revision == 1
    assert (
        RentalConsentRecord.objects.filter(
            subject_id=change.id, decision="termination_accept"
        ).count()
        == 0
    )


@pytest.mark.django_db
def test_exact_contract_notice_boundary_and_current_amended_terms(phase5_lease):
    owner, tenant, lease = phase5_lease
    lease.terms["termination_policy"] = {
        "notice_days": 20,
        "departure_duties": "Return keys separately",
    }
    lease.save(update_fields=["terms"])
    current = notice.policy(lease)
    assert current["notice_days"] == 20
    day = notice.today() + timedelta(days=20)
    assert current["earliest_effective_on"] == str(day)
    invalid = create(owner, lease, day=day - timedelta(days=1), mode="contract_notice")
    assert invalid.status_code == 409
    result = create(owner, lease, day=day, mode="contract_notice")
    assert result.status_code == 201, result.data
    item = result.data["resource"]
    accepted = respond(tenant, item, short_notice_acknowledged=False)
    assert accepted.status_code == 200, accepted.data
    lease.refresh_from_db()
    assert lease.end_date == day and lease.status == "termination_pending"
    assert not item["termination_notice"]["requires_short_notice_acknowledgement"]
    assert (
        item["termination_notice"]["termination_policy"]["departure_duties"]
        == "Return keys separately"
    )


@pytest.mark.django_db
def test_applied_signed_amendment_provenance_preserves_original_document(phase5_lease):
    from core_apps.features.tasks import process_rental_changes

    owner, tenant, lease = phase5_lease
    original_id = uuid.uuid4()
    lease.document_id, lease.document_hash = original_id, "a" * 64
    lease.save(update_fields=["document_id", "document_hash"])
    terms = copy.deepcopy(lease.terms)
    terms["termination_policy"]["notice_days"] = 20
    amendment = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind="amendment",
        status="signed",
        effective_on=notice.today(),
        terms=terms,
        previous_terms=lease.terms,
        document_id=uuid.uuid4(),
        document_hash="b" * 64,
        signed_by=[str(owner.id), str(tenant.id)],
        approvals=[str(owner.id), str(tenant.id)],
    )
    assert process_rental_changes()["applied"] == 1
    lease.refresh_from_db()
    assert notice.policy(lease)["notice_days"] == 20
    result = create(owner, lease)
    assert result.status_code == 201, result.data
    source = result.data["resource"]["termination_notice"]["material"]
    assert (
        source["document_id"] == str(original_id)
        and source["document_hash"] == "a" * 64
    )
    assert source["applied_amendment"] == {
        "id": str(amendment.id),
        "content_revision": 1,
        "document_id": str(amendment.document_id),
        "document_hash": "b" * 64,
    }
    amendment.document_hash = "c" * 64
    amendment.save(update_fields=["document_hash"])
    assert respond(tenant, result.data["resource"]).status_code == 409


@pytest.mark.django_db
@pytest.mark.parametrize(
    "clause", [{}, {"notice_days": "30"}, {"notice_days": True}, {"notice_days": -1}]
)
def test_missing_or_malformed_notice_blocks_early_end_but_not_natural_expiry(
    phase5_lease, clause
):
    owner, tenant, lease = phase5_lease
    lease.terms["termination_policy"] = clause
    lease.save(update_fields=["terms"])
    current = notice.policy(lease)
    assert not current["available"] and current["notice_days"] is None
    assert len(current["basis_digest"]) == 64
    assert create(owner, lease).status_code == 409
    created = create(owner, lease, day=lease.end_date, mode="natural_expiry")
    assert created.status_code == 201, created.data
    item = created.data["resource"]
    assert item["termination_notice"]["mode"] == "natural_expiry"
    assert not item["termination_notice"]["requires_short_notice_acknowledgement"]
    assert respond(tenant, item, short_notice_acknowledged=False).status_code == 200
    lease.refresh_from_db()
    assert lease.end_date == date(2027, 1, 1)


@pytest.mark.django_db
def test_automatic_expiry_needs_no_termination_or_notice_metadata(phase5_lease):
    _, _, lease = phase5_lease
    lease.end_date = notice.today()
    lease.terms.pop("termination_policy")
    lease.save(update_fields=["end_date", "terms"])
    assert end_due_leases() == 1
    lease.refresh_from_db()
    assert lease.status == "ended" and lease.occupancy_status == "move_out_pending"
    assert not lease.rental_changes.exists()


@pytest.mark.django_db
def test_natural_expiry_inside_notice_period_preserves_notice_clause(phase5_lease):
    owner, tenant, lease = phase5_lease
    lease.end_date = notice.today() + timedelta(days=1)
    lease.save(update_fields=["end_date"])
    current = notice.policy(lease)
    assert current["earliest_effective_on"] > current["natural_end_on"]
    result = create(owner, lease, day=lease.end_date, mode="natural_expiry")
    assert result.status_code == 201, result.data
    item = result.data["resource"]
    assert item["termination_notice"]["notice_days"] == 30
    assert not item["termination_notice"]["requires_short_notice_acknowledgement"]
    assert respond(tenant, item, short_notice_acknowledged=False).status_code == 200
    lease.refresh_from_db()
    assert lease.end_date == notice.today() + timedelta(days=1)
    assert lease.terms["termination_policy"]["notice_days"] == 30


@pytest.mark.django_db
def test_canonical_minimum_date_respects_future_start_and_bounds(phase5_lease):
    owner, _, lease = phase5_lease
    lease.start_date = notice.today() + timedelta(days=10)
    lease.save(update_fields=["start_date"])
    current = notice.policy(lease)
    assert current["minimum_effective_on"] == str(lease.start_date)
    assert create(owner, lease).status_code == 400
    assert (
        create(owner, lease, day=lease.end_date + timedelta(days=1)).status_code == 400
    )
    result = create(owner, lease, day=lease.start_date)
    assert result.status_code == 201, result.data
    assert result.data["resource"]["termination_notice"]["minimum_effective_on"] == str(
        lease.start_date
    )


@pytest.mark.django_db
def test_create_after_cairo_midnight_requires_fresh_policy_without_moving_date(
    phase5_lease, monkeypatch
):
    owner, _, lease = phase5_lease
    requested = notice.today() + timedelta(days=2)
    body = create_body(lease, day=requested)
    monkeypatch.setattr(
        timezone, "now", lambda: datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc)
    )
    assert create(owner, lease, body).status_code == 409
    assert not lease.rental_changes.exists()
    refreshed = create(owner, lease, day=requested)
    assert refreshed.status_code == 201, refreshed.data
    assert refreshed.data["resource"]["effective_on"] == str(requested)


@pytest.mark.django_db
def test_lease_and_center_projections_share_server_policy(phase5_lease):
    from core_apps.features.serializers_parts.lease_serializer import LeaseSerializer
    from core_apps.features.rental_serializers_parts.lease_phase2_serializer import (
        LeasePhase2Serializer,
    )

    owner, _, lease = phase5_lease
    expected = notice.policy(lease)
    assert LeaseSerializer(lease).data["termination_notice_policy"] == expected
    assert LeasePhase2Serializer(lease).data["termination_notice_policy"] == expected
    center = client_for(owner).get(API + f"leases/{lease.id}/rental-center/")
    assert center.status_code == 200, center.data
    assert center.data["termination_notice_policy"] == expected


@pytest.mark.django_db
def test_unrelated_lease_revision_does_not_restart_reviewed_notice(phase5_lease):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    lease.revision += 1
    lease.save(update_fields=["revision"])
    result = respond(tenant, item)
    assert result.status_code == 200, result.data
    assert (
        result.data["resource"]["termination_notice"]["digest"]
        == item["termination_notice"]["digest"]
    )


@pytest.mark.django_db
def test_same_day_end_issues_accrued_unissued_rent_and_only_cancels_future_schedule(
    phase5_lease,
):
    from core_apps.features.models import BillingPeriod

    owner, tenant, lease = phase5_lease
    elapsed = BillingPeriod.objects.create(
        lease=lease,
        sequence=1,
        start=notice.today() - timedelta(days=10),
        end_exclusive=notice.today() + timedelta(days=20),
        amount_minor=1000,
        issue_at=timezone.now() - timedelta(days=11),
        due_at=timezone.now() - timedelta(days=9),
    )
    future = BillingPeriod.objects.create(
        lease=lease,
        sequence=2,
        start=elapsed.end_exclusive,
        end_exclusive=elapsed.end_exclusive + timedelta(days=30),
        amount_minor=1000,
        issue_at=timezone.now() + timedelta(days=15),
        due_at=timezone.now() + timedelta(days=21),
    )
    item = create(owner, lease).data["resource"]
    result = respond(tenant, item)
    assert result.status_code == 200, result.data
    elapsed.refresh_from_db()
    future.refresh_from_db()
    invoice = lease.invoices.get(billing_period=elapsed)
    assert elapsed.status == "issued" and future.status == "cancelled"
    assert invoice.charges_minor == 1000 and invoice.applied_minor == 0
    assert invoice.status == "due"
    assert not lease.invoices.filter(billing_period=future).exists()


@pytest.mark.django_db
def test_historic_accepted_end_remains_effective_without_fabricated_consent(
    phase5_lease,
):
    from core_apps.features.tasks import process_rental_changes

    owner, _, lease = phase5_lease
    lease.end_date = notice.today()
    lease.status = "termination_pending"
    lease.save(update_fields=["end_date", "status"])
    legacy = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind="termination",
        status="accepted",
        effective_on=notice.today(),
    )
    assert process_rental_changes()["applied"] == 1
    lease.refresh_from_db()
    legacy.refresh_from_db()
    assert lease.status == "ended" and legacy.status == "applied"
    assert legacy.termination_notice_snapshot == {}
    assert not RentalConsentRecord.objects.filter(subject_id=legacy.id).exists()


@pytest.mark.django_db
def test_exact_end_requires_natural_expiry_and_no_notice_floor_is_invented(
    phase5_lease,
):
    owner, _, lease = phase5_lease
    assert (
        create(owner, lease, day=lease.end_date, mode="contract_notice").status_code
        == 409
    )
    lease.terms["termination_policy"]["notice_days"] = 0
    lease.save(update_fields=["terms"])
    created = create(owner, lease, mode="contract_notice")
    assert created.status_code == 201, created.data
    assert created.data["resource"]["termination_notice"]["notice_days"] == 0


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", ["terms", "end", "elapsed"])
def test_material_change_or_elapsed_date_requires_rejection_and_reproposal(
    phase5_lease, monkeypatch, mutation
):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    if mutation == "terms":
        lease.terms["termination_policy"]["notice_days"] = 15
        lease.save(update_fields=["terms"])
    elif mutation == "end":
        lease.end_date -= timedelta(days=1)
        lease.save(update_fields=["end_date"])
    else:
        monkeypatch.setattr(
            timezone, "now", lambda: datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc)
        )
    assert respond(tenant, item).status_code == 409
    detail = client_for(tenant).get(API + f"termination-requests/{item['id']}/")
    assert detail.data["termination_notice"]["review_required"] is True
    assert detail.data["allowed_actions"] == ["reject"]
    assert respond(tenant, item, action="reject").status_code == 200
    lease.refresh_from_db()
    assert lease.status == "active"
    assert create(owner, lease).status_code == 201


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["proposed", "changes_requested", "review_required"])
def test_legacy_pending_approvals_are_not_backfilled_or_reopened(phase5_lease, status):
    owner, tenant, lease = phase5_lease
    change = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind="termination",
        status=status,
        effective_on=notice.today(),
        approvals=[str(owner.id)],
    )
    item = {
        "id": str(change.id),
        "revision": 1,
        "termination_notice": {"digest": "a" * 64},
    }
    assert respond(tenant, item).status_code == 409
    assert respond(tenant, item, action="request_changes").status_code == 403
    assert not RentalConsentRecord.objects.filter(subject_id=change.id).exists()
    assert respond(tenant, item, action="reject").status_code == 200
    assert create(owner, lease).status_code == 201


@pytest.mark.django_db
def test_basis_digest_content_digest_and_revision_are_bound_to_commands(phase5_lease):
    owner, tenant, lease = phase5_lease
    assert create(owner, lease, notice_basis_digest="a" * 64).status_code == 409
    item = create(owner, lease).data["resource"]
    assert respond(tenant, item, termination_notice_digest="a" * 64).status_code == 409
    assert respond(tenant, item, expected_revision=99).status_code == 409
    assert create(owner, lease).status_code == 409
    change = RentalChange.objects.get(id=item["id"])
    change.effective_on += timedelta(days=1)
    change.save(update_fields=["effective_on"])
    assert respond(tenant, item).status_code == 409


@pytest.mark.django_db
def test_same_payload_replays_receipt_without_second_consent(phase5_lease, monkeypatch):
    owner, tenant, lease = phase5_lease
    body = create_body(lease)
    first = create(owner, lease, body)
    assert create(owner, lease, body).data == first.data
    item = first.data["resource"]
    answer = response_body(item)
    accepted = respond(tenant, item, answer)
    assert accepted.status_code == 200, accepted.data
    monkeypatch.setattr(
        timezone, "now", lambda: datetime(2026, 10, 30, 12, tzinfo=dt_timezone.utc)
    )
    assert respond(tenant, item, answer).data == accepted.data
    assert create(owner, lease, body).data == first.data
    assert (
        respond(
            tenant, item, {**answer, "short_notice_acknowledged": False}
        ).status_code
        == 409
    )
    assert (
        RentalConsentRecord.objects.filter(
            subject_id=item["id"], decision__startswith="termination_"
        ).count()
        == 2
    )


@pytest.mark.django_db
def test_lifecycle_cannot_apply_ordinary_approvals_without_bilateral_notice_evidence(
    phase5_lease,
):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    change = RentalChange.objects.get(id=item["id"])
    change.approvals = [str(owner.id), str(tenant.id)]
    change.status = "accepted"
    change.save(update_fields=["approvals", "status"])
    with pytest.raises(RentalConflict):
        accept_termination(change)
    lease.refresh_from_db()
    assert lease.end_date == date(2027, 1, 1) and lease.status == "active"
    assert not RentalConsentRecord.objects.filter(
        subject_id=change.id, decision="termination_accept"
    ).exists()


@pytest.mark.django_db
def test_lifecycle_rejects_in_memory_date_that_differs_from_locked_snapshot(
    phase5_lease,
):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    change = RentalChange.objects.get(id=item["id"])
    notice.record_decision(change, tenant, "accept", True)
    change.approvals = [str(owner.id), str(tenant.id)]
    change.status = "accepted"
    change.save(update_fields=["approvals", "status"])
    change.effective_on += timedelta(days=1)
    with pytest.raises(RentalConflict):
        accept_termination(change)
    lease.refresh_from_db()
    assert lease.end_date == date(2027, 1, 1)


@pytest.mark.django_db
def test_lifecycle_requires_requester_explicit_ack_even_with_both_ordinary_approvals(
    phase5_lease,
):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    change = RentalChange.objects.get(id=item["id"])
    consent = RentalConsentRecord.objects.get(
        subject_id=change.id, decision="termination_propose"
    )
    consent.snapshot["short_notice_acknowledged"] = False
    consent.save(update_fields=["snapshot"])
    notice.record_decision(change, tenant, "accept", True)
    change.approvals = [str(owner.id), str(tenant.id)]
    change.status = "accepted"
    change.save(update_fields=["approvals", "status"])
    with pytest.raises(RentalConflict):
        accept_termination(change)
    lease.refresh_from_db()
    assert lease.end_date == date(2027, 1, 1)


@pytest.mark.django_db
def test_policy_is_cairo_civil_date_even_when_request_timezone_changes(
    phase5_lease, monkeypatch
):
    _, _, lease = phase5_lease
    instant = datetime(2026, 10, 29, 22, 30, tzinfo=dt_timezone.utc)
    monkeypatch.setattr(timezone, "now", lambda: instant)
    with timezone.override("UTC"):
        current = notice.policy(lease)
        assert current["policy_date"] == str(instant.astimezone(notice.CAIRO).date())
        assert current["timezone"] == "Africa/Cairo"


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["proposed", "accepted", "signed", "applied"])
def test_renewal_created_after_termination_blocks_acceptance(phase5_lease, status):
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    renewal = RentalChange.objects.create(
        lease=lease, requester=owner, kind="renewal", status=status
    )
    rejected = respond(tenant, item)
    assert rejected.status_code == 409, rejected.data
    lease.refresh_from_db()
    assert lease.status == "active" and lease.end_date == date(2027, 1, 1)
    renewal.status = "rejected"
    renewal.save(update_fields=["status"])
    assert respond(tenant, item).status_code == 200


@pytest.mark.django_db(transaction=True)
def test_concurrent_accepts_apply_one_exact_revision(phase5_lease):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock behavior requires PostgreSQL")
    owner, tenant, lease = phase5_lease
    item = create(owner, lease).data["resource"]
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return respond(tenant, item).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        results = [future.result(timeout=30) for future in futures]
    assert sorted(results) == [200, 409]
    assert (
        RentalConsentRecord.objects.filter(
            subject_id=item["id"], decision="termination_accept"
        ).count()
        == 1
    )
    assert lease.timeline_events.filter(kind="legally_ended").count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_proposals_cannot_create_two_pending_terminations(phase5_lease):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock behavior requires PostgreSQL")
    owner, _, lease = phase5_lease
    bodies = [create_body(lease), create_body(lease)]
    barrier = Barrier(2)

    def worker(body):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return create(owner, lease, body).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, body) for body in bodies]
        results = [future.result(timeout=30) for future in futures]
    assert sorted(results) == [201, 409]
    assert lease.rental_changes.filter(kind="termination").count() == 1
