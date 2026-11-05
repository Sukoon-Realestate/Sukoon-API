"""Provider-free initial staff setup; synthetic human checks are not real assurance."""
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import User, StaffSecurityIdentity, TotpEnrollment, TotpFactor
from core_apps.users.services import sensitive_actions, staff_setup, totp, totp_recovery
from .test_totp_recovery import actors, request  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.fixture
def applicant(actors):
    account = User.objects.create_user(email='initial-staff@example.invalid', password='SyntheticLocalOnly!',
        is_staff=True, is_email_verified=True)
    StaffProfile.objects.create(user=account, role_name='support')
    return account


def body():
    return {'person_reference': 'synthetic-new-person', 'evidence_reference': 'synthetic-identity-check',
            'known_channel_reference': 'synthetic-known-channel', 'verification_method': 'known_channel_video',
            'identity_matched': True}


def document(actors, applicant):
    reviewer = actors[1]
    req, payload = request(reviewer), body()
    challenge = sensitive_actions.begin(req, {'action': 'account.mfa.manage',
        'resource_id': str(applicant.id), 'resource_revision': 0, 'payload': payload})
    factor = TotpFactor.objects.get(user=reviewer)
    code = totp.code_at(totp.unseal(factor.secret_ciphertext), int(timezone.now().timestamp()) // 30)
    proof = sensitive_actions.verify(req, challenge['id'], code)
    req.headers['X-Sokoun-Authorization'] = proof['proof']
    result = staff_setup.document_identity(req, applicant.id, payload)
    return result, req


def test_initial_staff_factor_requires_independent_documentation_and_self_confirmation(actors, applicant):
    with pytest.raises(PermissionDenied):
        staff_setup.enroll(request(applicant))
    projection, reviewer_request = document(actors, applicant)
    assert projection['documented'] and not projection['configured']
    assert staff_setup.document_identity(reviewer_request, applicant.id, body()) == projection
    assert StaffSecurityIdentity.objects.filter(user=applicant).count() == 1
    own_request = request(applicant)
    binding = staff_setup.enroll(own_request)
    assert staff_setup.enroll(own_request)['id'] == binding['id']
    private = TotpEnrollment.objects.get(id=binding['id'])
    assert private.expires_at <= timezone.now() + timedelta(minutes=5)
    assert binding['secret'] not in str(staff_setup.identities(request(actors[1])))
    assert binding['secret'] not in str(totp_recovery.status(own_request))
    code = totp.code_at(binding['secret'], int(timezone.now().timestamp()) // 30)
    totp_recovery.confirm(own_request, binding['id'], code)
    factor = TotpFactor.objects.get(user=applicant)
    assert factor.confirmed_at and totp.unseal(factor.secret_ciphertext) == binding['secret']
    private.refresh_from_db()
    assert private.consumed_at and private.secret_ciphertext == ''
    # Lost confirmation response returns the receipt without rebinding the factor.
    totp_recovery.confirm(own_request, binding['id'], code)
    assert TotpEnrollment.objects.filter(user=applicant).count() == 1
    assert staff_setup.initial_status(applicant)['requires_recovery']
    with pytest.raises(PermissionDenied):
        staff_setup.enroll(own_request)


@pytest.mark.parametrize('change', ['session', 'expiry', 'role'])
def test_pending_initial_binding_rechecks_session_expiry_and_current_role(actors, applicant, change):
    document(actors, applicant)
    own_request = request(applicant)
    binding = staff_setup.enroll(own_request)
    code = totp.code_at(binding['secret'], int(timezone.now().timestamp()) // 30)
    if change == 'session':
        own_request = request(applicant)
    elif change == 'expiry':
        TotpEnrollment.objects.filter(id=binding['id']).update(expires_at=timezone.now() - timedelta(seconds=1))
    else:
        StaffProfile.objects.filter(user=applicant).update(is_active=False)
    with pytest.raises(PermissionDenied):
        totp_recovery.confirm(own_request, binding['id'], code)
    assert TotpFactor.objects.get(user=applicant).confirmed_at is None


def test_documenting_staff_identity_rejects_self_or_same_person_before_creating_identity(actors, applicant):
    reviewer = actors[1]
    same_person = StaffSecurityIdentity.objects.get(user=reviewer).person_reference
    with pytest.raises(PermissionDenied):
        staff_setup.document_identity(request(reviewer), reviewer.id, body())
    with pytest.raises(PermissionDenied):
        staff_setup.document_identity(request(reviewer), applicant.id, {**body(), 'person_reference': same_person})
    assert not StaffSecurityIdentity.objects.filter(user=applicant).exists()


def test_authority_change_invalidates_the_pending_initial_binding(actors, applicant):
    from rest_framework.exceptions import APIException
    from core_apps.admin_api.services.staff_service import invite_staff_member

    document(actors, applicant)
    own_request = request(applicant)
    binding = staff_setup.enroll(own_request)
    invite_staff_member(applicant.email, 'Synthetic Staff', 'property_reviewer',
        actor=actors[1], reason='Synthetic role assignment changed')
    code = totp.code_at(binding['secret'], int(timezone.now().timestamp()) // 30)
    with pytest.raises(APIException) as denied:
        totp_recovery.confirm(own_request, binding['id'], code)
    assert denied.value.status_code in {401, 403}
    assert TotpFactor.objects.get(user=applicant).confirmed_at is None
    assert TotpEnrollment.objects.get(id=binding['id']).expires_at <= timezone.now()


def test_staff_invitation_grants_no_identity_or_factor_and_returns_no_password(actors, api_client):
    from django.urls import reverse

    api_client.force_authenticate(actors[1])
    response = api_client.post(reverse('admin-staff-invite'), {'email': 'invited-staff@example.invalid',
        'name': 'Synthetic Invited Staff', 'role_name': 'support', 'reason': 'Local setup regression'}, format='json')
    assert response.status_code == 201, response.data
    account = User.objects.get(email='invited-staff@example.invalid')
    assert StaffProfile.objects.get(user=account).role_name == 'support'
    assert not account.is_verified and not account.is_email_verified
    assert not StaffSecurityIdentity.objects.filter(user=account).exists()
    assert not TotpFactor.objects.filter(user=account).exists()
    assert not any(key in response.data for key in ['password', 'secret', 'token'])


def test_staff_password_setup_uses_shared_admin_link_without_documenting_identity(applicant, api_client, mailoutbox):
    import re

    response = api_client.post('/api/v1/auth/users/reset_password/', {'email': applicant.email}, format='json')
    assert response.status_code == 204, response.data
    assert len(mailoutbox) == 1 and mailoutbox[0].to == [applicant.email]
    link = re.search(r'admin/password-reset/([A-Za-z0-9_-]+)/([A-Za-z0-9-]+)', mailoutbox[0].body)
    assert link, 'Staff recovery email must target the shared admin password-setup route'
    uid, token = link.groups()
    password = 'AnotherSyntheticOnly!321'
    confirmed = api_client.post('/api/v1/auth/users/reset_password_confirm/', {
        'uid': uid, 'token': token, 'new_password': password, 're_new_password': password,
    }, format='json')
    assert confirmed.status_code == 204, confirmed.data
    applicant.refresh_from_db()
    assert applicant.check_password(password) and not applicant.is_verified
    assert not StaffSecurityIdentity.objects.filter(user=applicant).exists()
    assert not TotpFactor.objects.filter(user=applicant).exists()
