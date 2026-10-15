from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import copy
import pytest
from django.db import close_old_connections, connection
from rest_framework.test import APIClient
from core_apps.virtual_tours import services, sessions
from core_apps.virtual_tours.errors import TourError
from core_apps.virtual_tours.models import PropertyVirtualTour, TourOperation
from .test_tours import create, synthetic_draft


@pytest.mark.django_db
def test_deleted_tour_can_be_restored_without_publishing(auth_client, property_obj):
    first = create(auth_client, property_obj)
    tour = PropertyVirtualTour.objects.get(id=first.data["id"])
    url = f"/api/v1/properties/{property_obj.id}/virtual-tours/{tour.id}/"
    assert (
        auth_client.delete(
            url, {}, format="json", HTTP_IDEMPOTENCY_KEY="delete-tour-test"
        ).status_code
        == 200
    )
    restored = create(auth_client, property_obj, key="restore-tour-test")
    assert restored.status_code == 200
    assert restored.data["id"] == str(tour.id)
    assert restored.data["deleted"] is False and restored.data["disabled"] is True
    assert PropertyVirtualTour.objects.count() == 1


@pytest.mark.django_db
def test_invalid_revision_and_session_inputs_are_validation_errors(property_obj, user):
    tour, revision, _ = synthetic_draft(property_obj)
    with pytest.raises(TourError):
        services.clone_revision(tour, {"from_revision_id": "invalid"})
    for body in (
        {"preview": True, "revision_id": "invalid"},
        {"preview": []},
        {"offer_id": []},
    ):
        with pytest.raises(TourError):
            sessions.create_session(tour, user, body)


@pytest.mark.django_db(transaction=True)
def test_postgres_concurrent_replays_create_once(property_obj, user):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locking")
    barrier = Barrier(2)

    def submit(_):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user)
            barrier.wait(timeout=10)
            response = create(client, property_obj, key="concurrent-create")
            return response.status_code, response["Idempotency-Replayed"]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(results) == [(201, "false"), (201, "true")]
    assert PropertyVirtualTour.objects.count() == 1
    assert TourOperation.objects.count() == 1


@pytest.mark.django_db(transaction=True)
def test_postgres_competing_draft_versions_do_not_overwrite(property_obj, user):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locking")
    tour, revision, doc = synthetic_draft(property_obj)
    barrier = Barrier(2)

    def submit(index):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user)
            body = copy.deepcopy(doc)
            body["title"]["en"] = f"Concurrent edit {index}"
            barrier.wait(timeout=10)
            response = client.patch(
                f"/api/v1/properties/{property_obj.id}/virtual-tours/{tour.id}/revisions/{revision.id}/",
                {"authoring": body},
                format="json",
                HTTP_IDEMPOTENCY_KEY=f"concurrent-edit-{index}",
                HTTP_IF_MATCH='"draft-2"',
            )
            return response.status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(submit, range(2))) == [200, 412]
    revision.refresh_from_db()
    assert revision.draft_version == 3
