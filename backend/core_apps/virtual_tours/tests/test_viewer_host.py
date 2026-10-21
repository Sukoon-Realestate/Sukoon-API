import pytest


@pytest.fixture
def viewer_root(settings, tmp_path):
    root = tmp_path / "viewer"
    root.mkdir()
    (root / "assets").mkdir()
    (root / "index.html").write_text(
        '<script src="/tours/assets/app-hash.js"></script>'
    )
    (root / "assets" / "app-hash.js").write_text("window.sokounTour={};")
    settings.VIRTUAL_TOUR_VIEWER_ROOT = root
    return root


def test_viewer_has_same_origin_review_and_strict_security_headers(client, viewer_root):
    response = client.get("/tours/")
    assert response.status_code == 200
    assert b"/tours/assets/app-hash.js" in b"".join(response.streaming_content)
    assert response["X-Frame-Options"] == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in response["Content-Security-Policy"]
    assert "connect-src 'self'" in response["Content-Security-Policy"]
    assert response["Referrer-Policy"] == "no-referrer"
    assert response["Cache-Control"] == "no-cache"
    asset = client.get("/tours/assets/app-hash.js")
    assert asset.status_code == 200
    assert b"window.sokounTour" in b"".join(asset.streaming_content)
    assert "immutable" in asset["Cache-Control"]


@pytest.mark.parametrize(
    "path",
    [
        "/tours/assets/secret.json",
        "/tours/assets/.env",
        "/tours/assets/missing.js",
        "/tours/assets/%2e%2e%2fsecret.js",
        "/tours/assets/link.js",
    ],
)
def test_viewer_does_not_expose_other_files(client, viewer_root, path):
    secret = viewer_root.parent / "secret.js"
    secret.write_text("private")
    (viewer_root / "assets" / "link.js").symlink_to(secret)
    assert client.get(path).status_code == 404


def test_viewer_missing_bundle_and_writes_fail_closed(client, settings, tmp_path):
    settings.VIRTUAL_TOUR_VIEWER_ROOT = tmp_path / "missing"
    assert client.get("/tours/").status_code == 404
    assert client.post("/tours/").status_code == 405
