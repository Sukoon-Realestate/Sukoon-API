from datetime import timedelta
from unittest.mock import patch
import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from core_apps.features.models import SearchAlert
from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.search_alert_delivery import record_search_matches
from core_apps.features.services.planning_notifications import deliver_planning_events
from core_apps.features.serializers_parts.lease_serializer import AlertCreateSerializer
from core_apps.features.tests.test_rental_phase2 import rental_participants
from core_apps.properties.models import District
from core_apps.profiles.models import UserSettings
from core_apps.notifications.services import FCMService

pytestmark = pytest.mark.django_db


def make_alert(tenant, prop, district):
    alert = SearchAlert.objects.create(
        user=tenant,
        name="Synthetic saved search",
        cadence="instant",
        filters={"city": str(prop.city.id), "district_ids": [str(district.id)]},
    )
    SearchAlert.objects.filter(pk=alert.pk).update(
        created_at=timezone.now() - timedelta(days=2)
    )
    prop.district_catalog = district
    prop.save(update_fields=["district_catalog", "updated_at"])
    return alert


def test_matching_queues_one_original_event_and_rechecks_revocation(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    district = District.objects.create(city=prop.city, name="Synthetic district")
    alert = make_alert(tenant, prop, district)
    assert record_search_matches() == 1
    assert record_search_matches() == 0
    event = PlanningEvent.objects.get(event_key__startswith="search:")
    assert event.notification.notification_type == "new_property"
    assert event.destination["target_id"] == str(alert.id)
    assert "filters" not in event.notification.data
    alert.enabled = False
    alert.revision += 1
    alert.save()
    with patch.object(FCMService, "send_push_to_user") as send:
        assert deliver_planning_events() == 0
        send.assert_not_called()
    event.refresh_from_db()
    assert event.delivery_status == "stale_or_unauthorized"


def test_foreign_district_or_inactive_catalog_never_becomes_all_city(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    district = District.objects.create(city=prop.city, name="A")
    other = District.objects.create(city=prop.city, name="B")
    alert = make_alert(tenant, prop, district)
    prop.district_catalog = other
    prop.save()
    assert record_search_matches() == 0
    alert.last_checked_at = None
    alert.save()
    district.is_active = False
    district.save()
    assert record_search_matches() == 0
    alert.refresh_from_db()
    assert alert.matching_status == "criteria_need_review"
    with pytest.raises(ValidationError):
        AlertCreateSerializer().validate_filters({"district_ids": [str(other.id)]})


def test_daily_cadence_and_marketing_opt_out_do_not_hide_critical_receipts(
    rental_participants,
):
    _, tenant, _, prop, _ = rental_participants
    district = District.objects.create(city=prop.city, name="A")
    alert = make_alert(tenant, prop, district)
    alert.cadence = "daily"
    alert.last_checked_at = timezone.now()
    alert.save()
    assert record_search_matches() == 0
    prefs, _ = UserSettings.objects.get_or_create(user=tenant)
    prefs.promotions_and_updates = False
    prefs.property_updates = False
    prefs.new_properties_in_area = True
    prefs.save()
    assert not FCMService.should_send_to_user(tenant, "promotion")
    assert FCMService.should_send_to_user(tenant, "new_property")
    prefs.new_properties_in_area = False
    prefs.save()
    assert not FCMService.should_send_to_user(tenant, "new_property")
    assert FCMService.should_send_to_user(tenant, "payment_receipt")
