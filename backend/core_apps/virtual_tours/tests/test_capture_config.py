import io
import json
import urllib.error
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def configured_capture(settings, tmp_path):
    settings.BASE_DIR = tmp_path
    settings.PROPERTY_CAPTURE_ENABLED = True
    settings.GEMINI_API_KEY = "fixture-provider-key-never-log"
    settings.GEMINI_COACH_MODEL = "fixture-live-model"
    settings.CAPTURE_MAX_SESSION_BYTES = 1024
    settings.CAPTURE_RETENTION_DAYS = 30
    settings.COACH_DAILY_SESSION_LIMIT = 10


@pytest.mark.django_db
@pytest.mark.parametrize("provider_state", ["unreachable", "no_live", "live"])
def test_strict_preflight_requires_successful_requested_provider_probe(
    configured_capture, provider_state
):
    output = io.StringIO()
    response = io.BytesIO(
        json.dumps(
            {
                "supportedGenerationMethods": (
                    ["bidiGenerateContent"]
                    if provider_state == "live"
                    else ["generateContent"]
                )
            }
        ).encode()
    )
    response.status = 200
    with patch(
        "core_apps.virtual_tours.management.commands.check_property_capture_config.urllib.request.urlopen",
        return_value=response,
        side_effect=(
            urllib.error.URLError("unreachable")
            if provider_state == "unreachable"
            else None
        ),
    ):
        if provider_state == "live":
            call_command(
                "check_property_capture_config",
                strict=True,
                probe_gemini=True,
                stdout=output,
            )
        else:
            with pytest.raises(CommandError):
                call_command(
                    "check_property_capture_config",
                    strict=True,
                    probe_gemini=True,
                    stdout=output,
                )
    result = json.loads(output.getvalue())
    assert result["localConfigurationReady"] == (provider_state == "live")
    assert result["releaseReady"] is False
    assert "fixture-provider-key-never-log" not in output.getvalue()


@pytest.mark.django_db
def test_strict_preflight_does_not_report_disabled_capture_as_ready(
    configured_capture, settings
):
    settings.PROPERTY_CAPTURE_ENABLED = False
    output = io.StringIO()
    with pytest.raises(CommandError):
        call_command("check_property_capture_config", strict=True, stdout=output)
    assert json.loads(output.getvalue())["localConfigurationReady"] is False
