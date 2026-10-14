from copy import deepcopy
import json

import pytest

from scripts.digitalocean_runtime import (
    ConfigurationError,
    build_runtime_spec,
    digest,
    main,
    private_file,
    redact_spec,
)


@pytest.fixture
def current_spec():
    keys = (
        "SECRET_KEY",
        "RENTAL_PROVIDER_WEBHOOK_SECRET",
        "REDIS_URL",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    )
    return {
        "name": "sukoon-app",
        "region": "fra",
        "domains": [{"domain": "existing.example.test"}],
        "databases": [
            {
                "name": "existing-postgres",
                "cluster_name": "preserved",
                "engine": "PG",
                "production": True,
            }
        ],
        "envs": [
            {"key": key, "value": "EV[1:encrypted-test-value]", "type": "SECRET"}
            for key in keys
        ],
        "services": [
            {
                "name": "api",
                "github": {
                    "repo": "Sukoon-Realestate/Sukoon-API",
                    "branch": "main",
                    "deploy_on_push": True,
                },
                "source_dir": "backend",
                "instance_size_slug": "apps-s-1vcpu-1gb",
                "instance_count": 2,
                "envs": [
                    {
                        "key": "ALLOWED_HOSTS",
                        "value": "existing.example.test",
                        "type": "GENERAL",
                    }
                ],
                "routes": [{"path": "/"}],
            }
        ],
        "workers": [
            {
                "name": "unrelated-worker",
                "github": {"repo": "another/project", "branch": "main"},
                "run_command": "python service.py",
            }
        ],
    }


def test_plan_preserves_resources_secrets_and_original_spec(current_spec):
    untouched = deepcopy(current_spec)
    result, errors, api = build_runtime_spec(current_spec)
    assert errors == []
    assert current_spec == untouched
    for key in ("name", "region", "domains", "databases", "envs"):
        assert result[key] == current_spec[key]
    assert result["workers"][0] == current_spec["workers"][0]
    assert result["services"][0]["routes"] == current_spec["services"][0]["routes"]
    assert result["services"][0]["instance_count"] == 2
    assert api == "api"
    for component in [*result["services"], *result["workers"][1:], *result["jobs"]]:
        assert component["github"] == current_spec["services"][0]["github"]
        assert component["source_dir"] == "backend"
        env = {item["key"]: item["value"] for item in component["envs"]}
        assert env["DJANGO_SETTINGS_MODULE"] == "config.settings.staging_mock"
        assert env["RUNTIME_EVIDENCE_ENABLED"] == "True"
    assert result["jobs"][0]["kind"] == "PRE_DEPLOY"
    assert all(worker["instance_count"] == 1 for worker in result["workers"][1:])


def test_plan_repeatedly_converges_without_extra_workers(current_spec):
    first, _, _ = build_runtime_spec(current_spec)
    second, errors, _ = build_runtime_spec(first)
    assert not errors
    assert first == second


def test_background_environment_retains_api_bindings_and_own_commit(current_spec):
    current_spec["services"][0]["envs"].append(
        {"key": "CALLBACK_URL", "value": "${_self.PUBLIC_URL}"}
    )
    result, _, _ = build_runtime_spec(current_spec)
    env = {item["key"]: item["value"] for item in result["workers"][1]["envs"]}
    assert env["CALLBACK_URL"] == "${api.PUBLIC_URL}"
    assert env["SOKOUN_RELEASE_SHA"] == "${_self.COMMIT_HASH}"


def test_missing_secrets_never_get_placeholders(current_spec):
    current_spec["envs"] = []
    result, errors, _ = build_runtime_spec(current_spec)
    assert "missing_runtime_variable:RENTAL_PROVIDER_WEBHOOK_SECRET" in errors
    assert "missing_runtime_variable:REDIS_URL" in errors
    assert "RENTAL_PROVIDER_WEBHOOK_SECRET" not in {
        item["key"] for item in result["services"][0]["envs"]
    }


def test_existing_scheduler_blocks_apply_without_deleting_it(current_spec):
    current_spec["workers"].append(
        {"name": "old-beat", "run_command": "celery -A config worker --beat"}
    )
    result, errors, _ = build_runtime_spec(current_spec)
    assert "existing_scheduler_requires_review:old-beat" in errors
    assert any(worker["name"] == "old-beat" for worker in result["workers"])


def test_plan_hides_credentials_even_when_saved_as_general(current_spec):
    current_spec["services"][0]["envs"].append(
        {"key": "GOOGLE_CLIENT_SECRET", "value": "do-not-print", "type": "GENERAL"}
    )
    result, _, _ = build_runtime_spec(
        current_spec,
        private_env={"REDIS_URL": "rediss://username:redis-password@host:25061/0"},
    )
    output = json.dumps(redact_spec(result))
    for secret in ("do-not-print", "redis-password", "encrypted-test-value"):
        assert secret not in output
    assert "config.settings.staging_mock" in output


def test_current_spec_commands_and_logging_cannot_leak_credentials(current_spec):
    current_spec["services"][0][
        "run_command"
    ] = "PRIVATE_TOKEN=inline-secret python run.py"
    current_spec["services"][0]["log_destinations"] = [
        {"endpoint": "https://logs.invalid/?key=log-secret"}
    ]
    current_spec["workers"][0]["git"] = {
        "repo_clone_url": "https://user:repo-secret@github.com/example/repo"
    }
    output = json.dumps(redact_spec(current_spec))
    for secret in ("inline-secret", "log-secret", "repo-secret"):
        assert secret not in output


def test_private_files_reject_shared_permissions(tmp_path):
    path = tmp_path / "credential"
    path.write_text("private")
    path.chmod(0o644)
    with pytest.raises(ConfigurationError, match="owner-only"):
        private_file(path)
    path.chmod(0o600)
    assert private_file(path) == "private"


def test_offline_plan_never_connects_or_applies(
    current_spec, tmp_path, monkeypatch, capsys
):
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(current_spec))
    path.chmod(0o600)
    monkeypatch.setattr(
        "scripts.digitalocean_runtime.request",
        lambda *args, **kwargs: pytest.fail("must not connect"),
    )
    assert main(["--spec-file", str(path)]) == 0
    assert "encrypted-test-value" not in capsys.readouterr().out
    with pytest.raises(ConfigurationError, match="planning only"):
        main(["--spec-file", str(path), "--apply"])


def test_changed_current_spec_cannot_apply_previously_reviewed_hash(
    current_spec, tmp_path, monkeypatch
):
    token = tmp_path / "token"
    token.write_text("private-token")
    token.chmod(0o600)
    app = {"id": "test-app", "spec": current_spec}
    candidate, _, _ = build_runtime_spec(current_spec)
    reviewed = digest({"app_id": app["id"], "before": current_spec, "after": candidate})
    current_spec["services"][0]["instance_count"] = 3
    monkeypatch.setattr("scripts.digitalocean_runtime.find_app", lambda *args: app)
    monkeypatch.setattr(
        "scripts.digitalocean_runtime.request",
        lambda *args, **kwargs: pytest.fail("must not apply"),
    )
    with pytest.raises(ConfigurationError, match="reviewed hash"):
        main(["--token-file", str(token), "--apply", "--expect-plan-hash", reviewed])
