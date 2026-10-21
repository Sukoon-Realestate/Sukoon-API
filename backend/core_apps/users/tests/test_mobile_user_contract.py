import pytest
from core_apps.common.contract_testing import api_json


@pytest.mark.django_db
def test_current_user_uses_the_canonical_identity_keys(auth_client, user):
    user.first_name = 'Contract'
    user.last_name = 'Account'
    user.save(update_fields=['first_name', 'last_name'])
    user.profile.phone_number = '+201001234567'
    user.profile.save(update_fields=['phone_number'])

    response = auth_client.get('/api/v1/auth/users/me/')
    assert response.status_code == 200
    data = api_json(response)['data']
    assert data['id'] == str(user.id)
    assert data['full_name'] == 'Contract Account'
    assert data['phone_number'] == '+201001234567'
    assert data['email'] == user.email
    assert data['is_verified'] is user.is_verified
    assert 'name' not in data
    assert 'phone' not in data


@pytest.mark.django_db
def test_public_user_serializer_does_not_include_the_private_phone(user):
    from core_apps.users.serializers import CustomUserSerializer

    user.profile.phone_number = '+201001234567'
    user.profile.save(update_fields=['phone_number'])
    assert 'phone_number' not in CustomUserSerializer(user).data
