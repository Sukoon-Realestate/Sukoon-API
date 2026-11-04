"""Reuse owner inventory contracts without enabling a company or rental."""
import pytest
from core_apps.properties.models import Property, ResidentialBuilding
from core_apps.features.company_models import Company
from core_apps.features.models import Lease, TenancyInvitation
from core_apps.features.services.company import portfolio
from .test_rental_phase2 import rental_participants  # noqa: F401
from . import test_portfolio_owner_workflows as contracts


@pytest.fixture
def owner_portfolio(rental_participants):
    owner, other, stranger, prop, _ = rental_participants
    building = ResidentialBuilding.objects.create(manager=owner,
        name='Synthetic owner building', code='A', address='Synthetic Cairo',
        declared_units=2, authority_status='verified', authority_reviewed_by=owner,
        authority_reference='isolated-fixture')
    prop.building, prop.unit_code, prop.occupancy_capacity = building, '101', 4
    prop.save()
    second = Property.objects.create(
        **{key: getattr(prop, key) for key in portfolio.TEMPLATE_FIELDS},
        owner=owner, building=building, unit_code='102', occupancy_capacity=4,
        status='verified', is_verified=True, is_ownership_verified=True)
    return owner, other, stranger, None, building, [prop, second], None, None


def assert_no_deferred_records():
    assert not Company.objects.exists()
    assert not Lease.objects.exists()
    assert not TenancyInvitation.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize('contract', [
    'test_edit_asset_facts_private_fields_and_mode_validation',
    'test_bulk_inheritance_preserves_explicit_values_and_tracks_resets',
    'test_bulk_stale_unit_partial_results_and_idempotent_api',
    'test_merge_retains_both_originals',
    'test_move_preserves_ids_and_requires_destination_authority',
    'test_changed_child_defaults_invalidate_complex_bulk_preview',
    'test_whole_topology_change_rolls_back_on_duplicate_target_code',
    'test_preview_history_is_owner_scoped_and_recoverable',
])
def test_existing_owner_contract_without_company(owner_portfolio, contract):
    assert_no_deferred_records()
    getattr(contracts, contract)(owner_portfolio)
    assert_no_deferred_records()


@pytest.mark.django_db(transaction=True)
def test_owner_bulk_competing_apply_uses_one_receipt(owner_portfolio):
    contracts.test_competing_bulk_apply_cannot_overwrite_twice(owner_portfolio)
    assert_no_deferred_records()
