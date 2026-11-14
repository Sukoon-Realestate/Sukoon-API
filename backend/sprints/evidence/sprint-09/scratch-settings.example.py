"""Example only: choose a fresh scratch root/socket/role/test name before use."""
from config.settings.test import *
from pathlib import Path
ROOT = Path('/private/tmp/sukoon-sprint09-example')
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.postgresql', 'NAME': 'postgres',
    'USER': 'sprint09', 'HOST': str(ROOT / 'pg/socket'), 'PORT': '55449',
    'TEST': {'NAME': 'test_sprint09_example', 'CHARSET': 'UTF8', 'TEMPLATE': 'template0'},
}}
MEDIA_ROOT = str(ROOT / 'media')
STATIC_ROOT = str(ROOT / 'static')
CHAT_PRIVATE_MEDIA_ROOT = str(ROOT / 'chat')
SUPPORT_PRIVATE_MEDIA_ROOT = str(ROOT / 'support')
VIRTUAL_TOUR_PRIVATE_ROOT = str(ROOT / 'tours')
EVIDENCE_PRIVATE_ROOT = str(ROOT / 'evidence')
