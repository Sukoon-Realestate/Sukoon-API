"""Stable dashboard ordering even when the host clock produces equal instants."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.properties.models import PropertyVisit
from core_apps.features.tests.test_rental_phase2 import rental_participants  # noqa: F401

pytestmark = pytest.mark.django_db


def test_pending_owner_dashboard_has_stable_newest_first_order_at_equal_creation_times(rental_participants, api_client):
    owner, tenant, _, prop, _ = rental_participants
    rows = [PropertyVisit.objects.create(property=prop, tenant=tenant,
        visit_date=timezone.localdate() + timedelta(days=offset), visit_time='13:00:00',
        status='pending') for offset in [1, 2, 3]]
    PropertyVisit.objects.filter(pk__in=[r.pk for r in rows]).update(created_at=timezone.now())
    api_client.force_authenticate(owner)
    path = reverse('owner-dashboard')
    for _ in range(2):
        response = api_client.get(path)
        assert response.status_code == 200, response.data
        assert [row['id'] for row in response.json()['data']['pending_visits']] == [str(r.id) for r in reversed(rows)]
