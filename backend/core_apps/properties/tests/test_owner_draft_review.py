import pytest
from django.urls import reverse
from core_apps.common.models import ContentView
from .test_views import _create_published_property

pytestmark = pytest.mark.django_db


def test_owner_review_is_private_passive_and_owner_only(api_client, user, another_user):
    prop = _create_published_property(owner=user, price=1000)
    path = reverse('owner-draft-review', kwargs={'property_id': prop.id})
    before = ContentView.objects.count()
    api_client.force_authenticate(user=user)
    response = api_client.get(path)
    assert response.status_code == 200
    assert response['Cache-Control'] == 'private, no-store'
    assert str(response.data['id']) == str(prop.id)
    assert ContentView.objects.count() == before
    api_client.force_authenticate(user=another_user)
    assert api_client.get(path).status_code == 404
    api_client.force_authenticate(user=None)
    assert api_client.get(path).status_code in (401, 403)
    assert ContentView.objects.count() == before
