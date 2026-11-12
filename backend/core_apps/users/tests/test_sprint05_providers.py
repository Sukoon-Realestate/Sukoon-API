"""Real JWT crypto/claim validation against local keys; no live provider calls."""
from datetime import timedelta
import importlib
import json
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.utils import timezone
import jwt
from jwt.algorithms import RSAAlgorithm
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from core_apps.users.models import SocialAccount
from core_apps.users.services.sessions import issue_refresh, revoke_all, validate_session

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module")
def keys():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(private.public_key()))
    jwk["kid"] = "sprint05-local"
    pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, jwk, pem


@pytest.mark.parametrize("provider", ["google", "apple"])
@pytest.mark.parametrize("body_format", ["json", "multipart", "urlencoded"])
@pytest.mark.parametrize("mutation", [
    "valid", "audience", "issuer", "expired", "signature", "subject",
    "missing_issuer", "missing_expiry", "missing_issued_at",
])
def test_signed_provider_claims_link_without_restoring_revoked_sessions(
    user, settings, keys, provider, body_format, mutation,
):
    private, jwk, pem = keys
    settings.GOOGLE_CLIENT_IDS = ["sprint05-local-client"]
    settings.APPLE_CLIENT_IDS = ["sprint05-local-client"]
    old = issue_refresh(user)
    revoke_all(user)
    now = timezone.now()
    claims = {"sub": "sprint05-local-subject", "email": user.email, "email_verified": True,
              "iat": int(now.timestamp()), "exp": int((now + timedelta(minutes=5)).timestamp()),
              "aud": "sprint05-local-client",
              "iss": "https://appleid.apple.com" if provider == "apple" else "https://accounts.google.com"}
    if mutation == "audience":
        claims["aud"] = "other-client"
    elif mutation == "issuer":
        claims["iss"] = "https://untrusted.example.invalid"
    elif mutation == "expired":
        claims["exp"] = int((now - timedelta(minutes=5)).timestamp())
    if mutation == "subject":
        claims.pop("sub")
    for mutation_name, field in (("missing_issuer", "iss"), ("missing_expiry", "exp"), ("missing_issued_at", "iat")):
        if mutation == mutation_name:
            claims.pop(field)
    signing = private if mutation != "signature" else rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = jwt.encode(claims, signing, algorithm="RS256", headers={"kid": "sprint05-local"})
    apple = importlib.import_module("core_apps.users.services.social_auth_service_parts.authenticate_apple")
    client = APIClient()
    with patch("google.oauth2.id_token._fetch_certs", return_value={"sprint05-local": pem}), \
            patch.object(apple, "_get_apple_jwks", return_value={"keys": [jwk]}):
        payload = {"token": token}
        if body_format == "urlencoded":
            from urllib.parse import urlencode
            response = client.post(f"/api/v1/auth/{provider}/", urlencode(payload),
                                   content_type="application/x-www-form-urlencoded")
        else:
            response = client.post(f"/api/v1/auth/{provider}/", payload, format=body_format)
    user.refresh_from_db()
    with pytest.raises(AuthenticationFailed):
        validate_session(user, old)
    if mutation == "valid":
        assert response.status_code == 200, response.data
        current = AccessToken(response.cookies["access"].value)
        validate_session(user, current)
        assert current["security_epoch"] == user.security_epoch
        assert user.security_epoch >= 1
        assert user.is_email_verified and not user.is_verified
        assert SocialAccount.objects.filter(user=user, provider=provider).count() == 1
    else:
        assert response.status_code == 400, response.data
        assert not SocialAccount.objects.filter(user=user).exists()
        assert "access" not in response.cookies


def test_inherited_provider_strategy_uses_bound_issuer(user, api_client, settings):
    from djoser.conf import settings as djoser_settings
    from core_apps.users.services.sessions import revoke_all

    old = issue_refresh(user)
    user = revoke_all(user)
    with patch("djoser.social.serializers.ProviderAuthSerializer.validate", return_value={"user": user}):
        response = api_client.post("/api/v1/auth/o/google-oauth2/", {}, format="json")
    assert response.status_code == 201, response.data
    current = AccessToken(response.cookies["access"].value)
    validate_session(user, current)
    with pytest.raises(AuthenticationFailed):
        validate_session(user, old)
    assert djoser_settings.SOCIAL_AUTH_TOKEN_STRATEGY.__name__ == "BoundTokenStrategy"


@pytest.mark.parametrize("scenario", ["valid", "rejected", "timeout", "missing_subject"])
def test_facebook_provider_boundary_and_linking(user, scenario):
    from requests.exceptions import Timeout
    from unittest.mock import Mock

    old = issue_refresh(user)
    revoke_all(user)
    body = {"id": "local-facebook-subject", "email": user.email, "first_name": "Local", "last_name": "User"}
    if scenario == "missing_subject":
        body.pop("id")
    provider = Mock(status_code=401 if scenario == "rejected" else 200)
    provider.json.return_value = body
    client = APIClient()
    with patch("requests.get", side_effect=Timeout() if scenario == "timeout" else None,
               return_value=provider) as get:
        response = client.post("/api/v1/auth/facebook/", {"token": "local-only"}, format="json")
    assert get.call_count == 1 and get.call_args.kwargs["timeout"] == 5
    user.refresh_from_db()
    with pytest.raises(AuthenticationFailed):
        validate_session(user, old)
    if scenario == "valid":
        assert response.status_code == 200
        validate_session(user, AccessToken(response.cookies["access"].value))
        assert user.is_email_verified and not user.is_verified
    else:
        assert response.status_code == 400
        assert "access" not in response.cookies
