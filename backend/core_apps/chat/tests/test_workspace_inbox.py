import pytest
from core_apps.chat.models import ConversationWorkspace
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.chat.services.workspace_inbox import scoped, visible
from rest_framework.exceptions import ValidationError
from core_apps.features.tests.test_company_housing import company_setup, proposed
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.chat.services.company_access import provision
from core_apps.features.company_models import CompanyMembership

pytestmark = pytest.mark.django_db


def test_viewer_context_keeps_independent_direct_workspaces(user, another_user):
    first = get_or_create_direct_conversation(user=user, other_user=another_user, workspace="student")
    again = get_or_create_direct_conversation(user=user, other_user=another_user, workspace="owner")
    assert first.id != again.id
    assert list(scoped(user, "student")) == [first]
    assert list(scoped(user, "owner")) == [again]
    with pytest.raises(ValidationError):
        scoped(user, "all")
    assert not scoped(user, "general").exists()
    assert list(scoped(another_user, "student")) == [first]
    assert list(scoped(another_user, "owner")) == [again]


def test_filter_is_applied_before_pagination(user, another_user):
    conversation = get_or_create_direct_conversation(user=user, other_user=another_user)
    user.is_verified = True
    user.save()
    client = authenticated(user)
    url = "/api/v1/chat/conversations/"
    general = client.get(url, {"workspace": "general", "page_size": 1})
    assert general.status_code == 200, general.data
    assert general.data["count"] == 1
    assert client.get(url, {"workspace": "student"}).data["count"] == 0
    assert client.get(url, {"workspace": "unknown"}).status_code == 400
    assert client.get(url).data["count"] == 1  # Old contract remains direct-only.


def test_company_inbox_revokes_stale_membership_and_cross_company(company_setup):
    owner, coordinator, approver, company, building, props, offer, request = (
        company_setup
    )
    conversation = provision(request, coordinator)
    assert list(scoped(coordinator, "company", str(company.id))) == [conversation]
    assert conversation in visible(coordinator)
    assert not visible(owner).filter(pk=conversation.pk).exists()
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        revision=99
    )
    assert not scoped(coordinator, "company", str(company.id)).exists()
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        is_active=False
    )
    assert not visible(coordinator).filter(pk=conversation.pk).exists()


def test_summary_counts_distinct_conversations_and_context(user, another_user):
    user.is_verified = True
    user.save()
    for workspace in ["owner", "student"]:
        conversation = get_or_create_direct_conversation(user=user, other_user=another_user, workspace=workspace)
        conversation.participant_set.filter(user=user).update(unread_count=3)
    result = authenticated(user).get("/api/v1/features/v1/workspace-summary/")
    assert result.status_code == 200, result.data
    assert result.data["workspace_chat_counts"]["all"] == 6
    assert result.data["workspace_chat_counts"]["owner"] == 3
    assert result.data["workspace_chat_counts"]["student"] == 3
    assert result.data["workspace_chat_counts"]["individual"] == 0
