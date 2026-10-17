from io import StringIO
import pytest
from django.core.management import call_command, CommandError
from config.advanced_housing import POLICY_VERSION
from core_apps.features.models import RentalCommercialPolicy


@pytest.mark.django_db
def test_mock_policy_install_is_explicit_versioned_and_idempotent(settings):
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "disabled"
    with pytest.raises(CommandError):
        call_command("configure_advanced_mock", stdout=StringIO())
    assert not RentalCommercialPolicy.objects.filter(version=POLICY_VERSION).exists()
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "mock"
    call_command("configure_advanced_mock", stdout=StringIO())
    policy = RentalCommercialPolicy.objects.get(version=POLICY_VERSION)
    first = dict(policy.lifecycle_rules)
    call_command("configure_advanced_mock", stdout=StringIO())
    assert RentalCommercialPolicy.objects.filter(version=POLICY_VERSION).count() == 1
    policy.refresh_from_db()
    assert policy.lifecycle_rules == first
    assert first["turnover_days"] == 1 and first["hold_minutes"] == 30
    policy.lifecycle_rules = {**first, "hold_minutes": 5}
    policy.save()
    with pytest.raises(CommandError):
        call_command("configure_advanced_mock", stdout=StringIO())
    policy.refresh_from_db()
    assert policy.lifecycle_rules["hold_minutes"] == 5


@pytest.mark.django_db
def test_recovery_commands_are_bounded_and_safe_on_empty_queues():
    output = StringIO()
    call_command("process_advanced_housing_jobs", limit=0, stdout=output)
    assert "Reviewed 0 queued jobs" in output.getvalue()
