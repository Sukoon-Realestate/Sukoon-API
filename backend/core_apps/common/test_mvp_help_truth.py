"""Public help stays factual and cannot edit operational policy or tenancy data."""
import pytest
from django.contrib import admin
from django.test import RequestFactory
from django.urls import reverse

from core_apps.common.contract_testing import api_json
from core_apps.features.models import PolicyDecision, Lease
from core_apps.support.models import HelpContact, HelpArticle

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('workspace', ['tenant', 'owner'])
def test_missing_help_contact_is_empty_instead_of_a_fabricated_destination(api_client, workspace):
    HelpContact.objects.filter(workspace=workspace).delete()
    response = api_client.get(reverse('support-help-center'), {'workspace': workspace, 'lang': 'en'})
    assert response.status_code == 200
    data = api_json(response)['data']
    assert data['phone'] == data['email'] == data['hours'] == ''


def test_editing_help_text_preserves_operational_policy_and_creates_no_tenancy(superuser):
    decision = PolicyDecision.objects.create(code='D26', version='synthetic-existing',
        owner='synthetic owner', source='isolated fixture',
        rules={'proof_lifetime_seconds': 300}, scope=['account.contact.change'])
    before = list(PolicyDecision.objects.filter(pk=decision.pk).values())
    article = HelpArticle.objects.create(slug='synthetic-policy-help', workspace='tenant',
        question_en='Synthetic question', question_ar='Synthetic localized question',
        answer_en='Original explanation', answer_ar='Original localized explanation')
    request = RequestFactory().post('/admin/')
    request.user = superuser
    article.answer_en = 'Updated help explanation; not an operational approval'
    admin.site._registry[HelpArticle].save_model(request, article, None, True)
    assert list(PolicyDecision.objects.filter(pk=decision.pk).values()) == before
    assert not Lease.objects.exists()
