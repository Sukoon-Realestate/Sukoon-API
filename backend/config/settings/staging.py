"""Explicit staging settings; no fake provider or automatic financial grants."""

from os import getenv

from .production import *  # noqa: F401,F403

DEBUG = False
RENTAL_RUNTIME_ENVIRONMENT = "staging"
OWNER_TENANT_QA_ENABLED = True

# QA builds use the same server-authoritative route for every purchase.
COMMERCE_HOSTED_SANDBOX_ENABLED = getenv("COMMERCE_HOSTED_SANDBOX_ENABLED", "true").lower() in {"true", "1", "yes"}
