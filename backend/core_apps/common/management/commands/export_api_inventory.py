"""Read-only route discovery; consumer disposition still requires review."""
import csv
import inspect
from pathlib import Path
from django.core.management.base import BaseCommand
from django.urls import URLPattern, URLResolver, get_resolver


def rows(patterns, prefix=""):
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            yield from rows(pattern.url_patterns, route)
            continue
        if not isinstance(pattern, URLPattern):
            continue
        callback = pattern.callback
        cls = getattr(callback, "cls", getattr(callback, "view_class", None))
        actions = getattr(callback, "actions", None)
        if actions:
            methods = actions.items()
        elif cls:
            methods = [(name, name) for name in getattr(cls, "http_method_names", [])
                       if hasattr(cls, name) and name not in {"head", "options"}]
        else:
            methods = [("GET", getattr(callback, "__name__", "function"))]
        permissions = ", ".join(item.__name__ for item in getattr(cls, "permission_classes", []))
        for method, action in methods:
            handler = getattr(cls, action, callback) if cls else callback
            try:
                source = inspect.getsourcefile(handler) or ""
                line = inspect.getsourcelines(handler)[1]
            except (OSError, TypeError):
                source, line = "", ""
            yield {"method": method.upper(), "route": route,
                   "name": pattern.name or "", "handler": f"{getattr(cls, '__name__', '')}.{action}",
                   "source": source, "line": line, "permissions": permissions,
                   "disposition": "requires consumer/protocol review"}


class Command(BaseCommand):
    help = "Export method/route/handler/permissions without invoking endpoints."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        entries = list(rows(get_resolver().url_patterns))
        target = Path(options["output"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=entries[0].keys(), delimiter="\t")
            writer.writeheader()
            writer.writerows(entries)
        self.stdout.write(f"Discovered {len(entries)} method/route pairs. No endpoints invoked.")
