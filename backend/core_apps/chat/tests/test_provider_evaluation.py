"""Provider boundaries and honest resumable synthetic evaluation bookkeeping."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import requests

from core_apps.chat.moderation.provider import GeminiReviewer, ProviderUnavailable
from core_apps.chat.models import GeminiUsageReservation
from tools.chat_policy.evaluate_synthetic import (
    assert_local_synthetic_environment,
    candidates,
    completed_cases,
    evaluate_case,
    load_journal,
    persist,
    summarize,
)
from tools.chat_policy.synthetic_media import transcription_metrics


CASE = {
    "id": "fixture",
    "family": "explicit",
    "category": "circumvention",
    "synthetic": True,
    "expected": "circumvention",
    "context": "A rental viewing.",
    "text": "Let us pay outside Sokoun to avoid its fees.",
}


def verdict(label, *, confidence=0.99, actor="synthetic-owner", source="text"):
    return {
        "verdicts": [
            {
                "actor_id": actor,
                "label": label,
                "confidence": confidence,
                "evidence": (
                    [{"message_id": "current", "source": source, "quote": CASE["text"]}]
                    if label == "circumvention"
                    else []
                ),
            }
        ]
    }


def reviewer_with(*values):
    return SimpleNamespace(classify=Mock(side_effect=values))


def test_verifier_disagreement_fails_positive_case_and_cannot_confirm():
    reviewer = reviewer_with(verdict("circumvention"), verdict("compliant"))
    result = evaluate_case(CASE, reviewer)
    assert result["initial_label"] == "circumvention"
    assert result["final_label"] == "uncertain" and result["pass"] is False
    assert result["verified"] is False
    assert reviewer.classify.call_args.kwargs == {"verify": True}


def test_only_two_grounded_high_confidence_judgments_pass_violation():
    result = evaluate_case(
        CASE, reviewer_with(verdict("circumvention"), verdict("circumvention"))
    )
    assert result["complete"] and result["verified"] and result["pass"]


def test_missing_owner_verdict_is_never_implicitly_compliant():
    with pytest.raises(ProviderUnavailable, match="evaluation_missing_actor"):
        evaluate_case(
            {**CASE, "expected": "compliant"}, reviewer_with({"verdicts": []})
        )


def test_missing_verifier_is_uncertain_not_confirmed():
    result = evaluate_case(
        CASE, reviewer_with(verdict("circumvention"), {"verdicts": []})
    )
    assert result["verifier_label"] == "missing"
    assert result["final_label"] == "uncertain" and not result["pass"]


def test_partial_verifier_timeout_is_not_complete_but_retains_initial_evidence():
    result = {}
    with pytest.raises(ProviderUnavailable, match="provider_timeout"):
        evaluate_case(
            CASE,
            reviewer_with(
                verdict("circumvention"), ProviderUnavailable("provider_timeout")
            ),
            result=result,
        )
    assert result["initial_label"] == "circumvention" and not result.get("complete")


def test_confidence_downgrade_precedes_evaluation_and_does_not_reverify():
    reviewer = reviewer_with(verdict("circumvention", confidence=0.9))
    result = evaluate_case(CASE, reviewer)
    assert result["final_label"] == "uncertain" and not result["pass"]
    assert reviewer.classify.call_count == 1


def test_unreliable_transcription_cannot_ground_circumvention():
    reviewer = reviewer_with(verdict("circumvention", source="synthetic-media"))
    reviewer._extract_content = Mock(
        return_value={"text": CASE["text"], "uncertain": True}
    )
    with pytest.raises(ProviderUnavailable, match="invalid_quote"):
        evaluate_case(
            {**CASE, "medium": "image"}, reviewer, lambda _: (b"fixture", "image/png")
        )


def test_duplicate_attempts_and_partial_errors_do_not_inflate_coverage(tmp_path):
    journal = load_journal(tmp_path / "result.json", [CASE], "fixture-model")
    result = {**CASE, "complete": True, "final_label": "circumvention", "pass": True}
    journal["attempts"] = [
        result,
        {**result, "error": "provider_timeout", "complete": False},
        result,
    ]
    assert list(completed_cases(journal)) == [CASE["id"]]
    stats = summarize(journal)
    assert stats["unique_completed_cases"] == 1 and stats["attempts"] == 3
    assert stats["violation_recall"] == 1 and stats["false_positive_rate"] is None
    assert stats["provider_errors"] == {"provider_timeout": 1}


def test_failed_requests_have_unknown_accuracy_not_zero_or_full_pass(tmp_path):
    journal = load_journal(tmp_path / "result.json", [CASE], "fixture-model")
    journal["attempts"] = [{**CASE, "error": "provider_timeout", "complete": False}]
    assert summarize(journal)["accuracy"] is None
    assert summarize(journal)["unique_completed_cases"] == 0


def test_changed_model_corpus_legacy_results_rejected(tmp_path):
    path = tmp_path / "result.json"
    journal = load_journal(path, [CASE], "fixture-model")
    persist(path, journal)
    assert load_journal(path, [CASE], "fixture-model")["format_version"] == 2
    with pytest.raises(ValueError, match="changed"):
        load_journal(path, [CASE], "another-model")
    with pytest.raises(ValueError, match="changed"):
        load_journal(path, [{**CASE, "text": "different"}], "fixture-model")
    path.write_text("[]")
    with pytest.raises(ValueError, match="Legacy scoring"):
        load_journal(path, [CASE], "fixture-model")


def test_sampling_interleaves_categories_and_families_without_finished_ids(tmp_path):
    cases = [
        {
            **CASE,
            "id": f"{category}{family}{i}",
            "category": category,
            "family": f"{category}{family}",
        }
        for category in ("legitimate", "circumvention", "ambiguous")
        for family in range(2)
        for i in range(2)
    ]
    journal = load_journal(tmp_path / "result.json", cases, "fixture-model")
    sample = candidates(cases, journal, 6)
    assert len({c["family"] for c in sample}) == 6
    assert len({c["category"] for c in sample[:3]}) == 3
    journal["attempts"] = [{**sample[0], "complete": True}]
    assert sample[0]["id"] not in {c["id"] for c in candidates(cases, journal, 12)}


def test_resumed_sampling_prioritizes_unseen_families(tmp_path):
    cases = [
        {**CASE, "id": "a0", "family": "a"},
        {**CASE, "id": "a1", "family": "a"},
        {**CASE, "id": "b0", "family": "b"},
    ]
    journal = load_journal(tmp_path / "result.json", cases, "fixture-model")
    journal["attempts"] = [{**cases[0], "complete": True}]
    assert candidates(cases, journal, 1)[0]["family"] == "b"


def test_synthetic_override_refuses_production_database(monkeypatch):
    config = SimpleNamespace(
        DATABASES={"default": {"NAME": "capture_dev", "HOST": "127.0.0.1"}}
    )
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.production")
    with pytest.raises(ValueError, match="isolated local"):
        assert_local_synthetic_environment(config)
    monkeypatch.setenv("DJANGO_SETTINGS_MODULE", "config.settings.capture_dev")
    assert_local_synthetic_environment(config)
    config.DATABASES["default"]["HOST"] = "production.invalid"
    with pytest.raises(ValueError, match="isolated local"):
        assert_local_synthetic_environment(config)


def test_transcript_metrics_are_normalized_but_do_not_hide_negation_loss():
    assert transcription_metrics("أرفض الدفع خارج سكون.", "ارفض الدفع خارج سكون")[
        "normalized_exact"
    ]
    changed = transcription_metrics(
        "I refuse to pay outside Sokoun", "I pay outside Sokoun"
    )
    assert not changed["normalized_exact"] and changed["word_error_rate"] > 0
    assert changed["human_reviewed"] is False


@pytest.fixture
def enabled(settings):
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
    settings.GEMINI_API_KEY = "fixture-only"
    settings.CHAT_MODERATION_MODEL = "gemini-3.8-flash"
    settings.CHAT_MODERATION_DAILY_REQUESTS = 2


@pytest.mark.django_db
def test_provider_uses_supported_sampling_defaults_and_reserves_one_call(enabled):
    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        request.return_value.status_code = 200
        request.return_value.json.return_value = {
            "candidates": [
                {
                    "finishReason": "STOP",
                    "content": {"parts": [{"text": '{"verdicts": []}'}]},
                }
            ]
        }
        assert GeminiReviewer().classify([]) == {"verdicts": []}
    configuration = request.call_args.kwargs["json"]["generationConfig"]
    assert not {"temperature", "topP", "topK"} & configuration.keys()
    assert configuration["responseMimeType"] == "application/json"
    assert GeminiUsageReservation.objects.get().requests == 1


@pytest.mark.django_db
@pytest.mark.parametrize("failure", [503, 429, "timeout"])
def test_transient_failures_are_bounded_and_each_attempt_consumes_budget(
    enabled, failure
):
    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        if failure == "timeout":
            request.side_effect = requests.ReadTimeout()
            code = "provider_timeout"
        else:
            request.return_value.status_code = failure
            code = f"provider_http_{failure}"
        for _ in range(2):
            with pytest.raises(ProviderUnavailable, match=code):
                GeminiReviewer().classify([])
        with pytest.raises(ProviderUnavailable, match="daily_budget"):
            GeminiReviewer().classify([])
        # Durable worker retry owns backoff; no multiplicative immediate retries.
        assert request.call_count == 2
    assert GeminiUsageReservation.objects.get().requests == 2


@pytest.mark.django_db
def test_private_gate_applies_to_direct_fixture_extraction_too(settings):
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = False
    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        with pytest.raises(ProviderUnavailable, match="private_input_gate"):
            GeminiReviewer()._extract_content(b"fixture", "audio/wav")
        request.assert_not_called()
    assert not GeminiUsageReservation.objects.exists()


@pytest.mark.parametrize(
    "result",
    [
        {"text": "hello", "uncertain": "false"},
        {"text": "x" * 16001, "uncertain": False},
    ],
)
def test_invalid_extraction_never_reaches_classification(result):
    with patch.object(GeminiReviewer, "_call", return_value=result):
        with pytest.raises(ProviderUnavailable, match="media_invalid_response"):
            GeminiReviewer()._extract_content(b"fixture", "image/png")


def test_quota_diagnostics_keep_only_safe_numeric_metadata():
    from core_apps.chat.moderation.provider import retry_metadata

    response = Mock()
    response.headers = {"Retry-After": "10"}
    response.json.return_value = {
        "error": {
            "message": "secret payload must not be retained",
            "details": [
                {
                    "@type": "type.googleapis.com/google.rpc.RetryInfo",
                    "retryDelay": "38.5s",
                },
                {
                    "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                    "violations": [
                        {
                            "quotaId": "GenerateContentRequestsPerDayPerProjectPerModel-FreeTier",
                            "quotaValue": "20",
                            "subject": "private-project-id",
                        }
                    ],
                },
            ],
        }
    }
    metadata = retry_metadata(response)
    assert metadata == {
        "retry_after_seconds": 38.5,
        "quota_limits": [{"kind": "requests", "period": "day", "limit": 20}],
    }
    assert "secret" not in json.dumps(metadata) and "project-id" not in json.dumps(
        metadata
    )


@pytest.mark.parametrize(
    "header,body",
    [
        ("NaN", None),
        ("inf", []),
        ("invalid", {"error": {"details": "invalid"}}),
        (
            None,
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": {"bad": "data"},
                        }
                    ]
                }
            },
        ),
    ],
)
def test_invalid_retry_metadata_is_ignored_without_masking_provider_error(header, body):
    from core_apps.chat.moderation.provider import retry_metadata

    response = Mock()
    response.headers = {"Retry-After": header}
    response.json.return_value = body
    assert retry_metadata(response) == {"retry_after_seconds": None, "quota_limits": []}


@pytest.mark.django_db
def test_provider_retains_http_timing_and_retry_hints_without_error_payload(enabled):
    reviewer = GeminiReviewer()
    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        request.return_value.status_code = 429
        request.return_value.headers = {"Retry-After": "30"}
        request.return_value.json.return_value = {
            "error": {"message": "private diagnostic"}
        }
        with pytest.raises(ProviderUnavailable, match="provider_http_429") as raised:
            reviewer.classify([])
    assert raised.value.retry_after_seconds == 30
    assert len(reviewer.transport_events) == 1
    assert reviewer.transport_events[0]["status"] == 429
    assert reviewer.transport_events[0]["elapsed_ms"] >= 0
    assert "private diagnostic" not in repr(raised.value) + repr(
        reviewer.transport_events
    )


@pytest.mark.django_db
def test_timeout_timing_counts_actual_request_but_gate_failure_does_not(
    enabled, settings
):
    reviewer = GeminiReviewer()
    with patch(
        "core_apps.chat.moderation.provider.requests.post",
        side_effect=requests.ReadTimeout(),
    ):
        with pytest.raises(ProviderUnavailable, match="provider_timeout"):
            reviewer.classify([])
    assert reviewer.transport_events[0]["error"] == "provider_timeout"
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = False
    with pytest.raises(ProviderUnavailable, match="private_input_gate"):
        reviewer.classify([])
    assert len(reviewer.transport_events) == 1


def test_retry_after_delays_worker_beyond_local_exponential_backoff():
    from core_apps.chat.moderation.queue import retry_schedule
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    deadline, shared = retry_schedule(
        ProviderUnavailable("provider_http_503", retry_after_seconds=180), 1, now
    )
    assert deadline == now + timedelta(seconds=180) and shared


@pytest.mark.parametrize(
    "now_iso,reset_iso",
    [
        ("2026-10-22T10:00:00+00:00", "2026-10-23T07:00:00+00:00"),
        ("2026-11-01T07:01:00+00:00", "2026-11-02T08:00:00+00:00"),
    ],
)
def test_provider_daily_quota_waits_for_pacific_reset_including_dst(now_iso, reset_iso):
    from core_apps.chat.moderation.queue import retry_schedule
    from datetime import datetime

    error = ProviderUnavailable(
        "provider_http_429",
        quota_limits=[{"kind": "requests", "period": "day", "limit": 20}],
    )
    deadline, shared = retry_schedule(error, 1, datetime.fromisoformat(now_iso))
    assert deadline == datetime.fromisoformat(reset_iso) and shared


def test_retry_schedule_honors_later_server_hint_and_ignores_invalid_delays():
    from core_apps.chat.moderation.queue import retry_schedule
    from datetime import datetime, timedelta, timezone

    now = datetime(2026, 10, 22, 10, tzinfo=timezone.utc)
    error = ProviderUnavailable(
        "provider_http_429", retry_after_seconds=90000, quota_limits=[{"period": "day"}]
    )
    assert retry_schedule(error, 1, now)[0] == now + timedelta(seconds=90000)
    for invalid in (float("nan"), float("inf"), -10, "12", True):
        assert retry_schedule(
            ProviderUnavailable("provider_timeout", retry_after_seconds=invalid), 1, now
        )[0] == now + timedelta(seconds=60)


@pytest.mark.django_db
def test_global_provider_cooldown_survives_new_worker_and_blocks_other_chats(
    user, another_user, settings
):
    import uuid
    from datetime import timedelta
    from django.utils import timezone
    from core_apps.chat.models import (
        Conversation,
        Message,
        ChatModerationInput,
        ChatModerationBatch,
        ChatModerationCase,
    )
    from core_apps.chat.moderation.queue import process_one, claim
    from core_apps.chat.moderation.sealed import seal

    settings.CHAT_MODERATION_MODE = "enforce"
    first, second = Conversation.objects.create(), Conversation.objects.create()
    now = timezone.now()
    rows = []
    for index, chat in enumerate((first, second)):
        message = Message.objects.create(
            conversation=chat,
            sender=user,
            content="Synthetic rental test",
            client_message_id=uuid.uuid4(),
        )
        snapshot = {
            "message_id": str(message.pk),
            "revision": 1,
            "actor_id": str(user.pk),
            "sequence": index + 1,
            "created_at": now.isoformat(),
            "text": message.content,
            "attachments": [],
        }
        rows.append(
            ChatModerationInput.objects.create(
                message=message,
                revision=1,
                conversation=chat,
                ciphertext=seal(snapshot),
                due_at=now - timedelta(seconds=10 - index),
            )
        )
    error = ProviderUnavailable(
        "provider_http_429",
        retry_after_seconds=120,
        quota_limits=[{"kind": "requests", "period": "day", "limit": 20}],
    )
    reviewer = SimpleNamespace(model="fixture", classify=Mock(side_effect=error))
    factory = Mock(return_value=reviewer)
    assert process_one(factory)
    batch = ChatModerationBatch.objects.get()
    assert batch.state == "retry" and batch.attempts == 1
    assert batch.diagnostics["provider_backoff"] is True
    # A new worker/process reads the durable batch; no process-local timer needed.
    unused_factory = Mock()
    assert process_one(unused_factory) is False
    unused_factory.assert_not_called()
    rows[1].refresh_from_db()
    assert rows[1].state == "pending" and not ChatModerationCase.objects.exists()
    with patch(
        "core_apps.chat.moderation.queue.timezone.now",
        return_value=batch.next_attempt_at + timedelta(seconds=1),
    ):
        replacement = claim()
    assert replacement.pk == batch.pk and replacement.attempts == 2
    assert replacement.lease_token != batch.lease_token


@pytest.mark.django_db
def test_incomplete_json_counts_one_http_event(enabled):
    reviewer = GeminiReviewer()
    with patch("core_apps.chat.moderation.provider.requests.post") as request:
        request.return_value.status_code = 200
        request.return_value.json.side_effect = requests.exceptions.JSONDecodeError(
            "invalid", "not json", 0
        )
        with pytest.raises(ProviderUnavailable, match="provider_invalid_response"):
            reviewer.classify([])
    assert len(reviewer.transport_events) == 1
    assert reviewer.transport_events[0]["status"] == 200


def test_extraction_metrics_do_not_turn_partial_case_into_completed_score(tmp_path):
    journal = load_journal(tmp_path / "result.json", [CASE], "fixture-model")
    partial = {
        **CASE,
        "complete": False,
        "error": "provider_timeout",
        "extraction": {"text": CASE["text"], "uncertain": False},
        "transcription_metrics": transcription_metrics(CASE["text"], CASE["text"]),
    }
    journal["attempts"] = [partial, partial]
    summary = summarize(journal)
    assert (
        summary["unique_extracted_cases"] == 1
        and summary["normalized_exact_extractions"] == 1
    )
    assert summary["unique_completed_cases"] == 0 and summary["accuracy"] is None
