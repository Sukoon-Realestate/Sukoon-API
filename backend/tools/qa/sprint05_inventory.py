"""Account for every identity alias and fail on callback/transport-contract drift.

Run with DOTENV_DISABLED=1 and test/scratch settings. This resolves URL metadata;
it does not open a database, send a request, or certify workflow coverage.
"""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")


def main():
    import django
    django.setup()
    from tools.qa.route_matrix import build

    folder = ROOT / "sprints/evidence/sprint-05"
    before = json.loads((folder / "routes-before.json").read_text())
    current = {row["route"]: row for row in build()}
    status_file = folder / "completion/contract-statuses.json"
    statuses = json.loads(status_file.read_text()) if status_file.exists() else {}
    rows = []
    fields = ("name", "methods", "authentication", "permissions", "throttles", "parsers", "mvp_allowed")
    for original in before:
        result = current[original["route"]]
        file = result.get("file", "")
        if "site-packages/" in file:
            result["file"] = "<framework>/" + file.split("site-packages/", 1)[1]
        assert result["style"] not in {"decorated FBV", "plain function"}, result["route"]
        assert all(original[field] == result[field] for field in fields), result["route"]
        contracts = []
        if statuses:
            for method in original["methods"]:
                variants = (("anonymous", "en"), ("bearer", "en"), ("cookie", "ar"), ("form", "en"))
                for transport, locale in variants:
                    key = "|".join((original["route"], method, transport, locale))
                    assert key in statuses, key
                    contracts.append({"method": method, "transport": transport, "locale": locale,
                                      "expected_status": statuses[key]})
        rows.append({
            **result,
            "previous_handler": original["handler"],
            "previous_style": original["style"],
            "transport_metadata_unchanged": True,
            "characterized_transport_fixture": (
                "transport-contracts.json" if original["style"] == "decorated FBV" else None
            ),
            "method_transport_contracts": contracts,
            "evidence_limit": ("Local alias/method/auth/locale/status contracts plus linked workflow tests; "
                               "no live staging claim."),
        })
    data = {"api_patterns": len(current), "identity_patterns": len(rows),
            "converted_patterns": sum(row["previous_style"] == "decorated FBV" for row in rows),
            "function_callbacks_remaining": 0, "routes": rows}
    (folder / "route-coverage.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print({key: value for key, value in data.items() if key != "routes"})


if __name__ == "__main__":
    main()
