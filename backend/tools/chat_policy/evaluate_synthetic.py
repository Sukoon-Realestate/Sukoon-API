"""Evaluate only packaged/generated synthetic fixtures; never approve private inputs.

Results are an attempt journal, not a count of successful HTTP responses. A case
is complete only after evidence validation and any required independent verifier.
"""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import hashlib
import json
import os
from pathlib import Path
import time

FORMAT_VERSION = 2
RUBRIC_VERSION = "grounded-two-pass-v2"
TRANSIENT_ERRORS = {
    "provider_timeout",
    "provider_transport",
    "provider_http_408",
    "provider_http_429",
    "provider_http_500",
    "provider_http_502",
    "provider_http_503",
    "provider_http_504",
}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def corpus_digest(cases):
    return hashlib.sha256(
        json.dumps(cases, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def load_journal(path, cases, model):
    digest = corpus_digest(cases)
    if not path.exists():
        return {
            "format_version": FORMAT_VERSION,
            "rubric_version": RUBRIC_VERSION,
            "synthetic_only": True,
            "independently_human_reviewed": False,
            "corpus_sha256": digest,
            "total_corpus": len(cases),
            "semantic_families": len({c["family"] for c in cases}),
            "model": model,
            "created_at": utcnow(),
            "attempts": [],
        }
    journal = json.loads(path.read_text())
    if not isinstance(journal, dict) or journal.get("format_version") != FORMAT_VERSION:
        raise ValueError(
            "Legacy scoring did not verify final decisions; keep it as evidence and choose a new output file"
        )
    if (
        journal.get("corpus_sha256"),
        journal.get("model"),
        journal.get("rubric_version"),
    ) != (digest, model, RUBRIC_VERSION):
        raise ValueError("Corpus, model or rubric changed; choose a new output file")
    return journal


def completed_cases(journal):
    # A retry cannot inflate coverage. Failed/partial attempts never contribute.
    complete = {}
    for attempt in journal["attempts"]:
        if attempt.get("complete") is True and "error" not in attempt:
            complete[attempt["id"]] = attempt
    return complete


def summarize(journal):
    completed = completed_cases(journal)
    results = list(completed.values())
    non_violations = [r for r in results if r["expected"] != "circumvention"]
    violations = [r for r in results if r["expected"] == "circumvention"]
    false_positives = sum(r["final_label"] == "circumvention" for r in non_violations)
    missed = sum(r["final_label"] != "circumvention" for r in violations)
    extracted = {r["id"]: r for r in journal["attempts"] if "extraction" in r}
    extraction_metrics = [r["transcription_metrics"] for r in extracted.values()]
    return {
        "unique_completed_cases": len(completed),
        "total_corpus": journal["total_corpus"],
        "attempts": len(journal["attempts"]),
        "provider_errors": dict(
            Counter(r["error"] for r in journal["attempts"] if "error" in r)
        ),
        "completed_families": len({r["family"] for r in results}),
        "total_semantic_families": journal["semantic_families"],
        "expectation_passes": sum(r["pass"] for r in results),
        "accuracy": sum(r["pass"] for r in results) / len(results) if results else None,
        "non_violation_cases": len(non_violations),
        "false_positive_cases": false_positives,
        "false_positive_rate": (
            false_positives / len(non_violations) if non_violations else None
        ),
        "violation_cases": len(violations),
        "missed_violation_cases": missed,
        "violation_recall": (
            (len(violations) - missed) / len(violations) if violations else None
        ),
        "corpus_complete": len(completed) == journal["total_corpus"],
        "independently_human_reviewed": False,
        "unique_extracted_cases": len(extracted),
        "normalized_exact_extractions": sum(
            m["normalized_exact"] for m in extraction_metrics
        ),
        "mean_word_error_rate": (
            sum(m["word_error_rate"] for m in extraction_metrics)
            / len(extraction_metrics)
            if extraction_metrics
            else None
        ),
    }


def persist(path, journal):
    journal["updated_at"] = utcnow()
    journal["summary"] = summarize(journal)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(journal, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def candidates(cases, journal, limit):
    done = completed_cases(journal)
    # Visit distinct semantic families before filling contextual variants.
    available = sorted((c for c in cases if c["id"] not in done), key=lambda c: c["id"])
    grouped = {}
    for case in available:
        grouped.setdefault(case["family"], []).append(case)
    # Interleave categories as well as families so small budgeted runs do not
    # accidentally evaluate only the alphabetically first ambiguous families.
    families = {}
    for family, entries in grouped.items():
        families.setdefault(entries[0]["category"], []).append(family)
    completed_family_counts = Counter(r["family"] for r in done.values())
    for category in families:
        families[category].sort(
            key=lambda family: (completed_family_counts[family], family)
        )
    family_order = []
    while any(families.values()):
        for category in sorted(families):
            if families[category]:
                family_order.append(families[category].pop(0))
    result = []
    while grouped and len(result) < limit:
        for family in family_order:
            if family not in grouped:
                continue
            result.append(grouped[family].pop(0))
            if not grouped[family]:
                del grouped[family]
            if len(result) == limit:
                break
    return result


def evaluate_case(case, reviewer, prepare_media=None, result=None):
    from core_apps.chat.moderation.provider import ProviderUnavailable
    from core_apps.chat.moderation.queue import validated_verdicts

    messages = [
        {
            "message_id": "context",
            "actor_id": "synthetic-tenant",
            "new": False,
            "text": case["context"],
            "media": [],
        },
        {
            "message_id": "current",
            "actor_id": "synthetic-owner",
            "new": True,
            "text": case["text"],
            "media": [],
        },
    ]
    result = {} if result is None else result
    if case.get("medium"):
        content, mime_type = prepare_media(case)
        extracted = reviewer._extract_content(content, mime_type)
        result["extraction"] = extracted
        from tools.chat_policy.synthetic_media import transcription_metrics

        result["transcription_metrics"] = transcription_metrics(
            case["text"], extracted["text"]
        )
        messages[-1].update(
            text="",
            media=[{"source": "synthetic-media", "kind": case["medium"], **extracted}],
        )
    initial = validated_verdicts(reviewer.classify(messages), messages)
    first = next((v for v in initial if v["actor_id"] == "synthetic-owner"), None)
    if first is None:
        # Missing output is unknown, never an implicitly correct compliant result.
        raise ProviderUnavailable("evaluation_missing_actor")
    result["initial_label"] = first["label"]
    result["initial_confidence"] = first["confidence"]
    result["final_label"] = first["label"]
    if any(v["label"] == "circumvention" for v in initial):
        verified = validated_verdicts(
            reviewer.classify(messages, verify=True), messages
        )
        second = next((v for v in verified if v["actor_id"] == "synthetic-owner"), None)
        result["verifier_label"] = second["label"] if second else "missing"
        if first["label"] == "circumvention":
            shared = {r["message_id"] for r in first["evidence"]} & {
                r["message_id"] for r in (second or {}).get("evidence", [])
            }
            # Exactly as complete(): disagreement or disjoint evidence only
            # creates a review case. It cannot confirm a sanctionable finding.
            confirmed = (
                second is not None
                and second["label"] == "circumvention"
                and bool(shared)
            )
            result["final_label"] = "circumvention" if confirmed else "uncertain"
            result["verified"] = confirmed
    result["pass"] = (
        result["final_label"] != "circumvention"
        if case["expected"] == "no_circumvention"
        else result["final_label"] == case["expected"]
    )
    result["complete"] = True
    return result


def assert_local_synthetic_environment(settings):
    database = settings.DATABASES["default"]
    if (
        os.environ.get("DJANGO_SETTINGS_MODULE") != "config.settings.capture_dev"
        or database.get("NAME") != "capture_dev"
        or database.get("HOST") not in {"127.0.0.1", "localhost"}
    ):
        raise ValueError(
            "Synthetic override is restricted to the isolated local capture_dev database"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--synthetic-provider-check", action="store_true", required=True
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--max-requests", type=int, default=12)
    parser.add_argument("--attempts-per-case", type=int, default=2)
    parser.add_argument(
        "--evaluation-daily-limit",
        type=int,
        help="Explicit process-local synthetic allowance, at most600; never changes production",
    )
    parser.add_argument(
        "--media",
        action="store_true",
        help="Use generated text cards and computer speech only",
    )
    args = parser.parse_args()
    if (
        not 1 <= args.limit <= 300
        or not 1 <= args.max_requests <= 600
        or (
            args.evaluation_daily_limit is not None
            and not 1 <= args.evaluation_daily_limit <= 600
        )
        or not 1 <= args.attempts_per_case <= 3
    ):
        parser.error(
            "limit=1..300, max-requests/evaluation-daily-limit=1..600, attempts-per-case=1..3; provider quota remains authoritative"
        )
    import django

    django.setup()
    from django.conf import settings
    from core_apps.chat.moderation.provider import GeminiReviewer, ProviderUnavailable

    assert_local_synthetic_environment(settings)
    if args.evaluation_daily_limit is not None:
        settings.CHAT_MODERATION_DAILY_REQUESTS = args.evaluation_daily_limit
    if args.media:
        from tools.chat_policy.synthetic_media import CASES, prepare_media

        cases = CASES
    else:
        cases = json.loads(
            Path(__file__).with_name("synthetic-corpus.json").read_text()
        )
        prepare_media = None
        if len(cases) != 300:
            raise ValueError("Unexpected corpus")
    if not all(c.get("synthetic") is True for c in cases) or len(
        {c["id"] for c in cases}
    ) != len(cases):
        raise ValueError("Only unique packaged synthetic cases are allowed")
    journal = load_journal(args.output, cases, settings.CHAT_MODERATION_MODEL)
    not_before = journal.get("next_provider_attempt_at")
    if not_before and datetime.fromisoformat(not_before) > datetime.now(timezone.utc):
        print(
            json.dumps(
                {
                    "stopped": "provider_retry_window",
                    "next_provider_attempt_at": not_before,
                }
            ),
            flush=True,
        )
        return
    journal.pop("next_provider_attempt_at", None)
    # Only this isolated process is approved for these fixed generated fixtures.
    # The production flags, billing and private-user access remain unchanged.
    settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
    requests_used = 0
    last_request_started = None
    consecutive_failures = 0
    http_attempts = 0
    stop_provider = False

    class BoundedReviewer(GeminiReviewer):
        def _call(self, *arguments, **kwargs):
            nonlocal requests_used, last_request_started
            if requests_used >= args.max_requests:
                raise ProviderUnavailable("evaluation_run_budget")
            if last_request_started is not None:
                time.sleep(max(0, 15 - (time.monotonic() - last_request_started)))
            last_request_started = time.monotonic()
            requests_used += 1
            return super()._call(*arguments, **kwargs)

    for case in candidates(cases, journal, args.limit):
        for retry in range(args.attempts_per_case):
            start = time.monotonic()
            result = {
                "id": case["id"],
                "family": case["family"],
                "category": case["category"],
                "expected": case["expected"],
                "started_at": utcnow(),
                "complete": False,
            }
            reviewer = BoundedReviewer()
            retry_after = 0
            try:
                evaluate_case(case, reviewer, prepare_media, result)
                consecutive_failures = 0
            except ProviderUnavailable as error:
                result["error"] = str(error)
                consecutive_failures += 1
                retry_after = error.retry_after_seconds or 0
                if error.retry_after_seconds is not None:
                    result["retry_after_seconds"] = error.retry_after_seconds
                if error.quota_limits:
                    result["quota_limits"] = error.quota_limits
                if any(q["period"] == "day" for q in error.quota_limits):
                    local = datetime.now(ZoneInfo("America/Los_Angeles"))
                    reset = (local + timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    journal["next_provider_attempt_at"] = reset.astimezone(
                        timezone.utc
                    ).isoformat()
                    journal["stopped_reason"] = "provider_daily_quota"
                    stop_provider = True
                elif retry_after > 60:
                    journal["next_provider_attempt_at"] = (
                        datetime.now(timezone.utc) + timedelta(seconds=retry_after)
                    ).isoformat()
                    journal["stopped_reason"] = "provider_retry_window"
                    stop_provider = True
            result["transport_events"] = reviewer.transport_events
            http_attempts += len(reviewer.transport_events)
            result["elapsed_ms"] = round((time.monotonic() - start) * 1000)
            result["attempt"] = 1 + sum(
                r["id"] == case["id"] for r in journal["attempts"]
            )
            journal["attempts"].append(result)
            persist(args.output, journal)
            print(json.dumps(result, ensure_ascii=False), flush=True)
            if (
                result["complete"]
                or stop_provider
                or result.get("error") not in TRANSIENT_ERRORS
                or consecutive_failures >= 3
                or requests_used >= args.max_requests
            ):
                break
            time.sleep(max(8 * 2**retry, retry_after))
        if (
            stop_provider
            or consecutive_failures >= 3
            or requests_used >= args.max_requests
            or result.get("error")
            in {
                "daily_budget",
                "evaluation_run_budget",
                "provider_http_400",
                "provider_http_401",
                "provider_http_403",
                "provider_http_404",
            }
        ):
            break
        time.sleep(max(8, retry_after))  # Honor retry hints between cases too.
    persist(args.output, journal)
    print(
        json.dumps(
            {
                **journal["summary"],
                "calls_attempted_this_run": requests_used,
                "http_attempts_this_run": http_attempts,
                "stopped_reason": journal.get("stopped_reason"),
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
