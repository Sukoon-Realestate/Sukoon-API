# Tenancy Invitations — Backend Return Handoff

Date: 2026-10-08  
Repository: `Sukoon-API`  
Branch inspected: `main`  
Baseline commit inspected: `8e371ef`  
Delivery form: uncommitted working-tree implementation based on that commit  
Status: **Implemented and verified locally. Migrations have not been deployed to staging and real staging fixture IDs are not yet available. Keep `SOKOUN_TENANCY_INVITATIONS` disabled until staging verification is complete.**

## Backend understanding

The backend will add an explicit owner-to-tenant invitation before lease drafting. Acceptance grants temporary eligibility only for the exact property/accommodation and approved terms. It does not sign a lease, reserve inventory, mark an offer rented, or create invoices.

The implemented backend no longer uses broad `LeaseEligibleTenant` rows for picker or draft authorization. `GET lease-tenants/` is invitation-backed, and lease creation locks, revalidates, consumes, and links the exact invitation atomically.

## Agreed routes

No route rename is planned.

| Method | Route | Actor |
| --- | --- | --- |
| POST | `/api/v1/features/v1/tenancy-invitations/` | Verified current property owner |
| GET | `/api/v1/features/v1/tenancy-invitations/` | Participant selected by `workspace=owner|tenant` |
| GET | `/api/v1/features/v1/tenancy-invitations/{id}/` | Actual owner or addressed tenant |
| POST | `/api/v1/features/v1/tenancy-invitations/{id}/respond/` | Addressed verified tenant only |
| GET | `/api/v1/features/v1/lease-tenants/` | Verified current owner of `property_id` |
| POST | `/api/v1/features/v1/leases/` | Verified current owner |

Successful responses retain the existing envelope:

```json
{"key":"success","msg":"Localized message","data":{}}
```

Errors retain the backend's current localized envelope:

```json
{"message":"Localized error message"}
```

## Create request and response

Rental inventory v1:

```http
POST /api/v1/features/v1/tenancy-invitations/
Accept-Language: en
Authorization: Bearer <owner-token>
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

Planned HTTP 201 data:

```json
{
  "id": "invitation-uuid",
  "property_id": "property-uuid",
  "property_title": "Property title",
  "owner_id": "owner-account-uuid",
  "owner_name": "Owner name",
  "tenant_id": "tenant-account-uuid",
  "tenant_name": "Tenant name",
  "offer_id": "offer-uuid",
  "offer_snapshot": {
    "property_id": "property-uuid",
    "offer_id": "offer-uuid",
    "offer_revision": 7,
    "rental_scope": "bed",
    "name": "Bed name",
    "room_ids": ["room-uuid"],
    "room_names": ["Room name"],
    "bed_id": "bed-uuid",
    "bed_name": "Bed name",
    "capacity": 2,
    "bathroom_access": ["shared"],
    "availability": "available",
    "archived": false,
    "offer_link": "",
    "terms": {}
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
  "actions": {"can_respond": false}
}
```

Legacy properties omit `offer_id` and `expected_offer_revision`; the response returns an empty/null `offer_id` and `offer_snapshot: null`.

## Collection and detail

```http
GET /api/v1/features/v1/tenancy-invitations/?workspace=tenant&page=1&page_size=20
GET /api/v1/features/v1/tenancy-invitations/?workspace=owner&property_id=property-uuid&page=1&page_size=20
GET /api/v1/features/v1/tenancy-invitations/invitation-uuid/
```

Filtering by participant and authorized property occurs before counting. Items are ordered by descending creation time and descending ID. All historical states remain visible. Empty success is:

```json
{
  "key": "success",
  "msg": "",
  "data": {
    "results": [],
    "count": 0,
    "per_page": 20,
    "total_pages": 1,
    "next": null,
    "previous": null
  }
}
```

`actions.can_respond` is true only for the addressed tenant while the invitation is effectively pending and current. Non-participants receive 404.

## Tenant response

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

The result is HTTP 200 with the complete invitation, revision 2, and `accepted_at` or `rejected_at`. An accepted response returns `eligible_for_lease=true` only if all current eligibility checks pass.

Authorization is checked before idempotency replay. An identical retry returns the original response. Reusing a key with another body returns 409. A different request after a completed response also returns 409.

## Actor, verification, and source policy

- Both accounts must be active and `is_verified=true`.
- Owner identity is derived from authentication and must equal the property's current owner.
- Tenant identity must resolve to another active, verified account.
- For the first release, the owner/tenant pair must have an existing `PropertyVisit` for the exact property with status `pending` or `confirmed`.
- Rejected or cancelled visits do not authorize invitation creation.
- Chat-only invitation sourcing is deferred. Current conversations do not identify a property, so using chat participation alone would not safely authorize disclosure for a specific listing.
- Favorites, messages, accepted visits, and property views never create lease eligibility; the visit is only the privacy-safe source relationship allowing the owner to send an invitation.

## Expiry, revocation, duplicate, and cancellation policy

- `expires_at` is server time plus seven days.
- Pending and accepted-but-unconsumed invitations expire at that instant.
- Expiry is enforced on every read/mutation even if a cleanup worker has not persisted `status=expired` yet.
- Pending invitations can be revoked. Accepted invitations can be revoked only before they are linked to a lease.
- Ownership loss, inactive/unverified participants, changed offer revision/terms, archive/unavailability, or an allocation conflict immediately removes effective eligibility and may persist revocation/expiry during cleanup.
- Rejected, revoked, and expired invitations are never reactivated.
- Only one pending or accepted-unconsumed invitation may exist per owner/property/tenant/accommodation.
- Same `request_key` and body replay the original result; a changed body conflicts. A different key targeting a live duplicate conflicts.
- A cancelled draft leaves its original invitation linked and consumed. A fresh invitation is allowed afterward if the accommodation is currently available.

## Tenant picker and lease allocation

`GET /api/v1/features/v1/lease-tenants/?property_id=...&offer_id=...` keeps its existing item shape:

```json
{"id":"tenant-account-uuid","display_name":"Tenant name"}
```

With `offer_id`, only exact-offer invitations qualify. Without it, the result is the distinct union for the property, but that row does not authorize a different offer during draft creation.

Lease creation will resolve and lock one matching accepted invitation, recheck its expiry and terms, current ownership/accounts, offer availability, and conflicting live leases, then create and link the draft in one transaction. The invitation and lease keep independent snapshots. A stale picker result returns 409 instead of creating a draft.

Draft creation does not allocate inventory or create invoices. The agreed allocation point is the later transition to `active`, after required signatures/authorization: that transaction must lock the allocation, mark the exact offer rented/unavailable, and generate the initial invoice schedule. The current feature module does not yet contain a production activation/provider-webhook flow, so this is a separate end-to-end leasing rollout gap rather than an effect of invitation acceptance.

## Notifications

Tenant notification-center payload:

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

Owner response notifications use `notification_type=tenancy_invitation_response` and `workspace=owner`. FCM receives string values for `notification_type`, `action_type`, `target_id`, `workspace`, `title`, `body`, and `action_label`. Notifications are recorded once per logical transition and push dispatch starts only after commit.

Internally, the existing notification model stores the action values flat in `Notification.data`; the notification detail serializer projects them into the `actions.primary` response shown above.

Messages, display content, and notification text will support `Accept-Language: ar|en`. IDs and state values are never localized.

## HTTP errors

- 400: malformed query/body, missing required fields, or invalid decision.
- 401: missing/invalid authentication.
- 403: authenticated but unverified or not permitted to perform the action.
- 404: missing/invisible property or invitation; used to preserve participant privacy.
- 409: stale revision, duplicate live invitation, answered/revoked/expired state, changed terms, consumed eligibility, allocation conflict, or idempotency mismatch.

## Deviations and clarifications from the mobile proposal

1. Source policy is narrowed to a `pending` or `confirmed` visit for the exact property in the first release; chat-only sourcing is deferred.
2. Full invitation responses will always include `rejected_at` and `revoked_at`; the example omitted them.
3. Cancelled drafts do not release/reactivate the old invitation. They permit a new invitation.
4. The current backend error envelope is `{"message":"..."}`. Success remains `key/msg/data`.
5. Existing `LeaseEligibleTenant` records will not be converted into invitations because they do not prove tenant consent or exact-offer approval.

## Implementation files

- `backend/core_apps/features/models.py`: invitation persistence and live lease/invitation constraints.
- `backend/core_apps/features/services/tenancy_invitations.py`: source, account, snapshot, lifecycle, eligibility, and notification rules.
- `backend/core_apps/features/serializers.py`: create/respond/full invitation contracts.
- `backend/core_apps/features/views.py` and `urls.py`: four invitation routes, invitation-backed picker, and transactional lease creation.
- `backend/core_apps/features/migrations/0002_tenancyinvitation_alter_lease_options_and_more.py`.
- `backend/core_apps/notifications/models/notification.py` and migration `0004_alter_notification_notification_type.py`.
- `backend/core_apps/features/tests/test_tenancy_invitations.py`: legacy, all four offer scopes, authorization, lifecycle, idempotency, picker, draft, notifications, pagination, and privacy coverage.

## Delivery status and evidence

| Item | Status |
| --- | --- |
| Contract review | Complete |
| Implementation plan | Complete: `docs/TENANCY_INVITATIONS_BACKEND_IMPLEMENTATION_PLAN.md` |
| Models/migration | Implemented; migration generated and exercised by test database |
| Endpoints | Implemented locally at the agreed paths |
| Picker/lease integration | Implemented locally with invitation linking and database conflict protection |
| Automated verification | Passing locally; see commands/results below |
| Staging migration/deployment | Not deployed |
| Authorized fixture IDs | Not available yet |
| Mobile capability | Must remain disabled |

Local verification on 2026-10-08:

```text
python manage.py check                                      passed
python manage.py makemigrations --check --dry-run           no changes detected
pytest core_apps/features/tests/test_tenancy_invitations.py 13 passed
pytest -q                                                   497 passed, 3 skipped
flake8 on all changed Python files                           passed
```

The test database exercised the migrations and the complete owner → tenant → picker → draft flow.

The backend must still provide real owner/tenant/property/offer/invitation fixture IDs and staging evidence for the six requested verification groups after deployment. Local test fixtures are intentionally not presented as deployed identities or production-readiness evidence.
