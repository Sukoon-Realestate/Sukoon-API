"""MVP staff access does not restore deferred money or tenancy review tools."""
import pytest
from django.urls import reverse
from core_apps.admin_api.models import StaffProfile
from core_apps.common.mvp_scope import allows_path


@pytest.mark.django_db
def test_mvp_system_owner_has_no_deferred_menu_or_direct_api(api_client, user, settings):
    settings.SUKOON_MVP = True
    StaffProfile.objects.create(user=user, role_name='system_owner')
    api_client.force_authenticate(user)
    paths = api_client.get(reverse('admin-session')).data['allowedPaths']
    assert '/support' in paths and '/properties' in paths
    assert not any(path.startswith('/financials') for path in paths)
    for path in ['/api/v1/admin/financials/summary/',
                 '/api/v1/admin/financials/transactions/', '/api/v1/admin/reviews/',
                 '/api/v1/admin/review-cases/']:
        response = api_client.get(path)
        assert response.status_code == 403
        assert response.json()['code'] == 'mvp_feature_deferred'


def test_disabled_mvp_retains_original_staff_route_authorization(settings):
    settings.SUKOON_MVP = False
    assert allows_path('/api/v1/admin/financials/summary/')
    assert allows_path('/api/v1/admin/review-cases/')
