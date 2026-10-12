"""Explicit staging settings; no fake provider or automatic financial grants."""

from .production import *  # noqa: F401,F403

DEBUG = False
RENTAL_RUNTIME_ENVIRONMENT = "staging"
OWNER_TENANT_QA_ENABLED = True
