"""Removing a recovery gate must not activate old staging simulation settings."""

import pytest
from django.core.exceptions import ImproperlyConfigured
from config.rental_simulation import enabled_from_env
from core_apps.features.providers import (
    fake_provider_available,
    checkout_available,
    get_rental_provider,
)


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, False),
        ("false", False),
        ("true", True),
        ("TRUE", True),
        ("1", False),
        ("yes", False),
    ],
)
def test_staging_simulation_requires_explicit_opt_in(settings, value, expected):
    env = {} if value is None else {"RENTAL_STAGING_SIMULATION_ENABLED": value}
    settings.RENTAL_PROVIDER_BACKEND = "fake"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "staging"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = enabled_from_env(env)
    settings.RENTAL_CHECKOUT_ENABLED = expected
    assert fake_provider_available() is expected
    assert checkout_available() is expected
    if not expected:
        with pytest.raises(ImproperlyConfigured):
            get_rental_provider()


def test_opt_in_does_not_authorize_fake_provider_in_production(settings):
    settings.RENTAL_PROVIDER_BACKEND = "fake"
    settings.RENTAL_RUNTIME_ENVIRONMENT = "production"
    settings.RENTAL_FAKE_PROVIDER_ALLOWED = enabled_from_env(
        {"RENTAL_STAGING_SIMULATION_ENABLED": "true"}
    )
    assert not fake_provider_available()
