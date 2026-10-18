import uuid
import pytest
from django.test import Client
from django.urls import reverse
from core_apps.features.tests.test_rental_phase3 import phase3_lease
from core_apps.features.tests.test_rental_lifecycle_safety import operator
from core_apps.features.services.rental_lifecycle.cases import open_system_case
from core_apps.features.models import RentalAuditEvent

pytestmark = pytest.mark.django_db


def test_case_console_uses_current_assignee_revision_and_same_command_boundary(
    phase3_lease, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    owner, tenant, lease = phase3_lease
    agent = operator("support")
    case = open_system_case(
        kind="access_failure",
        source_key="console-test",
        lease=lease,
        actor=tenant,
        reason="Cannot enter",
        next_action="Independent review",
    )
    client = Client()
    client.force_login(agent)
    url = reverse("admin:features_rentaloperationalcase_change", args=[case.pk])
    assert client.get(url).status_code == 200
    payload = {
        "command_action": "assign",
        "decision_reason": "Take responsibility for this case",
        "assignee_id": str(agent.id),
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
        "_save": "Save",
    }
    assert client.post(url, payload).status_code == 302
    assert client.post(url, payload).status_code == 302
    case.refresh_from_db()
    assert case.assigned_to == agent and case.revision == 2
    payload.update(
        command_action="resolve",
        assignee_id="",
        decision_code="no_action_required",
        decision_reason="Reviewed evidence and no domain remedy is required",
        expected_revision=2,
        request_key=str(uuid.uuid4()),
    )
    assert client.post(url, payload).status_code == 302
    case.refresh_from_db()
    assert case.status == "resolved"
    assert (
        RentalAuditEvent.objects.filter(
            subject_id=case.id, action="case.resolve"
        ).count()
        == 1
    )
    agent.staff_profile.is_active = False
    agent.staff_profile.save()
    assert client.post(url, payload).status_code == 403
