"""Sprint 10 route parity and shared-service import boundaries; no database I/O."""

import ast
import inspect
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
    from django.conf import settings
    from django.urls import get_resolver
    from tools.qa.route_matrix import build, describe, walk

    folder = ROOT / "sprints/evidence/sprint-10"
    before = json.loads((folder / "routes-before.json").read_text())["routes"]
    current = build()
    by_route = {row["route"]: row for row in current}
    assert set(by_route) == {row["route"] for row in before}
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
    for previous in before:
        for key in fields:
            assert previous[key] == by_route[previous["route"]][key], (
                previous["route"],
                key,
            )
    scoped, framework, plain = [], [], []
    for route, pattern in walk(get_resolver().url_patterns):
        style, cls, methods, target = describe(pattern.callback)
        module = getattr(target, "__module__", "")
        if module.startswith(("core_apps.", "config.")):
            row = dict(
                route=route,
                name=pattern.name,
                style=style,
                methods=methods,
                handler=f"{module}.{target.__qualname__}",
            )
            if style not in {"DRF CBV", "DRF viewset", "Django CBV"}:
                plain.append(row)
            if module.startswith(
                ("core_apps.admin_api", "core_apps.common")
            ) or route.startswith(settings.ADMIN_URL):
                scoped.append(row)
        elif route.startswith(settings.ADMIN_URL):
            framework.append(route)
    assert not plain, plain
    view_imports = []
    # Scan every common production module and all admin service modules.
    files = list((ROOT / "core_apps/common").glob("*.py")) + list(
        (ROOT / "core_apps/admin_api/services").rglob("*.py")
    )
    files.append(ROOT / "core_apps/virtual_tours/admin_commands.py")
    for path in files:
        if path.name.startswith("test"):
            continue
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else []
                )
            )
            if any(
                "views" in name.split(".") or name.endswith("_views") for name in names
            ):
                # Importing framework classes is a transport adapter dependency,
                # not a domain service importing a project HTTP module.
                if any(name.startswith("core_apps.") for name in names):
                    view_imports.append(f"{path.relative_to(ROOT)}:{node.lineno}")
    assert not view_imports, view_imports
    report = dict(
        api_patterns=len(current),
        global_transport_metadata_parity=True,
        project_function_callbacks_remaining=plain,
        scoped_patterns=len(scoped),
        scoped_routes=scoped,
        framework_admin_callbacks=len(framework),
        shared_project_view_imports=view_imports,
        limits="Resolver/source evidence; positive authorization and effects require behavioral tests. "
        "Framework-owned admin callbacks remain framework-owned, including subclass ModelAdmin hooks.",
    )
    (folder / "route-coverage.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "scoped_routes"},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
