import pytest
from django.core.management import call_command, CommandError
from core_apps.features.models import SubscriptionPlan


@pytest.mark.django_db
@pytest.mark.parametrize("runtime,enabled", [("production", True), ("development", False)])
def test_qa_seed_refuses_nonlocal_configuration(settings, tmp_path, runtime, enabled):
    settings.RENTAL_RUNTIME_ENVIRONMENT = runtime
    settings.OWNER_TENANT_QA_ENABLED = enabled
    output = tmp_path / "fixture.json"
    with pytest.raises(CommandError):
        call_command("prepare_billing_qa", output=str(output))
    assert not output.exists()
    assert not SubscriptionPlan.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize("url", ["https://production.example/api/v1/", "file://127.0.0.1/api/v1/"])
def test_qa_seed_refuses_remote_or_non_http_api(tmp_path, url):
    output = tmp_path / "fixture.json"
    with pytest.raises(CommandError):
        call_command("prepare_billing_qa", output=str(output), base_url=url)
    assert not output.exists()
    assert not SubscriptionPlan.objects.exists()
