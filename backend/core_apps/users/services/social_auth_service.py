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
    _get_user_model,
    get_or_create_social_user,
    _verify_google,
    authenticate_google,
    _verify_facebook,
    authenticate_facebook,
    _apple_jwks_cache,
    _dev_apple_jwks,
)
from .social_auth_service_parts.authenticate_apple import (
    _get_apple_jwks,
    _verify_apple,
    authenticate_apple,
)
