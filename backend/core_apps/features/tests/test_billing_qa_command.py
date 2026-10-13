import pytest
import json
from django.core.management import call_command, CommandError
from core_apps.features.models import SubscriptionPlan


@pytest.mark.django_db
@pytest.mark.parametrize(
    "runtime,enabled", [("production", True), ("development", False)]
)
def test_qa_seed_refuses_nonlocal_configuration(settings, tmp_path, runtime, enabled):
    settings.RENTAL_RUNTIME_ENVIRONMENT = runtime
    settings.OWNER_TENANT_QA_ENABLED = enabled
    output = tmp_path / "fixture.json"
    with pytest.raises(CommandError):
        call_command("prepare_billing_qa", output=str(output))
    assert not output.exists()
    assert not SubscriptionPlan.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url", ["https://production.example/api/v1/", "file://127.0.0.1/api/v1/"]
)
def test_qa_seed_refuses_remote_or_non_http_api(tmp_path, url):
    output = tmp_path / "fixture.json"
    with pytest.raises(CommandError):
        call_command("prepare_billing_qa", output=str(output), base_url=url)
    assert not output.exists()
    assert not SubscriptionPlan.objects.exists()


@pytest.mark.django_db
def test_local_fixture_creates_only_unpaid_prerequisites(settings, tmp_path):
    from core_apps.advertising.models import Advertisement
    from core_apps.common.content_models import ReleaseNote
    from core_apps.features.models import RentInvoice, PaymentAttempt

    settings.RENTAL_RUNTIME_ENVIRONMENT = "test"
    settings.OWNER_TENANT_QA_ENABLED = True
    settings.MEDIA_ROOT = tmp_path / "media"
    output = tmp_path / "fixture.json"
    call_command("prepare_billing_qa", output=str(output))
    fixture = json.loads(output.read_text())
    assert output.stat().st_mode & 0o777 == 0o600
    ad = Advertisement.objects.get(id=fixture["advertisement_id"])
    assert str(ad.owner.id) == fixture["actors"]["owner"]["id"]
    assert ad.status == "pending_payment" and ad.activated_at is None
    assert ad.media.banner.storage.exists(ad.media.banner.name)
    assert ReleaseNote.objects.filter(version=fixture["release_version"]).exists()
    assert not RentInvoice.objects.exists()
    assert not PaymentAttempt.objects.exists()
