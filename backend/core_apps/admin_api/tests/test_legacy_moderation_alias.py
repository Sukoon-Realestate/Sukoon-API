"""A6-01: the legacy moderation-queue delete route uses the canonical decision service."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core_apps.features.models import RentalAuditEvent
from core_apps.features.planning_models import PlanningEvent
from core_apps.properties.models import Property, PropertyModerationDecision
from core_apps.properties.services.moderation import version
from core_apps.properties.tests.test_services import _create_property

pytestmark = pytest.mark.django_db


def _client(actor):
    client = APIClient()
    client.force_authenticate(actor)
    return client


def _url(prop):
    return reverse("admin-moderation-delete", kwargs={"property_id": prop.id})


def _effects(prop):
    return (
        PropertyModerationDecision.objects.filter(property=prop).count(),
        RentalAuditEvent.objects.filter(subject_id=prop.id, action="property.moderation.block").count(),
        PlanningEvent.objects.filter(recipient=prop.owner, event_key__startswith="property.moderation:").count(),
    )


def test_legacy_client_without_body_blocks_once_and_repeat_submit_cannot_duplicate(superuser, another_user):
    prop = _create_property(owner=another_user, title="Flagged", status="verified")
    client = _client(superuser)

    first = client.post(_url(prop))
    again = client.post(_url(prop))

    assert first.status_code == 200
    # Previously a second submit recorded a second decision; now it is the canonical
    # "already blocked" conflict and nothing is emitted twice.
    assert again.status_code == 409
    prop.refresh_from_db()
    assert (prop.status, prop.moderation_blocked, prop.is_verified) == ("hidden", True, False)
    assert _effects(prop) == (1, 1, 1)


def test_reviewer_cannot_moderate_their_own_listing(superuser):
    prop = _create_property(owner=superuser, title="Mine", status="verified")
    response = _client(superuser).post(_url(prop))
    assert response.status_code == 403
    assert _effects(prop) == (0, 0, 0)


def test_stale_version_is_rejected_when_supplied(superuser, another_user):
    prop = _create_property(owner=another_user, title="Stale", status="verified")
    prop.refresh_from_db()
    stale = version(prop)
    Property.objects.filter(pk=prop.pk).update(title="Edited after review opened")

    response = _client(superuser).post(
        _url(prop), {"expected_version": stale}, format="json", HTTP_IDEMPOTENCY_KEY="k1"
    )

    assert response.status_code == 409
    assert _effects(prop) == (0, 0, 0)


def test_conflicting_reuse_of_a_key_is_rejected(superuser, another_user):
    prop = _create_property(owner=another_user, title="Keyed", status="verified")
    prop.refresh_from_db()
    client = _client(superuser)
    ok = client.post(_url(prop), {"expected_version": version(prop)}, format="json", HTTP_IDEMPOTENCY_KEY="k2")
    conflict = client.post(_url(prop), {"expected_version": "different"}, format="json", HTTP_IDEMPOTENCY_KEY="k2")

    assert ok.status_code == 200
    assert conflict.status_code == 409
    assert _effects(prop) == (1, 1, 1)


def test_already_blocked_and_retired_listings_follow_canonical_conflicts(superuser, another_user):
    blocked = _create_property(owner=another_user, title="Blocked", status="hidden", moderation_blocked=True)
    retired = _create_property(owner=another_user, title="Retired", status="verified")
    from django.utils import timezone

    Property.objects.filter(pk=retired.pk).update(retired_at=timezone.now(), status="hidden")
    client = _client(superuser)
    assert client.post(_url(blocked)).status_code == 409
    assert client.post(_url(retired)).status_code == 409
    assert _effects(blocked) == (0, 0, 0)


def test_non_reviewer_is_still_refused(another_user, user):
    prop = _create_property(owner=another_user, title="Not mine", status="verified")
    assert _client(user).post(_url(prop)).status_code == 403
    assert _effects(prop) == (0, 0, 0)
