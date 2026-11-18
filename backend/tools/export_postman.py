"""Export resolved backend routes without making requests or opening a database.

Run with the backend virtualenv; --backend-root can point at a main worktree.
"""

import argparse
import inspect
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs/postman",
    )
    args = parser.parse_args()
    root = args.backend_root.resolve()
    sys.path.insert(0, str(root))
    os.environ["DOTENV_DISABLED"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.build"
    import django

    django.setup()
    from django.urls import get_resolver, resolve
    from rest_framework import serializers
    from rest_framework.permissions import AllowAny
    from rest_framework.test import APIRequestFactory
    from rest_framework.request import Request
    from django.contrib.auth.models import AnonymousUser
    from drf_yasg import openapi
    from drf_yasg.generators import OpenAPISchemaGenerator
    from drf_yasg.inspectors import SwaggerAutoSchema
    from core_apps.common.mvp_scope import allows_path
    from tools.qa.route_matrix import walk, describe, concrete_path, family_of

    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    branch = subprocess.check_output(
        ["git", "-C", str(root), "branch", "--show-current"], text=True
    ).strip()
    variables = {
        "base_url": "http://127.0.0.1:8000",
        "access_token": "",
        "refresh_token": "",
        "email": "",
        "password": "",
        "otp": "",
        "idempotency_key": "",
        "etag": "",
    }
    notes = {}
    folders = defaultdict(lambda: defaultdict(list))
    counts = defaultdict(int)
    covered = set()
    components = openapi.ReferenceResolver(openapi.SCHEMA_DEFINITIONS, force_init=True)
    generator = OpenAPISchemaGenerator(
        info=openapi.Info(title="Sukoon", default_version="v1")
    )

    def sample(field, name):
        if name in {"email", "password", "otp", "refresh"}:
            return "{{" + ("refresh_token" if name == "refresh" else name) + "}}"
        if isinstance(field, serializers.BaseSerializer) and hasattr(field, "fields"):
            return {
                k: sample(v, k)
                for k, v in field.fields.items()
                if not v.read_only and v.required
            }
        if isinstance(field, serializers.ListSerializer):
            return [sample(field.child, name)]
        if isinstance(field, serializers.ListField):
            return [sample(field.child, name)]
        if isinstance(field, serializers.BooleanField):
            return True
        if isinstance(field, serializers.IntegerField):
            return max(1, field.min_value or 0)
        if isinstance(field, (serializers.FloatField, serializers.DecimalField)):
            return 1
        if isinstance(field, serializers.ChoiceField) and field.choices:
            return next(iter(field.choices))
        if isinstance(field, serializers.UUIDField):
            return "00000000-0000-4000-8000-000000000001"
        if isinstance(field, serializers.DateTimeField):
            return "2027-01-01T12:00:00Z"
        if isinstance(field, serializers.DateField):
            return "1995-01-01"
        if isinstance(field, serializers.TimeField):
            return "12:00:00"
        if isinstance(field, serializers.DictField):
            return {}
        if name == "re_password":
            return "{{password}}"
        return "example"

    def schema_sample(schema, depth=0):
        if depth > 6:
            return None
        schema = openapi.resolve_ref(schema, components)
        if schema.get("enum"):
            return schema["enum"][0]
        if schema.get("type") == "object" or "properties" in schema:
            return {
                k: schema_sample(v, depth + 1)
                for k, v in schema.get("properties", {}).items()
                if not v.get("readOnly") and k in schema.get("required", [])
            }
        if schema.get("type") == "array":
            return [schema_sample(schema.get("items", {}), depth + 1)]
        return {"integer": 1, "number": 1, "boolean": True}.get(
            schema.get("type"), "example"
        )

    for route, pattern in walk(get_resolver().url_patterns):
        if not route.startswith(("api/", "^api/", "health/")):
            continue
        # Canonical routes cover identical DRF .json/.api format variants.
        if "format>" in route or ":format>" in route:
            counts["format_variants_omitted"] += 1
            continue
        callback = pattern.callback
        _, cls, methods, _ = describe(callback)
        concrete = concrete_path(route)
        # URL resolution order matters: later shadowed actions are not reachable.
        match = resolve(concrete)
        if match.func != callback:
            counts["shadowed_patterns_omitted"] += 1
            continue
        family = family_of(route)
        scope = re.sub(r"[^a-zA-Z0-9]+", "_", family.removeprefix("api/")).strip("_")

        def variable(name, kind="str"):
            key = scope + "_" + name
            variables.setdefault(
                key,
                {"uuid": "00000000-0000-4000-8000-000000000001", "int": "1"}.get(
                    kind, "example"
                ),
            )
            return "{{" + key + "}}"

        url_path = re.sub(r"\(\?P<(\w+)>[^)]*\)", lambda m: variable(m[1]), route)
        url_path = re.sub(
            r"<(?:(\w+):)?(\w+)>", lambda m: variable(m[2], m[1] or "str"), url_path
        )
        url_path = (
            url_path.replace("^", "")
            .replace("$", "")
            .replace("\\Z", "")
            .replace("\\.", ".")
        )
        url_path = "/" + url_path.lstrip("/")
        for method in methods:
            if method.lower() not in getattr(
                cls, "http_method_names", []
            ) or method in {"HEAD", "OPTIONS"}:
                continue
            identity = (url_path, method)
            if identity in covered:
                continue
            covered.add(identity)
            active = allows_path(concrete, pattern.name, method)
            section = (
                "MVP available" if active else "Deferred — requires SUKOON_MVP=false"
            )
            description = [
                f"Source: `{route}`",
                f"Handler: `{cls.__module__}.{cls.__name__}`",
                f'Permissions: {", ".join(p.__name__ for p in getattr(cls, "permission_classes", [])) or "handler-defined"}.',
                "MVP route policy: "
                + (
                    "available; other permissions and feature switches still apply."
                    if active
                    else "blocked with mvp_feature_deferred under the default MVP configuration."
                ),
            ]
            request = {
                "method": method,
                "header": [{"key": "Accept", "value": "application/json"}],
                "url": {
                    "raw": "{{base_url}}" + url_path,
                    "host": ["{{base_url}}"],
                    "path": url_path.lstrip("/").split("/"),
                },
                "description": "",
            }
            if not getattr(cls, "authentication_classes", None) or AllowAny in getattr(
                cls, "permission_classes", []
            ):
                request["auth"] = {"type": "noauth"}
            operation = {}
            if hasattr(callback, "cls"):
                view = generator.create_view(callback, method, None)
            else:
                view = cls(**getattr(callback, "view_initkwargs", {}))
                view.swagger_fake_view = True
            view.request = Request(APIRequestFactory().generic(method, concrete))
            view.request.user = AnonymousUser()
            view.kwargs = match.kwargs
            try:
                operation = SwaggerAutoSchema(
                    view, concrete, method, components, None, {}
                ).get_operation([scope, method.lower()])
            except Exception as error:
                counts["schema_inspection_failures"] += 1
                description.append(
                    f"Automatic schema unavailable ({type(error).__name__}); consult the handler for command fields."
                )
            query = []
            for parameter in operation.get("parameters", []):
                if parameter.get("in") == "query":
                    query.append(
                        {
                            "key": parameter["name"],
                            "value": str(parameter.get("default", "")),
                            "disabled": not parameter.get("required", False),
                            "description": parameter.get("description", ""),
                        }
                    )
            if query:
                request["url"]["query"] = query
                enabled = [
                    p["key"] + "=" + p["value"] for p in query if not p["disabled"]
                ]
                if enabled:
                    request["url"]["raw"] += "?" + "&".join(enabled)
            if method in {"POST", "PUT", "PATCH"}:
                serializer = None
                try:
                    serializer = (
                        view.get_serializer()
                        if hasattr(view, "get_serializer")
                        else None
                    )
                except Exception:
                    pass
                if serializer is None:
                    handler = getattr(cls, method.lower(), None)
                    try:
                        source = inspect.getsource(handler)
                        candidates = re.findall(
                            r"\b(\w+Serializer)\(\s*data\s*=\s*request.data", source
                        )
                        if len(set(candidates)) == 1:
                            serializer = handler.__globals__[candidates[0]]()
                    except (TypeError, OSError, KeyError):
                        pass
                payload = None
                if serializer is not None:
                    try:
                        payload = sample(serializer, "")
                        description.append(
                            f"Body template: required writable fields from `{type(serializer).__name__}`. Replace example values; validation and state requirements still apply."
                        )
                        counts["serializer_templates"] += 1
                    except Exception:
                        payload = None
                form = [
                    p
                    for p in operation.get("parameters", [])
                    if p.get("in") == "formData"
                ]
                if not form and serializer is not None:
                    try:
                        if any(
                            isinstance(f, serializers.FileField)
                            for f in serializer.fields.values()
                        ):
                            form = [
                                {
                                    "name": k,
                                    "type": (
                                        "file"
                                        if isinstance(f, serializers.FileField)
                                        else "string"
                                    ),
                                    "required": f.required,
                                }
                                for k, f in serializer.fields.items()
                                if not f.read_only
                            ]
                    except (AttributeError, TypeError):
                        pass
                if form:
                    request["body"] = {
                        "mode": "formdata",
                        "formdata": [
                            dict(
                                key=p["name"],
                                type="file" if p.get("type") == "file" else "text",
                                **(
                                    {"src": []}
                                    if p.get("type") == "file"
                                    else {
                                        "value": str((payload or {}).get(p["name"], ""))
                                    }
                                ),
                                disabled=not p.get("required", False),
                            )
                            for p in form
                        ],
                    }
                else:
                    if payload is None:
                        body = next(
                            (
                                p
                                for p in operation.get("parameters", [])
                                if p.get("in") == "body"
                            ),
                            None,
                        )
                        if body:
                            payload = schema_sample(body["schema"])
                    if payload is None:
                        payload = {}
                        description.append(
                            "Body template is incomplete: this endpoint has no inspectable request serializer. Fill command fields from the handler/service before sending."
                        )
                        counts["incomplete_templates"] += 1
                    request["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(payload, indent=2),
                        "options": {"raw": {"language": "json"}},
                    }
                    request["header"].append(
                        {"key": "Content-Type", "value": "application/json"}
                    )
            raw_parsers = [
                p
                for p in getattr(cls, "parser_classes", [])
                if p.__name__ == "RawPartParser"
            ]
            if raw_parsers and method in {"POST", "PUT", "PATCH"}:
                request["body"] = {"mode": "file", "file": {"src": ""}}
                request["header"] = [
                    h for h in request["header"] if h["key"] != "Content-Type"
                ]
                request["header"].append(
                    {"key": "Content-Type", "value": "application/octet-stream"}
                )
                description.append(
                    "Select the binary part file and supply the upload grant/checksum headers required by this handler."
                )
            if method in {"POST", "PUT", "PATCH", "DELETE"}:
                request["header"].extend(
                    [
                        {
                            "key": "Idempotency-Key",
                            "value": "{{idempotency_key}}",
                            "disabled": True,
                            "description": "Enable if required by this command. Use a new key per logical operation; retain it only for an identical retry.",
                        },
                        {
                            "key": "If-Match",
                            "value": "{{etag}}",
                            "disabled": True,
                            "description": "Enable for commands requiring an ETag; copy the current resource ETag.",
                        },
                    ]
                )
            request["description"] = "\n\n".join(description)
            item = {
                "name": method + " " + (pattern.name or url_path),
                "request": request,
                "response": [],
            }
            auth_path = concrete.removeprefix("/api/v1/auth/")
            if concrete.startswith("/api/v1/auth/") and auth_path in {
                "login/",
                "refresh/",
                "token/refresh/",
                "verify/",
                "verify-email/",
                "verify-otp/",
            }:
                item["event"] = [
                    {
                        "listen": "test",
                        "script": {
                            "type": "text/javascript",
                            "exec": [
                                "if (pm.response.code >= 200 && pm.response.code < 300) {",
                                "  let body = {}; try { body = pm.response.json(); } catch (_) {}",
                                "  const data = body.data || body;",
                                '  for (const name of ["access", "refresh"]) {',
                                "    const token = data[name] || body[name] || (pm.response.cookies.get(name) && pm.response.cookies.get(name).value);",
                                '    if (token) pm.collectionVariables.set(name + "_token", token);',
                                "  }",
                                "}",
                            ],
                        },
                    }
                ]
            folders[section][family].append(item)
            counts["requests"] += 1
            counts["mvp_available" if active else "deferred"] += 1

    collection = {
        "info": {
            "name": "Sukoon Backend — main",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "description": f"Generated from {branch} at {commit}. All reachable API methods plus health; canonical DRF routes only. Native Django admin, viewer/static pages and WebSockets are excluded. Body examples are templates, not an end-to-end scenario. See README.md.",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        },
        "variable": [
            {"key": k, "value": v, "type": "string"} for k, v in variables.items()
        ],
        "item": [
            {
                "name": section,
                "item": [
                    {"name": family, "item": items}
                    for family, items in sorted(groups.items())
                ],
            }
            for section, groups in sorted(folders.items(), reverse=True)
        ],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "Sukoon_Backend_main.postman_collection.json").write_text(
        json.dumps(collection, indent=2) + "\n"
    )
    environment = {
        "name": "Sukoon Backend — local",
        "_postman_variable_scope": "environment",
        "values": [
            {
                "key": "base_url",
                "value": variables["base_url"],
                "enabled": True,
                "type": "default",
            }
        ],
    }
    (args.output / "Sukoon_Backend_local.postman_environment.json").write_text(
        json.dumps(environment, indent=2) + "\n"
    )
    notes.update(source_branch=branch, source_commit=commit, **counts)
    (args.output / "coverage.json").write_text(json.dumps(notes, indent=2) + "\n")
    print(json.dumps(notes, indent=2))


if __name__ == "__main__":
    main()
