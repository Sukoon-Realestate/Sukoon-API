"""Unpaid prerequisites for the guarded local native commerce test."""

import hashlib
import io
import uuid

from django.core.files.base import ContentFile
from PIL import Image

from core_apps.advertising.models import (
    Advertisement,
    AdvertisementMedia,
    AdvertisementOperation,
    AdvertisingPlan,
)
from core_apps.common.content_models import ReleaseNote
from core_apps.advertising.services import plan_payload


def prepare_commerce_prerequisites(owner, run):
    plan = AdvertisingPlan.objects.create(
        id=f"qa-{run}",
        title_en="Local advertisement plan",
        title_ar="خطة إعلان للاختبار المحلي",
        duration_unit="week",
        duration_count=1,
        amount_minor=25000,
    )
    operation = AdvertisementOperation.objects.create(
        owner=owner,
        operation_id=str(uuid.uuid4()),
        state=AdvertisementOperation.State.FOUND,
    )
    advertisement = Advertisement.objects.create(
        owner=owner,
        operation=operation,
        title=f"Local commerce QA {run}",
        plan_snapshot=plan_payload(plan, "en"),
    )
    buffer = io.BytesIO()
    Image.new("RGB", (600, 300), color=(12, 55, 73)).save(buffer, format="PNG")
    artwork = buffer.getvalue()
    media = AdvertisementMedia(
        advertisement=advertisement,
        sha256=hashlib.sha256(artwork).hexdigest(),
        content_type="image/png",
        size_bytes=len(artwork),
    )
    media.banner.save(f"qa-{run}.png", ContentFile(artwork))
    note = ReleaseNote.objects.create(
        version=f"99.0.0-qa{run}",
        workspace="both",
        items_en=f"Local managed note {run}",
        items_ar=f"تحديث مُدار محليًا {run}",
    )
    return {
        "advertisement_id": str(advertisement.id),
        "release_version": note.version,
        "release_items": {"en": note.items_en, "ar": note.items_ar},
    }
