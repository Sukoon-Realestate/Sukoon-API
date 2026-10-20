import os
import subprocess
from unittest.mock import patch

import pytest

from core_apps.chat.services.group_limits import ChatUnavailable
from core_apps.chat.services.group_media_process import codec_environment
from core_apps.chat.services.group_media_validation import inspect_voice


def test_relocated_codec_libraries_include_nested_paths_without_global_change(tmp_path):
    binary = tmp_path / "usr/bin/ffmpeg"
    binary.parent.mkdir(parents=True)
    binary.touch()
    nested = tmp_path / "usr/lib/x86_64-linux-gnu"
    for name in ("pulseaudio", "blas", "lapack"):
        (nested / name).mkdir(parents=True)
    with patch("shutil.which", return_value=str(binary)), patch.dict(
        os.environ, {"LD_LIBRARY_PATH": "/existing-libraries"}
    ):
        result = codec_environment("ffmpeg")["LD_LIBRARY_PATH"].split(":")
        assert all(
            str(nested / name) in result for name in ("pulseaudio", "blas", "lapack")
        )
        assert result[-1] == "/existing-libraries"
        assert os.environ["LD_LIBRARY_PATH"] == "/existing-libraries"


def test_missing_codec_uses_default_process_environment():
    with patch("shutil.which", return_value=None):
        assert codec_environment("absent-ffmpeg") is None


def test_missing_loader_dependency_is_unavailable_not_invalid_user_media():
    with patch(
        "core_apps.chat.services.group_media_validation.subprocess.run",
        side_effect=subprocess.CalledProcessError(127, ["ffprobe"]),
    ):
        with pytest.raises(ChatUnavailable):
            inspect_voice("synthetic.m4a")
