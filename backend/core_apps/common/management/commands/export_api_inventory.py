"""Read-only route discovery; consumer disposition still requires review."""

import csv
import inspect
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.admin import AdminSite, ModelAdmin
from django.contrib.auth.views import LogoutView
from django.urls import URLPattern, URLResolver, get_resolver


def source_handler(handler):
    target = inspect.unwrap(handler)
    # DRF api_view constructs a class handler closing over the actual function.
    if inspect.isfunction(target):
        enclosed = inspect.getclosurevars(target).nonlocals.get("func")
        if inspect.isfunction(enclosed):
            return inspect.unwrap(enclosed)
    return target


def function_methods(callback):
    """Include real admin form submissions, without invoking any view."""
    target = source_handler(callback)
    owner = (
        getattr(target, "__self__", None)
        or getattr(callback, "model_admin", None)
        or getattr(callback, "admin_site", None)
    )
    name = getattr(target, "__name__", "function")
    if isinstance(owner, (AdminSite, ModelAdmin)):
        if name == "logout":
            return [
                (verb, name)
                for verb in LogoutView.http_method_names
                if verb not in {"head", "options"}
            ]
        if name in {
            "login",
            "password_change",
            "user_change_password",
            "add_view",
            "change_view",
            "changelist_view",
            "delete_view",
        }:
            return [("GET", name), ("POST", name)]
    # require_http_methods stores its explicit allowlist in a wrapper closure.
    wrapper = callback
    while inspect.isfunction(wrapper):
        allowed = inspect.getclosurevars(wrapper).nonlocals.get("request_method_list")
        if allowed:
            return [
                (verb, name)
                for verb in allowed
                if verb.lower() not in {"head", "options"}
            ]
        wrapper = getattr(wrapper, "__wrapped__", None)
    return [("GET", name)]


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
            methods = [
                (name, name)
                for name in getattr(cls, "http_method_names", [])
                if hasattr(cls, name) and name not in {"head", "options"}
            ]
        else:
            methods = function_methods(callback)
        permissions = ", ".join(
            item.__name__ for item in getattr(cls, "permission_classes", [])
        )
        for method, action in methods:
            handler = getattr(cls, action, callback) if cls else callback
            try:
                target = source_handler(handler)
                source = inspect.getsourcefile(target) or ""
                line = inspect.getsourcelines(target)[1]
            except (OSError, TypeError):
                source, line = "", ""
            yield {
                "method": method.upper(),
                "route": route,
                "name": pattern.name or "",
                "handler": f"{getattr(cls, '__name__', '')}.{action}",
                "source": source,
                "line": line,
                "permissions": permissions,
                "disposition": "requires consumer/protocol review",
            }


def websocket_rows():
    from core_apps.chat.routing import websocket_urlpatterns as chat
    from core_apps.common.routing import websocket_urlpatterns as common

    for pattern in [*common, *chat]:
        consumer = pattern.callback.consumer_class
        yield {
            "method": "WEBSOCKET",
            "route": str(pattern.pattern),
            "name": pattern.name or "",
            "handler": consumer.__name__,
            "source": inspect.getsourcefile(consumer) or "",
            "line": inspect.getsourcelines(consumer)[1],
            "permissions": "config.asgi middleware and consumer authorization",
            "disposition": "requires consumer/protocol review",
        }


class Command(BaseCommand):
    help = "Export method/route/handler/permissions without invoking endpoints."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        entries = [*rows(get_resolver().url_patterns), *websocket_rows()]
        target = Path(options["output"])
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", newline="") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=entries[0].keys(), delimiter="\t"
            )
            writer.writeheader()
            writer.writerows(entries)
        self.stdout.write(
            f"Discovered {len(entries)} method/route pairs. No endpoints invoked."
        )
