"""Explicit hosted simulation profile. Use a separate database from real rentals.

This keeps staging security and environment configuration while enabling only
authenticated mock provider operations. No external provider is contacted.
"""

from os import getenv
from .staging import *  # noqa: F401,F403
from config.advanced_housing import POLICY_VERSION, enabled_services_from_env

DEBUG = False
ADVANCED_HOUSING_PROVIDER_MODE = getenv("ADVANCED_HOUSING_PROVIDER_MODE", "mock")
ADVANCED_HOUSING_ENABLED_SERVICES = enabled_services_from_env(
    getenv("ADVANCED_HOUSING_ENABLED_SERVICES", "all")
)
RENTAL_PROVIDER_BACKEND = "fake"
RENTAL_FAKE_PROVIDER_ALLOWED = True
RENTAL_RUNTIME_ENVIRONMENT = "staging"
RENTAL_CHECKOUT_ENABLED = True
RENTAL_FAKE_AUTO_CAPTURE = False
RENTAL_CHECKOUT_ALLOWED_ORIGINS = ["https://fake-rental-provider.test"]
RENTAL_CHECKOUT_RETURN_URL = "https://fake-rental-provider.test/payments/return"
RENTAL_CHECKOUT_EXTERNAL_SCHEMES = []
RENTAL_LIFECYCLE_POLICY_VERSION = POLICY_VERSION
PLANNING_MOCK_DISCOVERY = True
COMPANY_HOUSING_ENABLED = True
CELERY_TASK_ALWAYS_EAGER = getenv("ADVANCED_MOCK_EAGER_JOBS", "true").lower() == "true"
CELERY_TASK_EAGER_PROPAGATES = True
