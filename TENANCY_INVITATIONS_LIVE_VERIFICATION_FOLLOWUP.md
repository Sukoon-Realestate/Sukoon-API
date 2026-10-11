# Tenancy invitations — deployed verification follow-up

Checked: **2026-10-11, Africa/Cairo** (live writes approximately 01:33–01:39; UTC 2026-10-10 22:33–22:39).

Outcome: **Not ready** for the complete app journey. The original invitation/draft HTTP 500 failures are resolved on the live legacy fixture. Invitation creation, tenant acceptance, picker eligibility, draft creation/linking, rejection and cancellation now succeed. The live lease configuration still blocks the app form with `can_create=false`, and new legacy drafts return contradictory mutation permissions.

API: `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`

This supplements [the original returned contract](TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md) and [the PostgreSQL fix handoff](MOBILE_TENANCY_INVITATIONS_FOLLOWUP_HANDOFF.md). The latter directly addresses the original failure: its reported PostgreSQL exception was `FOR UPDATE cannot be applied to the nullable side of an outer join`. Backend removed optional relation joins from locked queries. Successful deployed requests below verify that the previously failing legacy paths work now; the exact deployed revision and migration state were not supplied or independently inspected.

The app's legacy nullable-snapshot parser was corrected in this recheck. Capability defaults and server authorization/readiness gates were retained. The historical 2026-10-09 results below are preserved as dated evidence, not current failures.

## Current live verification: 2026-10-11

Fresh Google authentication succeeded for owner `3b6d5dd4-2077-4bad-9c59-32717915035e` (`emara8020@gmail.com`). The tenant is `4f5bd135-df44-409f-a2cf-712d8fc1fce8` (`emara8028@gmail.com`). Both current `auth/users/me/` responses returned `is_verified=true`. Property `13954644-cc37-49d9-a772-f1a88be81401` remains verified, owned by this owner, with legacy `rental_inventory={"offers":[]}`. Confirmed source visit `694602e9-1e4a-42cc-8d65-1bd73a685856` was reread successfully. `is_ownership_verified=false` remains in the property response but did not prevent these authorized mutations.

Both Firebase Remote Config flavor configurations were fetched successfully; their `base_url` and `dev_base_url` point to the API above. No Remote Config values were changed.

| Live check | Observed result |
| --- | --- |
| Correct legacy draft body before accepted eligibility, English and Arabic | HTTP 409 with localized JSON; no HTTP 500 |
| Owner creates pending invitation | HTTP 201; `26bafa3c-17bb-4fea-b1e5-42199a3f1b9f`, revision 1, seven-day server expiry |
| Identical invitation retry, Arabic | HTTP 201; same invitation ID |
| Picker before acceptance | HTTP 200; empty |
| Owner attempts tenant response | HTTP 403; only addressed tenant may respond |
| Tenant reads pending detail | HTTP 200; `actions.can_respond=true` |
| Tenant accepts | HTTP 200; revision 2, `accepted_at`, `eligible_for_lease=true` |
| Identical acceptance retry, Arabic | HTTP 200; same invitation ID and revision |
| Acceptance request key reused with a different decision | HTTP 409; idempotency mismatch |
| Owner picker after acceptance | HTTP 200; includes the actual tenant ID and display name |
| Eligible legacy draft POST | HTTP 201; `bbad3fde-e30a-41bd-8bac-a86d367366ea`, status `draft`, revision 1 |
| Identical draft retry, Arabic | HTTP 201; same lease ID |
| Invitation after draft | Links that lease; eligibility false; blocking reason says already consumed |
| Picker after draft consumption | HTTP 200; empty |
| Owner cancels test draft | HTTP 200; status `cancelled`, revision 2; detail confirms cancellation |
| Invitation after cancellation | Still accepted and linked/consumed; not eligible again |
| New draft using consumed eligibility | HTTP 409; no new lease |
| Owner sends a fresh invitation after cancellation | HTTP 201; `14dbb20a-e444-453a-b70b-63ea16ea15dd`, pending revision 1 |
| Tenant rejects fresh invitation, Arabic | HTTP 200; rejected revision 2, `rejected_at`, eligibility false |
| Picker and draft after rejection | Picker empty; draft HTTP 409 with Arabic JSON |
| Final owner and tenant invitation histories | HTTP 200; two records: accepted/consumed and rejected; no pending invitation |
| Final property-filtered lease history | HTTP 200; one cancelled test lease |
| Test lease invoice history | HTTP 200; empty |
| Property reread after draft creation/cancellation | Legacy inventory unchanged |

Histories require `workspace=owner|tenant`, e.g. `tenancy-invitations/?workspace=owner&property_id=...`; the actual app already supplies it. Diagnostic reads without workspace returned the expected JSON 400 and were corrected in the test client.

The successful draft used the documented legacy body: no offer, interest or proposal ID; template `eg-residential-v1`, version `1`; dates `2026-10-12` to `2027-04-12`; listing-derived rent `{"amount_minor":6000000000,"currency":"EGP","exponent":2}`. No agreement signing, payment, lease activation or occupancy allocation was executed. Authorized test sessions were logged out with HTTP 204 and discarded. Test history remains auditable.

## Remaining backend work: lease configuration and legacy permissions

### 1. Make the legacy draft capability agree with its mutation policy

**Priority:** Release blocker. **Evidence status:** Confirmed. **Owner:** Backend.

For the authenticated owner, `GET features/v1/lease-configuration/` repeatedly returns HTTP 200 in English and Arabic with:

```json
{
  "can_create": false,
  "templates": [{"id":"eg-residential-v1","version":"1"}],
  "allowed_actions": [],
  "blocking_reasons": ["Owner onboarding or agreement providers are not ready."]
}
```

The template above is abbreviated; the actual response also includes its title, jurisdiction, language and rental policy. The same authorized legacy `POST features/v1/leases/` nevertheless succeeded with HTTP 201 after acceptance. This is a confirmed capability/mutation inconsistency. In `lease_draft_content.dart`, the app displays the unavailable state when `configuration.canCreate` is false, so the owner cannot reach the form even though a direct API draft succeeds.

Determine the intended legacy policy and make both endpoints agree. If legacy draft creation is supported before signing/payment providers are ready, return its truthful capability and usable template while retaining separate provider gates for signing, activation and money movement. If onboarding/providers are mandatory even for draft creation, return the corresponding documented JSON rejection from POST and provide the actual onboarding path/prerequisites. Do not turn on provider capabilities merely to pass this test. If legacy and structured agreements require different configuration fields, return an explicit agreed compatibility contract; mobile must not infer new fields.

**Verification:** Reread configuration as this owner; open the real Create lease screen with the test build capability enabled; confirm access matches the authorized POST policy. Provider/signing/payment actions must remain governed by their own readiness.

### 2. Clarify permissions for newly created legacy drafts

**Priority:** Release blocker for continuing/cancelling drafts in the app. **Evidence status:** Confirmed. **Owner:** Backend contract, then mobile integration if a contract change is required.

The new draft's HTTP 201 response contains:

```json
{
  "id": "bbad3fde-e30a-41bd-8bac-a86d367366ea",
  "status": "draft",
  "lease_status": "draft",
  "revision": 1,
  "offer_id": "",
  "offer_snapshot": null,
  "can_sign": true,
  "can_cancel": true,
  "legacy_read_only": true,
  "allowed_actions": [],
  "blocking_reasons": ["This legacy agreement is not eligible for new rental mutations."],
  "invitation_id": "26bafa3c-17bb-4fea-b1e5-42199a3f1b9f"
}
```

The legacy cancellation endpoint accepted the owner request and returned a cancelled revision-2 receipt. The app's `DigitalLease.fromJson` deliberately disables cancellation/signing for `legacy_read_only=true`. Consequently, the new draft advertises `can_cancel=true` while also supplying the classification that blocks that action in the app. Do not remove the client safeguard without settling the server contract. Return consistent actionable capabilities for new legacy drafts, document whether legacy cancellation is an explicit exception, and distinguish retained historical read-only agreements from supported new legacy drafts. `can_sign=true` was observed, but signing/provider behavior was not tested and must not be treated as ready.

**Verification:** New draft/detail/list projections and actual cancellation authorization agree for both participants. Unsupported signing stays unavailable; supported cancellation is accessible without allowing other read-only agreement mutations.

## App correction and local verification

The deployed legacy DTO explicitly sends `offer_id=""` and `offer_snapshot=null`. Previously, `RentalSelection.fromRecord` treated a present null snapshot as an incomplete selection. `LeaseDraftCubit` then rejected the valid legacy draft receipt because legacy drafts require `rentalSelection==null`.

The data parser now treats an absent or null snapshot as no selection when the offer ID is empty. A nonempty offer ID with a missing/null snapshot remains incomplete, and non-null malformed snapshots remain invalid selections. No server capability or read-only gate was bypassed.

Regression coverage runs the real `LeaseDraftCubit` receipt validation with the live response shape and verifies incomplete/malformed offer snapshots remain protected. The prior 91 invitation/architecture checks passed before this correction. **All 160 focused checks passed after the correction; scoped analysis found no issues.** From `apps/sokoun_app`:

```sh
/Users/aait/Downloads/flutter_3.44_7/bin/flutter test --no-pub test/rental_backend_reply_contract_test.dart test/rental_offers_domain_test.dart test/tenancy_invitations_contract_test.dart test/tenancy_invitations_flow_test.dart test/feature_architecture_test.dart test/tenancy_invitations_backend_handoff_test.dart
/Users/aait/Downloads/flutter_3.44_7/bin/flutter analyze --no-pub lib/features/shared/rental_offers/data/models/rental_selection.dart test/rental_backend_reply_contract_test.dart test/rental_offers_domain_test.dart
```

Formatting and the scoped `git diff --check` passed. These are local fixtures, static analysis and Flutter widget checks, separate from the live API table above. No physical-device/build/full-suite recheck was performed.

## Evidence and rollout still needed

The mobile capability remains disabled by default. Resolve the two confirmed compatibility issues above before claiming that the actual app journey is usable. Then supply deployed revision/migration evidence and complete the requested version-1 offer scope, expiry/revocation, changed availability/terms, participant privacy, pagination, concurrency, real notification delivery/navigation and device checks. Backend-local PostgreSQL race tests in the returned handoff are useful evidence; they were not independently rerun here.

Local sanitized evidence:

- `/tmp/darak-tenancy-retry-2026-10-11-evidence.json`: timestamped API checks and safe request bodies.
- `/tmp/darak-tenancy-retry-2026-10-11-remote-config-urls.json`: current environment URL checks.
- `/tmp/darak-tenancy-retry-2026-10-11-app-tests-final.log`: focused checks after the parser correction.
- `/tmp/darak-tenancy-retry-2026-10-11-analysis.log`: scoped analyzer result.
- `/tmp/darak-tenancy-retry-2026-10-11-report.txt`: Arabic readiness report and remaining verification sheet.

No passwords, Google ID tokens, API tokens or session cookies are included in these files.

---

## Historical verification: 2026-10-09

The remaining sections record the failure before the PostgreSQL fix. Their HTTP 500 results, `can_create=true` snapshot and unverified-flow statements are historical and are superseded by the 2026-10-11 results above.

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
