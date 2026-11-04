import json
import os
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.urls import reverse
from rest_framework.exceptions import NotFound

from core_apps.features.planning_models import PlanningEvent
from core_apps.features.services.planning_notifications_parts.event_copy import event_copy
from core_apps.profiles.identity_expiry import card_version, record_reminders
from core_apps.profiles.models import IdentityDocumentExpiry
from core_apps.admin_api.models import KYCSubmission

pytestmark = pytest.mark.django_db


@pytest.fixture
def card(user):
    profile = user.profile
    profile.national_id = "29001011234567"
    profile.id_face = "image/authenticated/v1/identity/front"
    profile.id_back = "image/authenticated/v1/identity/back"
    profile.save()
    KYCSubmission.objects.create(profile=profile, status="pending")
    return profile


def save(client, body, key=None):
    return client.post(reverse("identity-expiry"), body, format="json", HTTP_IDEMPOTENCY_KEY=key or str(uuid4()))


def test_private_metadata_unknown_date_and_receipt_recovery(api_client, user, another_user, card):
    api_client.force_authenticate(user)
    initial = api_client.get(reverse("identity-expiry"))
    assert initial.status_code == 200 and initial.data["source"] == "unknown"
    assert initial["Cache-Control"] == "private, no-store"
    assert "29001011234567" not in json.dumps(initial.data) and "identity/front" not in json.dumps(initial.data)
    body = {"document_version": initial.data["document_version"], "expected_revision": 0,
            "expires_on": "2027-01-15", "reminder_days": [30, 7, 1]}
    key = str(uuid4())
    first = save(api_client, body, key)
    assert first.status_code == 200, first.data
    assert save(api_client, body, key).data == first.data
    assert IdentityDocumentExpiry.objects.count() == 1
    assert save(api_client, body).status_code == 409
    exported = os.environ.get("MVP_FIXTURE_DIR")
    if exported:
        (Path(exported) / "identity_expiry.json").write_text(json.dumps(first.data), encoding="utf8")
    api_client.force_authenticate(another_user)
    assert api_client.get(reverse("identity-expiry")).data["document_version"] is None
    assert save(api_client, body).status_code == 409
    api_client.force_authenticate(user)
    body.update(expected_revision=1, expires_on=None, reminder_days=[])
    assert save(api_client, body).data["source"] == "unknown"
    assert record_reminders(today=date(2027, 1, 14)) == 0
    assert not PlanningEvent.objects.exists()


def test_invalid_reminders_and_account_revocation(api_client, user, card):
    api_client.force_authenticate(user)
    body = {"document_version": card_version(card), "expected_revision": 0,
            "expires_on": "2027-01-15", "reminder_days": [14]}
    assert save(api_client, body).status_code == 400
    body["reminder_days"] = [7, 7]
    assert save(api_client, body).status_code == 400
    body.update(expires_on=None, reminder_days=[7])
    assert save(api_client, body).status_code == 400
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert api_client.get(reverse("identity-expiry")).status_code == 403


@pytest.mark.parametrize("days", [30, 7, 1])
def test_exact_threshold_deduplication_and_authority_on_every_delivery(user, card, days):
    today = date(2027, 4, 20)
    row = IdentityDocumentExpiry.objects.create(profile=card, document_version=card_version(card),
        expires_on=today + timedelta(days=days), reminder_days=[days])
    assert record_reminders(today=today - timedelta(days=1)) == 0
    assert record_reminders(today=today) == 1
    assert record_reminders(today=today) == 0
    event = PlanningEvent.objects.get()
    assert event_copy(event)["category"] == "identity_expiry"
    assert "identity/front" not in json.dumps(event.destination)
    row.reminder_days = []
    row.save()
    with pytest.raises(NotFound):
        event_copy(event)
    row.reminder_days = [days]
    row.expires_on += timedelta(days=1)
    row.save()
    with pytest.raises(NotFound):
        event_copy(event)
    assert record_reminders(today=today + timedelta(days=1)) == 1


def test_selfie_correction_retains_card_but_replacement_revokes_old_metadata(api_client, user, card):
    api_client.force_authenticate(user)
    version = card_version(card)
    body = {"document_version": version, "expected_revision": 0,
            "expires_on": "2027-01-15", "reminder_days": [1]}
    key = str(uuid4())
    assert save(api_client, body, key).status_code == 200
    card.confirmation_selfi = "image/authenticated/v2/identity/new-selfie"
    card.save()
    KYCSubmission.objects.create(profile=card, status="approved")
    assert card_version(card) == version
    assert api_client.get(reverse("identity-expiry")).data["revision"] == 1
    card.id_face = "image/authenticated/v2/identity/replacement"
    card.save()
    assert api_client.get(reverse("identity-expiry")).data["source"] == "unknown"
    assert save(api_client, body, key).status_code == 409
    assert record_reminders(today=date(2027, 1, 14)) == 0


def test_task_registered_and_uses_no_provider(settings, user, card):
    from core_apps.profiles.tasks import record_identity_expiry_reminders
    assert settings.BACKGROUND_SCHEDULE_CATALOG["record-identity-expiry-reminders"]["task"] == record_identity_expiry_reminders.name
    with patch("core_apps.profiles.identity_expiry.record_reminders", return_value=2) as record:
        assert record_identity_expiry_reminders.run() == 2
        record.assert_called_once_with()


@pytest.mark.django_db(transaction=True)
def test_concurrent_metadata_edits_and_workers_are_serialized(user, card):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections
    from rest_framework.test import APIClient

    version = card_version(card)
    barrier = Barrier(2)
    def edit(day):
        close_old_connections()
        try:
            api = APIClient(); api.force_authenticate(user)
            barrier.wait(timeout=10)
            return save(api, {"document_version": version, "expected_revision": 0,
                "expires_on": f"2027-01-{day}", "reminder_days": [1]}).status_code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(edit, [15, 16]))
    assert sorted(outcomes) == [200, 409]
    row = IdentityDocumentExpiry.objects.get()
    today = row.expires_on - timedelta(days=1)
    barrier = Barrier(2)
    def schedule(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return record_reminders(today=today)
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(schedule, range(2))) == 1
    assert PlanningEvent.objects.count() == 1
