"""Cancelling active-space delivery preserves sent receipts and stops the queue."""
from unittest.mock import patch

import pytest

from core_apps.admin_api.models import CampaignDelivery
from core_apps.admin_api.services.push_campaigns import transition
from core_apps.notifications.models import Notification
from .test_push_campaigns import target
from .test_workspace_campaigns import campaign, run_dispatch

pytestmark = pytest.mark.django_db


def test_active_campaign_cancel_preserves_sent_receipt_without_sending_remaining(superuser, user, another_user, settings):
    settings.ADMIN_CAMPAIGNS_ENABLED = True
    target(user, 'synthetic-first-device')
    target(another_user, 'synthetic-next-device')
    item = campaign(superuser)
    with patch('core_apps.admin_api.services.workspace_campaigns.FCMService.send_push_to_device', return_value=True) as send:
        assert run_dispatch(limit=1)['accepted_by_provider'] == 1
        delivered = list(Notification.objects.values_list('id', flat=True))
        # Durable in-app receipts are prepared before the bounded push batch.
        # Cancellation cannot retract either receipt already delivered in-app.
        assert len(delivered) == 2
        item.refresh_from_db()
        transition(superuser, item.id, {'expected_revision': item.revision,
            'preview_digest': item.preview_digest}, cancel=True)
        assert run_dispatch()['accepted_by_provider'] == 0
        assert send.call_count == 1
    assert list(Notification.objects.values_list('id', flat=True)) == delivered
    assert CampaignDelivery.objects.filter(recipient__campaign=item, state='cancelled').count() == 1
