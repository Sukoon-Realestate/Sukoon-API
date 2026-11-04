from unittest.mock import patch
import pytest
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.notifications.models import DeviceToken, Notification, PushDelivery
from core_apps.notifications.services.push_delivery import queue_notification, dispatch
from core_apps.notifications.services import preferences

pytestmark = pytest.mark.django_db


def test_active_summary_counts_current_personal_spaces_without_deferred_counts(auth_client, user, another_user):
    user.is_verified = True
    user.save(update_fields=['is_verified'])
    for space, count in [('individual', 5), ('owner', 3), ('student', 11)]:
        c = get_or_create_direct_conversation(user=user, other_user=another_user, workspace=space)
        c.participant_set.filter(user=user).update(unread_count=count)
    Notification.objects.create(user=user, title='Owner notice', data={'workspace': 'owner'})
    response = auth_client.get('/api/v1/features/v1/workspace-summary/', {'scope': 'owner'})
    assert response.status_code == 200, response.content
    data = response.data
    assert data['workspace_chat_counts']['all'] == 8
    assert data['workspace_chat_counts']['individual'] == 5
    assert data['workspace_chat_counts']['owner'] == 3
    assert data['workspace_chat_counts']['student'] == 0
    assert data['company_chat_counts'] == {}
    assert data['unread_notifications_count'] == 1
    assert 'company_approval_counts' not in data
    assert 'group_join_requests_count' not in data
    assert response['Cache-Control'] == 'private, no-store'
    for space in ['company', 'student']:
        assert auth_client.get('/api/v1/features/v1/workspace-summary/', {'scope': space}).status_code == 403
    assert auth_client.post('/api/v1/features/v1/workspace-summary/', {}, format='json').status_code == 403


def test_summary_read_does_not_change_active_push_target_without_explicit_selection(auth_client, user):
    for space in ['individual', 'owner']:
        response = auth_client.get('/api/v1/features/v1/workspace-summary/', {'scope': space})
        assert response.status_code == 200, response.content
        assert preferences.get(user, space).last_used_at is None
    response = auth_client.get('/api/v1/features/v1/workspace-summary/', {'scope': 'owner', 'active_workspace': 'true'})
    assert response.status_code == 200
    assert preferences.get(user, 'owner').last_used_at is not None
    assert preferences.get(user, 'individual').last_used_at is None


def test_deferred_push_is_suppressed_but_history_and_active_notices_remain(user):
    DeviceToken.objects.create(user=user, token='synthetic-device')
    active = Notification.objects.create(user=user, title='Owner', data={'workspace': 'owner'})
    deferred = Notification.objects.create(user=user, title='Student', data={'workspace': 'student'})
    queue_notification(active)
    queue_notification(deferred)
    with patch('core_apps.notifications.services.push_delivery.FCMService.send_push_to_device', return_value=True) as send:
        assert dispatch() == 1
        assert send.call_count == 1
        assert send.call_args.kwargs['data']['workspace'] == 'owner'
    assert PushDelivery.objects.get(notification=deferred).suppressed
    assert Notification.objects.filter(user=user).count() == 2
    deferred.refresh_from_db()
    assert not deferred.is_read
