"""The current payer reviews the exact settlement without the original contract."""

# flake8: noqa: F401,F811
import uuid
from unittest.mock import patch

import pytest

from core_apps.features.models import RentalEvidence
from .test_company_role_contexts import client
from .test_company_tenancy import (
    API,
    act,
    active_agreement,
    agreement,
    company_setup,
    cycle,
    decide_change,
    handover,
    policy,
    rental_participants,
    signed_agreement,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def returned_company(active_agreement):
    actors, item = active_agreement
    day = item.lease.start_date
    # A declared test date exercises the ordinary termination and return flow;
    # no payment, signature, lease or settlement status is assigned directly.
    with patch("django.utils.timezone.localdate", return_value=day):
        response = act(
            item,
            actors["owner"],
            "terminate",
            effective_on=str(day),
            reason="Synthetic agreed end before arrival",
        )
        assert response.status_code == 200, response.data
        change = item.changes.get(kind="termination")
        decide_change(
            actors,
            item,
            change,
            [(role, actors[role]) for role in ("owner", "signer", "payer")],
        )
        handover(actors, item, "move_out", day)
    item.lease.refresh_from_db()
    assert (item.lease.status, item.lease.occupancy_status) == ("ended", "returned")
    return actors, item


def propose(actors, item, lines=()):
    response = act(
        item,
        actors["owner"],
        "settlement",
        lines=list(lines),
        reason="Synthetic final return of the remaining deposit",
    )
    assert response.status_code == 200, response.data
    return item.changes.get(kind="settlement")


def read(actors, item, actor="payer", role="payer"):
    return client(actors[actor], actors["company"], role).get(
        API + f"company-tenancies/{item.id}/"
    )


def change_row(response, change):
    assert response.status_code == 200, response.data
    return next(row for row in response.data["changes"] if row["id"] == str(change.id))


def assert_payer_private_fields_absent(payload, row):
    assert (
        not {
            "terms",
            "package",
            "assignments",
            "signing_document",
            "signing_sessions",
            "document_hash",
            "business_policies",
        }
        & payload.keys()
    )
    assert not {"signing_document", "signing_sessions", "rental_change_id"} & row.keys()
    assert (
        not {"financial_snapshot", "terms", "roster", "correction_policy"}
        & row["content"].keys()
    )


@pytest.mark.parametrize("charge_minor", [0, 100])
def test_payer_sees_pending_and_applied_settlement_basis(
    returned_company, charge_minor
):
    actors, item = returned_company
    invoice = item.lease.invoices.get()
    attempt = invoice.payment_attempts.get(payment_status="captured")
    original_invoice = (
        invoice.revision,
        invoice.status,
        invoice.amount_minor,
        invoice.receipt_id,
    )
    deposit_minor = item.source_snapshot["deposit_minor"]
    lines, evidence = [], None
    if charge_minor:
        evidence = RentalEvidence.objects.create(
            lease=item.lease,
            uploader=actors["owner"],
            request_key=uuid.uuid4(),
            original_name="settlement-inspection.png",
            content_type="image/png",
            size_bytes=20,
            sha256="a" * 64,
            storage_key="private-settlement-evidence",
            malware_status="safe",
            media_metadata={"internal_note": "not-for-projection"},
        )
        lines = [
            {
                "id": "declared-cleaning-charge",
                "type": "cleaning",
                "description": "Agreed cleaning after the inspection",
                "amount": {
                    "amount_minor": charge_minor,
                    "currency": "EGP",
                    "exponent": 2,
                },
                "evidence_ids": [str(evidence.id)],
            }
        ]
    change = propose(actors, item, lines)
    decide_change(
        actors,
        item,
        change,
        [(role, actors[role]) for role in ("owner", "signer")],
    )
    pending = read(actors, item)
    row = change_row(pending, change)
    assert row["state"] == "pending" and row["roles_to_decide"] == ["payer"]
    assert row["reason"] == change.reason
    assert (
        row["digest"] == change.snapshot_digest and row["revision"] == change.revision
    )
    content = row["content"]
    assert content["kind_of_document"] == "summary"
    assert content["plan"]["rent_balance_minor"] == 0
    assert content["plan"]["deposit_to_return_minor"] == deposit_minor - charge_minor
    assert content["plan"]["refund_due_minor"] == 0
    assert content["plan"]["total_due_minor"] == -(deposit_minor - charge_minor)
    assert content["plan"]["refunds"] == [
        {
            "payment_attempt_id": str(attempt.id),
            "amount_minor": deposit_minor - charge_minor,
            "allocations": {"rent": 0, "deposit": deposit_minor - charge_minor},
        }
    ]
    if evidence:
        line = content["lines"][0]
        assert line["id"] == lines[0]["id"] and line["type"] == "cleaning"
        assert line["amount"] == lines[0]["amount"]
        assert line["description"] == lines[0]["description"]
        assert line["evidence_ids"] == [str(evidence.id)]
        assert line["evidence"][0]["id"] == str(evidence.id)
        assert line["evidence"][0]["lease_id"] == str(item.lease.id)
        assert line["evidence"][0]["status"] == "ready"
        assert "media_metadata" not in line["evidence"][0]
        assert "private-settlement-evidence" not in str(pending.data)
        assert "not-for-projection" not in str(pending.data)
        assert content["plan"]["deposit_applications"] == [
            {
                "invoice_id": "settlement_invoice",
                "amount_minor": charge_minor,
            }
        ]
    else:
        assert content["lines"] == []
        assert content["plan"]["charges"] == []
    assert_payer_private_fields_absent(pending.data, row)
    # The final decision is still an ordinary exact-digest HTTP command.
    response = act(
        item,
        actors["payer"],
        "respond_change",
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="payer",
        decision="accept",
    )
    assert response.status_code == 200, response.data
    assert response.data["resource"]["id"] == str(item.id)
    assert response.data["operation_receipt"]["subject_id"] == str(item.id)
    applied = read(actors, item)
    applied_row = change_row(applied, change)
    assert applied_row["state"] == "applied" and applied_row["roles_to_decide"] == []
    assert applied_row["reason"] == row["reason"]
    assert applied_row["content"] == content
    assert_payer_private_fields_absent(applied.data, applied_row)
    refund = item.lease.refund_requests.get()
    assert refund.amount_minor == deposit_minor - charge_minor
    assert str(refund.id) in {entry["id"] for entry in applied.data["refunds"]}
    invoice.refresh_from_db()
    assert (
        invoice.revision,
        invoice.status,
        invoice.amount_minor,
        invoice.receipt_id,
    ) == original_invoice
    assert invoice.payment_attempts.count() == 1


def test_settlement_projection_does_not_expand_other_roles(returned_company):
    actors, item = returned_company
    change = propose(actors, item)
    owner = change_row(read(actors, item, "owner", None), change)
    assert owner["reason"] == change.reason
    assert owner["content"]["plan"] == change.snapshot["content"]["plan"]
    assert "financial_snapshot" in owner["content"]
    signer = change_row(read(actors, item, "signer", "signer"), change)
    assert signer["content"]["plan"] == change.snapshot["content"]["plan"]
    for actor, role in [("coordinator", "coordinator"), ("employee", "employee")]:
        response = read(actors, item, actor, role)
        assert response.status_code == 200, response.data
        assert str(change.id) not in {row["id"] for row in response.data["changes"]}
        assert "refunds" not in response.data and "invoices" not in response.data
    for actor, role in [("coordinator", "admin"), ("approver", "approver")]:
        assert read(actors, item, actor, role).status_code == 404


def test_settlement_basis_requires_current_payer_and_exact_context(returned_company):
    actors, item = returned_company
    propose(actors, item)
    path = API + f"company-tenancies/{item.id}/"
    assert client(actors["payer"]).get(path).status_code == 404
    assert read(actors, item, "employee", "payer").status_code == 404
    foreign = client(actors["payer"], actors["company"], "payer")
    foreign.credentials(
        HTTP_X_SUKOON_COMPANY_ROLE="payer",
        HTTP_X_SUKOON_COMPANY_ID=str(uuid.uuid4()),
    )
    assert foreign.get(path).status_code == 404
    item.payer_mandate.state = "revoked"
    item.payer_mandate.save(update_fields=["state"])
    assert read(actors, item).status_code == 404


@pytest.mark.parametrize("unsafe", [True, False])
def test_settlement_rejects_unsafe_or_unrelated_evidence(returned_company, unsafe):
    actors, item = returned_company
    evidence = RentalEvidence.objects.create(
        lease=item.lease if unsafe else None,
        purpose="rental" if unsafe else "student",
        uploader=actors["owner"],
        request_key=uuid.uuid4(),
        original_name="excluded-inspection.png",
        content_type="image/png",
        size_bytes=20,
        sha256="b" * 64,
        storage_key="excluded-settlement-evidence",
        malware_status="unsafe" if unsafe else "safe",
    )
    response = act(
        item,
        actors["owner"],
        "settlement",
        reason="Rejected synthetic evidence",
        lines=[
            {
                "type": "cleaning",
                "description": "Unsupported evidence",
                "amount": {"amount_minor": 100, "currency": "EGP", "exponent": 2},
                "evidence_ids": [str(evidence.id)],
            }
        ],
    )
    assert response.status_code == 400, response.data
    assert not item.changes.filter(kind="settlement").exists()
