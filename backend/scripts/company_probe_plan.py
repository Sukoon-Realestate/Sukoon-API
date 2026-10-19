#!/usr/bin/env python3
"""Produce a private, reviewable App Platform probe plan. Never applies it."""
import argparse
from copy import deepcopy
import difflib
import json
from pathlib import Path
import yaml
from scripts.digitalocean_runtime import private_file, redact_spec, digest


def build(spec):
    result = deepcopy(spec)
    candidates = [s for s in spec.get("services", []) if s.get("name") == "sukoon-api"]
    if len(candidates) != 1:
        raise ValueError("Exactly one existing sukoon-api service is required")
    api = candidates[0]
    if api.get("github", {}).get("repo") != "Sukoon-Realestate/Sukoon-API" or api.get(
        "dockerfile_path"
    ):
        raise ValueError("Review the API source before preparing background components")
    workers = result.setdefault("workers", [])
    if any(w["name"] in {"sukoun-probe-worker", "sukoun-probe-beat"} for w in workers):
        raise ValueError("Inspect existing probe components instead of replacing them")
    for name, command in {
        "sukoun-probe-worker": "celery -A config worker --loglevel=INFO --concurrency=1 --queues=sokoun-background-probe --hostname=probe@%h",
        "sukoun-probe-beat": "celery -A config beat --loglevel=INFO --scheduler=config.runtime.LeaseScheduler --max-interval=15 --pidfile=/tmp/sokoun-probe-beat.pid",
    }.items():
        env = {v["key"]: deepcopy(v) for v in api.get("envs", [])}
        for value in env.values():
            value["value"] = value.get("value", "").replace("${_self.", "${sukoon-api.")
        for key, value in {
            "DJANGO_SETTINGS_MODULE": "config.settings.background_probe",
            "SOKOUN_RELEASE_SHA": "${_self.COMMIT_HASH}",
            "USE_IN_MEMORY_CHANNEL_LAYER": "False",
        }.items():
            env[key] = {"key": key, "value": value, "scope": "RUN_TIME"}
        workers.append(
            {
                "name": name,
                "github": deepcopy(api["github"]),
                "source_dir": api.get("source_dir", "backend"),
                "environment_slug": "python",
                "build_command": api.get("build_command", ""),
                "run_command": command,
                "envs": list(env.values()),
                "instance_count": 1,
                "instance_size_slug": "apps-s-1vcpu-1gb-fixed",
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    original = yaml.safe_load(private_file(args.source))
    spec = original.get("spec", original)
    plan = build(spec)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    target.touch(mode=0o600, exist_ok=False)
    target.write_text(yaml.safe_dump(plan, sort_keys=False))
    difference = "".join(
        difflib.unified_diff(
            yaml.safe_dump(redact_spec(spec), sort_keys=False).splitlines(True),
            yaml.safe_dump(redact_spec(plan), sort_keys=False).splitlines(True),
            fromfile="existing",
            tofile="probe-only-proposal",
        )
    )
    target.with_suffix(".redacted.diff").write_text(difference)
    print(
        json.dumps(
            {
                "source_digest": digest(spec),
                "plan_digest": digest(plan),
                "workers_added": 2,
                "api_changed": plan["services"] != spec["services"],
                "business_schedules": False,
                "migrations_added": False,
                "applied": False,
            }
        )
    )


if __name__ == "__main__":
    main()
