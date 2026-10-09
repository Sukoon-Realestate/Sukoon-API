# Tenancy invitations and lease eligibility — backend handoff

Updated: 2026-10-09

Status: **Mobile integration aligned with the returned contract. Live routes and verified test accounts work, but invitation creation and lease draft creation return HTTP 500. End-to-end verification remains blocked.**

API base: `/api/v1/`  
Mobile capability: `SOKOUN_TENANCY_INVITATIONS`, disabled by default.

The returned [backend handoff](TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md) defines the current contract and requires the mobile capability to remain disabled until deployed verification is complete. Its original deployment status has been superseded by live checks. See [the live verification follow-up](TENANCY_INVITATIONS_LIVE_VERIFICATION_FOLLOWUP.md) for the current server results, actual fixture IDs, and reproducible failures.

## Purpose and required flow

Owners currently cannot populate the eligible tenant picker. Add an explicit invitation process before drafting a lease:

1. The owner invites a tenant to proceed with a lease for an owned property and, where applicable, a specific rental offer. Validate ownership, tenant identity and accommodation availability. Create a pending invitation.
2. Only the addressed tenant accepts or rejects the invitation. Acceptance records willingness to proceed with a draft and creates lease eligibility for that exact accommodation.
3. The owner opens the tenant picker. Return only tenants with valid accepted invitations for the selected property/offer.
4. The owner creates a lease draft. Recheck invitation eligibility, ownership and current accommodation availability inside the creation transaction before saving.

An accepted viewing, chat message, favorite, or property visit must not create tenancy eligibility. Invitation acceptance does not sign a lease, mark accommodation rented, reserve inventory indefinitely, or create invoices. Those effects belong to documented lease/allocation/ledger transitions.

## Mobile entry points and rollout

- Owner: Requests → pending/confirmed request details → **Invite to rent**, for a verified tenant. The app supplies the actual tenant/property IDs. Rejected, cancelled, completed, unknown and missing visit states do not expose this action. The existing owner UI alias `accepted` represents `confirmed`. For rental inventory, the owner chooses a currently available offer from a fresh full-property read; historical viewing snapshots do not authorize an invitation.
- Both workspaces: Contracts → **Rental invitations** → invitation detail.
- Tenant detail: review the owner, property and accommodation, then **Accept invitation** or **Reject invitation**.
- Owner detail: pending/accepted/rejected/expired/revoked status and current lease eligibility. Accepted invitations do not create a lease automatically; continue through the existing Create lease flow.
- Notification: `action_type=open_tenancy_invitation`, a real invitation `target_id`, and explicit `workspace=tenant|owner`.

The app includes the agreed API adapter and fixture coverage. Default builds show an unavailable notice and make no invitation API calls. Enable the capability only after staging deployment and verification match the returned contract. Existing visit acceptance, chat and lease history continue independently.

## Invitation persistence and lifecycle

Persist an auditable record containing:

| Field | Meaning |
| --- | --- |
| `id` | Stable UUID invitation identity |
| `property_id` | Authorized property identity |
| `owner_id`, `tenant_id` | Actual account identities, distinct from each other |
| `offer_id` | Exact accommodation identity; null/empty only for legacy property-only accommodation |
| `offer_snapshot` | Immutable invitation-time accommodation/terms snapshot, using the existing rental selection contract |
| `status` | `pending`, `accepted`, `rejected`, `revoked`, or `expired` |
| `revision` | Positive integer incremented on state changes |
| `created_at`, `expires_at` | Time-zone-aware ISO 8601 instants; expiry must be supplied by the server |
| `accepted_at`, `rejected_at`, `revoked_at` | Nullable audited transition instants |
| `lease_id` | Nullable linked draft/lease identity |

Store the initiating/responding actor and idempotency records. Owner identity and expiry are server-derived; never trust owner identity or eligibility flags supplied by the client. Maintain an authoritative current participant/ownership relationship when ownership or account access changes.

Transitions: `pending → accepted|rejected|revoked|expired`. The server sets expiry to seven days after creation; pending and accepted-but-unconsumed invitations expire at that instant. An accepted invitation may be revoked only before it is linked to a lease. Linked history retains its snapshot and accepted status after its invitation deadline. A cancelled draft keeps the original invitation linked and consumed; a fresh invitation is allowed if the accommodation is currently available. Never reactivate a rejected/revoked/expired record or authorize a new draft with a consumed invitation.

Prevent duplicate live invitations for the same owner/property/tenant/accommodation. A stable identical retry returns its original result. A different request creating an already live invitation returns a readable conflict instead of generating duplicates. Multiple non-overlapping offers under one property remain separate subjects.

## Agreed endpoints

| Method | Path | Authorization |
| --- | --- | --- |
| POST | `features/v1/tenancy-invitations/` | Verified authenticated owner of the property |
| GET | `features/v1/tenancy-invitations/` | Authenticated participant; query workspace and optional property |
| GET | `features/v1/tenancy-invitations/{id}/` | Actual owner or addressed tenant |
| POST | `features/v1/tenancy-invitations/{id}/respond/` | Addressed tenant only |

The returned handoff confirms these names and local implementation. Live invitation routes are reachable on the configured API, but successful invitation creation has not been verified. The prepared mobile flow has no owner revocation mutation.

### Create an invitation

```http
POST /api/v1/features/v1/tenancy-invitations/
```

```json
{
  "property_id": "property-uuid",
  "tenant_id": "tenant-account-uuid",
  "offer_id": "offer-uuid",
  "expected_offer_revision": 7,
  "request_key": "client-generated-uuid"
}
```

For a legacy property without rental inventory, omit `offer_id` and `expected_offer_revision`. Require both for version-1 rental inventory. Reject unknown/unsupported inventory versions, stale revisions, unavailable/archived accommodation, invalid tenant accounts and owner-as-tenant. Confirm that the selected offer belongs to the authorized property and has no conflicting allocation.

For the first release, both accounts must be active and verified, and the exact owner/property/tenant pair must have a `PropertyVisit` with status `pending` or `confirmed`. Rejected/cancelled visits cannot source an invitation. Chat-only sourcing is deferred because current conversations do not identify a property. The mobile entry uses owner visit request details; the server remains responsible for current ownership, account access and source authorization.

Return HTTP 201 with the full invitation, `status=pending`, `eligible_for_lease=false`, and `actions.can_respond=false` for the owner. Notify the tenant only after the transaction commits, once per logical invitation.

### Full invitation response

Successful responses use the existing envelope:

```json
{
  "key": "success",
  "msg": "Localized result message",
  "data": {
    "id": "invitation-uuid",
    "property_id": "property-uuid",
    "property_title": "Property display title",
    "owner_id": "owner-account-uuid",
    "owner_name": "Owner display name",
    "tenant_id": "tenant-account-uuid",
    "tenant_name": "Tenant display name",
    "offer_id": "offer-uuid",
    "offer_snapshot": {
      "property_id": "property-uuid",
      "offer_id": "offer-uuid",
      "offer_revision": 7,
      "rental_scope": "bed",
      "name": "Bed in the first room",
      "room_ids": ["room-uuid"],
      "room_names": ["First room"],
      "bed_id": "bed-uuid",
      "bed_name": "First bed",
      "capacity": 2,
      "bathroom_access": ["shared"],
      "availability": "available",
      "archived": false,
      "offer_link": "",
      "terms": {
        "price": "1500",
        "price_period": "monthly",
        "rental_period": 3,
        "deposit": "one_month",
        "suitable_for": "students",
        "description": "Accommodation description",
        "smoking_allowed": false,
        "rules": ["Keep shared spaces clean"]
      }
    },
    "status": "pending",
    "revision": 1,
    "created_at": "2026-10-08T12:00:00+03:00",
    "expires_at": "2026-10-15T12:00:00+03:00",
    "accepted_at": null,
    "rejected_at": null,
    "revoked_at": null,
    "lease_id": null,
    "eligible_for_lease": false,
    "actions": {"can_respond": true}
  }
}
```

The example is a bed invitation. Return the equivalent complete snapshot for the selected entire property, room, room group or bed, with real property/offer identities, revisions, accommodation names and saved terms. Legacy records omit the snapshot or return null. Names/titles are server-localized/display content, not IDs. `actions` are computed for the authenticated account; only an addressed tenant with a live pending invitation can respond.

### Invitation collection

```http
GET /api/v1/features/v1/tenancy-invitations/?workspace=tenant&page=1&page_size=20
GET /api/v1/features/v1/tenancy-invitations/?workspace=owner&property_id=property-uuid&page=1&page_size=20
```

Filter by actual participant/account and optional authorized property **before** count and pagination. Return full invitation items in `data.results` with `count`, `per_page`, `total_pages`, `next`, and `previous`. Use deterministic descending creation order with an ID tie-breaker. Preserve accepted/rejected/expired/revoked history. Empty success is `results: []`, `count: 0`, `total_pages: 1`; failures are not empty successes.

### Tenant response

```http
POST /api/v1/features/v1/tenancy-invitations/invitation-uuid/respond/
```

```json
{
  "decision": "accepted",
  "revision": 1,
  "request_key": "client-generated-uuid"
}
```

`decision` accepts only `accepted` or `rejected`. Derive the responding tenant from authentication. Validate recipient, verification/access, pending status, revision and expiry. Recheck current invitation accommodation/terms before acceptance; conflicts require a refreshed/new invitation instead of accepting changed terms. Return HTTP 200 with the full updated invitation and incremented revision. Acceptance records `accepted_at` and returns computed eligibility; rejection creates no eligibility. Notify the owner after commit.

Authorize before resolving idempotency. An identical completed retry returns its original receipt even though the original revision is now old. Changing the decision/body with the same key returns HTTP 409. A different action after the invitation was already answered returns a state conflict.

## Existing tenant picker and lease creation

Keep this route compatible:

```http
GET /api/v1/features/v1/lease-tenants/?property_id=property-uuid&offer_id=offer-uuid&page=1&page_size=20
```

`property_id` is required and owned by the caller. `offer_id` is optional for existing property-only callers and required to narrow a specific accommodation. The app passes it when an offer is selected. With no offer filter, return the distinct union of currently eligible tenants for that property; a property-level result does not authorize another offer at draft creation.

Eligibility requires an accepted invitation belonging to the current owner/property/tenant and requested offer, current participant access/verification, valid expiry, unrevoked approval, unchanged approved accommodation terms, and no linked conflicting live draft/lease. Compute eligibility from server truth; do not accept a client-provided `eligible=true` or infer it from a visit status. Apply filtering/deduplication before pagination. Items retain the existing mobile shape:

```json
{"id": "tenant-account-uuid", "display_name": "Tenant name"}
```

Keep the current lease creation request (`property_id`, `tenant_id`, optional `offer_id`, template/version, dates, stored accounting rent, `request_key`). Resolve the matching valid accepted invitation and link it to the new draft. Inside one transaction, authorize ownership and tenant, recheck invitation expiry/revision/terms, lock the relevant invitation/allocation resources, check accommodation availability and duplicate/conflicting drafts, and save `status=draft`. Use database constraints for uniqueness and allocation conflicts. Return the original draft for an identical idempotent retry.

Do not trust a previously displayed picker row, stale cache, or invitation detail. Return a readable eligibility/availability conflict if approval was revoked, expired or consumed between selection and creation. Approval of a draft does not itself generate rent obligations; document which later lease transition allocates inventory and creates ledger/invoices. Preserve invitation and lease snapshots independently of subsequent listing edits.

## Notifications and localization

Use the existing global `Accept-Language: ar|en` convention; localize messages and display fields on the server. Preserve IDs and machine state values across languages. The app renders backend messages directly and scopes read caches by account, language, workspace and resource.

Example notification-center primary action:

```json
{
  "notification_type": "tenancy_invitation",
  "title": "Rental invitation",
  "body": "Review the invitation to proceed with a lease.",
  "actions": {
    "primary": {
      "label": "Review invitation",
      "action_type": "open_tenancy_invitation",
      "target_id": "invitation-uuid"
    }
  },
  "data": {"workspace": "tenant"}
}
```

Owner response notifications use `notification_type=tenancy_invitation_response` and `workspace=owner`. For FCM use string values for `notification_type`, `action_type`, `target_id`, `workspace`, `title`, `body`, and `action_label`. Reuse the existing notification ID/read pipeline. A push is only an entry point; the app fetches authorized invitation details before displaying actions.

## Errors and concurrency

- 400: malformed body/query or invalid decision.
- 401: no valid authentication.
- 403: verification or action permission failure.
- 404: missing/invisible invitation or property; do not expose another account's data.
- 409: stale revision, answered/expired/revoked/duplicate invitation, changed terms, consumed eligibility, allocation conflict, or idempotency mismatch.

Return the existing localized error envelope and meaningful message. Enforce participant checks for every list/detail/mutation, including owner attempting a tenant response and tenant A responding to tenant B's invitation. Use database transactions/constraints, stable idempotency keys, and post-commit notifications. Expiry must be enforced at read/mutation time even if a worker has not updated the persisted status yet.

The confirmed error envelope is `{"message":"Localized error message"}`; success uses `key/msg/data`. The shared response decoder accepts both `message` and `msg`, preserving the existing priority for `message` when both are present. Server text is displayed directly.

## Backend return and staging verification

The returned handoff documents repository/baseline, local migration and implementation status, exact routes and examples, actor/source policies, expiry/revocation, duplicate and cancellation rules, allocation, localization and notifications. Mobile adaptations for those differences are complete. Real authorized legacy fixture IDs are now recorded in the live follow-up. The backend must resolve the live HTTP 500 responses and supply the deployed revision, migration evidence, and successful round trips before enabling the capability.

Supply authorized owner/tenant fixture IDs and evidence for:

1. Owner creates a pending legacy invitation and all four supported offer scopes; wrong property/owner/tenant/offer and stale unavailable offers are rejected.
2. Only the addressed tenant responds; expired/revoked/answered records and changed terms cannot be accepted.
3. Accepted approval appears in the correct owner/property/offer tenant picker; pending/rejected/revoked/expired/consumed approvals do not.
4. Fresh draft creation succeeds and links the invitation; revocation/expiry/availability changes after picker loading are rejected.
5. Concurrent responses/drafts and identical retries produce one logical result and one notification; changed retry payloads conflict.
6. Arabic/English, real empty/error pages, pagination totals, participant privacy and notification navigation work.

The return handoff supplies local implementation and test evidence. Subsequent live checks confirm deployed routes and real legacy fixtures, but invitation creation returns HTTP 500 even after property verification. Resolve the failures and verify round trips on both roles, then build with `--dart-define=SOKOUN_TENANCY_INVITATIONS=true`. Fixture tests and UI preparation alone do not establish successful deployed behavior or production readiness. Lease activation/provider webhook rollout is also a separate backend gap; invitation acceptance and draft creation do not allocate inventory or create invoices.

## Prepared mobile implementation

The app-side code is under `apps/sokoun_app/lib/features/shared/tenancy_invitations/`:

- `data/`: typed invitation/request models, agreed route constants, account/role validation, scoped GET caches and the default-off capability.
- `presentation/cubits/`: explicit loading, fresh accommodation checks before creation, and stable idempotency keys for creation and responses.
- `presentation/screens/` and `widgets/`: owner invitation form, paginated history, participant detail, tenant confirmation actions and the existing lease draft entry point.

Owner request details and both Contracts workspaces expose the new entry points. The existing lease tenant picker accepts the selected offer ID when the capability is enabled; changing the draft accommodation clears the previously selected tenant. Cached invitation details remain readable, but response and draft actions require a fresh authorized result. The owner must review and select a refreshed offer if its terms change before sending.

Focused checks use test-only repository fixtures, never fabricated production invitation data. Reproduce them from `apps/sokoun_app`:

```sh
flutter test --no-pub test/tenancy_invitations_contract_test.dart test/tenancy_invitations_flow_test.dart test/tenancy_invitations_backend_handoff_test.dart test/feature_architecture_test.dart
```

Coverage includes default-off behavior, both owner/tenant entry points, all four rental scopes, acceptance/rejection, changed/expired/unavailable accommodation, identity and revision validation, retry keys, account changes, scoped caches, notification targets, empty history and Arabic/English layouts. Responsive checks cover 320, 390, 600, 768, 1024 and 1366 logical pixels with text scales 1, 1.3 and 2. These are Flutter widget checks; real-device and deployed-backend verification remain part of the returned handoff and staging enablement.

Before the return handoff, local verification on 2026-10-08 using Flutter 3.35.1 passed 75 focused invitation/architecture checks. The app analyzer reported no errors and two existing unused-import warnings. The full app suite reported 3,311 passes, three skips and 23 failures in existing visit/property test fixtures (`collection_endpoint_integration_test`, `collection_request_body_contract_test`, `property_media_handoff_test`, `api_feedback_messages_test`, and `static_data_integration_test`); it was not a clean full-suite result.

Return-handoff alignment also preserves `accepted_at`, `rejected_at` and `revoked_at` in cached invitation models, retains flat notification `data.target_id` as well as projected detail actions, and sends invitation detail reads without an undocumented workspace query. Backend-envelope tests exercise the real Dio/CRUD/cache pipeline with Arabic/English HTTP fixtures; they are not staging tests.

Return-handoff verification on 2026-10-08 using the current Flutter 3.44.7 SDK:

- 90 focused invitation/architecture checks passed, including 15 returned-contract checks.
- Four shared response-decoder checks passed; focused analysis of that decoder/test reported no issues.
- The app analyzer reported no errors, two existing unused-import warnings and four existing deprecation notices.
- The full app suite reported 3,407 passes, three skips and the same 23 failures in the older visit/property fixtures listed above. No invitation tests failed; the full suite remains unsuccessful.
- Arabic/English rendered screens and the six-width/three-text-scale layout matrix passed widget checks. No deployed staging or physical-device round trip was available.

Live recheck on 2026-10-09:

- Both test participants return `is_verified=true`. The test property now returns `status=verified` and `is_verified=true`.
- Invitation histories, the empty eligible tenant picker, and lease configuration return HTTP 200.
- Legacy invitation creation returns HTTP 500 in both Arabic and English. Lease draft creation without accepted eligibility also returns HTTP 500 rather than a localized validation response. Histories remain empty.
- All 90 focused invitation/architecture checks passed on the SDK referenced by the current package configuration, Flutter 3.35.1. These remain local fixture/widget checks.
- The mobile capability remains disabled by default because the live flow is failing. Reproduction details and the remaining verification steps are in [the backend follow-up](TENANCY_INVITATIONS_LIVE_VERIFICATION_FOLLOWUP.md).
