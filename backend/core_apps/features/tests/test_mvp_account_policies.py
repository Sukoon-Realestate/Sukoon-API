"""Publish the existing account assurance rules without enabling rental actions."""
from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
from datetime import timedelta
import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.admin_api.models import StaffProfile
from core_apps.features.models import PolicyDecision, PolicyDecisionHead
from core_apps.features.services import business_policies as policies
from core_apps.features.services.business_policy_catalog import CATALOG
from core_apps.features.services.business_policy_mvp import ACCOUNT_ACTIONS
from core_apps.features.services.policy_registry import approved_policy
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.users.models import SensitiveAuthorization
from core_apps.users.services import sensitive_actions
from core_apps.users.services.sessions import issue_refresh
from .test_business_policies import body, client, policy_admin  # noqa: F401

pytestmark = pytest.mark.django_db
API = '/api/v1/features/v1/'


def test_account_policy_publication_replay_history_and_active_scope(policy_admin):
    actor = client(policy_admin)
    templates = actor.get(API + 'operator/business-policies/').json()['data']['items']
    assert len(templates) == 1 and templates[0]['code'] == 'D26'
    assert templates[0]['scope'] == list(ACCOUNT_ACTIONS)
    assert not PolicyDecision.objects.exists()
    command = body('D26')
    first = actor.post(API + 'operator/business-policies/', command, format='json')
    replay = actor.post(API + 'operator/business-policies/', command, format='json')
    assert first.status_code == replay.status_code == 201
    assert first.json() == replay.json()
    original = PolicyDecision.objects.get()
    snapshot = policies.snapshot(original)
    assert set(original.scope) == set(ACCOUNT_ACTIONS)
    for action in ACCOUNT_ACTIONS:
        assert approved_policy('D26', action) == original
    for action in ['private.export', 'payout.execute', 'refund.execute', 'company.member.update']:
        with pytest.raises(RentalConflict):
            approved_policy('D26', action)
    assert actor.post(API + 'operator/business-policies/', body('D26'), format='json').status_code == 409
    second = actor.post(API + 'operator/business-policies/', body('D26', revision=1, proof_lifetime_seconds=120), format='json')
    assert second.status_code == 201
    original.refresh_from_db()
    assert policies.snapshot(original) == snapshot
    assert PolicyDecisionHead.objects.get().revision == 2
    for language in ['ar', 'en']:
        public = client().get(API + 'business-policies/', HTTP_ACCEPT_LANGUAGE=language).json()['data']['items']
        assert len(public) == 1 and public[0]['code'] == 'D26'
        assert public[0]['title'] and len(public[0]['values']) == 1
        assert not {'approver', 'rules', 'audit_reason', 'evidence_reference'} & public[0].keys()
        if os.environ.get('MVP_FIXTURE_DIR'):
            directory = Path(os.environ['MVP_FIXTURE_DIR'])
            directory.mkdir(parents=True, exist_ok=True)
            (directory / f'mvp-account-policy-{language}.json').write_text(json.dumps({'items': public}), encoding='utf-8')
    assert client().get(API + f'business-policies/D26/versions/{original.version}/').status_code == 200


@pytest.mark.parametrize('code', [key for key in CATALOG if key != 'D26'])
def test_mvp_cannot_publish_or_disclose_deferred_policy_family(policy_admin, code):
    response = client(policy_admin).post(API + 'operator/business-policies/', body(code), format='json')
    assert response.status_code == 403 and not PolicyDecision.objects.exists()
    assert client().get(API + f'business-policies/{code}/versions/old/').status_code == 403


def test_current_staff_authority_is_rechecked_even_for_cached_superuser(policy_admin):
    profile = StaffProfile.objects.create(user=policy_admin, role_name='system_owner')
    policies.publish(policy_admin, body('D26'))
    profile.is_active = False
    profile.save(update_fields=['is_active'])
    with pytest.raises(PermissionDenied):
        policies.publish(policy_admin, body('D26', revision=1))
    assert PolicyDecision.objects.count() == 1


def test_published_account_policy_has_real_action_bound_consumer(policy_admin, another_user, settings, monkeypatch):
    settings.SECURITY_TEST_BYPASS = False
    settings.SECURITY_ASSURANCE_PROVIDER = ''
    another_user.is_email_verified = True
    another_user.save(update_fields=['is_email_verified'])
    policies.publish(policy_admin, body('D26'))
    from core_apps.users.services import assurance
    monkeypatch.setattr(assurance, 'generate_otp', lambda: '135790')
    monkeypatch.setattr(assurance, 'send_otp_email', lambda *args, **kwargs: True)
    request = SimpleNamespace(user=another_user, auth=issue_refresh(another_user).access_token, data={}, headers={})
    data = {'action': 'account.contact.change', 'resource_id': str(uuid4()),
            'resource_revision': 1, 'payload': {'email': 'synthetic@sokoun.test'}}
    challenge = sensitive_actions.begin(request, data)
    item = SensitiveAuthorization.objects.get(id=challenge['id'])
    original_policy_id = item.policy_id
    assert item.code_hash and item.action == data['action']
    proof = sensitive_actions.verify(request, item.id, '135790')
    request.headers['X-Sokoun-Authorization'] = proof['proof']
    policies.publish(policy_admin, body('D26', revision=1, proof_lifetime_seconds=120))
    with pytest.raises(PermissionDenied), transaction.atomic():
        sensitive_actions.consume(request, action=data['action'], resource_id=data['resource_id'],
            revision=data['resource_revision'], payload=data['payload'])
    item.refresh_from_db()
    assert item.policy_id == original_policy_id and item.consumed_at is None
    SensitiveAuthorization.objects.filter(pk=item.pk).update(created_at=timezone.now() - timedelta(seconds=61))
    challenge = sensitive_actions.begin(request, data)
    proof = sensitive_actions.verify(request, challenge['id'], '135790')
    request.headers['X-Sokoun-Authorization'] = proof['proof']
    with transaction.atomic():
        sensitive_actions.consume(request, action=data['action'], resource_id=data['resource_id'],
            revision=data['resource_revision'], payload=data['payload'])
    assert SensitiveAuthorization.objects.get(id=challenge['id']).consumed_at is not None
    with pytest.raises(PermissionDenied), transaction.atomic():
        sensitive_actions.consume(request, action=data['action'], resource_id=data['resource_id'],
            revision=data['resource_revision'], payload=data['payload'])


def test_disabled_release_retains_original_policy_catalog(settings):
    settings.SUKOON_MVP = False
    assert set(policies.publication_codes()) == set(CATALOG)
    assert policies.publication_definition('D26') == deepcopy(CATALOG['D26'])
