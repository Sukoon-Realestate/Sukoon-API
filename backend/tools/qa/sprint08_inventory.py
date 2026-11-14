"""Reconcile original commerce functions, current routes and remaining adapter debt.

Read-only resolver/source inspection; no requests or database operations.
"""

import ast
import importlib
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
    from tools.qa.route_matrix import build, describe

    folder = ROOT / "sprints/evidence/sprint-08"
    before = json.loads((folder / "routes-before.json").read_text())
    global_before = json.loads((folder / "global-contract-before.json").read_text())
    original = json.loads((folder / "original-commerce-functions.json").read_text())
    with override_settings(SUKOON_MVP=True):
        current = {row["route"]: row for row in build()}
    assert len(original) == 73
    assert set(current) == {row["route"] for row in global_before}
    for old in global_before:
        new = current[old["route"]]
        fields = [
            "name",
            "authentication",
            "permissions",
            "parsers",
            "throttles",
            "aliases",
        ]
        if old["style"] != "plain function":
            fields += ["methods", "mvp_allowed"]
        for field in fields:
            assert old[field] == new[field], (old["route"], field)
    originals = []
    for row in original:
        module, name = row["handler"].rsplit(".", 1)
        callback = getattr(importlib.import_module(module), name)
        style, cls, methods, target = describe(callback)
        assert style in {"DRF CBV", "Django CBV"}, row
        originals.append(
            {
                **row,
                "current_class": f"{cls.__module__}.{cls.__name__}",
                "methods": methods,
                "style": style,
            }
        )
    routes = []
    debt = []
    classes = set()
    for old in before:
        new = current[old["route"]]
        assert new["style"] in {"DRF CBV", "Django CBV"}, new
        routes.append(
            {
                "route": new["route"],
                "methods": new["methods"],
                "handler": new["handler"],
                "previous_handler": old["handler"],
                "previous_style": old["style"],
                "style": new["style"],
            }
        )
        if new["handler"] in classes:
            continue
        classes.add(new["handler"])
        name = new["handler"].rsplit(".", 1)[1]
        tree = ast.parse((ROOT / new["file"]).read_text())
        cls = next(
            n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name
        )
        for method in cls.body:
            if not isinstance(method, ast.FunctionDef) or method.name not in {
                "get",
                "post",
                "patch",
                "delete",
                "put",
            }:
                continue
            signals = sorted(
                {
                    n.attr
                    for n in ast.walk(method)
                    if isinstance(n, ast.Attribute)
                    and n.attr
                    in {
                        "save",
                        "create",
                        "update",
                        "delete",
                        "atomic",
                        "bulk_create",
                        "get_or_create",
                    }
                }
            )
            if signals:
                debt.append(
                    {
                        "file": new["file"],
                        "class": name,
                        "method": method.name,
                        "signals": signals,
                    }
                )
    report = {
        "original_decorated_functions": len(originals),
        "originals": originals,
        "scoped_patterns": len(routes),
        "global_patterns": len(current),
        "global_transport_metadata_parity": True,
        "scoped_function_callbacks_remaining": 0,
        "domain_extraction_complete": False,
        "remaining_adapter_write_signals": debt,
        "routes": routes,
    }
    (folder / "route-coverage.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(
        {
            key: value
            for key, value in report.items()
            if key not in {"originals", "routes", "remaining_adapter_write_signals"}
        }
    )
    print("Adapter methods needing domain-write review:", len(debt))


if __name__ == "__main__":
    main()
