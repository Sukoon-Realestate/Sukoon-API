"""Map every baseline/current alias to honest Sprint 04 performance evidence.

No HTTP requests or databases are opened. Unmeasured routes remain pending, not
implicit exceptions. Service/selector probes never certify the whole route family.
"""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def evidence(row):
    handler, route = row["handler"], row["route"]
    if handler.endswith(".AdminSupportDetailAPIView"):
        return ["support-staff-thread", "support-bounded-thread"]
    if handler.endswith(".TicketDetailAPIView"):
        return ["support-information", "support-bounded-thread"]
    if handler.endswith(".PropertyListAPIView"):
        return ["saved-search-itemized"]
    if handler.endswith(".PropertyReviewListAPIView"):
        return ["public-property-reviews"]
    if handler.endswith("capture_views.sessions"):
        return ["capture-sessions", "capture-session-summary"]
    if handler.endswith("capture_views.jobs"):
        return ["capture-job-history"]
    if handler.endswith("owner_advertisement_collection"):
        return ["advertising-owner"]
    if handler.endswith("tenant_home_placement"):
        return ["advertising-rejection"]
    if handler.endswith(".AdminPropertyListAPIView") or handler.endswith(".AdminPropertyListView"):
        return ["admin-properties"]
    if handler.endswith(".AdminKYCListAPIView"):
        return ["kyc"]
    if "admin" in handler and ("ReportList" in handler or "ReportsList" in handler):
        return ["reports"]
    if handler.endswith(".AdminAnalyticsStatsAPIView"):
        return ["analytics"]
    if handler.endswith(".AdminExecutiveDashboardStatsView"):
        return ["executive-dashboard"]
    if handler.endswith(".AdminContentAPIView"):
        return [
            "content-cities",
            "content-districts",
            "content-campuses",
            "content-subscription_plans",
            "content-plan_benefits",
        ]
    if "admin/system/notifications/" in route:
        return ["campaign-history"]
    if handler.endswith(".owner_availability") or handler.endswith(".viewing_time_proposals"):
        return ["appointment-availability"]
    if handler.endswith(".PublicReputationSummaryView"):
        return ["public-payment-reliability"]
    if handler.endswith(".MessageListAPIView"):
        return ["group-message-history", "legacy-direct-message-history"]
    if handler.endswith(".GroupMessageContextAPIView"):
        return ["group-message-history"]
    if handler.endswith(
        (
            ".TicketDetailAPIView",
            ".TicketReplyAPIView",
            ".TicketReplyReceiptAPIView",
            ".TicketCreationReceiptAPIView",
        )
    ):
        return ["support-information"]
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observations", type=Path, action="append", default=[])
    args = parser.parse_args()
    observations = {}
    for path in args.observations:
        for line in path.read_text().splitlines():
            record = json.loads(line)
            observations.setdefault(record["case"], []).append(
                {
                    key: record[key]
                    for key in (
                        "size",
                        "queries",
                        "seconds",
                        "cpu_seconds",
                        "peak_python_bytes",
                        "payload_bytes",
                        "payload_measure",
                        "http_calls",
                        "storage_exists_calls",
                        "transaction_spans",
                        "max_transaction_seconds",
                    )
                    if key in record
                }
            )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    import django

    django.setup()
    from tools.qa.route_matrix import build

    baseline = json.loads((ROOT / "sprints/evidence/sprint-00/route-matrix.json").read_text())["routes"]
    current = build()

    def identity(row):
        return (row["route"], row["name"], tuple(row["methods"]))

    old, new = {identity(row) for row in baseline}, {identity(row) for row in current}
    rows = []
    for row in current:
        probes = evidence(row)
        rows.append(
            {key: row[key] for key in ("route", "name", "methods", "family", "handler", "aliases")}
            | {
                "probe_cases": probes,
                "observations": {key: observations[key] for key in probes if key in observations},
                "status": "partial-service-probe" if probes else "unmeasured",
                "remaining": (
                    "HTTP/auth/rejection/nested-history/provider/lock " "and full family budgets remain unaccepted."
                ),
            }
        )
    result = {
        "baseline_patterns": len(baseline),
        "current_patterns": len(current),
        "route_method_alias_parity": old == new,
        "added": [list(key) for key in sorted(new - old)],
        "removed": [list(key) for key in sorted(old - new)],
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "accepted_api_wide": False,
        "justified_exceptions": [],
        "routes": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "baseline_patterns",
                    "current_patterns",
                    "route_method_alias_parity",
                    "status_counts",
                    "accepted_api_wide",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
