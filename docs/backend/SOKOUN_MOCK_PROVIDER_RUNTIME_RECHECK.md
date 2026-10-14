# Current blocker: mock rental provider is still unavailable on the API

Verified on **2026-10-14, 08:24–08:31 UTC / 11:24–11:31 Africa/Cairo**, after the reported `config.settings.staging_mock` enablement. The onboarding command was rejected at 08:28 UTC; the final 08:31 UTC profile/capability reads still show no onboarding action. This file covers the current runtime blocker only.

Server: `https://sukoon-app-y4j5r.ondigitalocean.app`.

## Observed behavior

Fresh owner Google sign-in and tenant password sign-in succeeded. Both identities are verified. The selected property is published/verified and its ownership is verified. No new account or property permission is required for this observed failure.

- `GET /health/`: HTTP 200, `ready=true`. This checks database/Redis health, not provider readiness.
- Owner profile: `status="not_started"`, `allowed_actions=[]`; beneficiary onboarding is unavailable.
- Owner capability for the actual profile UUID and `action=onboard_beneficiary`: no enabled capabilities or allowed actions, in English and Arabic.
- Tenant capability for the actual property UUID and `action=create_rental_interest`: action unavailable.
- A valid owner onboarding request with current revision 1, a fresh persisted request key, and `accepted_policy_versions=["rental-policy-v1"]` returned **HTTP 403**:

```json
{
  "message": "A rental provider is not configured for this environment.",
  "data": null
}
```

The owner profile remained unchanged. No onboarding session, new invitation, agreement, signing session or payment was created in this recheck. The complete signing/payment/activation test cannot start yet.

## Verify the effective settings of the serving API

The behavior does not match the checked-in `config.settings.staging_mock` module. The external API does not expose its effective settings module or deployment SHA, so the exact configuration cause is not yet confirmed.

Open the **running API service's runtime console**, use its backend working directory and actual launch environment, and run the following. Do not add `--settings=config.settings.staging_mock` or temporarily export it just for this diagnostic; doing that would test an override instead of the existing deployment.

```sh
python manage.py shell <<'PYTHON'
import json
from django.conf import settings
from core_apps.features.providers import fake_provider_available, checkout_available

print(json.dumps({
    "settings_module": settings.SETTINGS_MODULE,
    "runtime_environment": settings.RENTAL_RUNTIME_ENVIRONMENT,
    "provider_backend": settings.RENTAL_PROVIDER_BACKEND,
    "fake_provider_allowed": settings.RENTAL_FAKE_PROVIDER_ALLOWED,
    "checkout_enabled": getattr(settings, "RENTAL_CHECKOUT_ENABLED", False),
    "webhook_secret_configured": bool(settings.RENTAL_PROVIDER_WEBHOOK_SECRET),
    "fake_provider_available": fake_provider_available(),
    "checkout_available": checkout_available(),
}, indent=2))
PYTHON
```

Expected values:

```json
{
  "settings_module": "config.settings.staging_mock",
  "runtime_environment": "staging",
  "provider_backend": "fake",
  "fake_provider_allowed": true,
  "checkout_enabled": true,
  "webhook_secret_configured": true,
  "fake_provider_available": true,
  "checkout_available": true
}
```

This diagnostic prints only safe flags and the presence of the private webhook secret, never its value. If the service launch command supplies its own settings assignment, inspect that assignment too; it must agree with the component environment.

## Apply the missing runtime setup

1. On the existing **isolated mock staging API component**, set the runtime environment variable `DJANGO_SETTINGS_MODULE` to exactly `config.settings.staging_mock`. Build-only configuration does not configure the running API. Check for a service-specific override or a launch-command assignment selecting another module.
2. Supply the existing private `RENTAL_PROVIDER_WEBHOOK_SECRET` in runtime scope. The mock settings module intentionally refuses startup when it is absent. Do not paste secret values into the reply or commit them.
3. Keep the API, Celery worker, beat and management commands on the same intended release, settings and staging database. Do not point test settings at production data.
4. Redeploy/restart the affected processes and confirm the intended deployment becomes active. A failed or incomplete deployment can leave the older API serving requests. Check startup logs for settings/import/secret failures.
5. Run the safe diagnostic above from the serving component and return its output plus the active deployment SHA/status. Do not reset users, bypass ownership checks, or manually mark the owner payment profile ready.

## API acceptance after restart

1. Read the actual owner's payment profile and current revision.
2. Call `GET /api/v1/features/v1/rental-capabilities/?subject_id=<profile UUID>&action=onboard_beneficiary`. `subject_id` is required by the current contract. Expect `onboard_beneficiary` in `allowed_actions` while the profile is not ready.
3. Send `POST /api/v1/features/v1/owner-payment-profile/onboarding-session/` with that revision, the required policy versions and a persisted UUID request key. Expect HTTP 201, `provider_mode="mock"` and the authenticated `mock_completion` descriptor.
4. Complete that exact session through its descriptor, using the returned revision and a distinct completion key. Verify profile `status="ready"` and the accepted policy.
5. Use fresh invitation/agreement records and continue both reviews, both mock signatures, the combined initial invoice, capture, settlement and activation. Previous template-test invitations are already consumed/revoked; do not reuse them.

The `fake-rental-provider.test` URLs are placeholders. Completion must use the authenticated mock API descriptors; no external bank, signing provider or real payment is required for this authorized test.

## Evidence

[Sanitized recheck summary](../../../darak-app/docs/qa/evidence/mock-runtime-recheck-2026-10-14/verification-summary.json): 21 timestamped HTTP requests. The earlier cancellation/revocation findings remain resolved in their separately dated evidence; no rental source changes were made in this recheck.
