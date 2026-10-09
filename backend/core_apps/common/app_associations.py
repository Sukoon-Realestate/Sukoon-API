from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET


def _unconfigured(kind):
    response = JsonResponse(
        {"error": f"{kind} association signing identities are not configured."},
        status=503,
    )
    response["Cache-Control"] = "no-store"
    return response


@require_GET
def android_asset_links(request):
    package_fingerprints = settings.SOKOUN_ANDROID_APP_LINKS
    if not package_fingerprints or any(
        not fingerprints for fingerprints in package_fingerprints.values()
    ):
        return _unconfigured("Android")

    payload = [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": package_name,
                "sha256_cert_fingerprints": fingerprints,
            },
        }
        for package_name, fingerprints in package_fingerprints.items()
    ]
    response = JsonResponse(payload, safe=False)
    response["Cache-Control"] = "public, max-age=3600"
    return response


@require_GET
def apple_app_site_association(request):
    team_id = settings.SOKOUN_APPLE_TEAM_ID
    bundle_ids = settings.SOKOUN_APPLE_BUNDLE_IDS
    if not team_id or not bundle_ids:
        return _unconfigured("Apple")

    payload = {
        "applinks": {
            "apps": [],
            "details": [
                {
                    "appID": f"{team_id}.{bundle_id}",
                    "paths": ["/properties/*"],
                }
                for bundle_id in bundle_ids
            ],
        }
    }
    response = JsonResponse(payload)
    response["Cache-Control"] = "public, max-age=3600"
    return response
