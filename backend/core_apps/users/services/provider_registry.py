"""Validate inherited OAuth provider names before invoking provider adapters."""
from django.conf import settings
from rest_framework.exceptions import NotFound
from social_core.backends.utils import get_backend
from social_core.exceptions import AuthConfigurationError


def require_supported_provider(name):
    try:
        return get_backend(settings.AUTHENTICATION_BACKENDS, name)
    except AuthConfigurationError as error:
        if error.code != "backend_missing":
            raise
        raise NotFound("Unknown authentication provider.") from error
