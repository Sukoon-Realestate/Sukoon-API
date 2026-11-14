"""Services: ensure media persisted."""

import calendar
from datetime import datetime, timedelta, timezone as datetime_timezone
from django.utils import timezone
from ..models import Advertisement, AdvertisingPlan
from .validate_banner import CAIRO, property_is_publishable, eligible_offer
from .create_advertisement import _valid_local_datetime


def resolve_cairo_local(naive):
    valid = [
        value
        for value in (_valid_local_datetime(naive, 0), _valid_local_datetime(naive, 1))
        if value
    ]
    if valid:
        return max(valid, key=lambda value: value.astimezone(datetime_timezone.utc))
    before = naive.replace(tzinfo=CAIRO, fold=0).utcoffset()
    after = naive.replace(tzinfo=CAIRO, fold=1).utcoffset()
    if before is not None and after is not None and after > before:
        shifted = naive + (after - before)
        valid = [
            value
            for value in (
                _valid_local_datetime(shifted, 0),
                _valid_local_datetime(shifted, 1),
            )
            if value
        ]
        if valid:
            return max(valid, key=lambda value: value.astimezone(datetime_timezone.utc))
    probe = naive
    for _ in range(180):
        probe += timedelta(minutes=1)
        valid = [
            value
            for value in (
                _valid_local_datetime(probe, 0),
                _valid_local_datetime(probe, 1),
            )
            if value
        ]
        if valid:
            return max(valid, key=lambda value: value.astimezone(datetime_timezone.utc))
    raise ValueError("Unable to resolve Cairo local datetime")


def calendar_expiry(starts_at, duration_unit, duration_count):
    if duration_unit == AdvertisingPlan.DurationUnit.WEEK:
        return starts_at + timedelta(days=7 * duration_count)
    local = starts_at.astimezone(CAIRO)
    year, month = local.year, local.month
    if duration_unit == AdvertisingPlan.DurationUnit.CALENDAR_MONTH:
        month_index = month - 1 + duration_count
        target_year = year + month_index // 12
        target_month = month_index % 12 + 1
    elif duration_unit == AdvertisingPlan.DurationUnit.CALENDAR_YEAR:
        target_year = year + duration_count
        target_month = month
    else:
        raise ValueError("Unsupported duration unit")
    target_day = min(local.day, calendar.monthrange(target_year, target_month)[1])
    naive = datetime(
        target_year,
        target_month,
        target_day,
        local.hour,
        local.minute,
        local.second,
        local.microsecond,
    )
    return resolve_cairo_local(naive).astimezone(datetime_timezone.utc)


def effective_status(advertisement, now=None):
    now = now or timezone.now()
    if (
        advertisement.status
        in {Advertisement.Status.ACTIVE, Advertisement.Status.EXPIRED}
        and advertisement.ends_at
        and now >= advertisement.ends_at
    ):
        return Advertisement.Status.EXPIRED
    return advertisement.status


def destination_is_eligible(advertisement):
    if not advertisement.property_id:
        return not advertisement.offer_id
    return (
        advertisement.property.owner_id == advertisement.owner_id
        and property_is_publishable(advertisement.property)
        and eligible_offer(advertisement.property, advertisement.offer_id)
    )


def ensure_media_persisted(media):
    """Compatibility probe; serving never repairs or invents source artwork.

    Missing historical files require the explicit restore_advertising_media
    command with original bytes matching the recorded length and digest.
    """
    if not media or not media.banner or media.size_bytes <= 0:
        return False
    return media.banner.storage.exists(media.banner.name)


def media_is_available(advertisement):
    media = getattr(advertisement, "media", None)
    if not media or not media.banner:
        return False
    if media.size_bytes <= 0:
        return False
    return media.banner.storage.exists(media.banner.name)


__all__ = [
    "calendar_expiry",
    "destination_is_eligible",
    "effective_status",
    "ensure_media_persisted",
    "media_is_available",
    "resolve_cairo_local",
]
