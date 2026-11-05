"""Mailbox replacement and real local TOTP proofs for active account contact changes."""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from core_apps.users.models import EmailChange, SensitiveAuthorization, TotpFactor
from core_apps.users.services import sensitive_actions, totp
from .test_email_change import mailbox, start  # noqa: F401
from .test_totp_recovery import actors, request  # noqa: F401

pytestmark = pytest.mark.django_db


def test_replacing_new_mailbox_invalidates_its_previous_code(mailbox, user):
    client, mail = mailbox
    with patch('core_apps.users.services.email_change.secrets.randbelow', side_effect=[111111, 222222, 333333]):
        identity = start(client)
        prefix = f'/api/v1/auth/email-change/{identity}/'
        assert client.post(prefix + 'verify-old/', {'otp': '111111'}).status_code == 200
        assert client.post(prefix + 'new-email/', {'email': 'first@example.invalid'}).status_code == 200
        EmailChange.objects.filter(pk=identity).update(resend_at=timezone.now() - timedelta(seconds=1))
        assert client.post(prefix + 'new-email/', {'email': 'second@example.invalid'}).status_code == 200
    assert mail.call_args.args == ('second@example.invalid', '333333')
    assert client.post(prefix + 'confirm/', {'otp': '222222'}).status_code == 400
    user.refresh_from_db()
    assert user.email != 'second@example.invalid'
    assert client.post(prefix + 'confirm/', {'otp': '333333'}).status_code == 200
    user.refresh_from_db()
    assert user.email == 'second@example.invalid' and not user.is_verified


@pytest.mark.parametrize('changed_payload', [False, True])
def test_staff_mailbox_codes_require_an_exact_totp_bound_change(actors, changed_payload):
    account = actors[0]
    req = request(account)
    client = APIClient()
    client.force_authenticate(user=account, token=req.auth)
    email = 'staff-new@example.invalid'
    with patch('core_apps.users.services.email_change.send_otp_email', return_value=True) as mail:
        identity = start(client)
        prefix = f'/api/v1/auth/email-change/{identity}/'
        assert client.post(prefix + 'verify-old/', {'otp': mail.call_args.args[1]}).status_code == 200
        assert client.post(prefix + 'new-email/', {'email': email}).status_code == 200
        code = mail.call_args.args[1]
    assert client.post(prefix + 'confirm/', {'otp': code}).status_code == 403
    challenge = sensitive_actions.begin(req, {
        'action': 'account.contact.change', 'resource_id': identity, 'resource_revision': 0,
        'payload': {'email': 'different@example.invalid' if changed_payload else email},
    })
    factor = TotpFactor.objects.get(user=account)
    totp_code = totp.code_at(totp.unseal(factor.secret_ciphertext), int(timezone.now().timestamp()) // 30)
    proof = sensitive_actions.verify(req, challenge['id'], totp_code)
    response = client.post(prefix + 'confirm/', {'otp': code}, HTTP_X_SOKOUN_AUTHORIZATION=proof['proof'])
    assert response.status_code == (403 if changed_payload else 200), response.data
    account.refresh_from_db()
    authorization = SensitiveAuthorization.objects.get(id=challenge['id'])
    assert (account.email == email) is (not changed_payload)
    assert (authorization.consumed_at is not None) is (not changed_payload)
