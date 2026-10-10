# Tenancy invitations — deployed verification follow-up

Checked: 2026-10-09, Africa/Cairo

Outcome: **Not ready** — invitation creation returns HTTP 500 after property verification. Lease draft validation also returns HTTP 500.

API: `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`

This supplements [the returned backend contract](TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md). Its original “not deployed” status is historical: authenticated invitation routes are reachable on the app's configured server. The blocker is now failing mutations. Mobile application code, tests, and configuration were not changed during this review; the invitation capability remains disabled by default.

## Current test fixtures

| Subject | Actual identity/state |
| --- | --- |
| Owner | `3b6d5dd4-2077-4bad-9c59-32717915035e` — `emara8020@gmail.com`, Google authentication succeeded; server `is_verified=true` |
| Tenant | `4f5bd135-df44-409f-a2cf-712d8fc1fce8` — `emara8028@gmail.com`, server `is_verified=true` |
| Property | `13954644-cc37-49d9-a772-f1a88be81401` — owned by the owner above |
| Latest property state | `status=verified`, `is_verified=true`, `owner_is_verified=true`, `is_ownership_verified=false` |
| Rental inventory | Legacy property: `rental_inventory={"offers":[]}`; no version-1 offer ID |
| Eligible source visit | `694602e9-1e4a-42cc-8d65-1bd73a685856` — `confirmed`, same property and tenant |
| Lease template | `eg-residential-v1`, version `1`, returned by the live lease configuration |

The original unverified `ahmed@gmail.com` owner is no longer the test owner. Property verification has been updated on the server. Previously, invitation creation returned HTTP 409, “The property is not currently available for leasing.” After `is_verified` became true, the same request returns HTTP 500. The remaining false ownership flag is recorded as context; its role in the failure is **not established**.

## 1. Fix invitation creation HTTP 500

**Priority:** Release blocker. **Evidence:** Confirmed on the deployed API, with both `Accept-Language: en` and `ar`.

Authenticate as the owner above using the supported Google authentication flow. Use an authorized API session, `Content-Type: application/json`, and `Accept: application/json`.

```http
POST /api/v1/features/v1/tenancy-invitations/
```

Exact body used:

```json
{
  "property_id": "13954644-cc37-49d9-a772-f1a88be81401",
  "tenant_id": "4f5bd135-df44-409f-a2cf-712d8fc1fce8",
  "request_key": "9aa2b40c-f5fa-4587-9649-10683d6d7735"
}
```

`offer_id` and `expected_offer_revision` are deliberately omitted, as required for the legacy-property path in the returned contract.

**Observed:** HTTP 500 with a non-JSON response in both languages. Subsequent owner and tenant invitation histories return HTTP 200 with `results=[]`, `count=0`; no invitation receipt or history record is visible. The owner tenant picker also remains empty.

**Expected:** HTTP 201 with a complete pending invitation, revision 1, server expiry, `eligible_for_lease=false`, and the returned-contract legacy nullable offer fields, once the server's property/account/source checks pass. Any remaining business-rule rejection must return the documented localized JSON 4xx error instead of HTTP 500.

**Backend work:** Reproduce this exact owner/property/tenant legacy request and inspect server logs for the exception. Fix its actual cause, verify the deployed revision and migrations, and cover this deployed fixture path with a regression check. The mobile response does not expose the exception; no specific schema, notification, or service failure has been established. If property ownership/availability still requires an approval step, complete that step through the backend workflow and return a readable rejection until it is complete. Property approval fields are read-only in owner API metadata.

## 2. Fix lease draft validation HTTP 500

**Priority:** Release blocker. **Evidence:** Confirmed before and after property verification, including a repeat with the same request key.

```http
POST /api/v1/features/v1/leases/
```

Exact body used:

```json
{
  "property_id": "13954644-cc37-49d9-a772-f1a88be81401",
  "tenant_id": "4f5bd135-df44-409f-a2cf-712d8fc1fce8",
  "template_id": "eg-residential-v1",
  "template_version": "1",
  "start_date": "2026-10-10",
  "end_date": "2027-04-10",
  "rent": {
    "amount_minor": 6000000000,
    "currency": "EGP",
    "exponent": 2
  },
  "request_key": "9d661b55-991c-4773-b08b-74c4f6449f62"
}
```

The rent comes from the test listing's `60000000.00` price, expressed in minor units. The configuration endpoint returns `can_create=true` and the template above. Refresh the dates when reproducing after the specified start date.

**Observed:** HTTP 500 with a non-JSON response. No accepted invitation exists, and subsequent property-filtered lease history remains empty.

**Expected for this request:** A documented localized JSON 4xx rejection because accepted invitation eligibility is absent. This is a negative eligibility test, not evidence that a fully eligible draft succeeds or fails. Correct request validation and business-rule exceptions must not become HTTP 500.

**Backend work:** Inspect the actual exception and fix it. Verify missing/pending/rejected/expired/revoked/consumed invitations and unavailable accommodation return the documented response without creating a draft. After invitation creation is fixed, separately verify the successful accepted-invitation draft path and atomic invitation consumption/linking.

## Checks completed

| Live check | Result |
| --- | --- |
| Owner Google authentication | HTTP 200; authenticated user is the replacement owner above |
| Both participants' `auth/users/me/` | HTTP 200, `is_verified=true` |
| Property detail after the latest backend change | HTTP 200, `status=verified`, `is_verified=true` |
| Confirmed source visit detail | HTTP 200; correct property and tenant |
| Owner/tenant invitation histories | HTTP 200; empty |
| Owner eligible tenant picker before acceptance | HTTP 200; empty, as expected |
| Lease configuration | HTTP 200; `can_create=true`, current template returned |
| Invitation creation after property verification | HTTP 500 in English and Arabic |
| Draft creation without accepted eligibility | HTTP 500, including after property verification |
| Owner invitation for another owner's property | HTTP 404 |
| Tenant attempting invitation creation for this property | HTTP 404 |
| Tenant attempting owner picker for this property | HTTP 404 |
| Invitation/lease histories after the failed requests | HTTP 200; empty |

Local app checks were rerun against the current code using the Flutter SDK referenced by `.dart_tool/package_config.json`:

```sh
cd apps/sokoun_app
/Users/aait/Downloads/flutter_3.35_1/bin/flutter test --no-pub test/tenancy_invitations_contract_test.dart test/tenancy_invitations_flow_test.dart test/feature_architecture_test.dart test/tenancy_invitations_backend_handoff_test.dart
```

Result: **90 passed**. These tests use fixtures, HTTP adapters, and Flutter widgets; they do not establish successful deployed mutations. No new device/build/full-suite verification was performed in this recheck.

## Return evidence needed to resume mobile rollout

1. Provide the deployed backend revision, migration status, and the identified exceptions/fixes for both requests above.
2. Create one pending legacy invitation using these participants and return its actual invitation ID and complete response. Verify pending invitations do not populate the picker and unauthorized actors cannot respond.
3. Have only the addressed tenant accept it: HTTP 200, revision increment, `accepted_at`, and current computed eligibility. Verify identical retries, changed request bodies, and response conflicts against the documented rules.
4. Verify the owner picker includes this tenant for this property after acceptance; verify rejection and expired/revoked/consumed invitations do not qualify.
5. Create a draft successfully after rechecking current eligibility and availability. Return the actual lease ID and evidence of the linked, consumed invitation. Verify changed availability between picker and draft returns JSON 4xx and saves no draft.
6. Cancel the test draft through the documented owner cancellation transition and confirm the invitation remains consumed. Draft creation/acceptance must not allocate inventory or create invoices.
7. Supply version-1 rental inventory fixtures for all supported offer scopes, plus deployed Arabic/English, notification, pagination, concurrency, and participant privacy evidence.

Acceptance, rejection, positive picker population, successful draft linking, notification delivery, and offer-scope round trips remain **not verified on the live service** because invitation creation is failing. Enable `SOKOUN_TENANCY_INVITATIONS` only after the required deployed round trips pass.

This file contains no passwords, Google ID tokens, API tokens, or session cookies.
