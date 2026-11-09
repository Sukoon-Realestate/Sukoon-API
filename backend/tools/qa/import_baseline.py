"""Import every project module once under Django test settings (Sprint 00 import baseline).

Usage: DJANGO_SETTINGS_MODULE=config.settings.test python tools/qa/import_baseline.py [--json PATH]

Imports have side effects (signal/admin registration), so this runs against test
settings only and never opens a database connection on purpose. Settings modules
other than the active one are skipped: several require deployment environment
variables by design and are not importable in isolation.
"""

import argparse
import importlib
import json
import os
import pkgutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ("core_apps", "config")


def module_names():
    for package in PACKAGES:
        for info in pkgutil.walk_packages([str(ROOT / package)], prefix=f"{package}."):
            name = info.name
            if name.startswith("config.settings."):
                continue
            yield name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    import django

    django.setup()
    ok, failures = 0, []
    for name in sorted(set(module_names())):
        try:
            importlib.import_module(name)
            ok += 1
        except Exception as exc:  # recorded, never hidden
            failures.append({"module": name, "error": f"{type(exc).__name__}: {exc}",
                             "trace": traceback.format_exc(limit=3)})
    report = {"settings": os.environ["DJANGO_SETTINGS_MODULE"], "imported": ok, "failed": len(failures),
              "failures": failures}
    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"imported={ok} failed={len(failures)}")
    for row in failures:
        print(f"  {row['module']}: {row['error']}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
