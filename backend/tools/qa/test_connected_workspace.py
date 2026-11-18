"""Safety boundaries for the disposable native workspace launcher."""

import subprocess
import sys

import pytest

from tools.qa import run_connected_workspace as workspace


def test_refuses_existing_workspace_without_touching_files(tmp_path, monkeypatch):
    root = tmp_path / "sukoon-sprint4-connected-existing"
    root.mkdir()
    preserved = root / "existing-data"
    preserved.write_text("preserve")
    monkeypatch.setattr(sys, "argv", ["workspace", "--root", str(root)])
    with pytest.raises(SystemExit) as result:
        workspace.main()
    assert result.value.code == 2
    assert preserved.read_text() == "preserve"


def test_refuses_repository_database_workspace(monkeypatch):
    root = workspace.BACKEND / "sukoon-sprint4-connected-unsafe"
    monkeypatch.setattr(sys, "argv", ["workspace", "--root", str(root)])
    with pytest.raises(SystemExit):
        workspace.main()
    assert not root.exists()


def test_invalid_port_creates_no_workspace(tmp_path, monkeypatch):
    root = tmp_path / "sukoon-sprint4-connected-invalid"
    monkeypatch.setattr(sys, "argv", ["workspace", "--root", str(root), "--http-port", "0"])
    with pytest.raises(SystemExit):
        workspace.main()
    assert not root.exists()


def test_fixture_failure_stops_only_the_cluster_this_run_started(tmp_path, monkeypatch):
    root = tmp_path / "sukoon-sprint4-connected-cleanup"
    monkeypatch.setattr(sys, "argv", ["workspace", "--root", str(root)])
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        if "shell" in command:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(subprocess, "run", run)
    with pytest.raises(subprocess.CalledProcessError):
        workspace.main()
    assert commands[-1] == ["pg_ctl", "-D", str(root / "postgres"), "-m", "fast", "-w", "stop"]
    assert root.exists()  # Diagnostic data is retained, never recursively deleted.
    assert all("db.sqlite3" not in argument for command in commands for argument in command)
