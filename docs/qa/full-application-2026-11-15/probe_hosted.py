"""Bounded, read-only hosted checks. No login, account or business mutations."""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path


def request(origin, path, expected, headers=None, method="GET"):
    started = time.monotonic()
    req = urllib.request.Request(origin + path, method=method, headers={
        "User-Agent": "Sukoon-Release-QA/1.0", **(headers or {}),
    })
    try:
        response = urllib.request.urlopen(req, timeout=25)
    except urllib.error.HTTPError as error:
        response = error
    except Exception as error:
        return dict(path=path, method=method, outcome="ERROR", error=type(error).__name__)
    with response:
        body = response.read(2_000_000)
        selected = {k.lower(): v for k, v in response.headers.items() if k.lower() in {
            "content-type", "strict-transport-security", "content-security-policy",
            "x-frame-options", "x-content-type-options", "access-control-allow-origin",
            "access-control-allow-credentials", "cache-control", "referrer-policy",
        }}
        return dict(path=path, method=method, status=response.status,
                    expected=expected, outcome="PASS" if response.status in expected else "FAIL",
                    seconds=round(time.monotonic()-started, 3), headers=selected,
                    bytes=len(body), traceback_exposed=b"Traceback (most recent call last)" in body,
                    final_url=response.url)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "evidence/hosted.json")
    args = parser.parse_args()
    api = "https://api.sukoon.rent"
    rows = []
    for path in ["/health/", "/api/v1/homepage/?page=1&rental_offers_version=1",
                 "/api/v1/properties/types/", "/api/v1/properties/cities/",
                 "/api/v1/properties/governorates/", "/api/v1/pages/about-us/",
                 "/api/v1/pages/privacy-policy/", "/api/v1/pages/terms/",
                 "/.well-known/assetlinks.json", "/.well-known/apple-app-site-association"]:
        rows.append(request(api, path, [200]))
    private = ["admin/session/", "admin/dashboard/", "admin/users/", "admin/kyc/",
               "admin/properties/", "admin/settings/", "admin/system/health/",
               "admin/system/logs/", "admin/analytics/", "admin/support/",
               "auth/security/sessions/", "auth/account-closure/", "properties/saved/",
               "properties/owned/", "properties/owner/dashboard/", "notifications/",
               "notifications/settings/", "support/", "features/v1/housing-groups/"]
    for path in private:
        rows.append(request(api, "/api/v1/" + path, [401, 403, 404]))
    for query in ["page=0", "page=-1", "page=abc", "page=999999", "page_size=-1",
                  "min_price=abc", "min_price=10000&max_price=100", "ordering=invalid"]:
        rows.append(request(api, "/api/v1/homepage/?" + query, [200, 400, 404]))
    rows.append(request(api, "/api/v1/admin/users/", [401, 403], {"Authorization": "Bearer invalid-qa-token"}))
    rows.append(request(api, "/api/v1/admin/users/", [200, 401, 403], {
        "Origin": "https://qa-untrusted.example", "Access-Control-Request-Method": "GET",
    }, "OPTIONS"))
    for path in ["/.env", "/.git/config", "/api/v1/qa-nonexistent-route/"]:
        rows.append(request(api, path, [403, 404]))
    web = "https://www.sukoon.rent"
    for path in ["/ar", "/en", "/ar/privacy", "/en/privacy", "/ar/terms", "/en/terms",
                 "/admin/login", "/admin/", "/admin/users", "/admin/properties",
                 "/admin/financials", "/admin/roles", "/admin/support", "/admin/system/health"]:
        rows.append(request(web, path, [200]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2) + "\n")
    for row in rows:
        print(row["outcome"], row.get("status", row.get("error")), row["path"])
    # HTTP 200 private page shells do not establish access to protected data.
    raise SystemExit(any(row["outcome"] != "PASS" for row in rows))


if __name__ == "__main__":
    main()
