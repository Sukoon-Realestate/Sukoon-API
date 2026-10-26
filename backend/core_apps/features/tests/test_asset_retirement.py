"""C70/C71 removal must not remove C18/C35-C38/C86 resources."""
import uuid
from datetime import timedelta
from django.apps import apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import Resolver404, resolve
from django.utils import timezone
import pytest
from core_apps.features.models import Lease, RentalEvidence, RentalHandover, MaintenanceRequest, RentalOperationalCase
from core_apps.features.tests.test_rental_phase5 import phase5_lease


@pytest.mark.parametrize('path', [
    'asset-passport-destinations/', 'properties/{id}/asset-items/', 'properties/{id}/asset-spaces/',
    'asset-items/{id}/', 'asset-items/{id}/sources/', 'asset-items/{id}/observe/',
    'asset-items/{id}/review-workspace/', 'asset-items/{id}/analysis/', 'asset-items/{id}/shared-systems/',
    'asset-items/{id}/warranties/', 'asset-analysis-jobs/{id}/', 'asset-analysis-jobs/{id}/cancel/',
    'asset-analysis-findings/{id}/review/', 'asset-shared-systems/{id}/cases/',
    'asset-pattern-cases/{id}/close/', 'asset-warranties/{id}/claim/',
])
def test_retired_routes_have_no_handler(path):
    with pytest.raises(Resolver404):
        resolve('/api/v1/features/v1/' + path.format(id=uuid.uuid4()))


def test_retired_capabilities_are_absent_even_from_stale_deployment_settings(settings):
    from config.advanced_housing import SERVICES, provider_configuration
    from core_apps.features.services.planning_parts.selection_payload import enabled_services
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = ['asset_passport', 'asset_assisted_analysis', 'corporate_housing_simulation']
    assert 'asset_passport' not in SERVICES
    assert 'asset_assisted_analysis' not in provider_configuration()
    assert set(enabled_services()).isdisjoint({'asset_passport', 'asset_assisted_analysis'})
    assert 'corporate_housing_simulation' in enabled_services()
    assert apps.get_model('features', 'Lease') is Lease
    with pytest.raises(LookupError):
        apps.get_model('features', 'AssetItem')


@pytest.mark.django_db(transaction=True)
def test_retirement_migration_preserves_shared_evidence_lease_maintenance_and_case(phase5_lease):
    owner, tenant, lease = phase5_lease
    today = timezone.localdate()
    evidence = RentalEvidence.objects.create(lease=lease, uploader=tenant, request_key=uuid.uuid4(),
        original_name='condition.png', content_type='image/png', size_bytes=7,
        sha256='a' * 64, storage_key=f'isolated-{uuid.uuid4()}', malware_status='safe', private_content=b'fixture')
    handover = RentalHandover.objects.create(lease=lease, kind='move_in', possession_on=today)
    handover.evidence.add(evidence)
    maintenance = MaintenanceRequest.objects.create(lease=lease, reporter=tenant, title='Existing repair',
        description='Keep this case', category='plumbing', priority='normal')
    maintenance.evidence.add(evidence)
    case = RentalOperationalCase.objects.create(lease=lease, property=lease.property, source_key=f'warranty:{uuid.uuid4()}',
        kind='maintenance', reason='Existing service history', next_action='Review existing record', due_at=timezone.now())
    case.evidence.add(evidence)
    executor = MigrationExecutor(connection)
    restore_targets = executor.loader.graph.leaf_nodes()
    target = ('features', '0077_remove_assetanalysissuggestion_job_and_more')
    previous = ('features', '0076_rentalchange_content_revision_rentalchangeversion_and_more')
    try:
        executor.migrate([previous])
        historical = executor.loader.project_state([previous]).apps
        Asset = historical.get_model('features', 'AssetItem')
        asset = Asset.objects.create(property_id=lease.property_id, registered_by_id=owner.pk, label='Fixture only', category='appliance')
        observation = historical.get_model('features', 'AssetObservation').objects.create(asset=asset,
            property_id=lease.property_id, lease_id=lease.pk, author_id=tenant.pk,
            observed_on=today, source_kind='handover', source_id=handover.id, source_revision=1, source_status='draft')
        observation.evidence.add(evidence.pk)
        historical.get_model('features', 'AssetWarrantyReference').objects.create(asset=asset,
            created_by_id=owner.pk, service_case_id=case.pk, issuer='Fixture', reference='Fixture only',
            starts_on=today, ends_on_exclusive=today+timedelta(days=1),
            source_kind='handover', source_id=handover.id, source_revision=1)
        historical.get_model('features', 'AssetAnalysisJob').objects.create(asset=asset,
            created_by_id=owner.pk, source_manifest={}, source_digest='a'*64)
        assert observation.evidence.count() == 1
        MigrationExecutor(connection).migrate([target])
    finally:
        MigrationExecutor(connection).migrate(restore_targets)
    assert not any(name.startswith('features_asset') for name in connection.introspection.table_names())
    for item in [lease, lease.property, evidence, handover, maintenance, case]:
        item.refresh_from_db()
    assert bytes(evidence.private_content) == b'fixture'
    assert list(handover.evidence.values_list('pk', flat=True)) == [evidence.pk]
    assert list(maintenance.evidence.values_list('pk', flat=True)) == [evidence.pk]
    assert list(case.evidence.values_list('pk', flat=True)) == [evidence.pk]
    assert lease.status == 'active' and case.status == 'open'
