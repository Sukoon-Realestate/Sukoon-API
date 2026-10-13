"""Social auth service: authenticate apple."""

import requests as http_requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
from core_apps.users.models import SocialAccount
from .get_or_create_social_user import (
    logger,
    get_or_create_social_user,
    _apple_jwks_cache,
    _dev_apple_jwks,
)


def _get_apple_jwks() -> dict:
    """Fetch Apple's public JWKS, cached in-process for the lifetime of the worker."""
    global _apple_jwks_cache
    if _apple_jwks_cache is not None:
        return _apple_jwks_cache

    dev_jwks = _dev_apple_jwks()
    if dev_jwks is not None:
        logger.error(
            "APPLE_DEV_PRIVATE_KEY_PATH is set — Apple tokens are being verified against a "
            "LOCAL DEV KEY, not Apple. Anyone can forge a login. Never use this on a server."
        )
        _apple_jwks_cache = dev_jwks
        return _apple_jwks_cache

    try:
        response = http_requests.get(
            "https://appleid.apple.com/auth/keys",
            timeout=5,
        )
        response.raise_for_status()
        _apple_jwks_cache = response.json()
        return _apple_jwks_cache
    except Exception as exc:
        logger.error("Failed to fetch Apple JWKS: %s", exc)
        raise ValidationError("Social provider is unavailable.")


def _verify_apple(identity_token: str) -> dict:
    """Return verified Apple identity token claims."""
    if not settings.APPLE_CLIENT_IDS:
        logger.error("APPLE_CLIENT_IDS is not configured")
        raise ValidationError("Social provider is unavailable.")

    import jwt
    from jwt.algorithms import RSAAlgorithm

    try:
        header = jwt.get_unverified_header(identity_token)
    except jwt.PyJWTError as exc:
        logger.warning("Apple token header decode failed: %s", exc)
        raise ValidationError("Apple token is invalid or expired.")

    jwks = _get_apple_jwks()
    kid = header.get("kid")
    key_data = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key_data is None:
        logger.warning("Apple token kid %r not found in JWKS", kid)
        raise ValidationError("Apple token is invalid or expired.")

    public_key = RSAAlgorithm.from_jwk(key_data)

    last_error = None
    for aud in settings.APPLE_CLIENT_IDS:
        try:
            claims = jwt.decode(
                identity_token,
                public_key,
                algorithms=["RS256"],
                audience=aud,
                issuer="https://appleid.apple.com",
            )
            return claims
        except jwt.PyJWTError as exc:
            last_error = exc

    logger.warning("Apple identity token verification failed: %s", last_error)
    raise ValidationError("Apple token is invalid or expired.")


def authenticate_apple(identity_token: str, first_name: str = "", last_name: str = ""):
    """Verify an Apple identity token and return a linked, verified User.

    first_name / last_name only come from the mobile client on the user's very first
    Apple authorization.
    """
    claims = _verify_apple(identity_token)
    email = claims.get("email", "")
    # ? Apple sends email_verified as the string "true" or the boolean True
    email_verified = str(claims.get("email_verified", "false")).lower() == "true"
    return get_or_create_social_user(
        provider=SocialAccount.PROVIDER_APPLE,
        provider_uid=claims["sub"],
        email=email,
        email_verified=email_verified,
        first_name=first_name,
        last_name=last_name,
    )
