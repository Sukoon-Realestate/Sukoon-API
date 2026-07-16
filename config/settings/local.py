from os import path, getenv
from dotenv import load_dotenv

from .base import *  # noqa

from .base import BASE_DIR

local_env_file = path.join(BASE_DIR, ".envs", ".env.local")

if path.isfile(local_env_file):
    load_dotenv(local_env_file)

DEBUG = True

SECRET_KEY = getenv("SECRET_KEY", "zymJqYSgQrxHLGS1MbVPB043BbXZPlBDHAkcIVPuskhiFMj4TY8")

SITE_NAME = getenv("SITE_NAME")

ADMIN_URL = getenv("DJANGO_ADMIN_URL", "admin/")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

EMAIL_HOST = getenv("EMAIL_HOST")

_email_port = getenv("EMAIL_PORT")
EMAIL_PORT = int(_email_port) if _email_port else 587

EMAIL_HOST_USER = getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = getenv("EMAIL_USE_SSL", "False") == "True"

DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")

DOMAIN = getenv("DOMAIN")


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)s %(name)-12s %(asctime)s %(module)s %(process)d %(thread)d  %(message)s",
            "log_colors": {
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "magenta",
            },
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "colored",
        }
    },
    "root": {"level": "INFO", "handlers": ["console"]},
}


CSRF_TRUSTED_ORIGINS = ["http://localhost:8000"]

ALLOWED_HOSTS = ["*"]
