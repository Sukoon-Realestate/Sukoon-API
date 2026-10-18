"""Changes cannot bypass the already approved structured-term contract."""

from datetime import timedelta
import uuid

import pytest
from django.utils import timezone

from core_apps.features.models import RentalChange, RentalOperationalCase
from core_apps.features.tasks import process_rental_changes
from .test_rental_phase2 import agreement_terms
from .test_rental_phase5 import phase5_lease, client_for


def command(revision=0, **values):
    return {"request_key": str(uuid.uuid4()), "expected_revision": revision, **values}


@pytest.mark.django_db
@pytest.mark.parametrize("invalid", ["billing_anchor", "deposit_custody"])
def test_renewal_rejects_unsupported_terms_before_consent(phase5_lease, invalid):
    owner, _, lease = phase5_lease
    terms = agreement_terms(lease.end_date, lease.end_date + timedelta(days=35))
    if invalid == "billing_anchor":
        terms["billing_anchor_day"] = 15
    else:
        terms["deposit_holder"] = "owner"
    response = client_for(owner).post(
        f"/api/v1/features/v1/leases/{lease.id}/renewals/",
        command(
            lease_revision=lease.revision, terms=terms, effective_on=str(lease.end_date)
        ),
        format="json",
    )
    assert response.status_code == 400, response.data
    assert not lease.rental_changes.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("stage", ["accept", "submit_for_signature"])
def test_historical_invalid_terms_cannot_gain_new_consent(phase5_lease, stage):
    owner, tenant, lease = phase5_lease
    terms = agreement_terms(lease.end_date, lease.end_date + timedelta(days=35))
    terms["billing_anchor_day"] = 15
    item = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind=RentalChange.Kind.RENEWAL,
        status=(
            RentalChange.Status.PROPOSED
            if stage == "accept"
            else RentalChange.Status.ACCEPTED
        ),
        terms=terms,
        approvals=[str(owner.id)],
        effective_on=lease.end_date,
    )
    endpoint = "respond" if stage == "accept" else "submit-for-signature"
    actor = tenant if stage == "accept" else owner
    response = client_for(actor).post(
        f"/api/v1/features/v1/renewals/{item.id}/{endpoint}/",
        command(item.revision, action=stage),
        format="json",
    )
    assert response.status_code == 400, response.data
    item.refresh_from_db()
    assert item.document_id is None
    assert item.approvals == [str(owner.id)]
    detail = client_for(actor).get(f"/api/v1/features/v1/renewals/{item.id}/")
    assert detail.status_code == 200
    assert detail.data["blocking_reasons"]
    assert "accept" not in detail.data["allowed_actions"]
    assert "submit_for_signature" not in detail.data["allowed_actions"]


@pytest.mark.django_db
def test_invalid_signed_change_is_preserved_and_does_not_stop_other_work(phase5_lease):
    owner, _, lease = phase5_lease
    today = timezone.localdate()
    lease.end_date = today
    lease.save(update_fields=["end_date"])
    valid_terms = agreement_terms(lease.start_date, today)
    valid = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind=RentalChange.Kind.AMENDMENT,
        status=RentalChange.Status.SIGNED,
        terms=valid_terms,
        effective_on=today,
        document_id=uuid.uuid4(),
        document_hash="a" * 64,
    )
    invalid_terms = agreement_terms(today, today + timedelta(days=35))
    invalid_terms["billing_anchor_day"] = 1 if today.day != 1 else 2
    invalid = RentalChange.objects.create(
        lease=lease,
        requester=owner,
        kind=RentalChange.Kind.RENEWAL,
        status=RentalChange.Status.SIGNED,
        terms=invalid_terms,
        effective_on=today,
        document_id=uuid.uuid4(),
        document_hash="b" * 64,
    )
    assert process_rental_changes()["applied"] == 1
    assert process_rental_changes()["applied"] == 0
    valid.refresh_from_db()
    invalid.refresh_from_db()
    assert valid.status == RentalChange.Status.APPLIED
    assert invalid.status == RentalChange.Status.SIGNED
    assert invalid.terms == invalid_terms and invalid.result_lease_id is None
    assert (
        RentalOperationalCase.objects.filter(
            kind="agreement_terms_review", lease=lease
        ).count()
        == 1
    )
    from .test_rental_lifecycle_safety import operator, post
    from core_apps.features.services.rental_lifecycle.cases import case_payload

    reviewer = operator("support")
    case = RentalOperationalCase.objects.get(kind="agreement_terms_review", lease=lease)
    case.assigned_to = reviewer
    case.save(update_fields=["assigned_to"])
    projection = case_payload(case, reviewer)
    assert (
        projection["blocking_reasons"]
        and "resolve" not in projection["allowed_actions"]
    )
    response = post(
        reviewer,
        f"rental-cases/{case.id}/actions/",
        command(
            case.revision,
            action="resolve",
            resolution_code="no_action_required",
            reason="Administrative closure cannot repair signed terms",
        ),
    )
    assert response.status_code == 409, response.data
    case.refresh_from_db()
    assert case.status == "open"
