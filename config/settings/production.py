from os import path, getenv
from dotenv import load_dotenv

from .base import *  # noqa

from .base import BASE_DIR

local_env_file = path.join(BASE_DIR, ".envs", ".env.local")

if path.isfile(local_env_file):
    load_dotenv(local_env_file)

DEBUG = getenv("DEBUG", "True")

SECRET_KEY = getenv("SECRET_KEY")

ADMIN_URL = getenv("DJANGO_ADMIN_URL", "admin/")

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = getenv("EMAIL_HOST")

_email_port = getenv("EMAIL_PORT")
EMAIL_PORT = int(_email_port) if _email_port else 587

EMAIL_HOST_USER = getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL = getenv("EMAIL_USE_SSL", "False") == "True"

DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")

DOMAIN = getenv("DOMAIN")

ALLOWED_HOSTS = getenv("ALLOWED_HOSTS", "*").split(",")

ADMINS = [
    ("Zeyad Mohammed Salama", "zeyadslama23@gmail.com"),
]
