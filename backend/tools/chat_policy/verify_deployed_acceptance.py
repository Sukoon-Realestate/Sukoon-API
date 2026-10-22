"""Rollback-only acceptance against the current checkout and configured database.

Usage (local first, then an explicitly authorized server console):
  DJANGO_SETTINGS_MODULE=config.settings.capture_dev .venv/bin/python \
    tools/chat_policy/verify_deployed_acceptance.py --synthetic-only

This is in-process API acceptance, NOT browser/JWT login or Gemini evaluation.
All seven accounts, three conversations and twelve messages are synthetic and
uncommitted. Production queue logic runs with its model references scoped to
those conversations; it cannot claim an unrelated pending/retry batch. A fixture
reviewer supplies judgments. The five-minute deadline is checked, then advanced
without sleeping. No private-input setting is changed. No callbacks run.

Run in a dedicated process. PostgreSQL sequences may advance despite rollback;
no fixture rows, account roles, sanctions, notices or messages persist.
"""

import argparse
from contextlib import ExitStack
from datetime import timedelta
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch
import uuid


BACKEND = Path(__file__).resolve().parents[2]
SOURCES = (
    "core_apps/chat/moderation/queue.py",
    "core_apps/chat/moderation/decisions.py",
    "core_apps/chat/moderation/policy.py",
    "core_apps/chat/moderation/views.py",
    "core_apps/chat/moderation/notifications.py",
    "core_apps/chat/services/message_service_parts/send_message.py",
    "core_apps/chat/services/group_events.py",
    "core_apps/admin_api/permissions.py",
)


def require(condition, code):
    # Explicit checks stay active even if an operator uses python -O.
    if not condition:
        raise AssertionError(code)


def source_digest():
    digest = hashlib.sha256()
    for relative in SOURCES:
        digest.update(relative.encode() + b"\0" + (BACKEND / relative).read_bytes())
    return digest.hexdigest()


def verify(*, synthetic_only=False):
    require(synthetic_only, "explicit_synthetic_only_required")
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.db import connection, transaction
    from django.test import override_settings
    from django.utils import timezone
    from rest_framework.test import APIClient
    import requests
    from core_apps.admin_api.models import StaffProfile, UserReport
    from core_apps.chat import models
    from core_apps.chat.moderation import queue
    from core_apps.chat.moderation.policy import VERSION, restricted
    from core_apps.chat.services.message_service import (
        get_or_create_direct_conversation,
    )
    from core_apps.notifications.models import Notification
    from core_apps.notifications.services.fcm_service import FCMService
    from core_apps.profiles.models import Profile, UserSettings

    User = get_user_model()
    connection.ensure_connection()
    require(connection.vendor == "postgresql", "postgresql_required")
    require(not connection.in_atomic_block, "dedicated_outer_transaction_required")
    require(not connection.run_on_commit, "preexisting_callbacks_not_allowed")
    original = {
        name: getattr(settings, name)
        for name in (
            "CHAT_MODERATION_MODE",
            "CHAT_MODERATION_PRIVATE_INPUTS_APPROVED",
            "CAPTURE_COACH_PRIVATE_INPUTS_APPROVED",
        )
    }
    require(original["CHAT_MODERATION_MODE"] == "off", "live_moderation_must_be_off")
    require(
        not original["CHAT_MODERATION_PRIVATE_INPUTS_APPROVED"]
        and not original["CAPTURE_COACH_PRIVATE_INPUTS_APPROVED"],
        "private_input_flags_must_remain_off",
    )
    run_id = uuid.uuid4().hex
    people, conversations = [], []
    callbacks = {"scheduled": 0, "executed": 0}
    outbound = {"attempts": 0}
    checks = []
    result = {
        "scope": "in_process_APIClient_force_authenticate",
        "settings": settings.SETTINGS_MODULE,
        "provider": "fixture_no_Gemini",
        "queue": "production_claim_scoped_synthetic_querysets",
        "clock": "deadline_checked_then_due_times_advanced",
        "at": timezone.now().isoformat(),
        "checks": checks,
        "code_sha256": source_digest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    client = APIClient()
    real_on_commit = transaction.on_commit

    def forbidden_outbound(*args, **kwargs):
        outbound["attempts"] += 1
        raise AssertionError("outbound_operation_forbidden")

    def deferred(callback, using=None, robust=False):
        callbacks["scheduled"] += 1

        def must_never_execute():
            callbacks["executed"] += 1
            raise AssertionError("rollback_callback_executed")

        # Keep Django's actual callback/savepoint/rollback mechanism. Replacing
        # callback bodies adds a fail-closed fence if code accidentally commits.
        return real_on_commit(must_never_execute, using=using, robust=robust)

    def api(user, method, path, data=None, status=200):
        client.force_authenticate(user=user)
        response = getattr(client, method)(path, data=data, format="json", secure=True)
        require(
            response.status_code == status,
            f"http_{method}_{status}_got_{response.status_code}",
        )
        return response.data

    def new_person(label, staff=False):
        person = User.objects.create_user(
            email=f"{run_id}-{label}@sokoun-qa.invalid",
            password=None,
            first_name="Synthetic QA",
            last_name=label,
            is_verified=True,
            is_staff=staff,
        )
        people.append(person.pk)
        return person

    def send(chat, sender, content, *, identity=None, status=201):
        return api(
            sender,
            "post",
            f"/api/v1/chat/conversations/{chat.id}/messages/create/",
            {"client_message_id": str(identity or uuid.uuid4()), "content": content},
            status=status,
        )

    class FixtureReviewer:
        model = "synthetic-acceptance-fixture"
        calls = 0

        def __init__(self, heartbeat):
            self.heartbeat = heartbeat

        def classify(self, messages, verify=False):
            FixtureReviewer.calls += 1
            self.heartbeat()
            current = [message for message in messages if message["new"]]
            require(bool(current), "fixture_expected_fresh_messages")
            require(
                all(
                    message["text"].startswith("[SYNTHETIC QA]") for message in messages
                ),
                "non_synthetic_input_rejected",
            )
            selected = next(
                (
                    message
                    for message in current
                    if "avoid Sokoun fees" in message["text"]
                ),
                current[-1],
            )
            violation = "avoid Sokoun fees" in selected["text"]
            return {
                "verdicts": [
                    {
                        "actor_id": selected["actor_id"],
                        "label": "circumvention" if violation else "compliant",
                        "confidence": 0.99,
                        "evidence": (
                            [
                                {
                                    "message_id": selected["message_id"],
                                    "source": "text",
                                    "quote": selected["text"],
                                }
                            ]
                            if violation
                            else []
                        ),
                    }
                ]
            }

    def due(chat_ids):
        models.ChatModerationInput.objects.filter(
            conversation_id__in=chat_ids, state="pending"
        ).update(due_at=timezone.now() - timedelta(seconds=1))

    def processed(chat=None):
        already_complete = list(
            models.ChatModerationBatch.objects.filter(
                conversation_id__in=conversations, state="complete"
            ).values_list("pk", flat=True)
        )
        require(queue.process_one(FixtureReviewer), "expected_scoped_batch")
        batch = (
            models.ChatModerationBatch.objects.filter(
                conversation_id__in=conversations, state="complete"
            )
            .exclude(pk__in=already_complete)
            .get()
        )
        require(batch.state == "complete", "fixture_batch_did_not_complete")
        require(
            chat is None or batch.conversation_id == chat.pk,
            "unexpected_synthetic_conversation",
        )
        require(batch.attempts == 1, "unexpected_batch_retry")
        return batch

    def rollback_queries():
        # Only this run's roots are inspected. Never count, update or delete the
        # deployment's other users, queued work, reports or sanctions.
        return [
            User.objects.filter(pk__in=people),
            Profile.objects.filter(user_id__in=people),
            UserSettings.objects.filter(user_id__in=people),
            StaffProfile.objects.filter(user_id__in=people),
            models.Conversation.objects.filter(pk__in=conversations),
            models.ConversationParticipant.objects.filter(
                conversation_id__in=conversations
            ),
            models.Message.objects.filter(conversation_id__in=conversations),
            models.ChatEvent.objects.filter(conversation_id__in=conversations),
            models.RentalChatContext.objects.filter(conversation_id__in=conversations),
            models.ChatPolicyConsent.objects.filter(user_id__in=people),
            models.ChatModerationInput.objects.filter(
                conversation_id__in=conversations
            ),
            models.ChatModerationBatch.objects.filter(
                conversation_id__in=conversations
            ),
            models.ChatModerationCase.objects.filter(conversation_id__in=conversations),
            models.ChatPolicyNotice.objects.filter(user_id__in=people),
            models.AccountRestriction.objects.filter(user_id__in=people),
            models.ChatModerationAppeal.objects.filter(
                case__conversation_id__in=conversations
            ),
            models.ChatModerationAction.objects.filter(
                case__conversation_id__in=conversations
            ),
            UserReport.objects.filter(reported_user_id__in=people),
            Notification.objects.filter(user_id__in=people),
        ]

    failure = None
    try:
        with ExitStack() as stack:
            stack.enter_context(
                override_settings(
                    CHAT_MODERATION_MODE="enforce",
                    ALLOWED_HOSTS=[*settings.ALLOWED_HOSTS, "testserver"],
                    CACHES={
                        "default": {
                            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                            "LOCATION": f"synthetic-policy-acceptance-{run_id}",
                        }
                    },
                )
            )
            stack.enter_context(patch.object(transaction, "on_commit", deferred))
            stack.enter_context(
                patch.object(requests.Session, "request", forbidden_outbound)
            )
            stack.enter_context(
                patch.object(socket.socket, "connect", forbidden_outbound)
            )
            stack.enter_context(
                patch.object(socket.socket, "connect_ex", forbidden_outbound)
            )
            stack.enter_context(
                patch.object(FCMService, "send_push_to_user", forbidden_outbound)
            )
            with transaction.atomic():
                try:
                    with connection.cursor() as cursor:
                        # Process/transaction-local limits; no session/global config.
                        cursor.execute("SET LOCAL lock_timeout = '2s'")
                        cursor.execute("SET LOCAL statement_timeout = '15s'")
                    pairs = []
                    admin = new_person("admin", staff=True)
                    admin_role = StaffProfile.objects.create(
                        user=admin, role_name="main_admin"
                    )
                    require(not admin.is_superuser, "must_exercise_real_staff_role")
                    for number in range(3):
                        owner = new_person(f"owner-{number}")
                        tenant = new_person(f"tenant-{number}")
                        chat = get_or_create_direct_conversation(
                            user=owner, other_user=tenant
                        )
                        conversations.append(chat.pk)
                        models.RentalChatContext.objects.create(
                            conversation=chat, owner=owner
                        )
                        for person in (owner, tenant):
                            api(
                                person,
                                "post",
                                f"/api/v1/chat/conversations/{chat.id}/policy/",
                                {"policy_version": VERSION},
                            )
                        pairs.append((chat, owner, tenant))

                    # These facades affect only queue.py in this dedicated process.
                    # Existing production rows cannot be selected or updated by
                    # claim(), including its expired-lease and retry branches.
                    for name in (
                        "Conversation",
                        "ChatModerationInput",
                        "ChatModerationBatch",
                    ):
                        model = getattr(models, name)
                        field = (
                            "pk__in"
                            if name == "Conversation"
                            else "conversation_id__in"
                        )
                        stack.enter_context(
                            patch.object(
                                queue,
                                name,
                                SimpleNamespace(
                                    objects=model.objects.filter(
                                        **{field: conversations}
                                    )
                                ),
                            )
                        )

                    chat, owner, tenant = pairs[0]
                    base = f"/api/v1/chat/conversations/{chat.id}/"
                    violation = (
                        "[SYNTHETIC QA] Pay outside Sokoun to avoid Sokoun fees."
                    )
                    first_id = uuid.uuid4()
                    started = timezone.now()
                    send(chat, owner, violation, identity=first_id)
                    first = models.ChatModerationInput.objects.get(conversation=chat)
                    require(
                        299 <= (first.due_at - started).total_seconds() <= 305,
                        "window_not_five_minutes",
                    )
                    send(
                        chat,
                        tenant,
                        "[SYNTHETIC QA] I refuse; the agreement and payment stay in Sokoun.",
                    )
                    send(chat, owner, violation, identity=first_id)
                    pending = models.ChatModerationInput.objects.filter(
                        conversation=chat
                    )
                    require(
                        pending.count() == 2
                        and set(pending.values_list("due_at", flat=True))
                        == {first.due_at},
                        "dirty_window_or_send_dedupe_failed",
                    )
                    require(
                        not queue.process_one(FixtureReviewer)
                        and FixtureReviewer.calls == 0,
                        "processed_before_deadline",
                    )
                    checks.extend(
                        ["five_minute_first_dirty_window", "send_replay_once"]
                    )

                    due([chat.pk])
                    processed(chat)
                    notice = models.ChatPolicyNotice.objects.get(
                        conversation=chat, kind="warning"
                    )
                    require(
                        notice.user_id == owner.pk
                        and not restricted(owner)
                        and not restricted(tenant),
                        "first_warning_actor_failed",
                    )
                    calls = FixtureReviewer.calls
                    require(
                        not queue.process_one(FixtureReviewer)
                        and FixtureReviewer.calls == calls,
                        "duplicate_batch_called_reviewer",
                    )
                    require(
                        models.ChatPolicyNotice.objects.filter(
                            conversation=chat
                        ).count()
                        == 1,
                        "duplicate_warning",
                    )
                    send(
                        chat,
                        owner,
                        "[SYNTHETIC QA] Waiting for acknowledgement.",
                        status=403,
                    )
                    unread = chat.participant_set.get(user=tenant).unread_count
                    api(
                        owner,
                        "post",
                        base + "policy/",
                        {"policy_version": VERSION, "notice_id": str(notice.id)},
                    )
                    require(
                        chat.participant_set.get(user=tenant).unread_count == unread,
                        "ack_changed_unread",
                    )
                    checks.extend(
                        [
                            "warning_ack_gate",
                            "duplicate_batch_no_notice",
                            "ack_unread_unchanged",
                        ]
                    )

                    send(chat, owner, violation)
                    due([chat.pk])
                    processed(chat)
                    case = models.ChatModerationCase.objects.get(
                        conversation=chat, state="pending_review"
                    )
                    require(
                        restricted(owner) and not restricted(tenant),
                        "restriction_actor_scope_failed",
                    )
                    owner.refresh_from_db()
                    require(owner.is_active, "restriction_deactivated_account")
                    account = api(owner, "get", "/api/v1/chat/account-policy/")
                    require(
                        account["restricted"]
                        and account["can_manage_existing_obligations"],
                        "restricted_account_access_failed",
                    )
                    api(owner, "get", base + "chat/")
                    send(chat, owner, "[SYNTHETIC QA] Restricted sender.", status=403)
                    checks.append("repeat_restricts_actor_keeps_account_and_history")

                    explanation = "Synthetic acceptance: human reviewer should release this fixture."
                    appeal_path = f"/api/v1/chat/policy-cases/{case.id}/appeal/"
                    appeal_body = {"client_id": str(uuid.uuid4()), "text": explanation}
                    appealed = api(owner, "post", appeal_path, appeal_body)
                    require(appealed["appeal_submitted"], "appeal_not_recorded")
                    require(
                        api(owner, "post", appeal_path, appeal_body)["revision"]
                        == appealed["revision"],
                        "appeal_replay_changed_revision",
                    )
                    api(
                        tenant,
                        "post",
                        appeal_path,
                        {"client_id": str(uuid.uuid4()), "text": explanation},
                        status=404,
                    )
                    review_path = f"/api/v1/chat/admin/policy-cases/{case.id}/"
                    decision = {
                        "client_id": str(uuid.uuid4()),
                        "expected_revision": case.revision,
                        "action": "release",
                        "notes": explanation,
                    }
                    api(tenant, "get", review_path, status=403)
                    api(tenant, "post", review_path, decision, status=403)
                    api(admin, "get", review_path)
                    api(admin, "post", review_path, decision, status=409)
                    require(case.actions.count() == 0, "stale_decision_wrote_receipt")
                    decision["expected_revision"] = appealed["revision"]
                    released = api(admin, "post", review_path, decision)
                    replay = api(admin, "post", review_path, decision)
                    require(
                        released["state"] == "released"
                        and replay["revision"] == released["revision"]
                        and case.actions.count() == 1,
                        "release_receipt_replay_failed",
                    )
                    api(
                        admin,
                        "post",
                        review_path,
                        {**decision, "notes": explanation + " changed"},
                        status=409,
                    )
                    admin_role.role_name = "kyc_reviewer"
                    admin_role.save(update_fields=["role_name"])
                    api(admin, "get", review_path, status=403)
                    owner.refresh_from_db()
                    require(
                        owner.is_active
                        and not restricted(owner)
                        and not restricted(tenant),
                        "release_or_active_flag_failed",
                    )
                    checks.extend(
                        [
                            "appeal_replay_and_ownership",
                            "current_staff_role_enforced",
                            "stale_409",
                            "release_receipt_once",
                        ]
                    )

                    # Exactly twelve total messages across three conversations.
                    # Nine pending compliant messages exercise three scoped batches.
                    start_usage = resource.getrusage(resource.RUSAGE_SELF)
                    load_start = time.perf_counter()
                    enqueue_times = {}
                    send(
                        chat,
                        owner,
                        "[SYNTHETIC QA] I will pay in Sokoun after release.",
                    )
                    enqueue_times[chat.pk] = time.perf_counter()
                    for extra_chat, extra_owner, extra_tenant in pairs[1:]:
                        enqueue_times[extra_chat.pk] = time.perf_counter()
                        for index in range(4):
                            send(
                                extra_chat,
                                extra_owner if index % 2 == 0 else extra_tenant,
                                f"[SYNTHETIC QA] Viewing question {index}; payment stays in Sokoun.",
                            )
                    require(
                        models.Message.objects.filter(
                            conversation_id__in=conversations
                        ).count()
                        == 12,
                        "bounded_message_count_exceeded",
                    )
                    require(
                        models.ChatModerationInput.objects.filter(
                            conversation_id__in=conversations, state="pending"
                        ).count()
                        == 9,
                        "bounded_backlog_count_wrong",
                    )
                    due(conversations)
                    batch_ms, queue_ms = [], []
                    for _ in pairs:
                        tick = time.perf_counter()
                        batch = processed()
                        queue_ms.append(
                            round(
                                (tick - enqueue_times[batch.conversation_id]) * 1000, 2
                            )
                        )
                        batch_ms.append(round((time.perf_counter() - tick) * 1000, 2))
                    require(
                        not queue.process_one(FixtureReviewer),
                        "bounded_queue_not_drained",
                    )
                    require(
                        models.ChatModerationCase.objects.filter(
                            conversation_id__in=conversations
                        ).count()
                        == 2,
                        "compliant_fixture_created_cases",
                    )
                    end_usage = resource.getrusage(resource.RUSAGE_SELF)
                    result["load"] = {
                        "conversations": 3,
                        "total_messages": 12,
                        "pending_messages": 9,
                        "batches": 3,
                        "wall_s": round(time.perf_counter() - load_start, 4),
                        "cpu_s": round(
                            end_usage.ru_utime
                            + end_usage.ru_stime
                            - start_usage.ru_utime
                            - start_usage.ru_stime,
                            4,
                        ),
                        "process_peak_rss_mb": round(
                            end_usage.ru_maxrss
                            / (1024**2 if sys.platform == "darwin" else 1024),
                            2,
                        ),
                        "batch_ms": batch_ms,
                        "queue_wait_ms": queue_ms,
                    }
                    checks.append("bounded_fixture_queue_drained")
                    require(
                        callbacks["scheduled"] > 0 and callbacks["executed"] == 0,
                        "callbacks_not_deferred",
                    )
                    require(outbound["attempts"] == 0, "outbound_attempt_detected")
                finally:
                    # Never allow this outer transaction to commit, including on
                    # failed assertions, HTTP exceptions or keyboard interruption.
                    transaction.set_rollback(True)
    except Exception as error:
        failure = error
    finally:
        rows = sum(query.count() for query in rollback_queries())
        settings_restored = all(
            getattr(settings, name) == value for name, value in original.items()
        )
        result["rollback"] = {
            "models_checked": len(rollback_queries()),
            "remaining_rows": rows,
            "callbacks_executed": callbacks["executed"],
            "network_attempts": outbound["attempts"],
        }
        result["settings_restored"] = settings_restored
        require(rows == 0 and not connection.run_on_commit, "fixture_rollback_failed")
        require(settings_restored, "process_settings_not_restored")
    result["ok"] = failure is None
    if failure:
        # Never serialize DB exceptions/requests containing connection details.
        result["failure"] = (
            str(failure)
            if isinstance(failure, AssertionError)
            else type(failure).__name__
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthetic-only", action="store_true", required=True)
    parser.add_argument("--settings", default=os.environ.get("DJANGO_SETTINGS_MODULE"))
    args = parser.parse_args()
    if not args.settings:
        parser.error("Set DJANGO_SETTINGS_MODULE or pass --settings explicitly.")
    os.environ["DJANGO_SETTINGS_MODULE"] = args.settings
    sys.path.insert(0, str(BACKEND))
    import django

    django.setup()
    result = verify(synthetic_only=args.synthetic_only)
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":")), flush=True)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
