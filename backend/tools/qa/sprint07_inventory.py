"""Reconcile Sprint 07 route contracts and list remaining architecture debt.

Read-only Django inspection: no requests, database writes or deployment actions.
"""

import ast
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
    from django.test import override_settings
    from tools.qa.route_matrix import build

    folder = ROOT / "sprints/evidence/sprint-07"
    before = json.loads((folder / "routes-before.json").read_text())
    global_before = json.loads((folder / "global-contract-before.json").read_text())
    with override_settings(SUKOON_MVP=True):
        current = {row["route"]: row for row in build()}
    contract_fields = (
        "name",
        "methods",
        "authentication",
        "permissions",
        "parsers",
        "throttles",
        "mvp_allowed",
        "aliases",
    )
    assert set(current) == {row["route"] for row in global_before}
    for old in global_before:
        new = current[old["route"]]
        assert all(old[field] == new[field] for field in contract_fields), old["route"]
    routes = []
    files = set()
    for old in before:
        new = current[old["route"]]
        assert new["style"] not in {"plain function", "decorated FBV"}, old["route"]
        files.add(new["file"])
        routes.append(
            {
                "route": new["route"],
                "methods": new["methods"],
                "previous_handler": old["handler"],
                "handler": new["handler"],
                "previous_style": old["style"],
                "style": new["style"],
                "transport_metadata_unchanged": True,
            }
        )
    # State-write signals flag review debt, not proof of a bug or a complete
    # state-machine inventory. Existing authored CBVs are included in this scan.
    remaining = []
    for name in sorted(files):
        source = (ROOT / name).read_text()
        for cls in ast.parse(source).body:
            if not isinstance(cls, ast.ClassDef):
                continue
            for method in cls.body:
                if not isinstance(method, ast.FunctionDef) or method.name not in {
                    "get",
                    "post",
                    "patch",
                    "put",
                    "delete",
                }:
                    continue
                signals = sorted(
                    {
                        node.attr
                        for node in ast.walk(method)
                        if isinstance(node, ast.Attribute)
                        and node.attr
                        in {
                            "save",
                            "create",
                            "update",
                            "delete",
                            "atomic",
                            "bulk_create",
                        }
                    }
                )
                if signals:
                    remaining.append(
                        {
                            "file": name,
                            "class": cls.name,
                            "method": method.name,
                            "signals": signals,
                            "review_status": "domain-extraction-pending",
                        }
                    )
    report = {
        "patterns": len(routes),
        "converted_patterns": sum(
            row["previous_style"] == "decorated FBV" for row in routes
        ),
        "function_callbacks_remaining": 0,
        "global_patterns": len(current),
        "global_transport_parity": True,
        "domain_extraction_complete": False,
        "state_write_signals_remaining": remaining,
        "routes": routes,
    }
    (folder / "route-coverage.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        {
            key: value
            for key, value in report.items()
            if key not in {"routes", "state_write_signals_remaining"}
        }
    )
    print("Adapter methods with remaining domain-write signals:", len(remaining))


if __name__ == "__main__":
    main()
