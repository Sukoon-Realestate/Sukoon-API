"""Safety boundaries for the rollback-only server acceptance utility."""

from datetime import timedelta
import hashlib
from unittest.mock import patch
import uuid

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection
from django.utils import timezone

from core_apps.chat import models
from core_apps.chat.moderation.policy import VERSION
from core_apps.chat.moderation.sealed import seal
from tools.chat_policy.verify_deployed_acceptance import verify


pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def isolated_acceptance_settings(settings):
    if connection.vendor != "postgresql":
        pytest.skip("Acceptance intentionally requires real PostgreSQL transactions")
    settings.CHAT_MODERATION_MODE = "off"
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = False
    settings.CAPTURE_COACH_PRIVATE_INPUTS_APPROVED = False


def test_explicit_synthetic_flag_is_required():
    with pytest.raises(AssertionError, match="explicit_synthetic_only_required"):
        verify()


def test_complete_acceptance_and_load_leave_no_rows_or_side_effects():
    before_users = get_user_model().objects.count()
    result = verify(synthetic_only=True)
    assert result["ok"], result
    assert result["load"]["total_messages"] == 12
    assert result["load"]["conversations"] == 3
    assert result["load"]["batches"] == 3
    assert result["rollback"]["remaining_rows"] == 0
    assert result["rollback"]["callbacks_executed"] == 0
    assert result["rollback"]["network_attempts"] == 0
    assert get_user_model().objects.count() == before_users
    assert result["settings_restored"]
    assert "current_staff_role_enforced" in result["checks"]


def test_failure_still_rolls_back_and_restores_flags():
    before_users = get_user_model().objects.count()
    with patch(
        "core_apps.chat.services.message_service.get_or_create_direct_conversation",
        side_effect=AssertionError("intentional_fixture_failure"),
    ):
        result = verify(synthetic_only=True)
    assert not result["ok"]
    assert result["failure"] == "intentional_fixture_failure"
    assert result["rollback"]["remaining_rows"] == 0
    assert get_user_model().objects.count() == before_users
    assert settings.CHAT_MODERATION_MODE == "off"
    assert settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED is False


def test_unrelated_due_input_and_retry_batch_cannot_be_claimed():
    user = get_user_model().objects.create_user(
        email=f"unrelated-{uuid.uuid4().hex}@example.invalid",
        first_name="Isolated",
        last_name="Other fixture",
    )
    conversation = models.Conversation.objects.create()
    message = models.Message.objects.create(
        conversation=conversation,
        sender=user,
        content="An unrelated fixture must not be classified.",
        sequence=1,
    )
    row = models.ChatModerationInput.objects.create(
        message=message,
        revision=1,
        conversation=conversation,
        ciphertext=seal({"text": message.content}),
        due_at=timezone.now() - timedelta(hours=1),
    )
    batch = models.ChatModerationBatch.objects.create(
        conversation=conversation,
        fingerprint=hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest(),
        input_ids=[row.pk],
        policy_version=VERSION,
        state="retry",
        next_attempt_at=timezone.now() - timedelta(hours=1),
    )
    before_row = models.ChatModerationInput.objects.filter(pk=row.pk).values().get()
    before_batch = models.ChatModerationBatch.objects.filter(pk=batch.pk).values().get()
    result = verify(synthetic_only=True)
    assert result["ok"], result
    assert (
        models.ChatModerationInput.objects.filter(pk=row.pk).values().get()
        == before_row
    )
    assert (
        models.ChatModerationBatch.objects.filter(pk=batch.pk).values().get()
        == before_batch
    )
    assert models.Message.objects.filter(pk=message.pk).exists()
    assert not models.ChatModerationCase.objects.filter(
        conversation=conversation
    ).exists()
