"""A versioned appointment authorizes only its explicitly reviewed interval."""

from django.utils import timezone


def access_window_current(item, *, now=None):
    now = now or timezone.now()
    return bool(
        item.appointment_at
        and item.appointment_ends_at
        and item.appointment_version == item.access_approved_version
        and item.appointment_at <= now < item.appointment_ends_at
    )


def appointment_reviewable(item, *, now=None):
    now = now or timezone.now()
    return bool(
        item.appointment_at
        and item.appointment_ends_at
        and item.appointment_at < item.appointment_ends_at
        and now < item.appointment_ends_at
    )
