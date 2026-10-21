import pytest
from core_apps.chat.models import ConversationWorkspace
from core_apps.chat.services.message_service import get_or_create_direct_conversation
from core_apps.chat.services.workspace_inbox import scoped
from core_apps.features.tests.test_company_housing import company_setup, proposed
from core_apps.features.tests.test_rental_phase2 import (
    rental_participants,
    authenticated,
)
from core_apps.features.tests.test_rental_lifecycle import policy
from core_apps.chat.services.company_access import provision
from core_apps.features.company_models import CompanyMembership

pytestmark = pytest.mark.django_db


def test_viewer_context_keeps_one_canonical_direct_pair(user, another_user):
    first = get_or_create_direct_conversation(user=user, other_user=another_user)
    ConversationWorkspace.objects.create(
        conversation=first, user=user, workspace="student"
    )
    again = get_or_create_direct_conversation(user=user, other_user=another_user)
    ConversationWorkspace.objects.create(
        conversation=again, user=user, workspace="owner"
    )
    assert first.id == again.id
    assert list(scoped(user, "student")) == [first]
    assert list(scoped(user, "owner")) == [first]
    assert list(scoped(user, "all")) == [first]
    assert not scoped(user, "general").exists()
    assert list(scoped(another_user, "general")) == [first]
    assert not scoped(another_user, "student").exists()


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
    assert conversation in scoped(coordinator, "all")
    assert not scoped(owner, "all").filter(pk=conversation.pk).exists()
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        revision=99
    )
    assert not scoped(coordinator, "company", str(company.id)).exists()
    CompanyMembership.objects.filter(company=company, user=coordinator).update(
        is_active=False
    )
    assert not scoped(coordinator, "all").filter(pk=conversation.pk).exists()


def test_summary_counts_distinct_conversations_and_context(user, another_user):
    user.is_verified = True
    user.save()
    conversation = get_or_create_direct_conversation(user=user, other_user=another_user)
    conversation.participant_set.filter(user=user).update(unread_count=3)
    for workspace in ["owner", "student"]:
        ConversationWorkspace.objects.create(
            conversation=conversation, user=user, workspace=workspace
        )
    result = authenticated(user).get("/api/v1/features/v1/workspace-summary/")
    assert result.status_code == 200, result.data
    assert result.data["workspace_chat_counts"]["all"] == 3
    assert result.data["workspace_chat_counts"]["owner"] == 3
    assert result.data["workspace_chat_counts"]["student"] == 3
    assert result.data["workspace_chat_counts"]["individual"] == 0
