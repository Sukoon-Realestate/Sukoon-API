import pytest

from core_apps.common.translation_catalog import EN_TO_AR_MESSAGES
from core_apps.features.models import MaintenanceEvent, MaintenanceRequest
from core_apps.features.rental_phase5_views_parts.maintenance_payload import (
    MAINTENANCE_ACTIONS,
    MAINTENANCE_EVENT_LABELS,
)
from core_apps.features.tests.test_rental_phase5 import client_for, phase5_lease

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("language", ["ar", "en"])
def test_event_labels_are_localized_without_translating_notes_or_codes(
    phase5_lease, language
):
    _, tenant, lease = phase5_lease
    item = MaintenanceRequest.objects.create(
        lease=lease, reporter=tenant, title="Synthetic repair",
        description="Synthetic request", category="water", priority="normal",
    )
    assert set(MAINTENANCE_EVENT_LABELS) == MAINTENANCE_ACTIONS | {"created"}
    note = "Maintenance request submitted."  # User text must remain verbatim.
    for action in MAINTENANCE_EVENT_LABELS:
        MaintenanceEvent.objects.create(
            maintenance_request=item, actor=tenant, action=action, note=note,
        )
    client = client_for(tenant)
    response = client.get(
        f"/api/v1/features/v1/maintenance-requests/{item.id}/",
        HTTP_ACCEPT_LANGUAGE=language,
    )
    assert response.status_code == 200
    events = response.json()["data"]["events"]
    for event in events:
        english = MAINTENANCE_EVENT_LABELS[event["action"]]
        assert event["label"] == (
            EN_TO_AR_MESSAGES[english] if language == "ar" else english
        )
        assert event["note"] == note
    item.refresh_from_db()
    assert item.status == "open" and item.revision == 1
