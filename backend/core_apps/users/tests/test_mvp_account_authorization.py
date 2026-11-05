"""Active personal-account action proofs; no rental or financial command runs."""
from datetime import timedelta
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, PermissionDenied

from core_apps.users.models import SensitiveAuthorization
from core_apps.users.services import sensitive_actions
from core_apps.users.services.sessions import revoke_all
from .test_totp_recovery import actors, request  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def account_proof(actors, user):
    user.is_email_verified = True
    user.save(update_fields=['is_email_verified'])
    req = request(user)
    data = {'action': 'account.contact.change', 'resource_id': str(user.id),
            'resource_revision': 3, 'payload': {'email': 'synthetic-new@example.invalid'}}
    with patch('core_apps.users.services.assurance.generate_otp', return_value='246810'), patch(
        'core_apps.users.services.assurance.send_otp_email', return_value=True,
    ):
        challenge = sensitive_actions.begin(req, data)
    proof = sensitive_actions.verify(req, challenge['id'], '246810')
    req.headers['X-Sokoun-Authorization'] = proof['proof']
    return req, data, SensitiveAuthorization.objects.get(id=challenge['id'])


def consume(req, data):
    with transaction.atomic():
        sensitive_actions.consume(req, action=data['action'], resource_id=data['resource_id'],
            revision=data['resource_revision'], payload=data['payload'])


@pytest.mark.parametrize('change', ['session', 'resource', 'revision', 'payload', 'action', 'expiry'])
def test_personal_action_proof_is_single_use_short_lived_and_bound_to_exact_command(account_proof, change):
    req, data, proof = account_proof
    assert proof.expires_at <= timezone.now() + timedelta(minutes=5)
    changed = dict(data)
    attempted = req
    if change == 'session':
        attempted = request(req.user)
        attempted.headers = dict(req.headers)
    elif change == 'resource':
        changed['resource_id'] = str(uuid4())
    elif change == 'revision':
        changed['resource_revision'] = 4
    elif change == 'payload':
        changed['payload'] = {'email': 'another@example.invalid'}
    elif change == 'action':
        changed['action'] = 'account.closure.request'
    else:
        SensitiveAuthorization.objects.filter(pk=proof.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(PermissionDenied):
        consume(attempted, changed)
    proof.refresh_from_db()
    assert proof.consumed_at is None
    if change != 'expiry':
        consume(req, data)
        with pytest.raises(PermissionDenied):
            consume(req, data)


def test_personal_action_proof_cannot_bypass_a_new_account_freeze(account_proof):
    req, data, proof = account_proof
    revoke_all(req.user, freeze=True)
    with pytest.raises(APIException) as denied:
        consume(req, data)
    assert denied.value.status_code in {401, 403}
    proof.refresh_from_db()
    assert proof.consumed_at is None  # The blocked command was never executed.
    assert proof.session.revoked_at is not None
