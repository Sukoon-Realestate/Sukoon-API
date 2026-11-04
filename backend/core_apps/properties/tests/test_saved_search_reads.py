from datetime import timedelta
import json
import os
from pathlib import Path
import pytest
from django.urls import reverse
from django.utils import timezone
from core_apps.properties.models import Property, SavedSearchVisit, SavedSearchRead
from core_apps.properties.tasks import purge_saved_search_reads
from .test_views import _create_published_property

pytestmark = pytest.mark.django_db


def read(client, **kwargs):
    return client.get(
        reverse("property-list"), {"saved_search_id": "stable-notebook-id", **kwargs}
    )


def ack(client, response):
    return client.post(
        reverse(
            "saved-search-read-ack",
            kwargs={"read_id": response.data["saved_search_read"]["read_id"]},
        ),
        {},
        format="json",
    )


def test_read_does_not_advance_watermark_until_ack_and_rename_keeps_baseline(
    api_client, user
):
    _create_published_property(owner=user)
    api_client.force_authenticate(user=user)
    first = read(api_client, saved_search_name="Old name")
    assert first.status_code == 200
    assert first.data["saved_search_read"]["baseline_state"] == "first_visit"
    assert SavedSearchVisit.objects.get(user=user).last_read_at is None
    assert ack(api_client, first).status_code == 200
    baseline = SavedSearchVisit.objects.get(user=user).last_read_at
    renamed = read(api_client, saved_search_name="New name")
    assert renamed.status_code == 200
    assert renamed.data["saved_search_read"]["baseline_state"] == "available"
    assert renamed.data["saved_search_read"]["new_count"] == 0
    assert SavedSearchVisit.objects.get(user=user).last_read_at == baseline
    assert ack(api_client, first).status_code == 200
    assert SavedSearchVisit.objects.get(user=user).last_read_at == baseline


def test_new_updated_and_republished_revisions_use_current_authorized_rows(
    api_client, user
):
    old = _create_published_property(owner=user)
    removed = _create_published_property(owner=user)
    api_client.force_authenticate(user=user)
    baseline = read(api_client)
    assert ack(api_client, baseline).status_code == 200
    # Publication decisions have an authoritative revision even if their
    # indexed timestamp is unchanged.
    Property.objects.filter(pk=old.pk).update(review_revision=old.review_revision + 1)
    Property.objects.filter(pk=removed.pk).update(status=Property.Status.HIDDEN)
    new = _create_published_property(owner=user)
    current = read(api_client, new_updated_only="true")
    assert current.status_code == 200
    assert current.data["count"] == 2
    metadata = current.data["saved_search_read"]
    assert metadata["new_count"] == metadata["updated_count"] == 1
    assert metadata["changes"] == {str(old.id): "updated", str(new.id): "new"}
    assert str(removed.id) not in str(current.data)
    if os.environ.get("MVP_FIXTURE_DIR"):
        directory = Path(os.environ["MVP_FIXTURE_DIR"])
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "saved_search_delta.json").write_text(
            json.dumps(current.data, indent=2) + "\n", encoding="utf-8"
        )


def test_snapshot_pagination_excludes_later_arrivals_and_rejects_changed_rows(
    api_client, user
):
    for index in range(3):
        _create_published_property(owner=user, title=f"Fixture {index}")
    api_client.force_authenticate(user=user)
    first = read(api_client, page_size=1)
    assert first.status_code == 200
    snapshot = first.data["saved_search_read"]["read_id"]
    _create_published_property(owner=user, title="Later arrival")
    second = read(api_client, page_size=1, page=2, saved_search_read_id=snapshot)
    assert second.status_code == 200
    assert second.data["count"] == 3
    target = second.data["results"][0]["id"]
    Property.objects.filter(id=target).update(review_revision=99)
    changed = read(api_client, page_size=1, page=2, saved_search_read_id=snapshot)
    assert changed.status_code == 409
    assert SavedSearchVisit.objects.get(user=user).last_read_at is None


def test_definition_change_and_expired_window_require_new_baselines(api_client, user):
    _create_published_property(owner=user, has_wifi=True)
    api_client.force_authenticate(user=user)
    baseline = read(api_client)
    assert ack(api_client, baseline).status_code == 200
    changed = read(api_client, has_wifi="true")
    assert changed.data["saved_search_read"]["baseline_state"] == "definition_changed"
    assert changed.data["saved_search_read"]["changes"] == {}
    assert SavedSearchVisit.objects.get(user=user).last_read_at is None
    assert ack(api_client, changed).status_code == 200
    SavedSearchVisit.objects.filter(user=user).update(
        last_read_at=timezone.now() - timedelta(days=31)
    )
    expired = read(api_client, has_wifi="true", new_updated_only="true")
    assert expired.status_code == 200
    assert expired.data["saved_search_read"]["baseline_state"] == "window_expired"
    assert expired.data["saved_search_read"]["changes"] == {}


def test_old_ack_cannot_overwrite_newer_read_and_accounts_are_isolated(
    api_client, user, another_user
):
    _create_published_property(owner=user)
    api_client.force_authenticate(user=user)
    older = read(api_client)
    newer = read(api_client)
    assert ack(api_client, newer).status_code == 200
    confirmed = SavedSearchVisit.objects.get(user=user).last_read_at
    assert ack(api_client, older).status_code == 409
    assert SavedSearchVisit.objects.get(user=user).last_read_at == confirmed
    api_client.force_authenticate(user=another_user)
    assert ack(api_client, newer).status_code == 404
    assert read(api_client).data["saved_search_read"]["baseline_state"] == "first_visit"


def test_cleanup_keeps_successful_watermark(api_client, user):
    _create_published_property(owner=user)
    api_client.force_authenticate(user=user)
    response = read(api_client)
    assert ack(api_client, response).status_code == 200
    SavedSearchRead.objects.update(expires_at=timezone.now() - timedelta(days=31))
    assert purge_saved_search_reads.run() > 0
    assert SavedSearchVisit.objects.get(user=user).last_read_at is not None
