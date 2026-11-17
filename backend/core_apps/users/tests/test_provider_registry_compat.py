"""Keep inherited OAuth validation and unknown-provider contracts after SDK updates."""
import pytest
from django.test import override_settings
from rest_framework.test import APIClient


@pytest.mark.parametrize('method,query,status', [
    ('get', '', 400),
    ('get', '?redirect_uri=https://client.example.test/callback', 404),
    ('post', '', 404),
])
@override_settings(DJOSER={'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': ['https://client.example.test/callback']})
def test_unknown_provider_preserves_validation_precedence(method, query, status):
    response = getattr(APIClient(), method)('/api/v1/auth/o/not-a-provider/' + query)
    assert response.status_code == status
    assert response['Cache-Control'] == 'private, no-store'
    assert response.json()['data'] is None


def test_provider_registry_does_not_mask_other_configuration_errors(monkeypatch):
    from core_apps.users.services import provider_registry
    from social_core.exceptions import AuthConfigurationError

    error = AuthConfigurationError(None, code='invalid_setting')

    def reject(*args):
        raise error

    monkeypatch.setattr(provider_registry, 'get_backend', reject)
    with pytest.raises(AuthConfigurationError) as caught:
        provider_registry.require_supported_provider('google-oauth2')
    assert caught.value is error
