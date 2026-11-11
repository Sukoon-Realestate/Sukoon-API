"""Optional push scheduling. In-app receipts are never delayed or removed."""
from datetime import date, datetime, timedelta, timezone as utc_timezone
from zoneinfo import ZoneInfo

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from core_apps.users.models import User
from ..models import NotificationDeliveryPolicy, NotificationDigestHold, NotificationDailyDigest, PushDelivery

CATEGORIES = ("viewings", "messages", "discovery", "identity_expiry", "support")
MODES = ("immediate", "daily", "off")
SUMMARY_KIND = "notification_daily_summary"


def category(notice):
    data = notice.data or {}
    if notice.scope in {"company", "student"}:
        return None
    if notice.notification_type in {"security_alert", "account_verification"} or notice.category == "account_policy":
        return None
    if data.get("event_kind") == "identity_document_expiry":
        return "identity_expiry"
    if data.get("action_type") == "open_support_ticket":
        return "support"
    if notice.notification_type == "new_message":
        return "messages"
    if notice.notification_type in {"visit_request", "visit_accepted", "visit_rejected"} or data.get("event_kind") == "viewing_changed":
        return "viewings"
    if notice.notification_type in {"new_property", "property_update", "property_verified", "property_views"}:
        return "discovery"
    return None


def projection(policy):
    return {"revision": policy.revision if policy else 0,
        "timezone": policy.timezone_name if policy else "Africa/Cairo",
        "modes": {key: policy.modes.get(key, "immediate") if policy else "immediate" for key in CATEGORIES},
        "quiet_start": policy.quiet_start if policy else None, "quiet_end": policy.quiet_end if policy else None,
        "summary_hour": 19, "categories": list(CATEGORIES)}


def local_instant(day, minute, zone, *, after=None):
    """Use the first real instant at/after a civil minute; skip DST gaps."""
    naive = datetime.combine(day, datetime.min.time()) + timedelta(minutes=minute)
    for offset in range(181):
        candidate = naive + timedelta(minutes=offset)
        valid = []
        for fold in (0, 1):
            instant = candidate.replace(tzinfo=zone, fold=fold).astimezone(utc_timezone.utc)
            if instant.astimezone(zone).replace(tzinfo=None) == candidate and (after is None or instant > after):
                valid.append(instant)
        if valid:
            return min(valid)
    raise ValueError("No valid scheduling instant")


def quiet_until(policy, now):
    if policy.quiet_start is None or policy.quiet_end is None:
        return None
    zone = ZoneInfo(policy.timezone_name)
    local = now.astimezone(zone)
    minute = local.hour * 60 + local.minute
    start, end = policy.quiet_start, policy.quiet_end
    quiet = start <= minute < end if start < end else minute >= start or minute < end
    if not quiet:
        return None
    day = local.date() + timedelta(days=int(start > end and minute >= start))
    return local_instant(day, end, zone, after=now)


def next_digest(policy, now):
    zone = ZoneInfo(policy.timezone_name)
    local = now.astimezone(zone)
    day = local.date() + timedelta(days=int(local.hour >= 19))
    due = local_instant(day, 19 * 60, zone)
    return max(due, quiet_until(policy, due) or due), day


def time_critical(notice, due, now):
    if category(notice) == "identity_expiry":
        try:
            day = date.fromisoformat((notice.data or {})["expires_on"])
        except (ValueError, TypeError, KeyError):
            return False
        expiry_end = datetime.combine(day + timedelta(days=1), datetime.min.time()).replace(tzinfo=ZoneInfo("Africa/Cairo"))
        return expiry_end <= due
    if category(notice) != "viewings":
        return False
    from core_apps.properties.models import PropertyVisit
    identity = (notice.data or {}).get("visit_id")
    if not identity:
        return False
    try:
        visit = PropertyVisit.objects.filter(id=identity).first()
    except (ValueError, TypeError, DjangoValidationError):
        return False
    if not visit:
        return False
    if visit.status == "canceled":
        return True
    if not visit.visit_date or not visit.visit_time:
        return False
    start = datetime.combine(visit.visit_date, visit.visit_time).replace(tzinfo=ZoneInfo("Africa/Cairo"))
    return start <= due


def consent_current(notice):
    selected = category(notice)
    policy = NotificationDeliveryPolicy.objects.filter(user=notice.user).first()
    return selected is None or policy is None or policy.modes.get(selected, "immediate") != "off"


def schedule(item, now):
    """Return send/defer/suppress and optional UTC next attempt without consuming retries."""
    notice = item.notification
    policy = NotificationDeliveryPolicy.objects.filter(user=notice.user).first()
    if (notice.data or {}).get("event_kind") == SUMMARY_KIND:
        return ("defer", quiet_until(policy, now)) if policy and quiet_until(policy, now) else ("send", None)
    selected = category(notice)
    if selected is None or policy is None:
        return "send", None
    mode = policy.modes.get(selected, "immediate")
    if mode == "off":
        return "suppress", None
    hold = NotificationDigestHold.objects.filter(notification=notice).first()
    if hold and hold.state == "summarized":
        return "suppress", None
    if mode == "daily" and not PushDelivery.objects.filter(notification=notice, accepted_at__isnull=False).exists():
        due, day = next_digest(policy, now)
        if time_critical(notice, due, now):
            return "send", None
        if hold is None:
            hold, _ = NotificationDigestHold.objects.get_or_create(notification=notice, defaults={
                "policy_revision": policy.revision, "due_at": due, "civil_day": day})
        elif hold.policy_revision != policy.revision:
            hold.due_at, hold.civil_day, hold.policy_revision = due, day, policy.revision
            hold.save(update_fields=["due_at", "civil_day", "policy_revision", "updated_at"])
        return "defer", max(hold.due_at, now + timedelta(seconds=60))
    until = quiet_until(policy, now)
    if until and not time_critical(notice, until, now):
        return "defer", until
    return "send", None


def authorized_source(notice):
    """Any eligible device may establish source access; dispatch rechecks each device."""
    from .push_delivery import allowed
    sources = PushDelivery.objects.filter(notification=notice, device__is_active=True).select_related(
        "notification__user", "device__auth_session").order_by("pk")
    return next((source for source in sources.iterator() if allowed(source)), None)


def summary_authorized(notice):
    policy = NotificationDeliveryPolicy.objects.filter(user=notice.user).first()
    if policy is None:
        return False
    for hold in NotificationDigestHold.objects.filter(summary=notice).select_related("notification__user"):
        if policy.modes.get(category(hold.notification), "immediate") != "daily":
            continue
        if authorized_source(hold.notification):
            return True
    return False


def build_digests(*, now=None):
    from .push_delivery import queue_notification
    from .notification_service import NotificationService
    now = now or timezone.now()
    count = 0
    users = NotificationDigestHold.objects.filter(state="pending", due_at__lte=now).order_by().values_list("notification__user_id", flat=True).distinct()
    for user_pk in list(users):
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_pk)
            if not user.is_active or user.closed_at:
                continue
            policy = NotificationDeliveryPolicy.objects.filter(user=user).first()
            if policy is None:
                continue
            holds = list(NotificationDigestHold.objects.select_for_update().filter(
                notification__user=user, state="pending", due_at__lte=now).select_related("notification"))
            groups = {}
            for hold in holds:
                if policy.modes.get(category(hold.notification), "immediate") != "daily":
                    continue
                source = authorized_source(hold.notification)
                if source is None or PushDelivery.objects.filter(
                    notification=hold.notification, accepted_at__isnull=False
                ).exists():
                    hold.state = "suppressed"; hold.save(update_fields=["state", "updated_at"])
                    continue
                if hold.policy_revision != policy.revision:
                    hold.due_at, hold.civil_day = next_digest(policy, now)
                    hold.policy_revision = policy.revision
                    hold.save(update_fields=["due_at", "civil_day", "policy_revision", "updated_at"])
                    continue
                groups.setdefault(hold.civil_day, []).append(hold)
            for day, entries in groups.items():
                existing = NotificationDailyDigest.objects.filter(user=user, civil_day=day).first()
                if existing:
                    # A civil day has one immutable summary. Late arrivals wait
                    # for the next day rather than editing an uncertain push.
                    for hold in entries:
                        hold.civil_day = day + timedelta(days=1)
                        hold.due_at = local_instant(hold.civil_day, 19 * 60, ZoneInfo(policy.timezone_name))
                        hold.save(update_fields=["civil_day", "due_at", "updated_at"])
                    continue
                notice = NotificationService.create_notification(user=user, notification_type="general",
                    title="Your daily notification summary", body="Open your inbox to review your updates.",
                    category="notification_summary", data={"event_kind": SUMMARY_KIND, "action_type": "open_general", "scope": "account"}, send_push=False)
                NotificationDailyDigest.objects.create(user=user, civil_day=day, notification=notice)
                NotificationDigestHold.objects.filter(pk__in=[row.pk for row in entries]).update(state="summarized", summary=notice)
                queue_notification(notice)
                count += 1
    return count
