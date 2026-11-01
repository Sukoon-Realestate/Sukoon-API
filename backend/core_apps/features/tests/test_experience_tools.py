import uuid
from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.features.experience.access import FEATURES
from core_apps.features.experience.models import ExperiencePreferences, DiscoveryInteraction
from core_apps.features.experience.action_center import ordering
from core_apps.features.planning_models import HousingGroup, GroupMembership
from core_apps.properties.models import PropertyVisit
from .test_rental_phase2 import rental_participants, authenticated  # noqa: F401
from .test_rental_phase3 import phase3_lease  # noqa: F401
from .test_company_contract_preparation import cycle  # noqa: F401
from .test_company_housing import company_setup, policy  # noqa: F401
from .test_company_role_contexts import tenancy  # noqa: F401

pytestmark = pytest.mark.django_db
ROOT = '/api/v1/features/v1/'


@pytest.fixture(autouse=True)
def experience_enabled(settings):
    settings.SOKOUN_EXPERIENCE_FEATURES = list(FEATURES)
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, 'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler'}


def sync(user, content, revision=0, operation=None, **extra):
    return authenticated(user).post(ROOT + 'experience/preferences/?workspace=individual', {
        'operation_id': operation or str(uuid.uuid4()), 'base_revision': revision, 'content': content, **extra,
    }, format='json')


def test_preferences_merge_independent_offline_edits_keep_conflicting_versions(rental_participants):
    _, user, *_ = rental_participants
    a, b = 'home_shortcuts::a', 'home_shortcuts::b'
    assert sync(user, {a: 'first'}).status_code == 200
    assert sync(user, {a: 'device-a'}, 1).status_code == 200
    merged = sync(user, {a: 'first', b: 'new'}, 1).json()['data']
    assert merged['content'] == {a: 'device-a', b: 'new'}
    conflict = sync(user, {a: 'device-b'}, 1).json()['data']
    assert conflict['conflicts'][a]['current'] == 'device-a'
    assert conflict['conflicts'][a]['incoming'] == 'device-b'


def test_deletion_cannot_be_revived_by_old_device_and_operations_are_idempotent(rental_participants):
    _, user, *_ = rental_participants
    key = 'quick_reply_pins::ids'
    operation = str(uuid.uuid4())
    assert sync(user, {key: 'one'}, operation=operation).status_code == 200
    assert sync(user, {key: 'one'}, operation=operation).json()['data']['revision'] == 1
    assert sync(user, {key: 'two'}, operation=operation).status_code == 409
    assert sync(user, {}, 1).status_code == 200
    value = sync(user, {key: 'offline'}, 1).json()['data']
    assert key not in value['content']
    assert value['conflicts'][key]['incoming'] == 'offline'


def test_sync_excludes_recent_history_and_account_company_leaks(rental_participants):
    _, user, stranger, *_ = rental_participants
    assert sync(user, {'recent_views::x': []}).status_code == 400
    assert sync(user, {'discovery_folders::a': {'id': 'a', 'name': 'A', 'items': [], 'recent': []}}).status_code == 400
    assert sync(user, {'company_pins::items': []}).status_code == 400
    assert sync(user, {'home_shortcuts::x': 'saved'}).status_code == 200
    value = authenticated(stranger).get(ROOT + 'experience/preferences/?workspace=individual').json()['data']
    assert value['content'] == {}
    assert authenticated(user).get(ROOT + 'experience/preferences/?workspace=company').status_code == 403


def test_preparation_authority_replay_revision_and_departed_assignee(rental_participants):
    manager, member, stranger, *_ = rental_participants
    group = HousingGroup.objects.create(name='Preparation')
    GroupMembership.objects.create(group=group, user=manager, role='admin', status='active', joined_revision=1)
    membership = GroupMembership.objects.create(group=group, user=member, status='active', joined_revision=1)
    url = ROOT + f'experience/preparation-tasks/?workspace=student&group_id={group.id}'
    command = {'operation_id': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'revision': 0,
        'title': 'Viewing checklist', 'assignee_id': str(member.id), 'status': 'todo'}
    assert authenticated(member).post(url, command, format='json').status_code == 403
    assert authenticated(stranger).get(url).status_code == 404
    response = authenticated(manager).post(url, command, format='json')
    assert response.status_code == 200, response.data
    assert authenticated(manager).post(url, command, format='json').json()['data']['revision'] == 1
    update = {'operation_id': str(uuid.uuid4()), 'id': command['id'], 'revision': 1, 'status': 'in_progress'}
    assert authenticated(member).post(url, update, format='json').status_code == 200
    assert authenticated(member).post(url, {**update, 'operation_id': str(uuid.uuid4())}, format='json').status_code == 409
    membership.status = 'left'; membership.save()
    assert authenticated(member).get(url).status_code == 404
    assert authenticated(manager).get(url).json()['data']['results'][0]['needs_reassignment']
    group.status = 'archived'; group.save()
    update['revision'] = 2
    assert authenticated(manager).post(url, update, format='json').status_code == 403


def test_action_center_uses_current_actor_and_revocation(phase3_lease):
    owner, tenant, lease = phase3_lease
    from core_apps.features.models import PrivateAccessRevocation
    url = ROOT + 'action-center/?workspace=individual&bucket=all'
    response = authenticated(tenant).get(url)
    assert response.status_code == 200, response.data
    PrivateAccessRevocation.objects.create(lease=lease, user=tenant, reason='Revoked')
    assert not any(row['resource_id'] == str(lease.id) for row in authenticated(tenant).get(url).json()['data']['results'])
    assert authenticated(tenant).get(ROOT + 'action-center/?workspace=company').status_code == 403


def test_deadlines_order_before_pagination_with_stable_ties():
    now = timezone.now()
    def item(key, due): return {'id': key, 'due_at': due}
    values = [item('none', None), item('later', now + timedelta(days=5)), item('soon', now + timedelta(hours=3)),
        item('past-b', now - timedelta(hours=1)), item('past-a', now - timedelta(hours=1))]
    assert [r['id'] for r in sorted(values, key=lambda r: ordering(r, now))] == ['past-a', 'past-b', 'soon', 'later', 'none']


def test_calendar_reads_current_authorized_snapshot_only(phase3_lease):
    owner, tenant, lease = phase3_lease
    visit = PropertyVisit.objects.create(property=lease.property, tenant=tenant, status='confirmed',
        visit_date=timezone.localdate(), visit_time='13:00')
    url = ROOT + f'experience/viewings/{visit.id}/calendar/'
    value = authenticated(tenant).get(url).json()['data']
    assert value['starts_at'].startswith(str(visit.visit_date))
    assert value['status'] == 'confirmed'
    assert 'phone' not in value
    visit.refresh_from_db()
    visit.status = 'canceled'; visit.save()
    assert authenticated(tenant).get(url).json()['data']['status'] == 'canceled'


def test_consent_is_required_and_revocation_deletes_signals(rental_participants):
    _, user, _, prop, _ = rental_participants
    url = ROOT + 'experience/discovery-preferences/?workspace=individual'
    event = ROOT + 'experience/discovery-interactions/?workspace=individual'
    offer = prop.rental_inventory['offers'][0]['id']
    body = {'property_id': str(prop.id), 'offer_id': str(offer), 'kind': 'open'}
    assert authenticated(user).post(event, body, format='json').status_code == 403
    prefs = {'priorities': ['price'], 'budget_minor': 500000, 'price_period': 'monthly', 'behavioral_consent': True}
    assert authenticated(user).post(url, prefs, format='json').status_code == 200
    first = authenticated(user).post(event, body, format='json')
    assert first.status_code == 200, first.data
    assert authenticated(user).post(event, body, format='json').status_code == 200
    assert DiscoveryInteraction.objects.count() == 1
    assert authenticated(user).delete(url).status_code == 200
    assert DiscoveryInteraction.objects.count() == 0
    assert not ExperiencePreferences.objects.get(user=user).behavioral_consent


def test_optional_features_default_closed(rental_participants, settings):
    settings.SOKOUN_EXPERIENCE_FEATURES = []
    user = rental_participants[1]
    assert authenticated(user).get(ROOT + 'experience/capabilities/').json()['data']['features'] == []
    assert authenticated(user).get(ROOT + 'action-center/').status_code == 404


def test_analysis_rejects_unbounded_or_non_image_inputs_without_creating_property(rental_participants):
    from core_apps.properties.models import Property
    from core_apps.features.experience.models import ListingAssessment
    user = rental_participants[0]
    before = Property.objects.count()
    response = authenticated(user).post(ROOT + 'experience/listing-assessments/?workspace=owner', {
        'operation_id': str(uuid.uuid4()), 'source_fingerprint': 'a' * 64, 'facts': {'title': 'Private draft'},
        'photos': [{'id': 'x', 'thumbnail': 'not an image'}],
    }, format='json')
    assert response.status_code == 400
    assert Property.objects.count() == before
    assert not ListingAssessment.objects.exists()


def test_sync_rejects_malformed_folders_and_resolves_explicit_conflict(rental_participants):
    _, user, *_ = rental_participants
    key = 'home_shortcuts::a'
    assert sync(user, {'discovery_folders::bad': []}).status_code == 400
    sync(user, {key: 'base'})
    sync(user, {key: 'current'}, 1)
    conflict = sync(user, {key: 'incoming'}, 1).json()['data']
    resolved = sync(user, conflict['content'], conflict['revision'], resolutions={key: 'incoming'})
    assert resolved.status_code == 200
    assert resolved.json()['data']['content'][key] == 'incoming'
    assert resolved.json()['data']['conflicts'] == {}


def test_personalized_order_keeps_eligibility_and_never_uses_parent_room_price(rental_participants):
    from types import SimpleNamespace
    from core_apps.properties.models import Property
    from core_apps.features.experience.discovery import rank
    _, user, _, prop, _ = rental_participants
    ExperiencePreferences.objects.create(user=user, scope='individual', ranking={
        'priorities': ['price', 'space'], 'budget_minor': 1000000, 'price_period': 'monthly', 'space': 80})
    request = SimpleNamespace(user=user, headers={}, query_params={'workspace': 'individual'})
    values = rank(Property.objects.filter(pk=prop.pk), request)
    assert [v.id for v in values] == [prop.id]
    assert values[0]._experience_ranking['unknown'] == ['price', 'space']
    assert not values[0]._experience_ranking['behavior_used']
    assert rank(Property.objects.none(), request) == []
    assert [p.id for p in rank(Property.objects.filter(pk=prop.pk), request)] == [p.id for p in values]


def test_suggestions_are_fresh_dismissible_and_push_is_opt_in(rental_participants):
    from core_apps.properties.models import SavedProperty
    from core_apps.features.experience.suggestions import record_suggestions, event_copy
    from core_apps.features.planning_models import PlanningEvent
    from rest_framework.exceptions import NotFound
    _, user, _, prop, offer = rental_participants
    SavedProperty.objects.create(user=user, property=prop, offer_id=offer)
    prop.status = 'needs_revision'; prop.save()
    item = ExperiencePreferences.objects.create(user=user, scope='individual')
    client = authenticated(user)
    url = ROOT + 'experience/suggestions/?workspace=individual'
    response = client.get(url)
    assert response.status_code == 200, response.data
    row = response.json()['data'][0]
    assert row['title'] == ''
    assert record_suggestions() == 1
    assert record_suggestions() == 0
    event = PlanningEvent.objects.get(recipient=user)
    assert event_copy(event)['push_enabled'] is False
    item.suggestion_push = True; item.save()
    assert event_copy(event)['push_enabled'] is True
    assert client.post(url, {'suggestion_id': row['suggestion_id']}, format='json').status_code == 200
    assert client.get(url).json()['data'] == []
    with pytest.raises(NotFound): event_copy(event)


def test_quality_batches_keep_success_retry_failed_and_expire_private_input(rental_participants, monkeypatch):
    from core_apps.features.experience import quality
    from core_apps.features.experience.models import ListingAssessment
    owner = rental_participants[0]
    item = ListingAssessment.objects.create(owner=owner, operation_id=uuid.uuid4(), fingerprint='x',
        snapshot={'source_fingerprint': 'a' * 64, 'facts': {}, 'photos': [], 'security_epoch': owner.security_epoch},
        batches=[{'index': 0, 'status': 'pending', 'findings': []}, {'index': 1, 'status': 'pending', 'findings': []}],
        expires_at=timezone.now() + timedelta(hours=1))
    calls = []
    def generate(snapshot, index):
        calls.append(index)
        if index == 1: raise quality.DiscoveryUnavailable()
        return [{'target': 'title', 'message': 'Review the title'}]
    monkeypatch.setattr(quality, 'generate', generate)
    quality.analyze(str(item.id)); item.refresh_from_db()
    assert item.status == 'partial'
    assert item.batches[0]['status'] == 'complete'
    monkeypatch.setattr(quality.analyze, 'delay', lambda *_: None)
    response = authenticated(owner).post(ROOT + f'experience/listing-assessments/{item.id}/?workspace=owner', {}, format='json')
    assert response.status_code == 200
    item.refresh_from_db()
    assert item.batches[0]['status'] == 'complete'
    assert item.batches[1]['status'] == 'pending'
    quality.analyze(str(item.id)); assert calls == [0, 1, 1]
    item.expires_at = timezone.now() - timedelta(seconds=1); item.save()
    quality.purge_snapshots(); item.refresh_from_db()
    assert item.snapshot == {} and item.batches == [] and item.status == 'expired'


def test_quality_stalled_attempt_can_be_retried_without_overwriting_later_result(rental_participants):
    from core_apps.features.experience.quality import recover_stalled
    from core_apps.features.experience.models import ListingAssessment
    item = ListingAssessment.objects.create(owner=rental_participants[0], operation_id=uuid.uuid4(), fingerprint='x',
        batches=[{'index': 0, 'status': 'running', 'attempt': 'old', 'started_at': (timezone.now() - timedelta(minutes=6)).isoformat()}],
        expires_at=timezone.now() + timedelta(hours=1))
    recover_stalled(item)
    assert item.batches[0]['status'] == 'failed' and item.batches[0]['attempt'] == ''


def test_company_preparation_rejects_wrong_role_and_company(rental_participants):
    from core_apps.features.company_models import Company, CompanyMembership, CompanyHousingRequest
    owner, user, stranger, *_ = rental_participants
    company = Company.objects.create(name='Team', registration_number='synthetic', contact_email='test@example.com')
    CompanyMembership.objects.create(company=company, user=owner, is_coordinator=True)
    CompanyMembership.objects.create(company=company, user=user, is_employee=True)
    today = timezone.localdate()
    request = CompanyHousingRequest.objects.create(company=company, requester=owner, coordinator=owner,
        title='Team housing', purpose='Synthetic', location='Cairo', starts_on=today, ends_on_exclusive=today+timedelta(days=30),
        headcount=2, commitment_ceiling_minor=100000, deposit_limit_minor=10000)
    path = ROOT + f'experience/preparation-tasks/?workspace=company&request_id={request.id}'
    body = {'operation_id': str(uuid.uuid4()), 'id': str(uuid.uuid4()), 'revision': 0, 'title': 'Prepare documents', 'assignee_id': str(user.id)}
    manager = authenticated(owner); manager.credentials(HTTP_X_SUKOON_COMPANY_ID=str(company.id), HTTP_X_SUKOON_COMPANY_ROLE='coordinator')
    assert manager.post(path, body, format='json').status_code == 200
    employee = authenticated(user); employee.credentials(HTTP_X_SUKOON_COMPANY_ID=str(company.id), HTTP_X_SUKOON_COMPANY_ROLE='employee')
    result = employee.get(path)
    assert result.status_code == 200, result.data
    assert result.json()['data']['results'][0]['can_update']
    employee.credentials(HTTP_X_SUKOON_COMPANY_ID=str(company.id), HTTP_X_SUKOON_COMPANY_ROLE='coordinator')
    assert employee.get(path).status_code == 403
    company.memberships.filter(user=user).update(is_active=False)
    employee.credentials(HTTP_X_SUKOON_COMPANY_ID=str(company.id), HTTP_X_SUKOON_COMPANY_ROLE='employee')
    assert employee.get(path).status_code in [403, 404]


def test_quality_valid_private_request_is_idempotent_and_requires_current_owner_context(rental_participants, monkeypatch):
    from io import BytesIO
    from base64 import b64encode
    from PIL import Image
    from core_apps.features.experience import quality
    from core_apps.features.experience.models import ListingAssessment
    owner, _, stranger, prop, *_ = rental_participants
    before = prop.updated_at
    file = BytesIO(); Image.new('RGB', (32, 32), 'white').save(file, format='JPEG')
    body = {'operation_id': str(uuid.uuid4()), 'facts': {'title': 'Supplied title'}, 'language': 'ar',
        'source_fingerprint': 'a' * 64, 'photos': [{'id': 'photo-a', 'thumbnail': b64encode(file.getvalue()).decode()}]}
    monkeypatch.setattr(quality, 'configured', lambda: True)
    monkeypatch.setattr(quality.analyze, 'delay', lambda *_: None)
    path = ROOT + 'experience/listing-assessments/?workspace=owner'
    response = authenticated(owner).post(path, body, format='json')
    assert response.status_code == 202, response.data
    assert authenticated(owner).post(path, body, format='json').status_code == 200
    assert ListingAssessment.objects.count() == 1
    identity = response.json()['data']['id']
    assert authenticated(stranger).get(ROOT + f'experience/listing-assessments/{identity}/?workspace=owner').status_code == 404
    assert authenticated(owner).get(ROOT + f'experience/listing-assessments/{identity}/?workspace=individual').status_code == 403
    assert authenticated(owner).post(path, {**body, 'facts': {'title': 'Changed title'}}, format='json').status_code == 409
    prop.refresh_from_db(); assert prop.updated_at == before


def test_suggestion_delivery_without_opt_in_stays_in_inbox(rental_participants, monkeypatch):
    from core_apps.properties.models import SavedProperty
    from core_apps.features.experience.suggestions import record_suggestions
    from core_apps.features.services.planning_notifications import deliver_planning_events
    from core_apps.features.planning_models import PlanningEvent
    _, user, _, prop, offer = rental_participants
    SavedProperty.objects.create(user=user, property=prop, offer_id=offer)
    prop.status = 'needs_revision'; prop.save()
    ExperiencePreferences.objects.create(user=user, scope='individual')
    record_suggestions()
    calls = []
    monkeypatch.setattr('core_apps.notifications.services.push_delivery.queue_notification', lambda n: calls.append(n.pk))
    assert deliver_planning_events(event_kinds=['experience_suggestion']) == 1
    event = PlanningEvent.objects.get(recipient=user)
    assert event.notification_id is not None
    assert event.delivery_status == 'inbox_only'
    assert calls == []


def test_company_sync_rejects_embedded_other_company_or_role():
    import base64
    from rest_framework.exceptions import ValidationError
    from core_apps.features.experience.sync import validate_scope
    def key(namespace, scope):
        return namespace + ':' + base64.urlsafe_b64encode(scope.encode()).decode() + ':items'
    validate_scope({key('company_pins', 'c/c:payer'): []}, 'company/c/payer')
    validate_scope({key('home_shortcuts', 'company/c:payer'): 'rentals'}, 'company/c/payer')
    for namespace, record in [('company_pins', 'other/c:payer'), ('company_pins', 'c/c:signer'),
                              ('company_pins', 'c/c:payer-extra'), ('discovery_pins', 'c/c:payer')]:
        with pytest.raises(ValidationError):
            validate_scope({key(namespace, record): []}, 'company/c/payer')


def test_quality_lost_queue_can_be_recovered_without_repeating_completed_batches(rental_participants):
    from core_apps.features.experience.models import ListingAssessment
    from core_apps.features.experience.quality import recover_stalled
    item = ListingAssessment.objects.create(owner=rental_participants[0], operation_id=uuid.uuid4(),
        fingerprint='x', expires_at=timezone.now() + timedelta(hours=1),
        batches=[{'index': 0, 'status': 'complete', 'findings': [{'target': 'title', 'message': 'Keep me'}]},
                 {'index': 1, 'status': 'pending', 'queued_at': (timezone.now() - timedelta(minutes=6)).isoformat()}])
    recover_stalled(item)
    item.refresh_from_db()
    assert item.status == 'partial'
    assert item.batches[0]['findings'][0]['message'] == 'Keep me'
    assert item.batches[1]['status'] == 'failed'


def test_action_center_excludes_paid_company_invoices_and_waits_for_payment_authority(tenancy):
    from core_apps.features.models import RentInvoice
    actors, item = tenancy
    invoice = RentInvoice.objects.create(lease=item.lease, purpose='rent', amount_minor=125,
        charges_minor=125, due_date=timezone.localdate(), reference='EXPERIENCE-COMPANY-WAIT')
    signer = authenticated(actors['signer'])
    signer.credentials(HTTP_X_SUKOON_COMPANY_ID=str(actors['company'].id), HTTP_X_SUKOON_COMPANY_ROLE='signer')
    sign_rows = signer.get(ROOT + 'action-center/?workspace=company&bucket=required').json()['data']['results']
    assert any(row['target_id'] == str(item.id) and row['reason'] == 'review' for row in sign_rows)
    payer = authenticated(actors['payer'])
    payer.credentials(HTTP_X_SUKOON_COMPANY_ID=str(actors['company'].id), HTTP_X_SUKOON_COMPANY_ROLE='payer')
    path = ROOT + 'action-center/?workspace=company&bucket=all'
    response = payer.get(path)
    assert response.status_code == 200, response.data
    rows = response.json()['data']['results']
    row = next(row for row in rows if row['target_id'] == str(invoice.id))
    # A draft contract has no current payment authority, even for its payer.
    assert row['bucket'] == 'waiting'
    assert row['due_at'] and row['revision'] == invoice.revision
    invoice.status = 'paid'; invoice.applied_minor = 125; invoice.save()
    assert not any(row['target_id'] == str(invoice.id) for row in payer.get(path).json()['data']['results'])


def test_bounded_worker_processes_one_requested_analysis_batch_without_replay(rental_participants, monkeypatch):
    from core_apps.features.experience import quality
    from core_apps.features.experience.models import ListingAssessment
    owner = rental_participants[0]
    now = timezone.now()
    item = ListingAssessment.objects.create(owner=owner, operation_id=uuid.uuid4(), fingerprint='q',
        snapshot={'security_epoch': owner.security_epoch, 'facts': {'title': 'Requested home'}, 'photos': []},
        expires_at=now + timedelta(hours=1),
        batches=[{'index': i, 'status': 'pending', 'queued_at': now.isoformat()} for i in range(2)])
    calls = []
    monkeypatch.setattr(quality, 'configured', lambda: True)
    monkeypatch.setattr(quality, 'generate', lambda snapshot, index: calls.append(index) or [])
    assert quality.process_pending_assessments() == 1
    item.refresh_from_db()
    assert [b['status'] for b in item.batches] == ['complete', 'pending']
    assert quality.process_pending_assessments() == 1
    assert quality.process_pending_assessments() == 0
    assert calls == [0, 1]
    item.refresh_from_db()
    assert item.status == 'complete'
