from datetime import date, timedelta
import uuid
import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient
from core_apps.features.tests.test_rental_phase6 import (
    phase6_lease,
    client_for,
    accepted_zero_settlement,
)
from core_apps.features.tests.test_rental_phase2 import agreement_terms
from core_apps.features.rental_serializers import RentalTermsSerializer
from core_apps.features.services.cycle_permissions import cycle_actions
from core_apps.features.services.rental_phase3_parts.issue_invoice import (
    generate_billing_schedule,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.models import Lease
from core_apps.common.idempotency import resolve_or_close
from core_apps.features.services.settlements_parts.prepare_settlement import (
    prepare_settlement,
)

pytestmark = pytest.mark.django_db


def test_unsupported_deposit_custody_and_anchor_rejected_before_signing():
    terms = agreement_terms(date(2028, 1, 31), date(2028, 4, 30))
    assert RentalTermsSerializer(data=terms).is_valid()
    serializer = RentalTermsSerializer(data={**terms, "deposit_holder": "owner"})
    assert not serializer.is_valid() and "deposit_holder" in serializer.errors
    serializer = RentalTermsSerializer(data={**terms, "billing_anchor_day": 15})
    assert not serializer.is_valid() and "billing_anchor_day" in serializer.errors


def test_anniversary_schedule_handles_february_without_drifting(phase6_lease):
    _, _, lease = phase6_lease
    lease.start_date, lease.end_date = date(2028, 1, 31), date(2028, 4, 30)
    lease.status = Lease.Status.SIGNED
    lease.hold_expires_at = timezone.now() + timedelta(hours=1)
    lease.terms = agreement_terms(lease.start_date, lease.end_date)
    lease.save()
    with transaction.atomic():
        periods = list(generate_billing_schedule(lease).order_by("sequence"))
    assert [(p.start, p.end_exclusive) for p in periods] == [
        (date(2028, 1, 31), date(2028, 2, 29)),
        (date(2028, 2, 29), date(2028, 3, 31)),
        (date(2028, 3, 31), date(2028, 4, 30)),
    ]


def test_settlement_entry_and_empty_settlement_follow_server_preconditions(
    phase6_lease,
):
    owner, tenant, lease = phase6_lease
    lease.status, lease.occupancy_status = "active", "occupied"
    lease.save()
    assert "propose_settlement" not in cycle_actions(owner, lease)
    response = client_for(owner).get(
        f"/api/v1/features/v1/leases/{lease.id}/final-settlement/"
    )
    assert response.data["blocking_reasons"]
    lease.status, lease.occupancy_status = "ended", "returned"
    lease.save()
    assert "propose_settlement" in cycle_actions(owner, lease)
    accepted_zero_settlement(owner, tenant, lease)
    assert lease.final_settlement.status == "accepted"


def test_public_put_is_unavailable_and_property_recovery_fences_late_patch(
    phase6_lease,
):
    owner, _, lease = phase6_lease
    prop = lease.property
    endpoint = f"/api/v1/properties/{prop.id}/"
    assert (
        APIClient().put(endpoint, {"title": "Unauthorized"}, format="json").status_code
        == 405
    )
    key = str(uuid.uuid4())
    recovery = client_for(owner).post(
        "/api/v1/properties/operation-recovery/",
        {"kind": "update", "property_id": str(prop.id).upper()},
        format="json",
        HTTP_IDEMPOTENCY_KEY=key,
    )
    assert recovery.status_code == 200 and recovery.data["outcome"] == "absent_final"
    late = client_for(owner).patch(
        endpoint, {"title": "Late change"}, format="json", HTTP_IDEMPOTENCY_KEY=key
    )
    assert late.status_code == 409
    prop.refresh_from_db()
    assert prop.title == "P6 Home"


def test_legacy_owner_held_deposit_requires_reconciliation_before_settlement(
    phase6_lease,
):
    owner, _, lease = phase6_lease
    lease.terms = {
        **lease.terms,
        "deposit_holder": "owner",
        "deposit": {"amount_minor": 1000, "currency": "EGP", "exponent": 2},
    }
    lease.save()
    assert "propose_settlement" not in cycle_actions(owner, lease)
    with pytest.raises(RentalConflict) as error:
        prepare_settlement(lease, [])
    assert error.value.get_codes() == "deposit_custody_review_required"
