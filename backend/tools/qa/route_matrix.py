"""Generate the maintained route/method/alias matrix (Sprint 00).

Usage (from backend/):
    DJANGO_SETTINGS_MODULE=config.settings.test python tools/qa/route_matrix.py \
        --json sprints/evidence/sprint-00/route-matrix.json --markdown sprints/ROUTE_MATRIX.md

Everything here is resolved at runtime from Django's URL resolver plus static source signals.
No request is made and no database is opened. Columns marked "signal" are handler-local
static text matches: they show where to look, not proof that a check, lock or receipt
exists (or is missing) deeper in a service call.
"""

import argparse
import inspect
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTTP = ("get", "post", "put", "patch", "delete")
SAMPLE = {"uuid": "00000000-0000-4000-8000-000000000000", "int": "1", "slug": "sample", "str": "sample",
          "path": "sample", "drf_format_suffix": ".json"}

# Route family -> owning review area and the sprint that converts it. Families are the
# first meaningful segments under api/v1/ (see family_of). Areas follow SOURCE_INVENTORY.md.
AREA_SPRINT = {1: "05", 2: "06", 3: "07", 4: "08", 5: "09", 6: "10"}
AREA_NAME = {1: "Identity/profiles", 2: "Properties/visits/tours", 3: "Rentals/housing/planning",
             4: "Commerce/providers/advertising", 5: "Communication/support", 6: "Admin/shared/config"}

SIGNALS = {
    "lock": re.compile(r"select_for_update|transaction\.atomic|@atomic|\block=True"),
    "receipt": re.compile(r"operation_id|idempotenc|Idempotency-Key|receipt|replay", re.I),
    "authority": re.compile(r"authorize\(|require_planning|require_capability|has_object_permission|"
                            r"check_object_permissions|role_routes|require_new_business|get_object_or_404\([^)]*user"),
    "headers": re.compile(r"Cache-Control|no.store|X-Sukoon|Content-Disposition|nosniff|ETag|Retry-After"),
    "upload": re.compile(r"request\.FILES|FileField|ImageField|MultiPartParser|FileUploadParser|base64"),
}


def area_index():
    """file path -> area from SOURCE_INVENTORY.md (the audit's ownership table)."""
    index = {}
    row = re.compile(r"^\| \[(core_apps/[^\]]+|config/[^\]]+)\]\([^)]*\) \| [^|]* \| (\d) \|")
    for line in (ROOT / "sprints" / "SOURCE_INVENTORY.md").read_text(encoding="utf-8").splitlines():
        match = row.match(line)
        if match:
            index[match.group(1)] = int(match.group(2))
    return index


def walk(patterns, prefix=""):
    from django.urls import URLPattern, URLResolver

    for entry in patterns:
        route = prefix + str(entry.pattern)
        if isinstance(entry, URLResolver):
            yield from walk(entry.url_patterns, route)
        elif isinstance(entry, URLPattern):
            yield route, entry


def concrete_path(route):
    # Regex named groups first, so their <name> is not mistaken for a path converter.
    path = re.sub(r"\(\?P<format>[^)]*\)", "json", route)
    path = re.sub(r"\(\?P<\w+>[^)]*\)", "sample", path)
    path = re.sub(r"<(?:(\w+):)?\w+>", lambda m: SAMPLE.get(m.group(1) or "str", "sample"), path)
    path = path.replace("^", "").replace("$", "").replace("\\.", ".").replace("\\Z", "").replace("/?", "/")
    path = re.sub(r"\.\(\?P?<?format>?[^)]*\)", "", path)
    return "/" + path.lstrip("/")


def describe(callback):
    """Return (style, view_class, methods, function-or-class used for source signals)."""
    cls = getattr(callback, "cls", None) or getattr(callback, "view_class", None)
    actions = getattr(callback, "actions", None)
    if cls is None:
        return "plain function", None, ["(adapter-defined)"], inspect.unwrap(callback)
    # @api_view renames the generated class after the function; its qualname keeps the origin.
    is_wrapped = "WrappedAPIView" in cls.__qualname__
    if actions:
        methods = sorted(m.upper() for m in actions)
    else:
        methods = [m.upper() for m in HTTP if hasattr(cls, m)]
    if is_wrapped:
        handler = next((getattr(cls, m) for m in HTTP if hasattr(cls, m)), None)
        original = callback
        # @api_view keeps the decorated function as the handler's closure target
        for cell in getattr(handler, "__closure__", None) or ():
            if inspect.isfunction(cell.cell_contents):
                original = inspect.unwrap(cell.cell_contents)
        return "decorated FBV", cls, methods, original
    from rest_framework.views import APIView

    style = ("DRF viewset" if actions else "DRF CBV") if issubclass(cls, APIView) else "Django CBV"
    return style, cls, methods, cls


def names(classes):
    return ", ".join(sorted({c.__name__ for c in classes or ()})) or "—"


def source_of(target):
    try:
        file = inspect.getsourcefile(target)
        lines, start = inspect.getsourcelines(target)
        return file, start, "".join(lines)
    except (TypeError, OSError):
        return None, None, ""


def serializer_hint(cls, source):
    found = set()
    if cls is not None and getattr(cls, "serializer_class", None):
        found.add(cls.serializer_class.__name__)
    found.update(re.findall(r"\b([A-Z]\w*(?:Serializer|Command|Definition|Input))\(", source))
    return ", ".join(sorted(found)) or "—"


def family_of(route):
    parts = [p for p in re.sub(r"<[^>]+>", "{}", route).split("/") if p]
    if not parts or parts[0] != "api":
        return parts[0] if parts else "/"
    rest = parts[2:] if len(parts) > 1 and parts[1].startswith("v") else parts[1:]
    if rest and rest[0] in {"features", "admin"} and len(rest) > 2 and rest[1].startswith("v"):
        rest = [rest[0]] + rest[2:]
    head = [p for p in rest[:2] if p != "{}"]
    return "api/" + "/".join(head[:2] if rest and rest[0] in {"features", "admin", "auth", "chat"} else head[:1])


def test_index():
    texts = []
    for path in (ROOT / "core_apps").rglob("test*.py"):
        if "/migrations/" not in str(path):
            texts.append((str(path.relative_to(ROOT)), path.read_text(encoding="utf-8", errors="ignore")))
    return texts


def tests_for(name, route, tests):
    literal = re.sub(r"<[^>]+>.*", "", route)
    hits = []
    for file, text in tests:
        if (name and (f'"{name}"' in text or f"'{name}'" in text)) or (len(literal) > 12 and literal in text):
            hits.append(file)
    return hits


def build():
    from django.urls import get_resolver
    from core_apps.common.mvp_scope import allows_path

    areas, tests = area_index(), test_index()
    rows, callbacks = [], defaultdict(list)
    for route, pattern in walk(get_resolver().url_patterns):
        if not (route.startswith("api/") or route.startswith("^api/")):
            continue
        style, cls, methods, target = describe(pattern.callback)
        file, line, source = source_of(target)
        rel = os.path.relpath(file, ROOT) if file else "?"
        if rel.startswith("..") or "site-packages" in rel:
            style = "framework-generated " + style
        path = concrete_path(route)
        identity = f"{getattr(target, '__module__', '?')}.{getattr(target, '__qualname__', '?')}"
        callbacks[identity].append(route)
        rows.append({
            "route": route, "name": pattern.name or "", "methods": methods, "style": style,
            "handler": identity, "file": rel, "line": line,
            "area": areas.get(rel), "family": family_of(route),
            "authentication": names(getattr(cls, "authentication_classes", None)),
            "permissions": names(getattr(cls, "permission_classes", None)),
            "throttles": names(getattr(cls, "throttle_classes", None)),
            "parsers": names(getattr(cls, "parser_classes", None)),
            "request_schema": serializer_hint(cls, source),
            "mvp_allowed": {m: allows_path(path, pattern.name, m) for m in methods if m.isalpha()},
            "signals": sorted(k for k, rx in SIGNALS.items() if rx.search(source)),
            "tests": tests_for(pattern.name, route, tests),
        })
    for row in rows:
        row["aliases"] = [r for r in callbacks[row["handler"]] if r != row["route"]]
    return rows


def family_table(rows):
    fam = defaultdict(list)
    for row in rows:
        fam[row["family"]].append(row)
    out = []
    for family, items in sorted(fam.items()):
        area_counts = Counter(r["area"] for r in items if r["area"])
        area = area_counts.most_common(1)[0][0] if area_counts else None
        deferred = sum(1 for r in items if r["mvp_allowed"] and not any(r["mvp_allowed"].values()))
        out.append({
            "family": family, "routes": len(items), "area": area,
            "owner": (f"Area {area} — {AREA_NAME[area]}" if area
                      else "Framework-generated (router root); owned with Area 1"),
            "sprint": AREA_SPRINT.get(area, "—"),
            "aliases": sum(1 for r in items if r["aliases"]),
            "methods": ", ".join(sorted({m for r in items for m in r["methods"]})),
            "styles": dict(Counter(r["style"] for r in items)),
            "auth": sorted({r["authentication"] for r in items}),
            "permissions": sorted({r["permissions"] for r in items}),
            "deferred": deferred,
            "lock": sum("lock" in r["signals"] for r in items),
            "receipt": sum("receipt" in r["signals"] for r in items),
            "authority": sum("authority" in r["signals"] for r in items),
            "headers": sum("headers" in r["signals"] for r in items),
            "upload": sum("upload" in r["signals"] for r in items),
            "untested": sum(1 for r in items if not r["tests"]),
        })
    return out


def markdown(rows, families):
    styles = Counter(r["style"] for r in rows)
    lines = [
        "# Route family compatibility matrix",
        "",
        "Generated by `tools/qa/route_matrix.py` from the runtime URL resolver; regenerate on every route change",
        "instead of editing by hand. Per-route detail (methods, auth/permission/throttle/parser classes, request",
        "schema hints, MVP availability per method, aliases, signals and referencing test files) is in",
        "[evidence/sprint-00/route-matrix.json](evidence/sprint-00/route-matrix.json).",
        "",
        f"**{len(rows)} API patterns**, {sum(1 for r in rows if r['aliases'])} sharing a handler with another pattern "
        "(aliases/format variants). Styles: " + ", ".join(f"{v} {k}" for k, v in styles.most_common()) + ".",
        "",
        "How to read the columns:",
        "",
        "- **Owner** is the owning review area from SOURCE_INVENTORY.md; **Sprint** is the CBV sprint for that area.",
        "  Named individuals must still be assigned per area by the backend lead (open Sprint 00 item).",
        "- **MVP-deferred** counts routes for which `mvp_scope.allows_path` refuses every declared method with",
        "  the production default `SUKOON_MVP=true`. Header/workspace-based deferral is not counted here.",
        "- **Lock / Receipt / Authority / Headers / Upload** count handlers whose own source matches a static signal.",
        "  Services called by the handler are not followed, so 0 is a prompt to trace, not a finding.",
        "- **Untested** counts routes whose URL name or literal path never appears in a test module. Tests that",
        "  call services directly are not counted, so this is an upper bound on HTTP-contract gaps.",
        "- Contract fixtures: before a family's migration batch starts, its owner adds request/response/status/header",
        "  fixtures for every row here, including aliases, and records them in the family checklist.",
        "",
        "| Family | Routes | Owner | Sprint | Aliases | Methods | Styles | Authentication | Permissions |"
        " MVP-deferred |"
        " Lock | Receipt | Authority | Headers | Upload | Untested |",
        "|---|---:|---|---|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for f in families:
        style = "; ".join(f"{k} {v}" for k, v in sorted(f["styles"].items()))
        auth = "<br>".join(f["auth"])
        perms = "<br>".join(f["permissions"])
        lines.append(
            f"| `{f['family']}` | {f['routes']} | {f['owner']} | {f['sprint']} | {f['aliases']}"
            f" | {f['methods']} | {style}"
            f" | {auth} | {perms} | {f['deferred']} | {f['lock']} | {f['receipt']} | {f['authority']} | {f['headers']}"
            f" | {f['upload']} | {f['untested']} |"
        )
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json")
    parser.add_argument("--markdown")
    args = parser.parse_args()
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
    import django

    django.setup()
    rows = build()
    families = family_table(rows)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        # One route/family per line keeps regeneration diffs reviewable.
        line = lambda item: json.dumps(item, default=str, sort_keys=True)  # noqa: E731
        Path(args.json).write_text(
            '{"routes": [\n' + ",\n".join(map(line, rows)) + '\n],\n"families": [\n'
            + ",\n".join(map(line, families)) + "\n]}\n",
            encoding="utf-8",
        )
    if args.markdown:
        Path(args.markdown).write_text(markdown(rows, families), encoding="utf-8")
    print(f"routes={len(rows)} families={len(families)} "
          f"unowned={sum(1 for f in families if not f['area'])} styles={dict(Counter(r['style'] for r in rows))}")


if __name__ == "__main__":
    main()
