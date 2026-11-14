"""Stable public imports for social auth service.

Implementation modules separate domain responsibilities without changing routes.
"""

import logging
from typing import Optional
import requests as http_requests
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError
from core_apps.users.models import SocialAccount

from .social_auth_service_parts.get_or_create_social_user import (
    logger,
    User,
    get_or_create_social_user,
    authenticate_google,
    authenticate_facebook,
)
# Supported private imports stay outside the public star-import surface.
from .social_auth_service_parts.get_or_create_social_user import (  # noqa: F401
    _get_user_model,
    _verify_google,
    _verify_facebook,
    _apple_jwks_cache,
    _dev_apple_jwks,
)
from .social_auth_service_parts.authenticate_apple import (
    authenticate_apple,
)
# Supported private imports stay outside the public star-import surface.
from .social_auth_service_parts.authenticate_apple import (  # noqa: F401
    _get_apple_jwks,
    _verify_apple,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'logging',
    'Optional',
    'http_requests',
    'settings',
    'transaction',
    'ValidationError',
    'SocialAccount',
    'logger',
    'User',
    'get_or_create_social_user',
    'authenticate_google',
    'authenticate_facebook',
    'authenticate_apple',
]
