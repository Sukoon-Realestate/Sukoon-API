import json

import pytest
from django.core.management import CommandError, call_command

from core_apps.features.models import (
    Lease,
    OwnerPaymentProfile,
    PaymentAttempt,
    RentInvoice,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "runtime,enabled", [("production", True), ("development", False)]
)
def test_rental_device_fixture_requires_explicit_local_mode(
    settings, tmp_path, runtime, enabled
):
    settings.RENTAL_RUNTIME_ENVIRONMENT = runtime
    settings.OWNER_TENANT_QA_ENABLED = enabled
    output = tmp_path / "fixture.json"
    with pytest.raises(CommandError):
        call_command("prepare_rental_device_qa", output=str(output))
    assert not output.exists()
    assert not Lease.objects.exists()


@pytest.mark.django_db
def test_rental_device_fixture_only_prepares_unsigned_unfunded_lease(
    settings, tmp_path
):
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.OWNER_TENANT_QA_ENABLED = True
    output = tmp_path / "fixture.json"
    call_command("prepare_rental_device_qa", output=str(output))
    fixture = json.loads(output.read_text())
    assert output.stat().st_mode & 0o777 == 0o600
    lease = Lease.objects.get(id=fixture["lease_id"])
    assert lease.status == Lease.Status.PENDING_SIGNATURES
    assert str(lease.owner.id) == fixture["actors"]["owner_a"]["id"]
    assert str(lease.tenant.id) == fixture["actors"]["tenant_a"]["id"]
    assert not RentInvoice.objects.exists()
    assert not PaymentAttempt.objects.exists()
    assert OwnerPaymentProfile.objects.get(owner_id=lease.owner_id).payout_ready
    assert not OwnerPaymentProfile.objects.get(
        owner__id=fixture["actors"]["owner_b"]["id"]
    ).payout_ready


@pytest.mark.django_db
def test_rental_device_fixture_rejects_remote_address(settings, tmp_path):
    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.OWNER_TENANT_QA_ENABLED = True
    with pytest.raises(CommandError):
        call_command(
            "prepare_rental_device_qa",
            output=str(tmp_path / "fixture.json"),
            base_url="http://production.example/api/v1/",
        )
    assert not Lease.objects.exists()
