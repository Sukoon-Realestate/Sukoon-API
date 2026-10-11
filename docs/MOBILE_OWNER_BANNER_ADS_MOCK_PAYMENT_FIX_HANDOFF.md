# Mobile handoff: owner banner mock-payment fix

Date: 2026-10-11 (Africa/Cairo). Baseline: `197de30`; this delivery is an uncommitted working-tree patch.

Source: [mobile failure report](../OWNER_BANNER_ADS_MOCK_PAYMENT_500_BACKEND_FIX.md). Existing contract: [banner ads API handoff](MOBILE_OWNER_BANNER_ADS_API_HANDOFF.md).

## Result and confirmed local cause

The reported informational-banner payment path was reproduced against an isolated PostgreSQL 15 database with the pre-fix backend. Its activation query raised:

```text
django.db.utils.NotSupportedError:
FOR UPDATE cannot be applied to the nullable side of an outer join
```

`activate_with_mock_payment()` joined optional `property__owner` while applying `select_for_update()`. PostgreSQL rejects that query, including for banners whose property is null. The fix removes the optional join from the locking query while retaining the transaction and locks on the advertisement, owner, and create operation. Optional destination validation runs separately. Informational banners remain supported.

This is a confirmed local reproduction, not an inspection of the deployed traceback at `2026-10-10T23:20:36Z`. Production logs, deployed revision, and migration state were not available in this task. No deployment or live reactivation was performed; no owner session was available. Do not treat the affected advertisement as activated based on this handoff.

## Contract fixes

- `payment.advertisement_id` now returns the public advertisement UUID rather than its internal numeric database key. Linked-banner `property_id` likewise returns the property UUID. This applies consistently to payment, detail, list, operation recovery, and relevant public projections.
- Ownership/account eligibility, the expected `<create-operation-id>-payment` ID, and mock mode are checked before replay. A wrong operation ID returns localized JSON 400 even after a successful payment; it cannot silently replay a success.
- Activation verifies that stored media has a file and that it exists in storage. Missing media returns JSON 400 with `errors.banner=["unavailable"]`, leaving payment and activation unset.
- Destination validation requires the property still belongs to the advertiser, remains verified, and has the selected eligible offer. Informational banners with both destination fields null remain valid.
- Feed and public media use the same live eligibility rule: active status, tenant-home placement, `starts_at <= now < ends_at`, active owner, successful mock payment, eligible destination, and available media. Missing files, future starts, wrong placement, and transferred destinations cannot remain publicly eligible. Public image cache lifetime is capped at the remaining advertisement duration.

The success envelope stays `key/message/data`; the full private advertisement includes its original content, create operation, purchased plan snapshot, server dates, and mock payment. The localized message remains “Simulated payment succeeded. No money collected.” No client changes, gateway, card collection, WebView, or price changes are required.

## Transaction and retry behavior

The existing one-to-one payment constraint plus the locked advertisement serialize activation. Both simultaneous identical requests return HTTP 200 with the same payment UUID and dates, and only one payment row exists. An injected payment-insert failure rolls back status and all activation timestamps; retrying the same operation can then succeed.

The purchased `plan_snapshot` remains authoritative even if the plan's live price, duration, revision, or availability changes. The weekly plan starts at actual activation and lasts 604800 seconds. Existing Cairo calendar-month/year and DST behavior is unchanged and remains tested.

Identical retries after natural expiry return the same payment, snapshot, and dates, with effective status `expired`. They do not extend the advertisement or create another payment. Public feed/media exclude expired ads immediately without waiting for a worker. Private owner media access remains available where the file exists.

No schema migration is introduced. Existing advertising migrations `0001` and `0002` and the payment one-to-one constraint are still required. Migrations were exercised on the isolated PostgreSQL test database; that is not evidence of deployed migration status.

## Required live retry: preserve the existing record

Deploy the patch and record its revision/migration status, then authenticate through the existing app login as the original owner. Inspect detail first, then repeat exactly:

```http
POST /api/v1/advertising/v1/owner-advertisements/85295dd1-f8bd-4c82-a903-9bdc3d90af98/mock-payment/
Accept: application/json
Accept-Language: en
Content-Type: application/json

{
  "operation_id": "74682688-4428-413c-a1ae-c4b87222c687-payment",
  "payment_mode": "mock"
}
```

Base URL: `https://sukoon-app-y4j5r.ondigitalocean.app`. Original create operation: `74682688-4428-413c-a1ae-c4b87222c687`. Do not create a replacement advertisement, change either operation ID, or reset the mobile journal.

Capture sanitized real response evidence: advertisement UUID, matching `payment.advertisement_id`, payment UUID, create/payment operation IDs, `active` status, `mock_succeeded`, purchased snapshot and server timestamps. Retry identically, including two concurrent requests, and confirm one payment with unchanged dates. If the stored banner file is missing on the deployed instance, the fixed endpoint returns the documented media validation error; durable shared media storage still needs operational verification.

Then check owner detail/list/operation lookup, other-account privacy, and guest/other-account feed and image reads in Arabic and English. Run the mobile report's opt-in `make bannerAdsLiveTest` with its existing journal and a privately supplied valid Google token, followed by the Owner A → Tenant B device journey. No credentials or fabricated live success receipt are included here.

## Verification

- Before the fix, the existing informational-banner activation test failed on PostgreSQL with the exception above.
- After the fix: **22 advertising tests passed on PostgreSQL 15**, including the two-connection concurrent retry, transaction rollback, plan snapshot preservation, English/Arabic round trip, public UUIDs, privacy, live eligibility, expired retry, and calendar/DST cases.
- Django system check passed; migration drift check reported no changes; focused flake8 and diff whitespace checks passed.
- Full backend suite (SQLite): **586 passed, 7 skipped, 1 failed**. The failure is the previously observed property-review ordering assertion in `core_apps/properties/tests/test_visit_request_api.py::TestPropertyReviewListAPI::test_list_reviews_happy_path_with_summary`; property-review code was not changed. Four skips require PostgreSQL (three invitation races and the new payment race); three are pre-existing skips.
- Advertising tests now use a separate in-memory cache per test so repeated fixture account IDs do not exhaust a shared throttle allowance in later tests. Production rate limits are unchanged.
- No deployed API, Flutter, device, production storage, or production log verification was performed.

From `backend/`, against an isolated test PostgreSQL server:

```powershell
$env:TEST_POSTGRES_DB = 'postgres'
$env:TEST_POSTGRES_USER = 'postgres'
$env:TEST_POSTGRES_HOST = '127.0.0.1'
$env:TEST_POSTGRES_PORT = '55440'
# Supply TEST_POSTGRES_PASSWORD privately if the test server requires it.
../.venv/Scripts/python.exe -m pytest core_apps/advertising/tests/test_advertising_api.py -q --ds=config.settings.postgres_test --tb=short
../.venv/Scripts/python.exe -m pytest -q --tb=short
../.venv/Scripts/python.exe manage.py check --settings=config.settings.test
../.venv/Scripts/python.exe manage.py makemigrations --check --dry-run --settings=config.settings.test
```

Changed files: `backend/core_apps/advertising/services.py`, `backend/core_apps/advertising/views.py`, and `backend/core_apps/advertising/tests/test_advertising_api.py`.
