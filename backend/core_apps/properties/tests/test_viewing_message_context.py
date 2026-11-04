import uuid
import json
import os
from pathlib import Path
from datetime import time,timedelta
import pytest
from django.urls import reverse
from django.utils import timezone
from core_apps.properties.models import PropertyVisit
from core_apps.chat.models import Conversation,Message
from .test_views import _create_published_property

pytestmark=pytest.mark.django_db


@pytest.fixture
def appointment(user,another_user):
    prop=_create_published_property(owner=user,price=1000)
    return PropertyVisit.objects.create(property=prop,tenant=another_user,status='confirmed',
        visit_date=timezone.localdate()+timedelta(days=1),visit_time=time(12),offer_id=str(uuid.uuid4()),
        offer_snapshot={'name':'Fixture room A'})


def test_delay_context_is_authorized_read_only_and_revision_bound(api_client,user,another_user,superuser,appointment):
    path=reverse('viewing-message-context',kwargs={'visit_id':appointment.id})
    api_client.force_authenticate(another_user)
    response=api_client.get(path)
    assert response.status_code==200,response.data
    assert response.data['other_user_id']==str(user.id)
    assert response.data['offer_name']=='Fixture room A'
    assert response.data['visit_id']==str(appointment.id)
    assert not Conversation.objects.exists() and not Message.objects.exists()
    exported=os.environ.get('MVP_FIXTURE_DIR')
    if exported:
        root=Path(exported);root.mkdir(parents=True,exist_ok=True)
        (root/'viewing_message_context.json').write_text(json.dumps(response.data),encoding='utf8')
    old_revision=appointment.revision
    appointment.visit_time=time(13)
    appointment.save(update_fields=['visit_time','updated_at'])
    assert api_client.get(path,{'expected_revision':old_revision}).status_code==409
    api_client.force_authenticate(superuser)
    assert api_client.get(path).status_code==403
    api_client.force_authenticate(another_user)
    appointment.status='canceled'
    appointment.save(update_fields=['status','updated_at'])
    assert api_client.get(path).status_code==409


def test_opening_chat_rechecks_viewing_revision_even_for_an_existing_conversation(api_client,user,another_user,appointment):
    api_client.force_authenticate(another_user)
    path=reverse('conversation-create')
    body={'user_id':str(user.id),'workspace':'individual','expected_visit_revision':appointment.revision,
        'rental_context':{'property_id':str(appointment.property.id),'visit_id':str(appointment.id)}}
    first=api_client.post(path,body,format='json')
    assert first.status_code==200,first.data
    assert Conversation.objects.count()==1 and Message.objects.count()==0
    appointment.status='canceled'
    appointment.save(update_fields=['status','updated_at'])
    assert api_client.post(path,body,format='json').status_code==409
    assert Message.objects.count()==0
    another_user.closed_at=timezone.now()
    another_user.save(update_fields=['closed_at'])
    assert api_client.post(path,body,format='json').status_code==403


def test_a_viewing_cannot_be_forged_as_another_renters_chat_context(api_client,user,another_user,superuser,appointment):
    other=PropertyVisit.objects.create(property=appointment.property,tenant=superuser,status='confirmed')
    api_client.force_authenticate(another_user)
    response=api_client.post(reverse('conversation-create'),{'user_id':str(user.id),'workspace':'individual',
        'rental_context':{'property_id':str(appointment.property.id),'visit_id':str(other.id)}},format='json')
    assert response.status_code==403
    assert not Conversation.objects.exists() and not Message.objects.exists()
