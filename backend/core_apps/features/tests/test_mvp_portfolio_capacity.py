"""Count physical owner units once across nested and standalone inventory."""
import pytest
from django.db import IntegrityError, transaction

from core_apps.properties.models import Property, ResidentialComplex
from core_apps.features.services.company import portfolio
from .test_mvp_owner_portfolio import owner_portfolio, assert_no_deferred_records  # noqa: F401
from .test_rental_phase2 import rental_participants  # noqa: F401

pytestmark = pytest.mark.django_db


def test_owner_complex_capacity_counts_nested_and_standalone_units_once(owner_portfolio):
    owner, _, _, _, building, props, *_ = owner_portfolio
    complex_obj = ResidentialComplex.objects.create(manager=owner, name='Synthetic complex',
        code='S', address='Synthetic Cairo', declared_standalone_units=1)
    building.complex = complex_obj
    building.save(update_fields=['complex'])
    standalone = Property.objects.create(
        **{key: getattr(props[0], key) for key in portfolio.TEMPLATE_FIELDS},
        owner=owner, complex=complex_obj, unit_code='S1', occupancy_capacity=3,
    )
    data = portfolio.container_payload(complex_obj)
    assert data['registered_units'] == 3 and data['capacity'] == 11
    assert {row['id'] for row in data['units']} == {str(p.id) for p in [*props, standalone]}
    assert data['buildings'][0]['registered_units'] == 2
    assert_no_deferred_records()


def test_owner_inventory_rejects_two_physical_parents_and_keeps_unknown_capacity(owner_portfolio):
    owner, _, _, _, building, props, *_ = owner_portfolio
    complex_obj = ResidentialComplex.objects.create(manager=owner, name='Synthetic complex',
        code='S', address='Synthetic Cairo', declared_standalone_units=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        Property.objects.filter(pk=props[0].pk).update(complex=complex_obj)
    props[0].refresh_from_db()
    assert props[0].complex_id is None and props[0].building_id == building.pk
    props[0].occupancy_capacity = None
    props[0].save(update_fields=['occupancy_capacity'])
    assert portfolio.container_payload(building)['capacity'] is None
    assert_no_deferred_records()
