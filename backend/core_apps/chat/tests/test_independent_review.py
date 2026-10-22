import csv
import tempfile
from pathlib import Path
from unittest import TestCase
from tools.chat_policy.independent_review import FIELDS, prepare, score, validate_key


class IndependentReviewTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cases = [{"id": str(i), "family": str(i//2), "synthetic": True,
            "context": "Rental planning", "text": "Pay outside the app", "expected": "circumvention"} for i in range(8)]
        self.key, self.packet = prepare(self.cases, "fixed-evaluation-seed")
        self.journal = {"format_version": 2, "rubric_version": "grounded-two-pass-v2",
            "synthetic_only": True, "corpus_sha256": self.key["corpus_sha256"], "attempts": []}

    def labels(self, name, reviewer, label="circumvention"):
        path = Path(self.directory.name)/name
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS); writer.writeheader()
            writer.writerows({"blind_id": c["blind_id"], "reviewer_id": reviewer, "independence_attested": "yes",
                "label": label, "actor": "speaker", "evidence": c["text"], "rationale": "Explicit synthetic request"} for c in self.packet)
        return path

    def test_blind_packet_and_family_holdout(self):
        self.assertEqual(set(self.packet[0]), {"blind_id", "context", "text"})
        validate_key(self.key)
        for family in {c["family"] for c in self.key["cases"]}:
            self.assertEqual(len({c["split"] for c in self.key["cases"] if c["family"] == family}), 1)
        self.key["cases"][0]["text"] = "modified"
        with self.assertRaisesRegex(ValueError, "changed"): validate_key(self.key)

    def test_missing_reviews_or_provider_remain_unknown(self):
        result = score(self.key, self.labels("a", "a", ""), self.labels("b", "b", ""), self.journal)
        self.assertEqual(len(result["missing_labels"]), 8)
        self.assertIsNone(result["splits"]["held_out"]["precision"]["value"])
        self.assertFalse(result["enforcement_approved"])
        self.assertIsNone(result["false_restriction_rate"])

    def test_same_reviewer_and_legacy_journal_rejected(self):
        a, b = self.labels("a", "same"), self.labels("b", "same")
        with self.assertRaisesRegex(ValueError, "different reviewers"): score(self.key, a, b, self.journal)
        self.journal["format_version"] = 1
        with self.assertRaisesRegex(ValueError, "v2"): score(self.key, a, b, self.journal)

    def test_retries_do_not_inflate_and_disagreements_not_scored(self):
        a, b = self.labels("a", "a"), self.labels("b", "b")
        self.journal["attempts"] = [{"id": "0", "complete": True, "final_label": "circumvention"}]*2 + [{"id": "1", "complete": False, "error": "quota"}]
        result = score(self.key, a, b, self.journal)
        self.assertEqual(sum(s["scored_cases"] for s in result["splits"].values()), 1)
        result = score(self.key, a, self.labels("b", "b", "uncertain"), self.journal)
        self.assertEqual(len(result["disagreements_require_adjudication"]), 8)
        self.assertEqual(sum(s["scored_cases"] for s in result["splits"].values()), 0)

    def test_non_synthetic_is_rejected(self):
        self.cases[0]["synthetic"] = False
        with self.assertRaises(ValueError): prepare(self.cases, "seed")
