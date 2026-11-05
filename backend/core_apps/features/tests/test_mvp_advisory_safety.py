"""Personal notes and alerts do not reserve accommodation or approve a listing."""
from copy import deepcopy
from uuid import uuid4

import pytest

from core_apps.features.models import Lease, TenancyInvitation
from core_apps.properties.models import PropertyVisit
from .test_rental_phase2 import rental_participants, authenticated  # noqa: F401
from .test_decision_notebooks import sync, content, note

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('tool', ['notebook', 'search_alert'])
def test_personal_advisory_tools_cannot_reserve_reprice_or_approve_accommodation(rental_participants, tool):
    _, tenant, _, prop, offer = rental_participants
    before = (prop.price, deepcopy(prop.rental_inventory), prop.status, prop.is_verified)
    if tool == 'notebook':
        response = sync(tenant, content(note('Synthetic private decision note', property_id=str(prop.id), offer_id=offer)))
        assert response.status_code == 200, response.data
    else:
        response = authenticated(tenant).post('/api/v1/features/v1/search-alerts/', {
            'name': 'Synthetic advisory alert', 'cadence': 'daily', 'filters': {},
            'request_key': str(uuid4()),
        }, format='json')
        assert response.status_code == 201, response.data
    prop.refresh_from_db()
    assert (prop.price, prop.rental_inventory, prop.status, prop.is_verified) == before
    assert not Lease.objects.exists() and not TenancyInvitation.objects.exists()
    assert not PropertyVisit.objects.exists()
