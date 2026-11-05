"""Scope is rechecked for both new campaigns and receipts queued before MVP."""
from uuid import uuid4
from unittest.mock import patch
import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError
from core_apps.admin_api.models import CampaignRecipient, PushCampaign
from core_apps.admin_api.services import push_campaigns, workspace_campaigns
from core_apps.notifications.models import Notification, DeviceToken
from core_apps.properties.tests.conftest import apartment_type, cairo_city, cairo_governorate  # noqa: F401
from .test_workspace_campaigns import four_spaces, campaign, run_dispatch  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('push_owner,expected_scope', [(True, 'owner'), (False, 'individual')])
def test_active_personal_owner_campaign_has_two_receipts_one_latest_enabled_push(
    superuser, user, apartment_type, cairo_city, cairo_governorate, settings,
    push_owner, expected_scope,
):
    from core_apps.notifications.services import preferences
    from core_apps.profiles.models import UserSettings
    from core_apps.properties.models import Property

    settings.SUKOON_MVP = True
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    UserSettings.objects.filter(user=user).update(promotions_and_updates=True)
    Property.objects.create(owner=user, title='Synthetic active campaign owner',
        property_type=apartment_type, city=cairo_city, governorate=cairo_governorate)
    for scope in ['individual', 'owner']:
        preferences.touch(user, scope)
    # Windows clocks can produce equal instants for sequential calls. Explicitly
    # model a later owner visit instead of depending on host timer resolution.
    from datetime import timedelta
    from django.utils import timezone
    from core_apps.notifications.models import NotificationScopePreference
    instant = timezone.now()
    NotificationScopePreference.objects.filter(user=user, scope='individual').update(last_used_at=instant - timedelta(seconds=1))
    NotificationScopePreference.objects.filter(user=user, scope='owner').update(last_used_at=instant)
    owner = preferences.get(user, 'owner')
    owner.push_enabled = push_owner
    owner.save(update_fields=['push_enabled'])
    DeviceToken.objects.create(user=user, token='synthetic-active-device')
    item = campaign(superuser)
    assert set(item.recipients.values_list('workspace', flat=True)) == {'individual', 'owner'}
    with patch.object(workspace_campaigns.FCMService, 'send_push_to_device', return_value=True) as send:
        assert run_dispatch()['accepted_by_provider'] == 1
        assert run_dispatch()['accepted_by_provider'] == 0
        assert send.call_count == 1
        assert send.call_args.kwargs['data']['workspace'] == expected_scope
    assert set(Notification.objects.filter(user=user).values_list('scope', flat=True)) == {'individual', 'owner'}
    individual = Notification.objects.get(user=user, scope='individual')
    individual.is_read = True
    individual.save(update_fields=['is_read'])
    assert not Notification.objects.get(user=user, scope='owner').is_read


@pytest.mark.parametrize('audience', [[], {}, 1])
def test_malformed_audience_is_validation_error_without_a_campaign(superuser, audience):
    with pytest.raises(ValidationError):
        push_campaigns.preview(superuser, {'title': 'Synthetic', 'body': 'Local only',
            'audience': audience, 'request_key': str(uuid4())})
    assert not PushCampaign.objects.exists()


def test_mvp_campaign_audience_configuration_matches_the_command_gate(api_client, superuser, settings):
    settings.SUKOON_MVP = True
    api_client.force_authenticate(superuser)
    path = '/api/v1/admin/system/notifications/'
    response = api_client.get(path, {'capabilities': '1'})
    assert response.status_code == 200
    assert set(response.data['audiences']) == {'all', 'tenants', 'landlords', 'verified'}
    assert response['Cache-Control'] == 'private, no-store'
    settings.SUKOON_MVP = False
    assert set(api_client.get(path, {'capabilities': '1'}).data['audiences']) == workspace_campaigns.AUDIENCES


def test_existing_memberships_do_not_restore_deferred_campaign_spaces(user, four_spaces, settings):
    settings.SUKOON_MVP = True
    assert workspace_campaigns.eligible_spaces(user, 'all') == {'individual', 'owner'}
    assert not workspace_campaigns.eligible_spaces(user, 'students')
    assert not workspace_campaigns.eligible_spaces(user, 'companies')


@pytest.mark.parametrize('audience', ['students', 'companies'])
def test_deferred_audience_is_rechecked_before_confirmation(superuser, user, four_spaces, settings, audience):
    settings.SUKOON_MVP = False
    item = push_campaigns.preview(superuser, {'title': 'Synthetic', 'body': 'Local only',
        'audience': audience, 'request_key': str(uuid4())})
    body = {'expected_revision': item.revision, 'preview_digest': item.preview_digest}
    settings.SUKOON_MVP = True
    with pytest.raises(PermissionDenied):
        push_campaigns.transition(superuser, item.id, body)
    item.refresh_from_db()
    assert item.state == 'preview'
    with pytest.raises(PermissionDenied):
        push_campaigns.preview(superuser, {'title': 'Synthetic', 'body': 'Local only',
            'audience': audience, 'request_key': str(uuid4())})
    assert PushCampaign.objects.count() == 1
    push_campaigns.transition(superuser, item.id, body, cancel=True)
    item.refresh_from_db()
    assert item.state == 'cancelled'


def test_queued_campaign_preserves_old_receipts_but_only_delivers_active_spaces(superuser, user, four_spaces, settings):
    settings.SUKOON_MVP = False
    item = campaign(superuser)
    assert item.recipients.count() == 4
    settings.SUKOON_MVP = True
    with patch.object(workspace_campaigns.FCMService, 'send_push_to_device', return_value=True) as send:
        assert run_dispatch()['accepted_by_provider'] == 1
        assert run_dispatch()['accepted_by_provider'] == 0
        assert send.call_count == 1
        assert send.call_args.kwargs['data']['workspace'] in {'individual', 'owner'}
    assert set(Notification.objects.values_list('scope', flat=True)) == {'individual', 'owner'}
    assert CampaignRecipient.objects.filter(campaign=item).count() == 4
    assert set(item.recipients.filter(receipt_state='skipped').values_list('workspace', flat=True)) == {'student', 'company'}


def test_legacy_delivery_rechecks_session_binding(user, four_spaces, settings):
    settings.SUKOON_MVP = True
    user.requires_bound_session = True
    user.save(update_fields=['requires_bound_session'])
    assert not push_campaigns.devices('all').exists()
