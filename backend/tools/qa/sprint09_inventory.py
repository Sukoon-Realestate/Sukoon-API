"""Reconcile Sprint 09 aliases, HTTP policies and function-removal evidence.

No requests, database operations, environment secrets or provider calls.
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
    from tools.qa.route_matrix import build
    from django.test import override_settings

    folder = ROOT / "sprints/evidence/sprint-09"
    before = json.loads((folder / "global-contract-before.json").read_text())
    scoped = json.loads((folder / "routes-before.json").read_text())
    with override_settings(SUKOON_MVP=True):
        rows = build()
    current = {row["route"]: row for row in rows}
    assert set(current) == {row["route"] for row in before}
    fields = [
        "name",
        "methods",
        "authentication",
        "permissions",
        "parsers",
        "throttles",
        "aliases",
        "mvp_allowed",
    ]
    for old in before:
        new = current[old["route"]]
        for field in fields:
            assert old[field] == new[field], (
                old["route"],
                field,
                old[field],
                new[field],
            )
    functions, scoped_rows = set(), []
    for old in scoped:
        row = current[old["route"]]
        assert row["style"] in {"DRF CBV", "Django CBV"}, row
        if old["style"] not in {"DRF CBV", "Django CBV"}:
            functions.add(old["handler"])
        scoped_rows.append(
            {
                "route": row["route"],
                "methods": row["methods"],
                "previous_handler": old["handler"],
                "handler": row["handler"],
                "style": row["style"],
            }
        )
    # A generated WrappedAPIView around a decorated function is not acceptance.
    decorated = []
    for path in (ROOT / "core_apps/chat/views").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef) and any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Name)
                and dec.func.id == "api_view"
                for dec in node.decorator_list
            ):
                decorated.append(f"{path.relative_to(ROOT)}:{node.name}")
    assert not decorated, decorated
    report = {
        "global_patterns": len(rows),
        "scoped_patterns": len(scoped_rows),
        "converted_original_functions": sorted(functions),
        "scoped_function_callbacks_remaining": 0,
        "global_transport_metadata_parity": True,
        "routes": scoped_rows,
    }
    (folder / "route-coverage.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "routes"}, indent=2
        )
    )


if __name__ == "__main__":
    main()
