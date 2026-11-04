import pytest
from core_apps.features.experience.access import FEATURES, enabled
from core_apps.features.experience.models import PreparationTask


@pytest.mark.django_db
def test_mvp_capabilities_do_not_advertise_group_preparation(auth_client, settings):
    settings.SUKOON_MVP = True
    settings.SOKOUN_EXPERIENCE_FEATURES = FEATURES
    response = auth_client.get('/api/v1/features/v1/experience/capabilities/')
    assert response.status_code == 200
    features = response.json()['data']['features']
    assert 'preparation' not in features and 'sync' in features
    for method in (auth_client.get, auth_client.post):
        result = method('/api/v1/features/v1/experience/preparation-tasks/')
        assert result.status_code == 403
        assert result.json()['code'] == 'mvp_feature_deferred'
    assert not PreparationTask.objects.exists()


def test_disabled_mvp_preserves_preparation_configuration(settings):
    settings.SUKOON_MVP = False
    settings.SOKOUN_EXPERIENCE_FEATURES = FEATURES
    assert enabled('preparation')
