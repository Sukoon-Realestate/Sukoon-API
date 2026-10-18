"""Historical classification must preserve valid work before signing."""

from io import StringIO

import pytest
from django.core.management import call_command

from core_apps.features.models import Lease
from .test_rental_phase6 import phase6_lease


@pytest.mark.django_db
def test_unsigned_structured_draft_is_not_classified_as_unsupported(phase6_lease):
    _, _, lease = phase6_lease
    lease.status = Lease.Status.DRAFT
    lease.occupancy_status = Lease.OccupancyStatus.NOT_STARTED
    lease.save()
    assert lease.document_id is None
    assert not lease.document_hash
    original_revision = lease.revision

    output = StringIO()
    call_command("reconcile_legacy_rentals", apply=True, stdout=output)

    lease.refresh_from_db()
    assert lease.legacy_read_only is False
    assert lease.revision == original_revision
    assert "would_classify=0" in output.getvalue()


@pytest.mark.django_db
def test_historical_classification_is_explicit_scoped_and_idempotent(phase6_lease):
    _, _, lease = phase6_lease
    original = (
        lease.revision,
        lease.rent_amount_minor,
        lease.status,
        lease.occupancy_status,
    )
    output = StringIO()
    call_command("reconcile_legacy_rentals", lease_id=lease.id, stdout=output)
    lease.refresh_from_db()
    assert lease.legacy_read_only is False
    assert "classified=0 would_classify=1" in output.getvalue()

    call_command(
        "reconcile_legacy_rentals", lease_id=lease.id, apply=True, stdout=StringIO()
    )
    lease.refresh_from_db()
    assert lease.legacy_read_only is True
    assert (
        lease.revision,
        lease.rent_amount_minor,
        lease.status,
        lease.occupancy_status,
    ) == (original[0] + 1, *original[1:])
    call_command(
        "reconcile_legacy_rentals", lease_id=lease.id, apply=True, stdout=StringIO()
    )
    lease.refresh_from_db()
    assert lease.revision == original[0] + 1


@pytest.mark.django_db
def test_malformed_historical_terms_do_not_abort_classification(phase6_lease):
    _, _, lease = phase6_lease
    lease.terms = ["invalid historical shape"]
    lease.save(update_fields=["terms"])
    call_command("reconcile_legacy_rentals", apply=True, stdout=StringIO())
    lease.refresh_from_db()
    assert lease.legacy_read_only is True
    assert lease.terms == ["invalid historical shape"]
