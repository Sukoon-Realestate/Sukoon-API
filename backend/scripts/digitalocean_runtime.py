#!/usr/bin/env python3
"""Review/apply a narrow runtime patch to an existing App Platform app.

Default is a read-only redacted plan. No app, database or cache is created.
Secrets are read from private files and never printed or written to evidence.
"""

import argparse
from copy import deepcopy
import difflib
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.digitalocean.com/v2"
REPOSITORY = "Sukoon-Realestate/Sukoon-API"
DOMAIN = "sukoon-app-y4j5r.ondigitalocean.app"
BUILD = "DJANGO_SETTINGS_MODULE=config.settings.build python manage.py collectstatic --noinput"
COMMANDS = {
    "api": "gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8080} --worker-tmp-dir /dev/shm",
    "sukoon-worker": "celery -A config worker --loglevel=INFO --concurrency=2 --hostname=worker@%h",
    "sukoon-beat": "celery -A config beat --loglevel=INFO --scheduler=config.runtime.LeaseScheduler --max-interval=15 --pidfile=/tmp/sokoun-beat.pid",
    "sukoon-migrate": "python manage.py check --deploy --fail-level ERROR && python manage.py migrate --noinput && python manage.py migrate --check",
}
SECRET_INPUT_KEYS = {
    "SECRET_KEY",
    "RENTAL_PROVIDER_WEBHOOK_SECRET",
    "REDIS_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
}
VISIBLE_ENV_KEYS = {
    "DJANGO_SETTINGS_MODULE",
    "DEBUG",
    "USE_IN_MEMORY_CHANNEL_LAYER",
    "SOKOUN_RELEASE_SHA",
    "RUNTIME_EVIDENCE_ENABLED",
    "RUNTIME_EVIDENCE_NAMESPACE",
    "POSTGRES_SSLMODE",
    "ALLOWED_HOSTS",
    "DOMAIN",
}


class ConfigurationError(Exception):
    pass


def private_file(path):
    path = Path(path).expanduser()
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode) or mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ConfigurationError(
            "Credential/spec files must be regular files with owner-only permissions (0600)."
        )
    return path.read_text().strip()


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def environment(items):
    return {item["key"]: deepcopy(item) for item in items}


def set_env(items, name, value, *, secret=False):
    items[name] = {
        "key": name,
        "value": value,
        "scope": "RUN_TIME",
        "type": "SECRET" if secret else "GENERAL",
    }


def redact_spec(value):
    """Only reviewed operational env values and bindable references are shown."""
    if isinstance(value, list):
        return [redact_spec(item) for item in value]
    if not isinstance(value, dict):
        return value
    if "key" in value and "value" in value:
        result = deepcopy(value)
        visible = value["key"] in VISIBLE_ENV_KEYS and value.get("type") != "SECRET"
        binding = re.fullmatch(r"\$\{[A-Za-z0-9_.-]+\}", str(value["value"]))
        result["value"] = value["value"] if visible or binding else "[redacted]"
        return result
    result = {}
    for name, item in value.items():
        sensitive = any(
            word in name.lower() for word in ("password", "token", "secret")
        )
        if name == "log_destinations":
            sensitive = True
        if name in {"run_command", "build_command"} and item not in {
            *COMMANDS.values(),
            BUILD,
        }:
            sensitive = True
        if isinstance(item, str) and re.search(r"://[^/\s]+@", item):
            sensitive = True
        result[name] = "[redacted]" if sensitive else redact_spec(item)
    return result


def build_runtime_spec(spec, *, api_name=None, worker_size=None, private_env=None):
    patched = deepcopy(spec)
    candidates = [
        service
        for service in patched.get("services", [])
        if service.get("github", {}).get("repo", "").lower() == REPOSITORY.lower()
        and (api_name is None or service.get("name") == api_name)
    ]
    if len(candidates) != 1:
        raise ConfigurationError(
            "Select the existing Django GitHub service with --api-component; exactly one must match the Sukoon repository."
        )
    api = candidates[0]
    if api.get("dockerfile_path"):
        raise ConfigurationError(
            "Existing API uses a Dockerfile; review its build context before changing runtime components."
        )
    name = api["name"]
    if name in set(COMMANDS) - {"api"}:
        raise ConfigurationError(
            "The API component name conflicts with a reserved runtime component name."
        )
    app_env = environment(patched.get("envs", []))
    api_env = environment(api.get("envs", []))
    runtime_env = {**app_env, **api_env}
    for key, value in (private_env or {}).items():
        if (
            key not in SECRET_INPUT_KEYS
            or not isinstance(value, str)
            or not value.strip()
        ):
            raise ConfigurationError(
                "Private environment input contains an unsupported key or empty/non-string value."
            )
        set_env(api_env, key, value, secret=True)
    for key, value in {
        "DJANGO_SETTINGS_MODULE": "config.settings.staging_mock",
        "DEBUG": "False",
        "USE_IN_MEMORY_CHANNEL_LAYER": "False",
        "SOKOUN_RELEASE_SHA": "${_self.COMMIT_HASH}",
        "RUNTIME_EVIDENCE_ENABLED": "True",
        "RUNTIME_EVIDENCE_NAMESPACE": patched["name"],
        "POSTGRES_SSLMODE": "require",
    }.items():
        set_env(api_env, key, value)
    # Existing brokers may have explicit component values. Normalize only the
    # absent settings to the exact configured Redis value, never a localhost fallback.
    runtime_env = {**runtime_env, **api_env}
    if runtime_env.get("REDIS_URL", {}).get("value"):
        for key in ("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"):
            if not runtime_env.get(key, {}).get("value"):
                api_env[key] = {
                    **runtime_env["REDIS_URL"],
                    "key": key,
                    "scope": "RUN_TIME",
                }
    runtime_env = {**app_env, **api_env}
    required = (
        "SECRET_KEY",
        "RENTAL_PROVIDER_WEBHOOK_SECRET",
        "REDIS_URL",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "ALLOWED_HOSTS",
    )
    missing = [key for key in required if not runtime_env.get(key, {}).get("value")]
    errors = [f"missing_runtime_variable:{key}" for key in missing]
    errors.extend(
        f"runtime_scope_required:{key}"
        for key in required
        if runtime_env.get(key, {}).get("scope") == "BUILD_TIME"
    )
    if runtime_env.get("ALLOWED_HOSTS", {}).get("value", "") == "*":
        errors.append("explicit_allowed_hosts_required")
    for key in ("REDIS_URL", "CELERY_BROKER_URL", "CELERY_RESULT_BACKEND"):
        value = runtime_env.get(key, {}).get("value", "")
        if any(
            local in value.lower() for local in ("localhost", "127.0.0.1", "0.0.0.0")
        ):
            errors.append(f"remote_connection_required:{key}")
    api["github"]["branch"] = "main"
    api["github"]["deploy_on_push"] = True
    api.update(
        source_dir="backend",
        environment_slug="python",
        build_command=BUILD,
        run_command=COMMANDS["api"],
        envs=list(api_env.values()),
        health_check={
            "http_path": "/health/",
            "initial_delay_seconds": 15,
            "period_seconds": 15,
        },
    )
    # Preserve API resources, routes, domains, app/env metadata and databases.
    # Background components inherit the same source and Django environment.
    common = {
        "github": deepcopy(api["github"]),
        "source_dir": api["source_dir"],
        "environment_slug": "python",
        "build_command": BUILD,
        "instance_count": 1,
    }
    size = worker_size or api.get("instance_size_slug")
    if not size:
        errors.append("worker_instance_size_required")
    else:
        common["instance_size_slug"] = size
    background_env = deepcopy(api_env)
    for item in background_env.values():
        if item["key"] != "SOKOUN_RELEASE_SHA":
            item["value"] = item.get("value", "").replace("${_self.", "${" + name + ".")
    for collection, component_names in (
        ("workers", ("sukoon-worker", "sukoon-beat")),
        ("jobs", ("sukoon-migrate",)),
    ):
        existing = patched.setdefault(collection, [])
        for component_name in component_names:
            matches = [item for item in existing if item.get("name") == component_name]
            if len(matches) > 1:
                raise ConfigurationError(
                    "Duplicate runtime component names in current app spec."
                )
            if (
                matches
                and matches[0].get("github", {}).get("repo", "").lower()
                != REPOSITORY.lower()
            ):
                raise ConfigurationError(
                    "A runtime component name is already used by another source."
                )
            component = matches[0] if matches else {"name": component_name}
            # Remove alternative sources/autoscaling before fixing one instance.
            for field in (
                "git",
                "gitlab",
                "image",
                "bitbucket",
                "dockerfile_path",
                "autoscaling",
            ):
                component.pop(field, None)
            component.update(deepcopy(common))
            component.update(
                run_command=COMMANDS[component_name],
                envs=list(deepcopy(background_env).values()),
            )
            if collection == "jobs":
                component["kind"] = "PRE_DEPLOY"
                # Job bindable commit hashes are not documented. Its source is
                # verified from the deployment API alongside the three processes.
                component["envs"] = [
                    item
                    for item in component["envs"]
                    if item["key"] != "SOKOUN_RELEASE_SHA"
                ]
            if not matches:
                existing.append(component)
    # Existing additional beat commands must be explicitly reconciled, not silently removed.
    duplicate_beat = [
        item["name"]
        for item in patched.get("workers", [])
        if item["name"] != "sukoon-beat"
        and re.search(
            r"\bcelery\b.*\bbeat\b|\bworker\b.*(?:\s-B\b|--beat\b)",
            item.get("run_command", ""),
        )
    ]
    if duplicate_beat:
        errors.append("existing_scheduler_requires_review:" + ",".join(duplicate_beat))
    return patched, errors, name


def request(token, method, path, body=None):
    payload = None if body is None else json.dumps(body).encode()
    req = Request(
        API + path,
        data=payload,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=30) as response:
            return json.load(response)
    except HTTPError as error:
        # Vendor errors may echo submitted specs, so never print their body.
        raise ConfigurationError(
            f"DigitalOcean {method} request failed with HTTP {error.code}."
        ) from None
    except URLError:
        raise ConfigurationError(
            "DigitalOcean request failed before a response was received; reconcile remote state before retrying an apply."
        ) from None


def find_app(token, app_id, domain):
    if app_id:
        if not re.fullmatch(r"[a-fA-F0-9-]{36}", app_id):
            raise ConfigurationError("--app-id must be a UUID.")
        return request(token, "GET", f"/apps/{app_id}")["app"]
    matches = []
    for page in range(1, 21):
        result = request(token, "GET", f"/apps?per_page=200&page={page}")
        for app in result.get("apps", []):
            urls = [app.get("default_ingress", ""), app.get("live_url", "")]
            if any(url.removeprefix("https://").rstrip("/") == domain for url in urls):
                matches.append(app)
        if not result.get("links", {}).get("pages", {}).get("next"):
            break
    if len(matches) != 1:
        raise ConfigurationError(
            "Could not uniquely locate the existing app by domain; specify its --app-id."
        )
    return request(token, "GET", f"/apps/{matches[0]['id']}")["app"]


def deployment_status(app):
    deployment = app.get("active_deployment") or {}
    components = []
    for kind in ("services", "workers", "jobs"):
        for item in deployment.get(kind, []):
            components.append(
                {
                    "kind": kind,
                    "name": item.get("name"),
                    "source_commit_hash": item.get("source_commit_hash"),
                }
            )
    return {
        "app_id": app.get("id"),
        "app_name": app.get("spec", {}).get("name"),
        "active_deployment_id": deployment.get("id"),
        "phase": deployment.get("phase"),
        "updated_at": deployment.get("updated_at"),
        "components": components,
        "in_progress_deployment_id": (app.get("in_progress_deployment") or {}).get(
            "id"
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--token-file", help="Owner-only file containing the DigitalOcean API token."
    )
    parser.add_argument("--app-id")
    parser.add_argument("--app-domain", default=DOMAIN)
    parser.add_argument("--api-component")
    parser.add_argument(
        "--worker-size",
        help="Explicit approved App Platform instance_size_slug; default preserves API size.",
    )
    parser.add_argument(
        "--private-env-file",
        help="Owner-only JSON object for missing secrets; never saved in the repo.",
    )
    parser.add_argument(
        "--spec-file", help="Owner-only existing spec JSON, for an offline plan only."
    )
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--expect-plan-hash",
        help="Exact hash from the reviewed plan; required to apply.",
    )
    options = parser.parse_args(argv)
    if options.spec_file and (options.apply or options.status):
        raise ConfigurationError("Offline specs support planning only.")
    token = private_file(options.token_file) if options.token_file else None
    if options.spec_file:
        spec = json.loads(private_file(options.spec_file))
        app = {"spec": spec.get("spec", spec)}
    elif token:
        app = find_app(token, options.app_id, options.app_domain)
    else:
        raise ConfigurationError(
            "Supply --token-file for the existing app or --spec-file for an offline plan."
        )
    if options.status:
        print(json.dumps(deployment_status(app), indent=2, sort_keys=True))
        return 0
    private_env = (
        json.loads(private_file(options.private_env_file))
        if options.private_env_file
        else {}
    )
    if not isinstance(private_env, dict):
        raise ConfigurationError("Private environment file must contain a JSON object.")
    candidate, errors, api_name = build_runtime_spec(
        app["spec"],
        api_name=options.api_component,
        worker_size=options.worker_size,
        private_env=private_env,
    )
    plan_hash = digest(
        {"app_id": app.get("id"), "before": app["spec"], "after": candidate}
    )
    before = json.dumps(redact_spec(app["spec"]), indent=2, sort_keys=True).splitlines()
    after = json.dumps(redact_spec(candidate), indent=2, sort_keys=True).splitlines()
    print(
        json.dumps(
            {
                "mode": "apply" if options.apply else "plan",
                "app_id": app.get("id"),
                "api_component": api_name,
                "plan_hash": plan_hash,
                "blocking_requirements": errors,
                "runtime_components": [
                    api_name,
                    "sukoon-worker",
                    "sukoon-beat",
                    "sukoon-migrate",
                ],
                "creates_databases_or_caches": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    print(
        "\n".join(
            difflib.unified_diff(
                before,
                after,
                fromfile="current-redacted",
                tofile="planned-redacted",
                lineterm="",
            )
        )
    )
    if options.apply:
        if errors:
            raise ConfigurationError(
                "Runtime prerequisites are incomplete; nothing was applied."
            )
        if options.expect_plan_hash != plan_hash:
            raise ConfigurationError(
                "The current plan differs from the reviewed hash; nothing was applied."
            )
        result = request(token, "PUT", f"/apps/{app['id']}", {"spec": candidate})
        print(
            json.dumps(
                {"applied": True, "status": deployment_status(result["app"])}, indent=2
            )
        )
    return 1 if errors else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ConfigurationError, OSError, ValueError) as error:
        message = (
            str(error)
            if isinstance(error, ConfigurationError)
            else type(error).__name__
        )
        print(f"Runtime setup failed: {message}", file=sys.stderr)
        sys.exit(2)
