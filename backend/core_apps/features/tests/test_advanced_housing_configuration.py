import pytest
from django.core.exceptions import ImproperlyConfigured
from config.advanced_housing import (
    PLANNING_SERVICES,
    PROVIDER_SERVICES,
    SERVICES,
    mock_mode_available,
    enabled_services_from_env,
)
from core_apps.features.services.planning import enabled_services
from core_apps.features.services.planning_providers import ready_services
from core_apps.common.response_messages import _extract_message


def test_advanced_execution_requires_explicit_mock_and_existing_provider(settings):
    assert enabled_services_from_env("none") == []
    assert set(enabled_services_from_env("all")) == set(SERVICES)
    with pytest.raises(ImproperlyConfigured):
        enabled_services_from_env("unknown_provider_capability")
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = list(SERVICES)
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "disabled"
    assert not set(PROVIDER_SERVICES) & set(ready_services(enabled_services()))
    settings.ADVANCED_HOUSING_PROVIDER_MODE = "mock"
    assert mock_mode_available()
    assert set(PROVIDER_SERVICES) <= set(ready_services(enabled_services()))
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    assert not mock_mode_available()
    assert not set(PROVIDER_SERVICES) & set(ready_services(enabled_services()))


@pytest.mark.parametrize(
    "message",
    [
        "Explicit matching consent is required.",
        "Choose one person, exact scope, dates, monthly rent and a budget.",
        "Use an integer within the supported range.",
    ],
)
def test_advanced_errors_follow_bilingual_response_contract(message):
    rendered = _extract_message({"criteria": message}, "ar")
    assert "متطلبات السكن" in rendered and message not in rendered
    assert _extract_message({"detail": message}, "en") == message
