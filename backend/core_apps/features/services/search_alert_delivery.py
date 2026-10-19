"""User-requested search matches through the existing inbox/outbox transport."""

import hashlib
from datetime import timedelta
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.properties.filters import PropertyFilter
from core_apps.notifications.services import NotificationService
from ..models import SearchAlert
from ..planning_models import PlanningEvent
from ..serializers_parts.lease_serializer import AlertCreateSerializer
from .planning_parts.selection_payload import public_properties
from .planning_parts.districts import filter_districts


def record_search_matches(limit=100):
    now = timezone.now()
    due = (
        SearchAlert.objects.filter(
            enabled=True, deleted_at__isnull=True, user__is_active=True
        )
        .filter(
            Q(last_checked_at__isnull=True)
            | Q(cadence="instant", last_checked_at__lt=now - timedelta(minutes=1))
            | Q(cadence="daily", last_checked_at__lt=now - timedelta(days=1))
        )
        .order_by(F("last_checked_at").asc(nulls_first=True), "pkid")
    )
    recorded = 0
    for identity in list(due.values_list("pk", flat=True)[:limit]):
        with transaction.atomic():
            alert = (
                SearchAlert.objects.select_for_update()
                .select_related("user")
                .get(pk=identity)
            )
            if not alert.enabled or alert.deleted_at or not alert.user.is_active:
                continue
            cadence = (
                timedelta(days=1) if alert.cadence == "daily" else timedelta(minutes=1)
            )
            if alert.last_checked_at and alert.last_checked_at > now - cadence:
                continue
            try:
                filters = AlertCreateSerializer().validate_filters(alert.filters)
                matching = PropertyFilter(
                    {
                        **filters,
                        "district_ids": ",".join(filters.get("district_ids", [])),
                    },
                    queryset=public_properties(),
                )
                if not matching.is_valid():
                    raise ValidationError("Search filters require review.")
                properties = (
                    filter_districts(matching.qs, filters)
                    .filter(
                        updated_at__gt=alert.last_matched_at or alert.created_at,
                        updated_at__lte=now,
                    )
                    .exclude(owner=alert.user)
                )
                latest = properties.order_by("-updated_at", "-pkid").first()
                alert.matching_status = "current"
            except ValidationError:
                alert.matching_status = "criteria_need_review"
                latest = None
            if latest:
                key = hashlib.sha256(
                    f"{alert.id}:{alert.revision}:{latest.id}:{latest.updated_at.isoformat()}".encode()
                ).hexdigest()
                event, created = PlanningEvent.objects.get_or_create(
                    recipient=alert.user,
                    event_key="search:" + key,
                    defaults={
                        "destination": {
                            "action_type": "open_search_alert",
                            "target_id": str(alert.id),
                            "revision": alert.revision,
                            "workspace": "tenant",
                            "schema_version": "1",
                        }
                    },
                )
                if created:
                    event.notification = NotificationService.create_notification(
                        user=alert.user,
                        title="تحديث لبحثك المحفوظ / Saved search update",
                        body="افتح التطبيق لمراجعة النتائج الحالية / Open the app to review current results.",
                        notification_type="new_property",
                        category="search_alert",
                        data=event.destination,
                        send_push=False,
                    )
                    event.save(update_fields=["notification", "updated_at"])
                    recorded += 1
                alert.last_matched_at = latest.updated_at
            alert.last_checked_at = now
            alert.save(
                update_fields=[
                    "last_checked_at",
                    "last_matched_at",
                    "matching_status",
                    "updated_at",
                ]
            )
    return recorded
