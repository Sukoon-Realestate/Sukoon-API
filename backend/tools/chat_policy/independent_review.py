"""Offline blind review packets and family-separated evaluation. No provider calls.

Reviewer identities/independence are attestations, not programmatically proven
human review. Missing/disputed labels and incomplete provider attempts stay unknown.
"""
import argparse
import csv
import hashlib
import hmac
import json
import math
from pathlib import Path

LABELS = {"compliant", "circumvention", "uncertain"}
RUBRIC = "independent-rental-chat-v1"
FIELDS = ["blind_id", "reviewer_id", "independence_attested", "label", "actor", "evidence", "rationale"]


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def prepare(cases, seed):
    if not seed or not cases or any(c.get("synthetic") is not True for c in cases):
        raise ValueError("Only the declared synthetic corpus may enter a review packet")
    ids = [c["id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate corpus identity")
    families = sorted({c["family"] for c in cases}, key=lambda f: digest([seed, f]))
    if len(families) < 3:
        raise ValueError("At least three independent semantic families are required")
    held = set(families[:max(1, math.ceil(len(families) * .3))])
    private, public = [], []
    for c in cases:
        blind = hmac.new(seed.encode(), c["id"].encode(), hashlib.sha256).hexdigest()[:20]
        # Do not expose IDs such as L00/C00, category, expectation or split.
        public.append({"blind_id": blind, "context": c["context"], "text": c["text"]})
        private.append({**c, "blind_id": blind, "split": "held_out" if c["family"] in held else "development"})
    public.sort(key=lambda c: c["blind_id"])
    return {
        "rubric": RUBRIC, "synthetic_only": True, "corpus_sha256": digest(cases),
        "packet_sha256": digest(public), "cases": private,
    }, public


def read_labels(path, key):
    lookup = {c["blind_id"]: c for c in key["cases"]}
    labels, reviewers = {}, set()
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != FIELDS:
            raise ValueError("Review columns differ from the bound packet")
        for row in reader:
            identity = row["blind_id"]
            if identity not in lookup or identity in labels:
                raise ValueError("Unknown/duplicate blind case")
            labels[identity] = None
            if not row["label"].strip():
                continue
            if row["label"] not in LABELS or row["actor"] not in {"speaker", "none", "unknown"}:
                raise ValueError("Invalid label/actor")
            if not row["reviewer_id"].strip() or row["independence_attested"] != "yes" or not row["rationale"].strip():
                raise ValueError("Review identity, independence attestation and rationale are required")
            if row["label"] == "circumvention" and (
                row["actor"] != "speaker" or not row["evidence"].strip()
                or row["evidence"] not in lookup[identity]["text"]
            ):
                raise ValueError("A positive decision requires the actual speaker and verbatim evidence")
            reviewers.add(row["reviewer_id"].strip())
            labels[identity] = row
    if set(labels) != set(lookup) or len(reviewers) > 1:
        raise ValueError("One complete packet and one reviewer per file are required")
    return labels, next(iter(reviewers), None)


def proportion(numerator, denominator):
    if not denominator:
        return {"numerator": numerator, "denominator": 0, "value": None, "wilson_95": None}
    p, z = numerator / denominator, 1.959963984540054
    center = (p + z*z/(2*denominator)) / (1 + z*z/denominator)
    half = z * math.sqrt(p*(1-p)/denominator + z*z/(4*denominator**2)) / (1 + z*z/denominator)
    return {"numerator": numerator, "denominator": denominator, "value": p, "wilson_95": [max(0, center-half), min(1, center+half)]}


def validate_key(key):
    cases = key.get("cases", [])
    if not cases or any(c.get("synthetic") is not True for c in cases):
        raise ValueError("Invalid synthetic packet")
    originals = [{k: v for k, v in c.items() if k not in {"blind_id", "split"}} for c in cases]
    packet = sorted(({"blind_id": c["blind_id"], "context": c["context"], "text": c["text"]} for c in cases), key=lambda c: c["blind_id"])
    if digest(originals) != key.get("corpus_sha256") or digest(packet) != key.get("packet_sha256"):
        raise ValueError("Packet content changed")
    if len({c["id"] for c in cases}) != len(cases) or len({c["blind_id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate packet identity")
    families = {}
    for c in cases:
        if c.get("split") not in {"development", "held_out"}:
            raise ValueError("Unknown split")
        if c["family"] in families and families[c["family"]] != c["split"]:
            raise ValueError("Semantic family leaks across splits")
        families[c["family"]] = c["split"]
    if set(families.values()) != {"development", "held_out"}:
        raise ValueError("Both development and held-out families are required")


def score(key, first, second, journal):
    if key.get("rubric") != RUBRIC or key.get("synthetic_only") is not True:
        raise ValueError("Unknown review rubric/corpus")
    validate_key(key)
    if journal.get("format_version") != 2 or journal.get("rubric_version") != "grounded-two-pass-v2":
        raise ValueError("Only final grounded v2 decisions may be scored")
    if journal.get("corpus_sha256") != key["corpus_sha256"] or journal.get("synthetic_only") is not True:
        raise ValueError("Journal belongs to another corpus")
    a, reviewer_a = read_labels(first, key); b, reviewer_b = read_labels(second, key)
    if reviewer_a and reviewer_a == reviewer_b:
        raise ValueError("Two different reviewers must label independently")
    complete = {}
    valid_ids = {c["id"] for c in key["cases"]}
    for attempt in journal.get("attempts", []):
        if attempt.get("id") not in valid_ids:
            raise ValueError("Journal contains an unknown case")
        if attempt.get("complete") is True and "error" not in attempt:
            if attempt.get("final_label") not in LABELS | {"off_topic"}:
                raise ValueError("Unknown final decision")
            complete[attempt["id"]] = {**attempt, "final_label": "compliant" if attempt["final_label"] == "off_topic" else attempt["final_label"]}
    missing, disputed, agreed = [], [], {}
    for case in key["cases"]:
        identity = case["blind_id"]
        if a[identity] is None or b[identity] is None:
            missing.append(identity)
        elif (a[identity]["label"], a[identity]["actor"]) != (b[identity]["label"], b[identity]["actor"]):
            disputed.append(identity)
        else:
            agreed[case["id"]] = a[identity]["label"]
    results = {}
    for split in ("development", "held_out"):
        ids = [c["id"] for c in key["cases"] if c["split"] == split]
        pairs = [(agreed[i], complete[i]["final_label"]) for i in ids if i in agreed and i in complete]
        tp = sum(expected == actual == "circumvention" for expected, actual in pairs)
        fp = sum(expected == "compliant" and actual == "circumvention" for expected, actual in pairs)
        predicted = sum(actual == "circumvention" for _, actual in pairs)
        ambiguous_positive = sum(expected == "uncertain" and actual == "circumvention" for expected, actual in pairs)
        results[split] = {
            "corpus_cases": len(ids), "scored_cases": len(pairs),
            "provider_complete_cases": sum(i in complete for i in ids),
            "independently_agreed_labels": sum(i in agreed for i in ids),
            "missing_provider_or_label": len(ids) - len(pairs),
            # Ambiguous positives are unsafe for automatic restriction and do
            # not count as correct positives in conservative precision.
            "precision": proportion(tp, predicted),
            "false_positive_rate": proportion(fp, sum(e == "compliant" for e, _ in pairs)),
            "unsafe_positive_on_ambiguous": ambiguous_positive,
            "recall": proportion(tp, sum(e == "circumvention" for e, _ in pairs)),
            "abstention": proportion(sum(v == "uncertain" for _, v in pairs), len(pairs)),
        }
    return {
        "rubric": RUBRIC, "corpus_sha256": key["corpus_sha256"], "splits": results,
        "missing_labels": missing, "disagreements_require_adjudication": disputed,
        "reviewer_independence": "self_attested_unverified", "enforcement_approved": False,
        "false_restriction_rate": None,
        "limitation": "This offline label evaluation never executes account restrictions. Operational restriction outcomes need a separate shadow/review audit. Intervals describe cases, not independent family sampling.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("prepare"); build.add_argument("--seed", required=True); build.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("score")
    for name in ("key", "review-a", "review-b", "journal", "output"):
        check.add_argument("--"+name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        cases = json.loads(Path(__file__).with_name("synthetic-corpus.json").read_text())
        key, packet = prepare(cases, args.seed)
        args.output.mkdir(parents=True, exist_ok=False)
        (args.output/"packet.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2))
        private = args.output/"private-key.json"; private.write_text(json.dumps(key, ensure_ascii=False, indent=2)); private.chmod(0o600)
        for reviewer in ("a", "b"):
            with (args.output/f"review-{reviewer}.csv").open("w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.DictWriter(stream, fieldnames=FIELDS); writer.writeheader()
                writer.writerows({"blind_id": c["blind_id"]} for c in packet)
    else:
        result = score(json.loads(args.key.read_text()), args.review_a, args.review_b, json.loads(args.journal.read_text()))
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
