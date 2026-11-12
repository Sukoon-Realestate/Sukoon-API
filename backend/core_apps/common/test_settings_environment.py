"""Scratch tooling can prevent environment-file loading with the pinned dotenv SDK."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("module", ["base", "production"])
@pytest.mark.parametrize("disabled", [None, "0", "false", "1", "true", "yes"])
def test_settings_environment_file_opt_out(module, disabled):
    script = """
import importlib, json, os
from unittest.mock import patch
from django.conf import settings
settings.configure(INSTALLED_APPS=[])
seen = []
original = os.path.isfile
with patch('os.path.isfile', side_effect=lambda p: str(p).endswith('/.envs/.env.local') or original(p)):
    with patch('dotenv.load_dotenv', side_effect=lambda p: seen.append(str(p))):
        importlib.import_module('config.settings.' + os.environ['QA_SETTINGS_MODULE'])
print(json.dumps({'loads': len(seen)}))
"""
    environment = {**os.environ, "QA_SETTINGS_MODULE": module}
    environment.pop("DOTENV_DISABLED", None)
    environment.pop("DJANGO_SETTINGS_MODULE", None)
    if disabled is not None:
        environment["DOTENV_DISABLED"] = disabled
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[2],
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    expected = 0 if disabled in {"1", "true", "yes"} else 1 if module == "base" else 2
    assert json.loads(result.stdout)["loads"] == expected
