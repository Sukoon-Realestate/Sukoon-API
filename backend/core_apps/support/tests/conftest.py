import pytest


@pytest.fixture(autouse=True)
def isolated_private_support_media(settings, tmp_path):
    settings.SUPPORT_PRIVATE_MEDIA_ROOT = str(tmp_path / "private-support")
