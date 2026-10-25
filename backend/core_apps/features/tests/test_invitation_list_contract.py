"""The server filters authorized collections before pagination."""
import copy
import uuid

import pytest
from core_apps.properties.models import PropertyVisit
from .test_tenancy_invitations import (  # noqa: F401
    authenticated, create_invitation, owned_property, participants,
)


@pytest.mark.django_db
@pytest.mark.parametrize('workspace', ['owner', 'tenant'])
def test_invitation_property_filter_and_actor_scope(participants, owned_property, workspace):
    owner, tenant, stranger = participants
    other = copy.copy(owned_property)
    other.pk = None
    other.id = uuid.uuid4()
    other.save()
    first_visit = PropertyVisit.objects.get(property=owned_property, tenant=tenant)
    PropertyVisit.objects.create(
        property=other, tenant=tenant, visit_date=first_visit.visit_date,
        visit_time=first_visit.visit_time, status=PropertyVisit.Status.CONFIRMED,
    )
    first, _ = create_invitation(owner, tenant, owned_property)
    second, _ = create_invitation(owner, tenant, other)
    assert first.status_code == second.status_code == 201
    actor = owner if workspace == 'owner' else tenant
    url = '/api/v1/features/v1/tenancy-invitations/'
    selected = authenticated(actor).get(url, {
        'workspace': workspace, 'property_id': str(owned_property.id),
        'page': 1, 'page_size': 1,
    })
    assert selected.status_code == 200
    assert selected.data['count'] == 1
    assert [row['id'] for row in selected.data['results']] == [first.data['id']]
    assert selected.data['next'] is None
    hidden = authenticated(stranger).get(url, {'workspace': workspace})
    assert hidden.status_code == 200
    assert hidden.data['count'] == 0
    assert hidden.data['results'] == []
