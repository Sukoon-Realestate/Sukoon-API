"""The exact new reply is selected even when all message timestamps tie."""
import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.support.models import Ticket
from core_apps.features.models import IdempotencyRecord

pytestmark = pytest.mark.django_db


def test_reply_response_and_history_keep_insertion_order_at_one_timestamp(auth_client, user):
    instant = timezone.now()
    with patch('django.utils.timezone.now', return_value=instant):
        created = auth_client.post(reverse('support-ticket-list-create'), {
            'workspace': 'account', 'category': 'other', 'subject': 'Synthetic enquiry',
            'description': 'Original synthetic message',
        }, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
        assert created.status_code == 201, created.data
        identity = created.json()['data']['id']
        reply_key = str(uuid.uuid4())
        reply = auth_client.post(reverse('support-ticket-reply', kwargs={'id': identity}) + '?workspace=account',
            {'body': 'Second synthetic message'}, format='json',
            HTTP_IDEMPOTENCY_KEY=reply_key)
        assert reply.status_code == 200, reply.data
    ticket = Ticket.objects.get(id=identity)
    assert ticket.messages.last().body == 'Second synthetic message'
    assert list(ticket.messages.values_list('body', flat=True)) == ['Original synthetic message', 'Second synthetic message']
    assert reply.json()['data']['messages'][-1]['body'] == 'Second synthetic message'
    receipt = IdempotencyRecord.objects.get(user=user, request_key=reply_key,
        operation=f'support.ticket.reply:{identity}')
    assert receipt.result_subject_id == ticket.messages.last().id
    response = auth_client.get(reverse('support-ticket-detail', kwargs={'id': identity}), {'workspace': 'account'})
    assert response.status_code == 200
    assert [row['body'] for row in response.json()['data']['messages']] == ['Original synthetic message', 'Second synthetic message']
