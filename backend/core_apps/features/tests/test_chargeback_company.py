"""Company budget and existing commitments survive chargeback resolution."""

import pytest
from django.db import transaction
from core_apps.features.tests.test_company_tenancy import (
    cycle,
    person,
    company_setup,
    rental_participants,
    policy,
    command,
    authenticated,
    API,
    agreement,
    signed_agreement,
    active_agreement,
    expose_unexpected_exceptions,
)
from core_apps.features.models import (
    Lease,
    FinalSettlement,
    OwnerPayable,
    RentalChargeback,
    CompanyBudgetReservation,
)
from core_apps.features.tests.test_rental_lifecycle_safety import event
from core_apps.features.tests.test_chargeback_resolution import (
    fact,
    restore,
    replacement,
)
from core_apps.features.services.rental_phase3 import process_provider_event
from core_apps.features.services.rental_phase6 import evaluate_financial_closure
from core_apps.features.services.rental_lifecycle.locks import lock_financial_lease


@pytest.mark.django_db
@pytest.mark.parametrize("resolution", ["restored", "replacement"])
def test_company_closed_chargeback_restoration_closes_without_inventory_or_second_payable(
    active_agreement,
    client,
    settings,
    resolution,
):
    actors, tenancy = active_agreement
    attempt = tenancy.lease.invoices.get().payment_attempts.get()
    process_provider_event(event(attempt, "settled"))
    Lease.objects.filter(pk=tenancy.lease_id).update(
        status="ended", occupancy_status="returned"
    )
    tenancy.lease.inventory_day_locks.all().delete()
    tenancy.lease.deposit_agreement.delete()
    OwnerPayable.objects.filter(lease=tenancy.lease).update(payout_status="succeeded")
    FinalSettlement.objects.create(
        lease=tenancy.lease, status="accepted", execution_status="executed"
    )
    with transaction.atomic():
        assert not evaluate_financial_closure(lock_financial_lease(tenancy.lease))
    reservation = CompanyBudgetReservation.objects.get(item=tenancy.preparation.booking)
    original_exposure = reservation.rent_minor, reservation.deposit_minor
    assert reservation.status == "released"
    process_provider_event(event(attempt, "chargeback"))
    reservation.refresh_from_db()
    assert reservation.status == "committed"
    item = RentalChargeback.objects.get(payment_attempt=attempt)
    employee = authenticated(actors["employee"]).get(
        API + f"company-tenancies/{tenancy.id}/"
    )
    payer = authenticated(actors["payer"]).get(API + f"company-tenancies/{tenancy.id}/")
    assert employee.status_code == payer.status_code == 200
    assert employee.data["chargebacks"] == []
    assert payer.data["chargebacks"][0]["id"] == str(item.id)
    assert payer.data["chargebacks"][0]["resolved"] is False
    outsider = person("other-company-chargeback-reader")
    for actor in (actors["employee"], actors["payer"], outsider):
        response = authenticated(actor).get(API + f"operator/chargebacks/{item.id}/")
        assert response.status_code == 403
    assert (
        authenticated(outsider)
        .get(API + f"company-tenancies/{tenancy.id}/")
        .status_code
        == 404
    )
    fact(item, "decided", outcome="won" if resolution == "restored" else "lost")
    if resolution == "restored":
        restore(item)
    else:
        paid = replacement(item)
        process_provider_event(event(paid, "captured"))
        process_provider_event(event(paid, "settled"))
    tenancy.lease.refresh_from_db()
    reservation.refresh_from_db()
    assert tenancy.lease.financial_closure_status == "closed"
    assert reservation.status == "released"
    assert (reservation.rent_minor, reservation.deposit_minor) == original_exposure
    assert not tenancy.lease.inventory_day_locks.exists()
    assert tenancy.lease.tenant_id is None and tenancy.lease.status == "ended"
    assert OwnerPayable.objects.filter(lease=tenancy.lease).count() == 1
    completed = authenticated(actors["payer"]).get(
        API + f"company-tenancies/{tenancy.id}/"
    )
    assert completed.data["chargebacks"][0]["resolved"] is True
    assert completed.data["chargebacks"][0]["remaining_funding_minor"] == 0
    from django.urls import reverse
    from core_apps.admin_api.models import StaffProfile

    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    payer = actors["payer"]
    payer.is_staff = True
    payer.save()
    StaffProfile.objects.create(user=payer, role_name="financial_approver")
    client.force_login(payer)
    assert (
        client.get(reverse("admin:chargeback-review", args=[item.pk])).status_code
        == 403
    )
    for row in [item, *item.restorations.all(), *item.replacement_payments.all()]:
        model = row._meta.model_name
        listing = client.get(reverse(f"admin:features_{model}_changelist"))
        assert (
            listing.status_code == 200 and str(item.id).encode() not in listing.content
        )
        assert client.get(
            reverse(f"admin:features_{model}_change", args=[row.pk])
        ).status_code in {302, 403, 404}
