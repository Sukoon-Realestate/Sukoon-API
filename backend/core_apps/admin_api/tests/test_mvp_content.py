"""Existing content editor retains active catalogs and fences deferred branches."""
from uuid import uuid4
import pytest
from django.urls import reverse
from core_apps.admin_api.services import content_registry
from core_apps.support.models import HelpArticle
from core_apps.common.content_models import ContentEditAudit
from .test_content_editor import client, operator, save, article, ROOT
from .test_catalog_editor import created, location

pytestmark = pytest.mark.django_db


def test_mvp_catalog_edit_localization_history_recovery_and_reactivation(api_client):
    api = client(operator())
    schemas = {row['kind']: row for row in api.get(ROOT).data['catalogs']}
    assert set(schemas) == {'pages', 'contacts', 'articles', 'releases', 'governorates', 'cities', 'districts', 'property_types'}
    assert not {'student', 'company'} & {row['value'] for row in next(f for f in schemas['articles']['fields'] if f['name'] == 'workspace')['choices']}
    region = created(api, 'governorates', location('Synthetic MVP region'))
    city = created(api, 'cities', location('Synthetic MVP city', governorate=region['id']))
    updated, key = save(api, 'cities', {'name_en': 'Updated city', 'name_ar': 'مدينة محدثة'}, 1, city['id'])
    assert updated.status_code == 200 and updated.data['revision'] == 2
    for language, name in [('en', 'Updated city'), ('ar', 'مدينة محدثة')]:
        public = api_client.get(reverse('city-list'), {'governorate': region['id'], 'lang': language}, HTTP_X_APP_TYPE='mobile')
        assert public.data['results'][0]['name'] == name
    recovered = api.post(ROOT + f'cities/receipts/{key}/', {'identity': city['id']}, format='json')
    assert recovered.data['receipt'] == updated.data
    assert save(api, 'cities', {'name_en': 'Stale'}, 1, city['id'])[0].status_code == 409
    assert save(api, 'cities', {'is_active': False}, 2, city['id'])[0].status_code == 200
    assert api_client.get(reverse('city-list'), {'governorate': region['id']}).data['count'] == 0
    assert save(api, 'cities', {'is_active': True}, 3, city['id'])[0].status_code == 200
    assert len(api.get(ROOT + f'cities/{city["id"]}/').data['history']) == 4


def test_mvp_help_content_has_real_public_consumer_and_preserves_history(api_client):
    api = client(operator())
    values = article(); values['workspace'] = 'owner'
    response, key = save(api, 'articles', values)
    assert response.status_code == 201
    assert next(row for row in api_client.get(reverse('support-help-center'), {'workspace': 'owner', 'lang': 'en'}).data['faqs'] if row['id'] == 'content-proof')['answer'] == values['answer_en']
    replay, _ = save(api, 'articles', values, key=key)
    assert replay.status_code == 201 and replay.data == response.data
    response, _ = save(api, 'articles', {'answer_en': 'Updated answer'}, 1, 'content-proof')
    assert response.status_code == 200 and ContentEditAudit.objects.count() == 2
    assert next(row for row in api_client.get(reverse('support-help-center'), {'workspace': 'owner', 'lang': 'en'}).data['faqs'] if row['id'] == 'content-proof')['answer'] == 'Updated answer'


@pytest.mark.parametrize('workspace', ['student', 'company'])
def test_mvp_content_creation_and_old_receipts_cannot_restore_deferred_scope(settings, workspace):
    api = client(operator())
    values = article(); values['workspace'] = workspace
    assert save(api, 'articles', values)[0].status_code == 403
    assert not HelpArticle.objects.exists()
    settings.SUKOON_MVP = False
    created, key = save(api, 'articles', values)
    assert created.status_code == 201
    settings.SUKOON_MVP = True
    assert api.get(ROOT + 'articles/content-proof/').status_code == 404
    assert api.get(ROOT + 'articles/').data['count'] == 0
    assert save(api, 'articles', {'answer_en': 'Blocked'}, 1, 'content-proof')[0].status_code == 403
    assert save(api, 'articles', values, key=key)[0].status_code == 403
    assert api.post(ROOT + f'articles/receipts/{key}/', {'identity': None}, format='json').status_code == 403
    assert HelpArticle.objects.get().answer_en == values['answer_en']


@pytest.mark.parametrize('kind', ['universities', 'campuses', 'subscription_plans', 'advertising_plans', 'commerce_features'])
def test_deferred_catalog_direct_reads_commands_and_receipts_are_blocked(kind):
    api = client(operator())
    assert api.get(ROOT + kind + '/').status_code == 403
    assert save(api, kind, {})[0].status_code == 403
    assert api.post(ROOT + f'{kind}/receipts/{uuid4()}/', {'identity': None}, format='json').status_code == 403


def test_full_release_preserves_original_catalogs(settings):
    settings.SUKOON_MVP = False
    assert content_registry.spec('universities')
    assert content_registry.spec('subscription_plans')
