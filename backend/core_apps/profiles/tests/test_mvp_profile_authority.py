"""Profile labels/preferences never grant deferred workspace or staff authority."""
import pytest
from django.urls import reverse

from core_apps.admin_api.models import StaffProfile
from core_apps.features.company_models import CompanyMembership
from core_apps.features.student_models import StudentProfile

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('label', ['owner', 'company', 'student'])
def test_profile_edit_cannot_grant_staff_membership_or_verification(auth_client, user, label):
    before = (CompanyMembership.objects.count(), StudentProfile.objects.count())
    response = auth_client.patch(reverse('profile-edit'), {
        'full_name': 'Synthetic Profile', 'type': label, 'account_type': label,
        'is_staff': True, 'is_superuser': True, 'is_verified': True,
        'is_email_verified': True, 'student_verified': True,
        'company_id': '11111111-1111-4111-8111-111111111111',
    }, format='json')
    assert response.status_code == 200, response.data
    user.refresh_from_db()
    assert user.first_name == 'Synthetic' and user.last_name == 'Profile'
    assert not user.is_staff and not user.is_superuser and not user.is_verified
    assert not StaffProfile.objects.filter(user=user).exists()
    assert before == (CompanyMembership.objects.count(), StudentProfile.objects.count())
    assert auth_client.get(reverse('admin-session')).status_code == 403


def test_locked_privacy_preference_is_explicit_and_cannot_be_overridden(auth_client, user):
    response = auth_client.patch(reverse('user-settings'), {'always_hide_mobile_number': False}, format='json')
    assert response.status_code == 200
    assert response.data['always_hide_mobile_number'] is True
    assert response.data['always_hide_mobile_number_locked'] is True
    user.settings.refresh_from_db()
    assert user.settings.always_hide_mobile_number
