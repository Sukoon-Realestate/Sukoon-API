"""A2-01: one publication policy for visit creation and public property reads (Sprint 01)."""

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.test import APIClient

from core_apps.properties.models import Property, PropertyVisit
from core_apps.properties.services import PropertyVisitService
from core_apps.properties.tests.test_services import _create_property
from core_apps.users.models import AccountClosureRequest

BODY = {"visit_date": "2099-07-20", "visit_time": "14:00:00", "note": "Can I view it?"}


def _unpublish(prop, state):
    if state in {"hidden", "under_review", "needs_revision"}:
        Property.objects.filter(pk=prop.pk).update(status=state)
    elif state == "retired":
        Property.objects.filter(pk=prop.pk).update(retired_at=timezone.now(), status="hidden")
    elif state == "blocked":
        Property.objects.filter(pk=prop.pk).update(moderation_blocked=True)
    elif state == "closure_pending":
        AccountClosureRequest.objects.create(user=prop.owner)
    elif state == "owner_closed":
        type(prop.owner).objects.filter(pk=prop.owner_id).update(closed_at=timezone.now())


STATES = ["hidden", "under_review", "needs_revision", "retired", "blocked", "closure_pending", "owner_closed"]


@pytest.mark.django_db
@pytest.mark.parametrize("state", STATES)
def test_unpublished_inventory_cannot_start_a_visit(auth_client, user, another_user, state):
    prop = _create_property(owner=another_user, title="Unavailable", status="verified")
    _unpublish(prop, state)

    response = auth_client.post(reverse("property-visit-create", kwargs={"property_id": prop.id}), BODY, format="json")

    assert response.status_code == 404, (state, response.status_code, response.content)
    assert not PropertyVisit.objects.filter(property=prop).exists()


@pytest.mark.django_db
def test_eligible_public_property_still_books(auth_client, user, another_user):
    prop = _create_property(owner=another_user, title="Public", status="verified")
    response = auth_client.post(reverse("property-visit-create", kwargs={"property_id": prop.id}), BODY, format="json")
    assert response.status_code == 201
    assert PropertyVisit.objects.filter(property=prop, tenant=user).count() == 1


@pytest.mark.django_db
def test_withdrawn_closure_restores_only_otherwise_eligible_publication(auth_client, user, another_user):
    public = _create_property(owner=another_user, title="Public", status="verified")
    hidden = _create_property(owner=another_user, title="Hidden", status="hidden")
    AccountClosureRequest.objects.create(user=another_user, active=False, status="withdrawn")

    ok = auth_client.post(reverse("property-visit-create", kwargs={"property_id": public.id}), BODY, format="json")
    refused = auth_client.post(reverse("property-visit-create", kwargs={"property_id": hidden.id}), BODY, format="json")

    assert ok.status_code == 201
    assert refused.status_code == 404


@pytest.mark.django_db
def test_state_change_after_lookup_is_caught_under_the_lock(user, another_user):
    prop = _create_property(owner=another_user, title="Raced", status="verified")
    stale = Property.objects.get(pk=prop.pk)  # what the view resolved before the lock
    Property.objects.filter(pk=prop.pk).update(status="hidden")

    with pytest.raises(NotFound):
        PropertyVisitService.create_visit(tenant=user, property_obj=stale, validated_data=dict(BODY))
    assert not PropertyVisit.objects.filter(property=prop).exists()


@pytest.mark.django_db
def test_anonymous_reviews_follow_the_catalog_policy_but_owner_keeps_history(another_user):
    prop = _create_property(owner=another_user, title="Hidden reviews", status="hidden")
    url = reverse("property-review-list", kwargs={"property_id": prop.id})

    assert APIClient().get(url).status_code == 404
    owner = APIClient()
    owner.force_authenticate(another_user)
    assert owner.get(url).status_code == 200


@pytest.mark.django_db
def test_places_exclude_closure_pending_owners(api_client, another_user):
    prop = _create_property(owner=another_user, title="Place", status="verified", district="Zamalek")
    from core_apps.properties.services import PropertyService

    before = PropertyService.get_available_places(prop.property_type)
    AccountClosureRequest.objects.create(user=another_user)
    after = PropertyService.get_available_places(prop.property_type)

    assert any(p["district"] == "Zamalek" for p in before)
    assert not any(p["district"] == "Zamalek" for p in after)
