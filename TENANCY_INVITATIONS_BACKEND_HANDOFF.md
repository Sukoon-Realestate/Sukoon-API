# Tenancy invitations and lease eligibility — backend handoff

Date: 2026-10-08  
Status: **Proposed contract; backend implementation and returned handoff required.**  
API base: `/api/v1/`  
Mobile capability: `SOKOUN_TENANCY_INVITATIONS`, disabled by default.

## Purpose and required flow

Owners currently cannot populate the eligible tenant picker. Add an explicit invitation process before drafting a lease:

1. The owner invites a tenant to proceed with a lease for an owned property and, where applicable, a specific rental offer. Validate ownership, tenant identity and accommodation availability. Create a pending invitation.
2. Only the addressed tenant accepts or rejects the invitation. Acceptance records willingness to proceed with a draft and creates lease eligibility for that exact accommodation.
3. The owner opens the tenant picker. Return only tenants with valid accepted invitations for the selected property/offer.
4. The owner creates a lease draft. Recheck invitation eligibility, ownership and current accommodation availability inside the creation transaction before saving.

An accepted viewing, chat message, favorite, or property visit must not create tenancy eligibility. Invitation acceptance does not sign a lease, mark accommodation rented, reserve inventory indefinitely, or create invoices. Those effects belong to documented lease/allocation/ledger transitions.

## Mobile entry points and rollout

- Owner: Requests → request details → **Invite to rent**. The app supplies the actual tenant/property IDs. For rental inventory, the owner chooses a currently available offer from a fresh full-property read; historical viewing snapshots do not authorize an invitation.
- Both workspaces: Contracts → **Rental invitations** → invitation detail.
- Tenant detail: review the owner, property and accommodation, then **Accept invitation** or **Reject invitation**.
- Owner detail: pending/accepted/rejected/expired/revoked status and current lease eligibility. Accepted invitations do not create a lease automatically; continue through the existing Create lease flow.
- Notification: `action_type=open_tenancy_invitation`, a real invitation `target_id`, and explicit `workspace=tenant|owner`.

The app includes a proposed API adapter and fixture coverage. Default builds show an unavailable notice and make no invitation API calls. Enable the capability only after the returned backend handoff and staging verification match this contract. Existing visit acceptance, chat and lease history continue independently.

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

Transitions: `pending → accepted|rejected|revoked|expired`; an accepted invitation may become revoked/expired before use according to the documented policy. Linked lease history retains its snapshot. Define the precise expiry and revocation rules in the returned handoff, including whether a cancelled draft permits a fresh invitation. Do not silently reactivate a rejected/revoked/expired record.

Prevent duplicate live invitations for the same owner/property/tenant/accommodation. A stable identical retry returns its original result. A different request creating an already live invitation returns a readable conflict instead of generating duplicates. Multiple non-overlapping offers under one property remain separate subjects.

## Proposed endpoints

| Method | Path | Authorization |
| --- | --- | --- |
| POST | `features/v1/tenancy-invitations/` | Verified authenticated owner of the property |
| GET | `features/v1/tenancy-invitations/` | Authenticated participant; query workspace and optional property |
| GET | `features/v1/tenancy-invitations/{id}/` | Actual owner or addressed tenant |
| POST | `features/v1/tenancy-invitations/{id}/respond/` | Addressed tenant only |

These names are a proposal, not a claim that deployed routes exist. Return any agreed naming changes before mobile enablement. Owner revocation/admin operations may be added by the backend, but the prepared mobile flow has no revocation mutation.

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

Owner invitations may originate from a viewing relationship or an existing authorized conversation. Validate the eligible source relationship under the agreed product policy; receiving an arbitrary UUID does not authorize access to another account's private information. The prepared first mobile entry uses owner visit request details.

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
    "offer_snapshot": {},
    "status": "pending",
    "revision": 1,
    "created_at": "2026-10-08T12:00:00+03:00",
    "expires_at": "2026-10-15T12:00:00+03:00",
    "accepted_at": null,
    "lease_id": null,
    "eligible_for_lease": false,
    "actions": {"can_respond": true}
  }
}
```

`offer_snapshot: {}` above marks the insertion point for the **complete existing rental snapshot**, not an acceptable production offer snapshot. Offer-specific responses must contain the real property/offer identities, revisions, scope, accommodation names and saved terms. Legacy records omit the snapshot. Names/titles are server-localized/display content, not IDs. `actions` are computed for the authenticated account; only an addressed tenant with a live pending invitation can respond.

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

## Required backend return handoff and verification

Return a Markdown handoff with repository/commit, migration and deployment status, exact routes and request/response examples, actor/verification/source-relationship policies, expiry/revocation rules, duplicate handling, accommodation/lease allocation rules, localization behavior and notification payloads. Identify every deviation from this proposal so the adapter can be updated before enabling the mobile capability.

Supply authorized owner/tenant fixture IDs and evidence for:

1. Owner creates a pending legacy invitation and all four supported offer scopes; wrong property/owner/tenant/offer and stale unavailable offers are rejected.
2. Only the addressed tenant responds; expired/revoked/answered records and changed terms cannot be accepted.
3. Accepted approval appears in the correct owner/property/offer tenant picker; pending/rejected/revoked/expired/consumed approvals do not.
4. Fresh draft creation succeeds and links the invitation; revocation/expiry/availability changes after picker loading are rejected.
5. Concurrent responses/drafts and identical retries produce one logical result and one notification; changed retry payloads conflict.
6. Arabic/English, real empty/error pages, pagination totals, participant privacy and notification navigation work.

After receiving this evidence: update the mobile adapter for any differences, verify staging round trips on both roles, then build with `--dart-define=SOKOUN_TENANCY_INVITATIONS=true`. Fixture tests and UI preparation alone do not establish server implementation or production readiness.
