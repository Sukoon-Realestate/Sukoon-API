# Mobile integration of the implemented backend handoff

Integration date: 2026-10-08. Contract: [`MOBILE_ALL_FEATURES_BACKEND_HANDOFF.md`](../MOBILE_ALL_FEATURES_BACKEND_HANDOFF.md).

The current Remote Config API is `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/` for both configured environments. Owner and tenant authentication succeeded against that API. The supplied test credentials were not added to the repository; temporary session and response files were removed after verification.

## Implementation

The existing `data/` and `presentation/` structure is retained. Typed models and request serialization stay in data, requests and realtime subscriptions stay in Cubits, and screens use extracted widgets. API collections continue to use `AppPagify`; detail reads use the shared cache pipeline and shimmer/status rendering.

The added sections are `LeaseDetailsSummary`, `RentInvoiceSummary`, `PremiumAlertDetailsView` and `AlertFiltersSummary`. `LeasePropertyCubit` owns the full-property request for the extracted `LeaseRentalOfferSelector`. Chat ACK mapping, service capability flags and retry-key ownership live under their features' data folders.

| Area | Result |
| --- | --- |
| Chat | Each outgoing message gets one UUID `client_message_id`, persisted with its outbox/draft and reused across socket sends, REST fallback and recovery. `message.ack` confirms that exact pending message using the server ID. Another conversation or mismatched REST identity cannot confirm a send. Editing recovered content starts a new message identity. |
| Lease creation | The form reads the full selected property, selects an available whole-property/room/group/bed offer, and includes `offer_id`. The Cubit verifies fresh identity, availability, revisions and terms before creating the draft, then checks the returned property, snapshot, status and manually entered accounting rent. Failed submissions retain entered data and refresh the offer inventory. |
| Lease details | Show participant names, start/end dates, stored rent, status, and complete saved accommodation terms: scope, offer/room/bed names, capacity, bathroom access, offer price/period, minimum duration, deposit, suitability, description, smoking and rules. Signed/active leases retain their invoice entry. Owner-only draft cancellation remains available when authorized. |
| Invoice details | Show reference, status, due date and the stored minor-unit amount independently of the historical offer price. Show the complete accommodation snapshot and link to its authorized lease while preserving workspace. Checkout controls are tenant-only and provider-gated. |
| Alerts | History cards open authorized details. Details show cadence, enabled state, last match time, and the complete saved search criteria, using localized API metadata when available. Numeric and boolean JSON filter values are retained. Updates/deletion use a stable UUID per subject/revision/action; failure retains state and refreshes history. |
| Owner collections | Send `rental_scope` to the backend before pagination. Preserve `rental_scopes` and `manageable_offer_count` in models/cache and show them on owner cards. Changing category starts a separate paginated collection. |
| Configuration, analytics, promotions, suggestions | Retain the implemented free configuration and existing paginated histories, measured analytics and facts-only suggestion flows. Promotion history shows duration, supplied dates and any stored impressions, with a notice when the worker is unavailable. |
| Cache and response checks | Feature reads include language as well as existing resource/query dimensions and account scoping. Detail reads reject mismatched resource IDs. Feature mutations reject responses from a previous account session. |
| Legacy listings | The deployed legacy `rental_inventory: {"offers": []}` projection and a null discovery schema marker remain legacy. Explicit malformed inventories and unknown schema versions remain unsupported. |
| Accommodation photo chooser | Give each photo checkbox its own transparent Material surface so card decoration does not obscure tap feedback. Stable photo identity and exact bed/shared-room associations are preserved. |

Arabic and English app text is generated from `packages/core/assets/translations/lang.json`. Backend-localized labels and messages are displayed directly. Dates on the updated detail screens use the selected language.

Existing rental inventory serialization, permanent ID/client-key read-back, exact-offer favorites, visit snapshots, dedicated availability timestamps, and conditional accommodation details remain in their existing feature architecture. Unsupported local accommodation extensions and unconfirmed media associations keep their submission guards; the implemented version-1 handoff does not establish a contract for additional draft-only fields.

## Current API verification

Requests were authenticated with the supplied test accounts. The following foundation checks succeeded:

| Requests | Observed result |
| --- | --- |
| Owner/tenant configuration with `lang=ar` and `lang=en` | HTTP 200; owner boost options and tenant alert cadences parsed correctly. |
| Lease configuration | HTTP 200; creation permission and an approved versioned Arabic residential template returned. |
| Owner properties, full property details and eligible lease tenants | HTTP 200; the owner's listing is legacy and currently has no eligible tenant records. |
| Owner analytics for 30 days | HTTP 200; measured metrics, methodology and timestamp returned; no signed export URL. |
| Tenant discovery/homepage, saved properties and conversation history | HTTP 200; existing legacy records remain readable. |
| Owner and tenant leases/invoices, owner promotions, tenant alerts | HTTP 200 with valid empty paginated collections on these accounts. |
| Owner/tenant `rental_scope=room` collection requests | HTTP 200 with empty results for the available legacy inventory. |
| Property filter options in Arabic and English | HTTP 200; labels and catalogs available. |
| Protected feature reads without authentication | HTTP 401 with the appropriate Arabic/English authentication message. |
| Alert create, fetch, pause, refresh and delete | Creation returned HTTP 201, all saved filters round-tripped, update returned HTTP 200, deletion returned a cancellation receipt. The temporary test alert was removed. |
| Repeating alert creation with the same key/payload | HTTP 201 with the same receipt; changing the payload with that key returned HTTP 409. |
| Sending a stale alert revision | HTTP 409, as required. |

The test accounts contain no version-1 rental inventory, existing lease/invoice records, or eligible tenant for the owner's property. Successful live offer writes, lease creation/cancellation, invoice checkout and provider settlement/signing were therefore **not** established. All four accommodation scopes and the chat ACK/retry behavior are checked with injected contract fixtures. No live chat message or promotion was sent/created as part of these checks.

### Backend discrepancy: successful alert PATCH retry

The deployed API applies revision validation before recognizing a successful repeated update:

1. `PATCH features/v1/search-alerts/{id}/` with `enabled=false`, `revision=1` and a stable UUID returned HTTP 200 and revision 2.
2. Repeating the identical request with the same UUID returned HTTP 409, `Alert revision conflict.`, instead of the original receipt.
3. A fresh GET confirmed the alert was paused at revision 2; deletion using that revision succeeded.

Backend follow-up: after authorizing the resource, recognize a previously completed matching request key/fingerprint before rejecting its old revision. Repeated identical mutations should return their original receipt; changed payloads must still return HTTP 409. The app preserves retry identity, reports the conflict and refreshes current state instead of inferring success.

## Provider and worker readiness

`FeatureServiceCapabilities.configured` defaults every flag below to false. Reading records and managing persisted drafts/alerts does not require these providers.

| Build define | Enables after confirmed staging verification |
| --- | --- |
| `SOKOUN_RENT_CHECKOUT` | Tenant checkout session creation and hosted payment entry; requires real invoice authorization, settlement and authenticated webhook verification. |
| `SOKOUN_LEASE_SIGNING` | Authorized signing sessions; requires verified document access, real signature completion and authenticated webhooks. |
| `SOKOUN_SIGNED_DOCUMENTS` | Signed lease/receipt URL actions after access and expiry checks are confirmed. |
| `SOKOUN_ANALYTICS_EXPORTS` | Signed analytics export actions. |
| `SOKOUN_ALERT_DELIVERY` | Removes the unavailable-delivery notice after matching, quiet hours, deduplication, preferences and push are confirmed. It does not deploy a worker. |
| `SOKOUN_PROMOTION_WORKER` | Removes the unavailable-worker notice after expiry and impression counting are confirmed. It does not deploy a worker. |

Existing per-operation `RENTAL_OFFERS_*` defines remain off by default, including media association. Enable each only with its actual staging round trip and dependency evidence; a responding route or these fixture tests are insufficient. External AI execution, scheduled invoice generation and production App/Universal Links are not enabled by this integration.

## Verification commands

From `apps/sokoun_app`:

```sh
make mobileBackendCheck
make featureToolsCheck
make featureToolsUiReview TOOLS_REVIEW_DIR=/tmp/sokoun-handoff-ui
flutter test --no-pub
```

The handoff tests cover all four offer lease scopes, changed/unavailable/cached selections, mismatched returned identities/terms/accounting amounts, legacy compatibility, account/language cache boundaries, owner scope queries, stable alert retries, authorized detail navigation and provider gates. Chat tests cover exact ACK correlation, UUID reuse after lost ACKs, rejected REST identities, durable recovery and repeated identical text.

The tool UI matrix covers Arabic/English, both themes, widths 320/390/600/768/1024/1366, and text scales 1/1.3/2. Detail checks scroll to the full saved terms and final actions; exports include the initial viewport and the lower detail/action region. These are Flutter-rendered fixtures rather than physical-device/provider round trips.

Final verification on Flutter 3.44.7:

- Full Sokoun app suite: **3,236 tests passed, zero failed**.
- Tool layout suite: **76 cases**, including 72 language/theme/width/text-scale combinations and keyboard/split-view checks; 448 rendered images exported, including 96 lower detail/action captures.
- Analysis of the 25 changed feature/test targets: **no issues**. Repository-wide analysis has zero errors and six pre-existing warnings/informational findings in unrelated/generated files.
- Formatting check: 69 edited/new Dart files unchanged by the final formatter check. `git diff --check` passed.
- The temporary live alert was deleted; temporary account sessions and API response files were removed.
