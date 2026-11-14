"""Visible lint classification and a no-new-debt gate, never a dead-code verdict.

The strict changed-file lint gate is separate. This ledger intentionally retains
uncertain imports and pytest registration rather than deleting them by count.
"""

import argparse
import ast
from collections import Counter
import configparser
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "sprints/evidence/sprint-11"
PATTERN = re.compile(r"(.+?):(\d+):(\d+): (F\d+) (.+)")


def diagnostics(text):
    rows = []
    for line in text.splitlines():
        match = PATTERN.fullmatch(line)
        if not match:
            raise ValueError(f"Unrecognized lint output: {line}")
        path, number, column, code, message = match.groups()
        if "/tests/" in path:
            category = "pytest registration or test dependency; retained for fixture/caller review"
        elif "/models/" in path or path.endswith(("models.py", "tasks.py", "admin.py", "apps.py")):
            category = "model/task/admin/signal registration or public import; retained"
        elif path.startswith("config/settings/"):
            category = "settings composition; retained"
        else:
            category = "uncertain implementation/import consumer; candidate retained"
        rows.append({"path": path, "line": int(number), "column": int(column),
                     "code": code, "message": message, "classification": category})
    return rows


def identity(row):
    return row["path"], row["code"], row["message"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=EVIDENCE / "lint-classification.json")
    args = parser.parse_args()
    config = configparser.ConfigParser()
    config.read(ROOT / ".flake8")
    ignored = config.get("flake8", "ignore", fallback="") + "," + config.get(
        "flake8", "extend-ignore", fallback=""
    )
    if any("F401".startswith(code.strip()) for code in ignored.split(",") if code.strip()):
        raise ValueError("Global F401 suppression is forbidden; classify consumers explicitly.")
    command = [sys.executable, "-m", "flake8", "--isolated", "--select=F401,F811,F841",
               "--exclude=.venv,migrations,__pycache__", "core_apps", "config", "tools", "scripts"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    if result.returncode not in (0, 1) or result.stderr:
        raise RuntimeError(result.stderr or f"Flake8 failed: {result.returncode}")
    before = diagnostics((EVIDENCE / "logs/lint-before.txt").read_text())
    current = diagnostics(result.stdout)
    old_counts = Counter(identity(row) for row in before)
    current_counts = Counter(identity(row) for row in current)
    additions = current_counts - old_counts
    public_surfaces = json.loads((EVIDENCE / "facade-exports.json").read_text())
    export_failures = []
    for facade in public_surfaces:
        tree = ast.parse((ROOT / facade["path"]).read_text())
        exports = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets))
        if exports != facade["public"] or len(exports) != len(set(exports)):
            export_failures.append(facade["path"])
    report = {
        "scope": "core_apps/config/tools/scripts; migrations and virtualenv excluded",
        "historical_f401": 2476,
        "historical_limit": "Original audit used a different tree/scope; not a one-to-one deletion list.",
        "before_counts": dict(Counter(row["code"] for row in before)),
        "current_counts": dict(Counter(row["code"] for row in current)),
        "classifications": dict(Counter(row["classification"] for row in current)),
        "policy": "No global F401 ignore. All remaining candidates visible; no claim of deadness. This baseline gate does not make full-tree lint green.",
        "new_diagnostics": [{"path": key[0], "code": key[1], "message": key[2], "count": count}
                            for key, count in sorted(additions.items())],
        "facade_export_failures": export_failures,
        "baseline_classified": before,
        "remaining_classified": current,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Before: {report['before_counts']}; remaining: {report['current_counts']}")
    print(f"Remaining classifications: {report['classifications']}")
    print(f"New diagnostics: {sum(additions.values())}; facade surface failures: {len(export_failures)}")
    return int(bool(additions or export_failures))


if __name__ == "__main__":
    raise SystemExit(main())
