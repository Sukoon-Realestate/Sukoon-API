"""Opt-in provider evaluation of the packaged synthetic corpus only, with resumable IDs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

parser = argparse.ArgumentParser()
parser.add_argument("--synthetic-provider-check", action="store_true", required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--limit", type=int, default=12)
args = parser.parse_args()
if not 1 <= args.limit <= 100:
    parser.error("limit must be 1..100; the existing daily budget is still authoritative")
import django
django.setup()
from django.conf import settings
from core_apps.chat.moderation.provider import GeminiReviewer, ProviderUnavailable
from core_apps.chat.moderation.queue import validated_verdicts
corpus_path = Path(__file__).with_name("synthetic-corpus.json")
corpus = json.loads(corpus_path.read_text())
digest = hashlib.sha256(corpus_path.read_bytes()).hexdigest()
assert len(corpus) == 300 and all(c["synthetic"] is True for c in corpus)
# Process-only attestation: inputs below come exclusively from the fixed synthetic file.
# This does not switch deployment mode, billing or any server/account policy flag.
settings.CHAT_MODERATION_PRIVATE_INPUTS_APPROVED = True
results = json.loads(args.output.read_text()) if args.output.exists() else []
if any(r.get("corpus_sha256") != digest for r in results):
    raise SystemExit("Corpus changed; choose a new output file")
done = {r["id"] for r in results if "error" not in r}
candidates = sorted([c for c in corpus if c["id"] not in done], key=lambda c: hashlib.sha256(c["id"].encode()).hexdigest())[:args.limit]
args.output.parent.mkdir(parents=True, exist_ok=True)
for case in candidates:
    messages = [
        {"message_id": "context", "actor_id": "synthetic-tenant", "new": False, "text": case["context"], "media": []},
        {"message_id": "current", "actor_id": "synthetic-owner", "new": True, "text": case["text"], "media": []},
    ]
    start = time.monotonic()
    result = {"id": case["id"], "category": case["category"], "expected": case["expected"], "corpus_sha256": digest, "model": settings.CHAT_MODERATION_MODEL}
    try:
        reviewer = GeminiReviewer()
        verdicts = validated_verdicts(reviewer.classify(messages), messages)
        observed = next((v["label"] for v in verdicts if v["actor_id"] == "synthetic-owner"), "compliant")
        result["observed"] = observed
        result["pass"] = observed != "circumvention" if case["expected"] == "no_circumvention" else observed == case["expected"]
        if observed == "circumvention":
            verified = validated_verdicts(reviewer.classify(messages, verify=True), messages)
            result["verified"] = any(v["actor_id"] == "synthetic-owner" and v["label"] == "circumvention" for v in verified)
    except ProviderUnavailable as error:
        result["error"] = str(error)
    result["elapsed_ms"] = round((time.monotonic() - start) * 1000)
    results.append(result)
    temp = args.output.with_suffix(".tmp")
    temp.write_text(json.dumps(results, indent=2) + "\n")
    temp.replace(args.output)
    print(json.dumps(result), flush=True)
    if "error" in result:
        break
print(json.dumps({"successful_cases": sum("observed" in r for r in results), "total_corpus": len(corpus), "synthetic_only": True}))
