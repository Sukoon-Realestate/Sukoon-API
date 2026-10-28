from pathlib import Path
from os import getenv, path
from config.student_housing import enabled_from_env as student_services_from_env

from dotenv import load_dotenv
from datetime import timedelta
import ssl
import json

from config.planning import enabled_services_from_env
from config.advanced_housing import (
    enabled_services_from_env as advanced_services_from_env,
)

# todo refactor the code, write explaining comments

# ? Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

APPS_DIR = BASE_DIR / "core_apps"

local_env_file = path.join(BASE_DIR, ".envs", ".env.local")

if path.isfile(local_env_file):
    load_dotenv(local_env_file)

ADVANCED_HOUSING_ENABLED_SERVICES = advanced_services_from_env(
    getenv("ADVANCED_HOUSING_ENABLED_SERVICES", "none")
)
ADVANCED_HOUSING_PROVIDER_MODE = getenv("ADVANCED_HOUSING_PROVIDER_MODE", "disabled")
LIVING_LAB_MAX_PARTICIPANTS = 6
LIVING_LAB_MAX_ROOMS = 6
LIVING_LAB_MAX_RUNS_PER_LAB = 6
LIVING_LAB_MAX_RUNS_PER_GROUP_DAY = 12
LIVING_LAB_MAX_LABS_PER_GROUP_DAY = 8
LIVING_LAB_ACTIVE_DAYS = 14
LIVING_LAB_PRIVATE_RETENTION_DAYS = 30
LIVING_LAB_UNCOMMITTED_RETENTION_DAYS = 30
LIVING_LAB_MAX_SHARE_RATIO = 4

STUDENT_ENABLED_SERVICES = student_services_from_env(
    getenv("STUDENT_ENABLED_SERVICES", "none")
)

# New commitments may be stopped without removing historical company access.
COMPANY_HOUSING_ENABLED = getenv("COMPANY_HOUSING_ENABLED", "false").lower() == "true"
COMPANY_ACTIVATION_EMAIL_ENABLED = (
    getenv("COMPANY_ACTIVATION_EMAIL_ENABLED", "false").lower() == "true"
)

## Application definition

DJANGO_APPS = [
    "core_apps.common.admin_apps.SokounAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # ? allows to manage multiple domains within a single django project
]

LOCAL_APPS = [
    "core_apps.common",
    "core_apps.users",
    "core_apps.profiles",
    "core_apps.properties",
    "core_apps.notifications",
    "core_apps.chat",
    "core_apps.admin_api",
    "core_apps.support",
    "core_apps.features",
    "core_apps.advertising",
    "core_apps.virtual_tours",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "django_countries",
    "phonenumber_field",
    "drf_yasg",
    "djoser",
    "social_django",
    "taggit",
    "django_filters",
    "django_extensions",
    "cloudinary",
]

INSTALLED_APPS = (
    DJANGO_APPS
    + LOCAL_APPS
    + THIRD_PARTY_APPS
    + ["channels", "django.contrib.postgres"]
)

MIDDLEWARE = [
    "core_apps.common.runtime_metrics.RuntimeMetricsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "core_apps.common.locale_middleware.MobileLocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core_apps.features.services.company.role_context.CompanyRoleMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [str(APPS_DIR / "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# * ASGI / WebSockets (Django Channels)
ASGI_APPLICATION = "config.asgi.application"

# ? Redis backs the channel layer so WebSocket groups work across processes/workers
REDIS_URL = getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = getenv("CELERY_RESULT_BACKEND", REDIS_URL)
if CELERY_BROKER_URL.startswith("rediss://"):
    CELERY_BROKER_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
if CELERY_RESULT_BACKEND.startswith("rediss://"):
    CELERY_REDIS_BACKEND_USE_SSL = {"ssl_cert_reqs": ssl.CERT_REQUIRED}
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TIMEZONE = "Africa/Cairo"
CELERY_TASK_ALWAYS_EAGER = False
SOKOUN_RELEASE_SHA = getenv("SOKOUN_RELEASE_SHA", "")
RUNTIME_EVIDENCE_ENABLED = getenv("RUNTIME_EVIDENCE_ENABLED", "False").lower() == "true"
RUNTIME_EVIDENCE_NAMESPACE = getenv("RUNTIME_EVIDENCE_NAMESPACE", "sukoon")
CELERY_BEAT_SCHEDULE = {
    "deliver-security-notices": {
        "task": "core_apps.users.tasks.deliver_security_notices",
        "schedule": 60.0,
    },
    "rent-payment-notifications": {
        "task": "core_apps.features.tasks.process_rent_payment_notifications",
        "schedule": 300.0,
    },
    "expire-advertisements": {
        "task": "core_apps.advertising.tasks.expire_advertisements",
        "schedule": 300.0,
    },
    "expire-purchase-services": {
        "task": "core_apps.features.tasks.expire_purchase_services",
        "schedule": 300.0,
    },
    "expire-rental-sources-and-holds": {
        "task": "core_apps.features.tasks.expire_rental_sources_and_holds",
        "schedule": 300.0,
    },
    "reconcile-rental-provider-sessions": {
        "task": "core_apps.features.tasks.reconcile_rental_provider_sessions",
        "schedule": 300.0,
    },
    "run-rental-billing-cycle": {
        "task": "core_apps.features.tasks_parts.expire_rental_sources_and_holds.run_rental_billing_cycle",
        "schedule": 300.0,
    },
    "reconcile-ambiguous-rental-payments": {
        "task": "core_apps.features.tasks.reconcile_ambiguous_rental_payments",
        "schedule": 300.0,
    },
    "scan-rental-evidence": {
        "task": "core_apps.features.tasks.scan_rental_evidence",
        "schedule": 60.0,
    },
    "reconcile-approved-payouts": {
        "task": "core_apps.features.tasks.reconcile_approved_payouts",
        "schedule": 300.0,
    },
    "process-rental-changes": {
        "task": "core_apps.features.tasks.process_rental_changes",
        "schedule": 300.0,
    },
    "process-rental-closure": {
        "task": "core_apps.features.tasks.process_rental_closure",
        "schedule": 300.0,
    },
}

RENTAL_PROVIDER_BACKEND = getenv("RENTAL_PROVIDER_BACKEND", "disabled")
SIGNWELL_TEST_ENABLED = getenv("SIGNWELL_TEST_ENABLED", "false").lower() == "true"
SIGNWELL_API_KEY = getenv("SIGNWELL_API_KEY", "")
SIGNWELL_WEBHOOK_ID = getenv("SIGNWELL_WEBHOOK_ID", "")
RENTAL_RUNTIME_ENVIRONMENT = "production"
RENTAL_FAKE_PROVIDER_ALLOWED = False
OWNER_TENANT_QA_ENABLED = False
SHARED_HOUSING_ENABLED = getenv("SHARED_HOUSING_ENABLED", "false").lower() == "true"

PLANNING_ENABLED_SERVICES = enabled_services_from_env(
    getenv("PLANNING_ENABLED_SERVICES")
)
PLANNING_MOCK_DISCOVERY = False
CELERY_BEAT_SCHEDULE["process-planning-jobs"] = {
    "task": "core_apps.features.tasks.process_planning_jobs",
    "schedule": 30.0,
}
CELERY_BEAT_SCHEDULE["reconcile-signing-documents"] = {
    "task": "core_apps.features.tasks.reconcile_signing_documents",
    "schedule": 30.0,
}
CELERY_BEAT_SCHEDULE["reconcile-advanced-execution"] = {
    "task": "core_apps.features.tasks.reconcile_advanced_execution",
    "schedule": 30.0,
}
CELERY_BEAT_SCHEDULE["recover-advanced-housing-jobs"] = {
    "task": "advanced_housing.recover_jobs",
    "schedule": 300.0,
}
CELERY_BEAT_SCHEDULE["purge-advanced-private-inputs"] = {
    "task": "advanced_housing.purge_private_inputs",
    "schedule": 86400.0,
}
CELERY_BEAT_SCHEDULE["drain-group-chat-outbox"] = {
    "task": "core_apps.chat.tasks.drain_chat_outbox",
    "schedule": 5.0,
}
CELERY_BEAT_SCHEDULE["clean-group-chat-media"] = {
    "task": "core_apps.chat.tasks.clean_chat_media",
    "schedule": 3600.0,
}
CHAT_PRIVATE_MEDIA_ROOT = getenv(
    "CHAT_PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_chat_media")
)
CHAT_FFPROBE = getenv("CHAT_FFPROBE", "ffprobe")
VIRTUAL_TOUR_PRIVATE_ROOT = getenv(
    "VIRTUAL_TOUR_PRIVATE_ROOT", str(BASE_DIR / "private_virtual_tours")
)
VIRTUAL_TOUR_S3_BUCKET = getenv("VIRTUAL_TOUR_S3_BUCKET", "")
VIRTUAL_TOUR_S3_ENDPOINT = getenv("VIRTUAL_TOUR_S3_ENDPOINT", "")
VIRTUAL_TOUR_S3_REGION = getenv("VIRTUAL_TOUR_S3_REGION", "us-east-1")
VIRTUAL_TOUR_S3_PREFIX = getenv("VIRTUAL_TOUR_S3_PREFIX", "sokoun-virtual-tours")
VIRTUAL_TOUR_STORAGE_PROVIDER = getenv("VIRTUAL_TOUR_STORAGE_PROVIDER", "s3")
VIRTUAL_TOUR_CLOUDINARY_PREFIX = getenv(
    "VIRTUAL_TOUR_CLOUDINARY_PREFIX", "sokoun-virtual-tours"
)
# Reuse the explicitly configured private provider; local development stays local.
CHAT_PRIVATE_STORAGE_PROVIDER = getenv(
    "CHAT_PRIVATE_STORAGE_PROVIDER",
    "cloudinary" if VIRTUAL_TOUR_STORAGE_PROVIDER == "cloudinary" else "local",
)
CHAT_CLOUDINARY_PREFIX = getenv("CHAT_CLOUDINARY_PREFIX", "sokoun-chat-media")
VIRTUAL_TOUR_VIEWER_URL = getenv("VIRTUAL_TOUR_VIEWER_URL", "")
VIRTUAL_TOUR_VIEWER_ROOT = getenv(
    "VIRTUAL_TOUR_VIEWER_ROOT", str(BASE_DIR / "tour_viewer")
)
VIRTUAL_TOUR_PROCESSOR_MODE = getenv("VIRTUAL_TOUR_PROCESSOR_MODE", "celery")
PROPERTY_CAPTURE_ENABLED = getenv("PROPERTY_CAPTURE_ENABLED", "false").lower() == "true"
CAPTURE_RECONSTRUCTION_ENABLED = (
    getenv("CAPTURE_RECONSTRUCTION_ENABLED", "false").lower() == "true"
)
CAPTURE_RECONSTRUCTION_PYTHON = getenv("CAPTURE_RECONSTRUCTION_PYTHON", "").strip()
CAPTURE_RECONSTRUCTION_COLMAP = getenv("CAPTURE_RECONSTRUCTION_COLMAP", "").strip()
GEMINI_API_KEY = getenv("GEMINI_API_KEY", "").strip()
GEMINI_COACH_MODEL = getenv("GEMINI_COACH_MODEL", "gemini-3.8-live").strip()
COACH_DAILY_SESSION_LIMIT = int(getenv("COACH_DAILY_SESSION_LIMIT", "10"))
CAPTURE_MAX_SESSION_BYTES = int(getenv("CAPTURE_MAX_SESSION_BYTES", str(512 * 1024**2)))
CAPTURE_RETENTION_DAYS = int(getenv("CAPTURE_RETENTION_DAYS", "30"))
VIRTUAL_TOUR_PROCESSING_WIDTH = int(getenv("VIRTUAL_TOUR_PROCESSING_WIDTH", "8192"))
VIRTUAL_TOUR_KINDS = {
    kind: {
        action: getenv(f"VIRTUAL_TOUR_{prefix}_{action.upper()}", "false").lower()
        == "true"
        for action in ("read", "write")
    }
    for kind, prefix in (("panorama_360", "PANORAMA"), ("model_3d", "MODEL"))
}
VIRTUAL_TOUR_GLTF_VALIDATOR = getenv("VIRTUAL_TOUR_GLTF_VALIDATOR", "")
VIRTUAL_TOUR_SPAWN_VALIDATOR = getenv("VIRTUAL_TOUR_SPAWN_VALIDATOR", "")
CELERY_BEAT_SCHEDULE["clean-virtual-tours"] = {
    "task": "core_apps.virtual_tours.tasks.cleanup_tours",
    "schedule": 3600.0,
}
CELERY_BEAT_SCHEDULE["dispatch-virtual-tours"] = {
    "task": "core_apps.virtual_tours.tasks.dispatch_pending_tours",
    "schedule": 60.0,
}
CHAT_FFMPEG = getenv("CHAT_FFMPEG", "ffmpeg")
PLANNING_ROUTES_API_KEY = getenv("PLANNING_ROUTES_API_KEY", "").strip()
PLANNING_GEMINI_API_KEY = getenv("PLANNING_GEMINI_API_KEY", "").strip()
PLANNING_GEMINI_MODEL = getenv("PLANNING_GEMINI_MODEL", "").strip()
PLANNING_PROVIDER_TIMEOUT_SECONDS = int(
    getenv("PLANNING_PROVIDER_TIMEOUT_SECONDS", "20")
)
PLANNING_ROUTE_MODES = [
    x for x in getenv("PLANNING_ROUTE_MODES", "driving,walking,transit").split(",") if x
]
PLANNING_ROUTE_MAX_ORIGINS = int(getenv("PLANNING_ROUTE_MAX_ORIGINS", "1000"))
PLANNING_REQUEST_TTL_DAYS = int(getenv("PLANNING_REQUEST_TTL_DAYS", "30"))
PLANNING_PROVIDER_REQUESTS_PER_MINUTE = int(
    getenv("PLANNING_PROVIDER_REQUESTS_PER_MINUTE", "10")
)
PLANNING_MAX_LIVE_REQUESTS = int(getenv("PLANNING_MAX_LIVE_REQUESTS", "3"))
PLANNING_LEASE_REMINDER_DAYS = int(getenv("PLANNING_LEASE_REMINDER_DAYS", "30"))
PLANNING_OWNER_OFFERS_PER_REQUEST_PER_DAY = int(
    getenv("PLANNING_OWNER_OFFERS_PER_REQUEST_PER_DAY", "5")
)
RENTAL_ONBOARDING_TTL_MINUTES = int(getenv("RENTAL_ONBOARDING_TTL_MINUTES", "30"))
RENTAL_SIGNING_TTL_MINUTES = int(getenv("RENTAL_SIGNING_TTL_MINUTES", "30"))
RENTAL_HOLD_TTL_MINUTES = int(getenv("RENTAL_HOLD_TTL_MINUTES", "30"))
# Unset until a reviewed commercial policy supplies lifecycle rules.
RENTAL_LIFECYCLE_POLICY_VERSION = getenv("RENTAL_LIFECYCLE_POLICY_VERSION", "")
RENTAL_PROVIDER_WEBHOOK_SECRET = getenv("RENTAL_PROVIDER_WEBHOOK_SECRET", "")
RENTAL_QUOTE_TTL_MINUTES = int(getenv("RENTAL_QUOTE_TTL_MINUTES", "5"))
RENTAL_CHECKOUT_TTL_MINUTES = int(getenv("RENTAL_CHECKOUT_TTL_MINUTES", "15"))
RENTAL_CHECKOUT_ALLOWED_ORIGINS = []
RENTAL_CHECKOUT_RETURN_URL = ""
RENTAL_CHECKOUT_EXTERNAL_SCHEMES = []

# Paymob configuration only; payment routes and provider activation are separate.
PAYMOB_API_KEY = getenv("PAYMOB_API_KEY", "").strip()
PAYMOB_PUBLIC_KEY = getenv("PAYMOB_PUBLIC_KEY", "").strip()
PAYMOB_SECRET_KEY = getenv("PAYMOB_SECRET_KEY", "").strip()
PAYMOB_HMAC_SECRET = getenv("PAYMOB_HMAC_SECRET", "").strip()
PAYMOB_INTEGRATION_ID = getenv("PAYMOB_INTEGRATION_ID", "").strip()
PAYMOB_WEBHOOK_URL = getenv("PAYMOB_WEBHOOK_URL", "").strip()
PAYMOB_RETURN_URL = getenv("PAYMOB_RETURN_URL", "").strip()
PAYMOB_TEST_CHECKOUT_ENABLED = getenv(
    "PAYMOB_TEST_CHECKOUT_ENABLED", "false"
).lower() in ("true", "1", "yes")

USE_IN_MEMORY_CHANNEL_LAYER = getenv(
    "USE_IN_MEMORY_CHANNEL_LAYER", "False"
).lower() in ("true", "1", "yes")

if USE_IN_MEMORY_CHANNEL_LAYER:
    CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [REDIS_URL]},
        }
    }


## Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("POSTGRES_DB"),
        "USER": getenv("POSTGRES_USER"),
        "PASSWORD": getenv("POSTGRES_PASSWORD"),
        "HOST": getenv("POSTGRES_HOST"),
        "PORT": getenv("POSTGRES_PORT"),
    }
}

if getenv("POSTGRES_SSLMODE"):
    DATABASES["default"]["OPTIONS"] = {"sslmode": getenv("POSTGRES_SSLMODE")}


## Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

## Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Cairo"

USE_I18N = True

USE_TZ = True

# Confirmed mutation responses are replayable for this many days. Deployments may
# increase the window, but shortening it can make very late mobile retries unsafe.
IDEMPOTENCY_RETENTION_DAYS = int(getenv("IDEMPOTENCY_RETENTION_DAYS", "30"))


def _comma_separated_environment(name):
    return [value.strip() for value in getenv(name, "").split(",") if value.strip()]


# Well-known app-link responses remain unavailable until release signing values are
# configured. Never substitute debug fingerprints or a placeholder Apple Team ID.
SOKOUN_ANDROID_APP_LINKS = {
    "com.app.sokoon.real.estate": _comma_separated_environment(
        "SOKOUN_ANDROID_PROD_SHA256_FINGERPRINTS"
    ),
    "com.app.sokoon.real.estate.dev": _comma_separated_environment(
        "SOKOUN_ANDROID_DEV_SHA256_FINGERPRINTS"
    ),
}
SOKOUN_APPLE_TEAM_ID = getenv("SOKOUN_APPLE_TEAM_ID", "").strip()
SOKOUN_APPLE_BUNDLE_IDS = [
    "com.app.sokoon.real.estate",
    "com.app.sokoon.real.estate.dev",
]

LANGUAGES = [
    ("en", "English"),
    ("ar", "Arabic"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

SITE_ID = 1

## Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")
SUPPORT_PRIVATE_MEDIA_ROOT = getenv(
    "SUPPORT_PRIVATE_MEDIA_ROOT", str(BASE_DIR / "private_support_media")
)
SUPPORT_PRIVATE_STORAGE_PROVIDER = getenv(
    "SUPPORT_PRIVATE_STORAGE_PROVIDER",
    "cloudinary" if VIRTUAL_TOUR_STORAGE_PROVIDER == "cloudinary" else "local",
)
SUPPORT_CLOUDINARY_PREFIX = getenv(
    "SUPPORT_CLOUDINARY_PREFIX", "sokoun-support-private"
)
EVIDENCE_STORAGE_PROVIDER = getenv("EVIDENCE_STORAGE_PROVIDER", "disabled")
EVIDENCE_PRIVATE_ROOT = getenv(
    "EVIDENCE_PRIVATE_ROOT", str(BASE_DIR / "private_evidence")
)
EVIDENCE_CLOUDINARY_PREFIX = getenv(
    "EVIDENCE_CLOUDINARY_PREFIX", "sokoun-evidence-private"
)
EVIDENCE_SCANNER_BACKEND = getenv("EVIDENCE_SCANNER_BACKEND", "disabled")
# Optional staging-run scope. An explicitly empty list admits no fake scans;
# real scanners and the existing runtime/production guards are unchanged.
_evidence_fake_uploaders = getenv("EVIDENCE_FAKE_SCANNER_UPLOADER_IDS")
EVIDENCE_FAKE_SCANNER_UPLOADER_IDS = (
    None
    if _evidence_fake_uploaders is None
    else tuple(
        value.strip() for value in _evidence_fake_uploaders.split(",") if value.strip()
    )
)
EVIDENCE_CLAMSCAN_PATH = getenv("EVIDENCE_CLAMSCAN_PATH", "clamscan")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TAGGIT_CASE_INSENSITIVE = True

SWAGGER_USE_COMPAT_RENDERERS = False

AUTH_USER_MODEL = "users.User"

## Cookies Settings

COOKIE_NAME = "access"

"""
? cookie will be sent with the same site request and with cross side top-level navigation
? this will provide balance between security and usability
? this helps against CSRF Attacks by not sending cookies with potentially dangerous requests
? while allowing the cookies to be sent with top-level navigation that is initiated by user actions
"""
COOKIE_SAMESITE = "Lax"
COOKIE_PATH = "/"  # ? cookies will be accessed project widest
COOKIE_HTTPONLY = True  # ? can't be accessed via js
# ?HTTPS only or HTTP && HTTPS
COOKIE_SECURE = getenv("COOKIE_SECURE", "True") == "True"


## Rest FrameWork Settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core_apps.common.cookie_auth.CookieAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "core_apps.common.pagination.StandardResultsSetPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "PAGE_SIZE": 10,
    "DEFAULT_RENDERER_CLASSES": ("core_apps.common.renderers.GenericJsonRenderer",),
    "EXCEPTION_HANDLER": "core_apps.common.renderers.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",  # ? throttle users who are not authenticated.
        "rest_framework.throttling.UserRateThrottle",  # ? throttle auth-users to a given rate of requests.
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "2000/day",
        "user": "2000/day",
    },
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
    "ROTATE_REFRESH_TOKENS": True,  # ? return new refresh when the old one is used
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",  # ? the claim used in generated tokens, which will be used to store user identifiers.
}

_signing_key = getenv("SIGNING_KEY")
if _signing_key:
    SIMPLE_JWT["SIGNING_KEY"] = (
        _signing_key  # ? secret crypt-key, used to sign a JWT to ensure it's authenticity.
    )


## Djoser Settings
DJOSER = {
    "USER_ID_FIELD": "id",
    "LOGIN_FIELD": "email",
    "TOKEN_MODEL": None,
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SEND_ACTIVATION_EMAIL": False,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": getenv(
        "PASSWORD_CHANGED_EMAIL_CONFIRMATION", "True"
    )
    == "True",
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "EMAIL": {
        "password_reset": "core_apps.users.emails.RecoveryPasswordResetEmail",
        "activation": "core_apps.users.emails.RecoveryActivationEmail",
        "password_changed_confirmation": "core_apps.users.emails.SafePasswordChangedConfirmationEmail",
    },
    "ACTIVATION_URL": "activate/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "DOMAIN": getenv("DOMAIN", "sukoon-app-y4j5r.ondigitalocean.app"),
    "SITE_NAME": getenv("SITE_NAME", "sukoon.com"),
    "DEFAULT_HTTP_PROTOCOL": "https",
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": getenv("REDIRECT_URIS", "").split(","),
    "SERIALIZERS": {
        "user_create": "core_apps.users.serializers.CreateUserSerializer",
        "user_create_password_retype": "core_apps.users.serializers.CreateUserSerializer",
        "current_user": "core_apps.users.serializers.CurrentUserSerializer",
    },
}

SITE_NAME = getenv("SITE_NAME", "Sukoon")

## Social Auth Settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv("GOOGLE_CLIENT_ID")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv("GOOGLE_CLIENT_SECRET")

# ? values we want to get from google.
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]

SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ["first_name", "last_name"]

SOCIAL_AUTH_PIPELINE = [
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "core_apps.profiles.pipeline.save_profile",
]

AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]


# * Custom Social Auth Settings (Google, Apple, Facebook)
GOOGLE_CLIENT_IDS = [
    c.strip() for c in getenv("GOOGLE_CLIENT_IDS", "").split(",") if c.strip()
]
_google_client_id_single = getenv("GOOGLE_CLIENT_ID")
if _google_client_id_single and _google_client_id_single not in GOOGLE_CLIENT_IDS:
    GOOGLE_CLIENT_IDS.append(_google_client_id_single)

APPLE_CLIENT_IDS = [
    c.strip() for c in getenv("APPLE_CLIENT_IDS", "").split(",") if c.strip()
]
APPLE_DEV_PRIVATE_KEY_PATH = getenv("APPLE_DEV_PRIVATE_KEY_PATH", "").strip()

FACEBOOK_APP_ID = getenv("FACEBOOK_APP_ID", "").strip()


# Cloudinary Settings
import cloudinary

CLOUDINARY_URL = getenv("CLOUDINARY_URL")
if CLOUDINARY_URL:
    cloudinary.config(cloudinary_url=CLOUDINARY_URL)
else:
    cloudinary.config(
        cloud_name=getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=getenv("CLOUDINARY_API_KEY"),
        api_secret=getenv("CLOUDINARY_API_SECRET"),
        secure=True,
    )


# * Firebase Cloud Messaging Settings
FIREBASE_PROJECT_ID = getenv("FIREBASE_PROJECT_ID", "sokoun-99c7b")
FIREBASE_CLIENT_EMAIL = getenv("FIREBASE_CLIENT_EMAIL")
FIREBASE_PRIVATE_KEY = getenv("FIREBASE_PRIVATE_KEY")
FIREBASE_CREDENTIALS_JSON = getenv("FIREBASE_CREDENTIALS_JSON")
FIREBASE_CREDENTIALS_FILE = getenv(
    "FIREBASE_CREDENTIALS_FILE",
    str(BASE_DIR / "config" / "credentials" / "firebase-tenant-service-account.json"),
)

# New rating writes require an explicit rollout; reads/receipts remain available.
REVIEWS_ENABLED = getenv("REVIEWS_ENABLED", "false").lower() == "true"

CELERY_BEAT_SCHEDULE["reconcile-reviews"] = {
    "task": "core_apps.features.tasks.reconcile_reviews",
    "schedule": 300.0,
}

# Independent disaster recovery is deferred. Account-sensitive action assurance remains separate.
SECURITY_ASSURANCE_PROVIDER = getenv("SECURITY_ASSURANCE_PROVIDER", "")

# Rental chat protection is opt-in until the existing Gemini project terms and
# synthetic evaluation have been verified. No billing/subscription changes.
CHAT_MODERATION_MODE = getenv("CHAT_MODERATION_MODE", "off")
CHAT_MODERATION_MODEL = getenv("CHAT_MODERATION_MODEL", "gemini-3.8-flash")
CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = (
    getenv("CHAT_MODERATION_PRIVATE_INPUTS_APPROVED", "false").lower() == "true"
)
CHAT_MODERATION_DAILY_REQUESTS = int(getenv("CHAT_MODERATION_DAILY_REQUESTS", "100"))
CAPTURE_COACH_ENABLED = getenv("CAPTURE_COACH_ENABLED", "true").lower() == "true"

CAPTURE_COACH_PRIVATE_INPUTS_APPROVED = (
    getenv("CAPTURE_COACH_PRIVATE_INPUTS_APPROVED", "false").lower() == "true"
)

ADMIN_CAMPAIGNS_ENABLED = getenv("ADMIN_CAMPAIGNS_ENABLED", "false").lower() == "true"

# Commerce v1 rollout. Configured adapters must verify server-to-server; no mock
# fallback is permitted in live environments. Reads/recovery ignore sale flags.
COMMERCE_STORE_PURCHASES_ENABLED = False
COMMERCE_ENTITLEMENTS_ENABLED = False
COMMERCE_STORE_ENVIRONMENT = "sandbox"
COMMERCE_STORE_ADAPTERS = {}

# Temporary, account-scoped subscription testing. This never enables live keys
# or company purchases and does not alter native-store rollout.
COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED = getenv(
    "COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED", "false"
).lower() in {"true", "1", "yes"}
COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS = [
    value.strip()
    for value in getenv("COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS", "").split(",")
    if value.strip()
]

# Invoice-linked Paymob collection is separate from the public landing test.
PAYMOB_INVOICE_CHECKOUT_ENABLED = getenv(
    "PAYMOB_INVOICE_CHECKOUT_ENABLED", "false"
).lower() in {"true", "1", "yes"}
PAYMOB_CHECKOUT_EXTRA_ORIGINS = []

PAYMOB_REFUNDS_ENABLED = getenv("PAYMOB_REFUNDS_ENABLED", "false").lower() in {
    "true",
    "1",
    "yes",
}

# Separate, explicitly provisioned Payouts staging account. Never reuse Accept
# credentials, auto-fund its budget, or enable a production endpoint.
PAYMOB_PAYOUTS_ENABLED = getenv("PAYMOB_PAYOUTS_ENABLED", "false").lower() in {
    "true",
    "1",
    "yes",
}
PAYMOB_PAYOUTS_CLIENT_ID = getenv("PAYMOB_PAYOUTS_CLIENT_ID", "").strip()
PAYMOB_PAYOUTS_CLIENT_SECRET = getenv("PAYMOB_PAYOUTS_CLIENT_SECRET", "").strip()
PAYMOB_PAYOUTS_USERNAME = getenv("PAYMOB_PAYOUTS_USERNAME", "").strip()
PAYMOB_PAYOUTS_PASSWORD = getenv("PAYMOB_PAYOUTS_PASSWORD", "").strip()
PAYMOB_PAYOUTS_STAGING_EVIDENCE = getenv("PAYMOB_PAYOUTS_STAGING_EVIDENCE", "").strip()
PAYMOB_PAYOUTS_CHANNEL_EVIDENCE = json.loads(
    getenv("PAYMOB_PAYOUTS_CHANNEL_EVIDENCE", "{}")
)
PAYMOB_PAYOUTS_BENEFICIARIES = json.loads(getenv("PAYMOB_PAYOUTS_BENEFICIARIES", "{}"))

# Hosted Sandbox checkout for all authorized accounts/products; never Live.
COMMERCE_HOSTED_SANDBOX_ENABLED = getenv(
    "COMMERCE_HOSTED_SANDBOX_ENABLED", "false"
).lower() in {"true", "1", "yes"}

CELERY_BEAT_SCHEDULE["reconcile-hosted-checkout"] = {
    "task": "core_apps.features.tasks.reconcile_hosted_checkout",
    "schedule": 60.0,
}

# Finalize after every domain has registered its schedule, including checkout.
from config.background import configure as configure_background

configure_background(globals())
