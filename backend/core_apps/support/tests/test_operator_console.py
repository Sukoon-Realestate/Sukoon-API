import uuid
import pytest
from django.urls import reverse
from django.test import Client
from core_apps.features.tests.test_rental_lifecycle_safety import operator
from core_apps.support.services import create_ticket
from core_apps.support.models import TicketMessage

pytestmark = pytest.mark.django_db


def test_support_console_submits_one_reply_and_rejects_stale_or_revoked_write(
    user, settings
):
    settings.STATICFILES_STORAGE = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
    )
    agent = operator("support")
    ticket = create_ticket(
        user, "tenant", "other", "Help needed", "Please review the case."
    )
    client = Client()
    client.force_login(agent)
    url = reverse("admin:support_ticket_change", args=[ticket.pk])
    assert client.get(url).status_code == 200
    payload = {
        "reply": "Advice only; no refund has been executed.",
        "expected_revision": 1,
        "request_key": str(uuid.uuid4()),
        "_save": "Save",
    }
    assert client.post(url, payload).status_code == 302
    assert client.post(url, payload).status_code == 302
    assert TicketMessage.objects.filter(ticket=ticket, sender="support").count() == 1
    assert (
        client.post(url, {**payload, "request_key": str(uuid.uuid4())}).status_code
        == 302
    )
    assert TicketMessage.objects.filter(ticket=ticket, sender="support").count() == 1
    agent.staff_profile.is_active = False
    agent.staff_profile.save()
    assert (
        client.post(
            url, {**payload, "expected_revision": 2, "request_key": str(uuid.uuid4())}
        ).status_code
        == 403
    )
