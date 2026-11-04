"""Prepare only the explicitly named isolated loopback DB; print no credentials."""
import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.mvp_http_test'
import django
django.setup()
from django.conf import settings
from django.contrib.auth import get_user_model
from core_apps.properties.models import Property, PropertyType, Governorate, City

assert settings.DATABASES['default']['NAME'] == 'mvp_http_isolated'
assert settings.DATABASES['default']['HOST'] == '127.0.0.1'
assert settings.SUKOON_MVP and not settings.RENTAL_CHECKOUT_ENABLED
password = secrets.token_urlsafe(24)
user, _ = get_user_model().objects.get_or_create(email='mvp-http@sokoun.test',
    defaults={'first_name': 'Synthetic', 'last_name': 'MVP'})
user.set_password(password)
user.is_verified = True
user.is_active = True
user.save()
gov, _ = Governorate.objects.get_or_create(slug='mvp-http', defaults={'name': 'Synthetic'})
city, _ = City.objects.get_or_create(slug='mvp-http', defaults={'name': 'Synthetic', 'governorate': gov})
kind, _ = PropertyType.objects.get_or_create(slug='mvp-http', defaults={'name': 'Synthetic'})
prop, _ = Property.objects.get_or_create(owner=user, title='Synthetic private MVP HTTP fixture',
    defaults={'property_type': kind, 'governorate': gov, 'city': city, 'district': 'Synthetic', 'status': 'hidden'})
assert prop.status != 'verified'
target = Path(os.environ['MVP_HTTP_ROOT']) / 'fixture.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps({'base_url': 'http://127.0.0.1:8026/api/v1/',
    'property_id': str(prop.id), 'user_id': str(user.id), 'email': user.email,
    'password': password}), encoding='utf-8')
print('Prepared synthetic private fixture in the isolated loopback database.')
