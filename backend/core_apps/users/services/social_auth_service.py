import logging
from typing import Optional
import requests as http_requests
from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError

from core_apps.users.models import SocialAccount

logger = logging.getLogger(__name__)

User = None  # resolved lazily via get_user_model() to avoid import cycles


def _get_user_model():
    global User
    if User is None:
        from django.contrib.auth import get_user_model

        User = get_user_model()
    return User


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def authenticate_google(token: str):
    """Verify a Google ID token and return a linked, verified User.

    Raises ValidationError on bad/expired token.
    """
    claims = _verify_google(token)
    return get_or_create_social_user(
        provider=SocialAccount.PROVIDER_GOOGLE,
        provider_uid=claims["sub"],
        email=claims.get("email", ""),
        email_verified=claims.get("email_verified", False),
        first_name=claims.get("given_name", ""),
        last_name=claims.get("family_name", ""),
    )


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


def authenticate_facebook(token: str):
    """Verify a Facebook access token and return a linked, verified User.

    Raises ValidationError on bad/expired token.
    """
    claims = _verify_facebook(token)
    email = claims.get("email", "")
    # If Facebook returns an email, we assume it is verified.
    email_verified = bool(email)
    return get_or_create_social_user(
        provider=SocialAccount.PROVIDER_FACEBOOK,
        provider_uid=claims["id"],
        email=email,
        email_verified=email_verified,
        first_name=claims.get("first_name", ""),
        last_name=claims.get("last_name", ""),
    )


# ---------------------------------------------------------------------------
# Core find-or-create logic
# ---------------------------------------------------------------------------


@transaction.atomic
def get_or_create_social_user(
    *,
    provider: str,
    provider_uid: str,
    email: str,
    email_verified: bool,
    first_name: str,
    last_name: str
):
    """Find or create a User for the given social identity.

    Lookup order:
    1. Existing SocialAccount row.
    2. Existing User with the same verified email → auto-link.
    3. Create a new User.
    """
    UserModel = _get_user_model()

    try:
        social = SocialAccount.objects.select_related("user").get(
            provider=provider, provider_uid=provider_uid
        )
        return social.user
    except SocialAccount.DoesNotExist:
        pass

    if email and email_verified:
        email = email.lower().strip()
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            user = UserModel.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=None,
                is_active=True,
            )
        SocialAccount.objects.create(
            user=user,
            provider=provider,
            provider_uid=provider_uid,
            email=email,
        )
        return user

    # No email and no existing SocialAccount — cannot resolve identity.
    raise ValidationError("Social email is unavailable.")


# ---------------------------------------------------------------------------
# Provider verification
# ---------------------------------------------------------------------------


def _verify_google(token: str) -> dict:
    """Return verified Google ID token claims."""
    if not settings.GOOGLE_CLIENT_IDS:
        logger.error("GOOGLE_CLIENT_IDS is not configured")
        raise ValidationError("Social provider is unavailable.")

    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests

    last_error = None
    for client_id in settings.GOOGLE_CLIENT_IDS:
        try:
            claims = google_id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                audience=client_id,
            )
            return claims
        except ValueError as exc:
            last_error = exc

    logger.warning("Google ID token verification failed: %s", last_error)
    raise ValidationError("Google token is invalid or expired.")


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


def _verify_facebook(token: str) -> dict:
    """Return verified Facebook profile claims from Graph API."""
    try:
        response = http_requests.get(
            "https://graph.facebook.com/v19.0/me",
            params={
                "fields": "id,email,first_name,last_name",
                "access_token": token,
            },
            timeout=5,
        )
        if response.status_code != 200:
            logger.warning("Facebook token verification failed: %s", response.text)
            raise ValidationError("Facebook token is invalid or expired.")
        return response.json()
    except Exception as exc:
        logger.error("Facebook API connection error: %s", exc)
        raise ValidationError("Failed to verify Facebook token.")


_apple_jwks_cache: Optional[dict] = None


def _dev_apple_jwks() -> Optional[dict]:
    """Publish the local dev keypair in place of Apple's JWKS. Development only."""
    if not settings.APPLE_DEV_PRIVATE_KEY_PATH:
        return None

    from core_apps.users.services.apple_dev_key import build_dev_jwks, load_dev_key

    private_key = load_dev_key(settings.APPLE_DEV_PRIVATE_KEY_PATH)
    if private_key is None:
        logger.error(
            "APPLE_DEV_PRIVATE_KEY_PATH=%s is set but no key file exists there. Ignoring it and "
            "using Apple's real JWKS. If this is a server, UNSET the variable.",
            settings.APPLE_DEV_PRIVATE_KEY_PATH,
        )
        return None

    return build_dev_jwks(private_key)


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
