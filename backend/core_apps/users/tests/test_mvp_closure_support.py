"""Pending deletion preserves ordinary account support without tenancy context."""
import uuid

import pytest
from django.urls import reverse

from core_apps.support.models import Ticket
from core_apps.users.models import AccountClosureRequest
from .test_account_closure import submit

pytestmark = pytest.mark.django_db


def test_pending_deletion_keeps_account_support_available_without_implicit_evidence(auth_client, user):
    closure = submit(user)
    created = auth_client.post(reverse('support-ticket-list-create'), {
        'workspace': 'account', 'category': 'other', 'subject': 'Synthetic account enquiry',
        'description': 'Please explain the pending deletion request.',
    }, format='json', HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    assert created.status_code == 201, created.data
    identity = created.json()['data']['id']
    ticket = Ticket.objects.get(id=identity)
    assert ticket.workspace == 'account' and ticket.rental_context == {}
    assert not ticket.messages.get().attachments.exists()
    reply = auth_client.post(reverse('support-ticket-reply', kwargs={'id': identity}) + '?workspace=account',
        {'body': 'Synthetic follow-up while deletion is pending.'}, format='json',
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()))
    assert reply.status_code == 200, reply.data
    detail = auth_client.get(reverse('support-ticket-detail', kwargs={'id': identity}), {'workspace': 'account'})
    assert detail.status_code == 200
    assert ticket.messages.count() == 2
    assert AccountClosureRequest.objects.get(id=closure['id']).active
