"""Opt-in HTTPS acceptance environment. Does not change existing deployment settings.

Use only with a dedicated staging host. HSTS policy and proxy trust must be
configured for that host; provider/device checks remain separate release gates.
"""

from os import getenv
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .staging import *  # noqa: F401,F403
from .staging import ALLOWED_HOSTS, COOKIE_TRUSTED_ORIGINS

if not ALLOWED_HOSTS or any(not host.strip() or "*" in host or host.strip().startswith(".") for host in ALLOWED_HOSTS):
    raise ImproperlyConfigured("Acceptance requires explicit isolated staging ALLOWED_HOSTS.")
if not COOKIE_TRUSTED_ORIGINS:
    raise ImproperlyConfigured("Acceptance requires explicit HTTPS COOKIE_TRUSTED_ORIGINS.")
for origin in COOKIE_TRUSTED_ORIGINS:
    try:
        parsed = urlsplit(origin)
        port = parsed.port
    except ValueError as error:
        raise ImproperlyConfigured("Acceptance cookie origins require a valid HTTPS host and port.") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or "*" in parsed.hostname
        or any(character.isspace() for character in origin)
        or port == 0
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ImproperlyConfigured("Acceptance cookie origins must be complete HTTPS origins.")
try:
    SECURE_HSTS_SECONDS = int(getenv("STAGING_HSTS_SECONDS", ""))
    if not 1 <= SECURE_HSTS_SECONDS <= 31536000:
        raise ValueError
except ValueError as error:
    raise ImproperlyConfigured(
        "Set STAGING_HSTS_SECONDS after verifying HTTPS on the isolated staging host."
    ) from error

_proxy = getenv("STAGING_TRUST_HTTPS_PROXY", "false").lower()
if _proxy not in {"true", "false"}:
    raise ImproperlyConfigured("STAGING_TRUST_HTTPS_PROXY must be true or false.")
# Enable only where the trusted ingress strips client-supplied forwarding headers.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if _proxy == "true" else None
SECURE_SSL_REDIRECT = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = COOKIE_TRUSTED_ORIGINS
COOKIE_SECURE = True
COOKIE_HTTPONLY = True
