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

EMAIL_PORT = getenv("EMAIL_PORT")

DEFAULT_FROM_EMAIL = getenv("DEFAULT_FROM_EMAIL")

DOMAIN = getenv("DOMAIN")

ALLOWED_HOSTS = getenv("ALLOWED_HOSTS", "*").split(",")

ADMINS = [
    ("Zeyad Mohammed Salama", "zeyadslama23@gmail.com"),
]
