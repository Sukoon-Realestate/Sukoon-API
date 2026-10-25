from decimal import Decimal

import pytest
from django.urls import reverse
from core_apps.properties.models import Property
from core_apps.properties.serializers import PropertyListSerializer, PropertyNewListSerializer
from core_apps.properties.tests.test_views import _create_property


@pytest.mark.django_db
@pytest.mark.parametrize('latitude,longitude', [('30.044400', '31.235700'), (None, None)])
def test_public_listing_includes_map_coordinates_without_inventing_missing_locations(api_client, user, latitude, longitude):
    prop = _create_property(owner=user, status=Property.Status.VERIFIED,
                            latitude=latitude, longitude=longitude)
    response = api_client.get(reverse('property-list'))
    assert response.status_code == 200
    row = next(item for item in response.json()['data'] if item['id'] == str(prop.id))
    if latitude is None:
        assert row['latitude'] is None and row['longitude'] is None
    else:
        assert Decimal(row['latitude']) == Decimal(latitude)
        assert Decimal(row['longitude']) == Decimal(longitude)


@pytest.mark.django_db
@pytest.mark.parametrize('serializer', [PropertyListSerializer, PropertyNewListSerializer])
def test_both_listing_serializers_keep_coordinates(user, serializer):
    prop = _create_property(owner=user, latitude='0.000000', longitude='0.000000')
    row = serializer(prop).data
    assert Decimal(row['latitude']) == 0
    assert Decimal(row['longitude']) == 0
