from pathlib import Path
from os import getenv, path
from dotenv import load_dotenv
from datetime import timedelta

# todo refactor the code, write explaining comments

# ? Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

APPS_DIR = BASE_DIR / "core_apps"

local_env_file = path.join(BASE_DIR, ".envs", ".env.local")

if path.isfile(local_env_file):
    load_dotenv(local_env_file)


## Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",  # ? allows to manage multiple domains within a single django project
]

LOCAL_APPS = ["core_apps.common", "core_apps.users", "core_apps.profiles"]

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
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS + ["channels"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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

SITE_ID = 1

## Static files (CSS, JavaScript, Images)

STATIC_URL = "/static/"
STATIC_ROOT = str(BASE_DIR / "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = str(BASE_DIR / "media")

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
COOKIE_PATH = "/"  # ? cookies will be accessed project wide
COOKIE_HTTPONLY = True  # ? can't be accessed via js
# ?HTTPS only or HTTP && HTTPS
COOKIE_SECURE = getenv("COOKIE_SECURE", "True") == "True"


## Rest FrameWork Settings

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core_apps.common.cookie_auth.CookieAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "PAGE_SIZE": 10,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",  # ? throttle users who are not authenticated.
        "rest_framework.throttling.UserRateThrottle",  # ? throttle auth-users to a given rate of requests.
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "200/day",
        "user": "500/day",
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
    SIMPLE_JWT["SIGNING_KEY"] = _signing_key  # ? secret crypt-key, used to sign a JWT to ensure it's authenticity.


## Djoser Settings
DJOSER = {
    "USER_ID_FIELD": "id",
    "LOGIN_FIELD": "email",
    "TOKEN_MODEL": None,
    "USER_CREATE_PASSWORD_RETYPE": True,
    "SEND_ACTIVATION_EMAIL": False,
    "PASSWORD_CHANGED_EMAIL_CONFIRMATION": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "ACTIVATION_URL": "activate/{uid}/{token}",
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "DOMAIN": getenv("DOMAIN", "sukoon-app-y4j5r.ondigitalocean.app"),
    "SITE_NAME": getenv("SITE_NAME", "sukoon.com"),
    "DEFAULT_HTTP_PROTOCOL": "https",
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": getenv("REDIRECT_URIS", "").split(","),
    "SERIALIZERS": {
        "user_create": "core_apps.users.serializers.CreateUserSerializer",
        "user_create_password_retype": "core_apps.users.serializers.CreateUserSerializer",
        "current_user": "core_apps.users.serializers.CustomUserSerializer",
    },
}


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
GOOGLE_CLIENT_IDS = [c.strip() for c in getenv("GOOGLE_CLIENT_IDS", "").split(",") if c.strip()]
_google_client_id_single = getenv("GOOGLE_CLIENT_ID")
if _google_client_id_single and _google_client_id_single not in GOOGLE_CLIENT_IDS:
    GOOGLE_CLIENT_IDS.append(_google_client_id_single)

APPLE_CLIENT_IDS = [c.strip() for c in getenv("APPLE_CLIENT_IDS", "").split(",") if c.strip()]
APPLE_DEV_PRIVATE_KEY_PATH = getenv("APPLE_DEV_PRIVATE_KEY_PATH", "").strip()

FACEBOOK_APP_ID = getenv("FACEBOOK_APP_ID", "").strip()

