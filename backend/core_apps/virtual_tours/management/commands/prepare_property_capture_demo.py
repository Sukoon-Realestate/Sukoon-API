"""Prepare a private local listing for the later physical-room capture test."""

import json
import os
import secrets
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from core_apps.properties.models import Property, PropertyType, Governorate, City


class Command(BaseCommand):
    help = "Create/reuse an unpublished local capture demo; save credentials privately."

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "config.settings.capture_dev":
            raise CommandError("Use --settings=config.settings.capture_dev only.")
        target = Path(settings.BASE_DIR) / ".envs" / "property-capture-demo.json"
        existing = json.loads(target.read_text()) if target.exists() else {}
        password = existing.get("password") or secrets.token_urlsafe(24)
        with transaction.atomic():
            user, created = get_user_model().objects.get_or_create(
                email="capture-demo@sokoun.test",
                defaults={
                    "first_name": "Capture",
                    "last_name": "Demo",
                    "is_active": True,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            # This isolated QA identity represents a verified owner solely so
            # the normal app gate can open. It is not identity-provider evidence.
            user.is_verified = True
            user.is_email_verified = True
            user.save(update_fields=["is_verified", "is_email_verified"])
            gov, _ = Governorate.objects.get_or_create(name="محافظة اختبار التصوير")
            city, _ = City.objects.get_or_create(
                name="مدينة الاختبار",
                governorate=gov,
            )
            kind, _ = PropertyType.objects.get_or_create(name="شقة اختبار")
            prop, _ = Property.objects.get_or_create(
                owner=user,
                title="عقار اختبار الجولة الافتراضية",
                defaults={
                    "description": "عقار تجريبي خاص لتصوير غرفة حقيقية لاحقًا. لا توجد نتائج 360 أو 3D بعد.",
                    "property_type": kind,
                    "governorate": gov,
                    "city": city,
                    "district": "اختبار",
                    "status": Property.Status.HIDDEN,
                },
            )
        payload = {
            "base_url": "http://127.0.0.1:8026/api/v1/",
            "property_id": str(prop.id),
            "user_id": str(user.id),
            "email": user.email,
            "password": password,
            "access_token": str(RefreshToken.for_user(user).access_token),
        }
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w") as output:
            os.fchmod(output.fileno(), 0o600)
            json.dump(payload, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        self.stdout.write(
            json.dumps(
                {
                    "property_id": str(prop.id),
                    "title": prop.title,
                    "status": prop.status,
                    "fixture": str(target),
                },
                ensure_ascii=False,
            )
        )
