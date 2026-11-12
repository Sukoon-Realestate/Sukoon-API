"""Account for every property/tour alias and fail on transport metadata drift."""

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

    folder = ROOT / "sprints/evidence/sprint-06"
    before = json.loads((folder / "routes-before.json").read_text())
    from django.test import override_settings

    with override_settings(SUKOON_MVP=True):
        current = {row["route"]: row for row in build()}
    rows = []
    fields = [
        "name",
        "methods",
        "authentication",
        "permissions",
        "parsers",
        "throttles",
        "mvp_allowed",
    ]
    for old in before:
        new = current[old["route"]]
        assert new["style"] not in {"plain function", "decorated FBV"}, old["route"]
        assert all(new[field] == old[field] for field in fields), old["route"]
        rows.append(
            {
                **new,
                "previous_handler": old["handler"],
                "previous_style": old["style"],
                "transport_metadata_unchanged": True,
            }
        )
    from django.urls import resolve
    from core_apps.virtual_tours.viewer_views import TourViewerView

    non_api = []
    for path in ["/tours/", "/tours/assets/synthetic.js"]:
        callback = resolve(path).func
        assert callback.view_class is TourViewerView
        assert callback.view_class.http_method_names == ["get", "head"]
        non_api.append(
            {
                "path": path,
                "handler": "core_apps.virtual_tours.viewer_views.TourViewerView",
                "methods": ["GET", "HEAD"],
            }
        )

    report = {
        "patterns": len(rows),
        "converted_patterns": sum(
            row["previous_style"] == "decorated FBV" for row in rows
        ),
        "function_callbacks_remaining": 0,
        "routes": rows,
        "html_viewer_aliases": non_api,
    }
    (folder / "route-coverage.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print({key: value for key, value in report.items() if key != "routes"})


if __name__ == "__main__":
    main()
