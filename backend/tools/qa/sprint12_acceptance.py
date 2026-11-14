"""Refresh local release evidence without granting deployment acceptance.

Run with DOTENV_DISABLED=1 and explicitly isolated Django settings. Inventory
does not issue requests or open a database. JUnit omissions remain visible.
"""

import argparse
import ast
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
TRANSPORT_FIELDS = (
    "name", "methods", "authentication", "permissions", "parsers",
    "throttles", "aliases", "mvp_allowed",
)


def junit_result(path):
    """Count individual outcomes; xfail is never a passing acceptance case."""
    cases = list(ET.parse(path).getroot().iter("testcase"))
    counts = Counter()
    omissions = []
    for case in cases:
        outcome = "passed"
        detail = next((case.find(tag) for tag in ("failure", "error", "skipped")
                       if case.find(tag) is not None), None)
        if detail is not None:
            outcome = detail.tag
            if outcome == "skipped" and detail.get("type") == "pytest.xfail":
                outcome = "expected_failure"
            omissions.append({
                "test": f"{case.get('classname')}::{case.get('name')}",
                "outcome": outcome,
                "reason": detail.get("message") or detail.text or "",
            })
        counts[outcome] += 1
    return {
        "cases": len(cases), "counts": dict(counts), "omissions": omissions,
        "regression_passed": bool(cases) and not (counts["failure"] or counts["error"]),
        "all_cases_passed": bool(cases) and counts["passed"] == len(cases),
    }


def transport_differences(before, after):
    old = {row["route"]: row for row in before}
    new = {row["route"]: row for row in after}
    return {
        "removed": sorted(old.keys() - new.keys()),
        "added": sorted(new.keys() - old.keys()),
        "changed": [
            {"route": route, "field": key, "before": old[route][key], "after": new[route][key]}
            for route in sorted(old.keys() & new.keys())
            for key in TRANSPORT_FIELDS if old[route][key] != new[route][key]
        ],
    }


def project_view_imports(source, module, is_package=False):
    """Resolve relative imports as well as `from package import views`."""
    result = []
    package = module if is_package else module.rpartition(".")[0]
    for node in ast.walk(ast.parse(source)):
        names = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                base = importlib.util.resolve_name("." * node.level + base, package)
            names = [base, *(f"{base}.{alias.name}" for alias in node.names)]
        for name in names:
            if name.startswith("core_apps.") and any(
                part in {"views", "views_parts"} or part.endswith(("_views", "_views_parts"))
                for part in name.split(".")
            ):
                result.append({"line": node.lineno, "import": name})
    return result


def inventory():
    import django

    django.setup()
    from django.urls import get_resolver
    from tools.qa.route_matrix import build, describe, family_table, walk

    rows = build()
    baseline_path = ROOT / "sprints/evidence/sprint-11/routes-after.json"
    if not baseline_path.exists():
        baseline_path = ROOT / "sprints/evidence/sprint-10/routes-before.json"
    baseline = json.loads(baseline_path.read_text())
    before = baseline["routes"] if isinstance(baseline, dict) else baseline
    callbacks, framework = [], []
    for route, pattern in walk(get_resolver().url_patterns):
        style, _, methods, target = describe(pattern.callback)
        module = getattr(target, "__module__", "")
        item = {"route": route, "style": style, "methods": methods,
                "handler": f"{module}.{target.__qualname__}"}
        if module.startswith(("core_apps.", "config.")):
            callbacks.append(item)
        else:
            framework.append(item)
    imports, scanned = [], []
    for path in sorted((ROOT / "core_apps").rglob("*.py")):
        rel = path.relative_to(ROOT)
        if "services" not in rel.parts or "tests" in rel.parts or path.name.startswith("test"):
            continue
        scanned.append(str(rel))
        module = ".".join(rel.with_suffix("").parts)
        if path.name == "__init__.py":
            module = module.removesuffix(".__init__")
        imports.extend({"file": str(rel), **item} for item in project_view_imports(
            path.read_text(encoding="utf-8-sig"), module, path.name == "__init__.py",
        ))
    return {
        "baseline": str(baseline_path.relative_to(ROOT)),
        "api_patterns": len(rows), "routes": rows, "families": family_table(rows),
        "transport_differences": transport_differences(before, rows),
        "project_callbacks": callbacks,
        "project_function_callbacks": [row for row in callbacks if row["style"] not in
                                       {"DRF CBV", "DRF viewset", "Django CBV"}],
        "framework_callback_count": len(framework),
        "service_modules_scanned": scanned, "service_view_imports": imports,
        "limits": "Resolver metadata and static imports only. Not positive role/workspace, "
                  "envelope/header/locale coverage or proof of cohesive use-case extraction. "
                  "Dynamic imports and domain modules outside services/ need manual review.",
    }


def source_manifest():
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT,
    ).decode().split("\0")
    files = {}
    for name in paths:
        path = ROOT / name
        if path.is_file() and path.suffix == ".py" and not name.startswith("sprints/"):
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--junit", type=Path, action="append", default=[])
    args = parser.parse_args()
    if os.environ.get("DOTENV_DISABLED") != "1" or not os.environ.get("DJANGO_SETTINGS_MODULE"):
        parser.error("Set DOTENV_DISABLED=1 and explicit isolated DJANGO_SETTINGS_MODULE")
    sys.path.insert(0, str(ROOT))
    report = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree": subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True),
        "settings": os.environ["DJANGO_SETTINGS_MODULE"],
        "inventory": inventory(),
        "test_runs": {str(path): junit_result(path) for path in args.junit},
        "python_source_sha256": source_manifest(),
        "release_accepted": False,
        "release_acceptance_reason": "Local evidence cannot approve providers, devices, deployed "
                                     "security, API-wide budgets or independent human review; see README.md.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    inv = report["inventory"]
    failed = bool(inv["project_function_callbacks"] or inv["service_view_imports"] or
                  any(inv["transport_differences"].values()) or
                  any(not run["regression_passed"] for run in report["test_runs"].values()))
    print(json.dumps({"output": str(args.output), "local_checks_passed": not failed,
                      "release_accepted": False}))
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
