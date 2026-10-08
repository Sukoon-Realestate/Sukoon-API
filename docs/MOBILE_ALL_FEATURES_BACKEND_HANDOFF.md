# Sokoun mobile backend handoff — implemented features

Date: 2026-10-08
API prefix: `/api/v1/`
Feature prefix: `/api/v1/features/v1/`
Rental inventory version: `1`

## 1. Integration status

The backend implementation and migrations are complete locally. It has not been deployed to staging by this change.

Mobile can integrate and test the API/persistence contracts below against a deployed backend. Keep provider- and worker-dependent capabilities disabled until staging confirms the items in section 8.

All product tools are free. Rent checkout is only for the amount on a real server-authorized invoice.

## 2. Response conventions

Successful `features/v1` responses use:

```json
{
  "key": "success",
  "msg": "",
  "data": {}
}
```

Feature collections return this inside `data`:

```json
{
  "results": [],
  "count": 0,
  "per_page": 20,
  "total_pages": 1,
  "next": null,
  "previous": null
}
```

Errors retain the existing non-success shape and appropriate HTTP status:

```json
{"message": "Readable error message"}
```

IDs are opaque UUID strings. Instants are time-zone-aware ISO 8601 values. Lease and invoice money uses integer minor units:

```json
{"amount_minor": 1200000, "currency": "EGP", "exponent": 2}
```

## 3. Free-feature endpoints

| Method | Path | Mobile use |
|---|---|---|
| GET | `features/v1/configuration/` | Query `workspace=owner|tenant&lang=ar|en`. Returns free boost options or alert cadences. |
| GET | `features/v1/boost-campaigns/` | Owner campaign history with normal pagination. |
| POST | `features/v1/boost-campaigns/` | Body: `property_id`, `option_id`, `request_key`. |
| GET | `features/v1/search-alerts/` | Current account's non-deleted alerts. |
| POST | `features/v1/search-alerts/` | Body: `name`, `cadence`, complete `filters`, `request_key`. |
| GET | `features/v1/search-alerts/{id}/` | Authorized alert details. |
| PATCH | `features/v1/search-alerts/{id}/` | Body: `enabled`, `revision`, `request_key`. Stale revision returns `409`. |
| DELETE | `features/v1/search-alerts/{id}/` | JSON body: `revision`, `request_key`. Returns a cancellation receipt. |
| GET | `features/v1/owner-analytics/{property_id}/` | Query `period_days=7|30|90`. Owner-only measured metrics. |
| POST | `features/v1/listing-suggestions/` | Facts-only ar/en listing suggestion with `request_key`. |
| GET | `features/v1/lease-configuration/` | Returns creation permission and approved templates. |
| GET | `features/v1/lease-tenants/` | Query owned `property_id`; returns explicitly eligible tenants. |
| GET | `features/v1/leases/` | Query `workspace`, optional `property_id`, and paging. |
| POST | `features/v1/leases/` | Creates a draft using template, tenant, dates, minor-unit rent, request key, and optional `offer_id`. |
| GET | `features/v1/leases/{id}/` | Authorized participant detail. |
| POST | `features/v1/leases/{id}/signing-session/` | Body: `revision`, `request_key`. |
| POST | `features/v1/leases/{id}/cancel/` | Owner-only draft cancellation using `revision` and `request_key`. |
| GET | `features/v1/rent-invoices/` | Query `workspace`; optional `lease_id`, comma-separated `status`, `ordering`, and paging. |
| GET | `features/v1/rent-invoices/{id}/` | Authorized owner/tenant invoice detail. |
| POST | `features/v1/rent-invoices/{id}/checkout/` | Body: matching `invoice_id` and `request_key`. Tenant-only. |

### Idempotent mutations

For feature mutations, generate one stable UUID `request_key` per logical action. Reuse it for retries. Reusing the key with a changed payload returns `409`.

## 4. Rental inventory integration

### Owner create and edit

Existing endpoints remain:

- `POST properties/create/`
- `GET/PATCH properties/{property_id}/`

For a rental-inventory create, send:

```text
X-Rental-Offers-Version: 1
Idempotency-Key: <stable draft submission UUID>
```

The multipart field `rental_inventory` contains JSON with:

- `schema_version: 1`
- `mode: whole|partial`
- `expected_revision`
- `rooms`, nested `beds`, `shared_defaults`, `shared_media_ids`, and `offers`

New rooms, beds, and offers use a local `client_key`. The backend returns permanent `id` values while echoing client keys. Persist those IDs in the mobile draft after a successful response.

The backend supports these scopes:

- `entire_property`
- `room`
- `room_group`
- `bed`

The full saved property response includes resolved `terms`, stable IDs, inventory revision, offer revisions, availability, archive state, media references, links, and owner actions.

Mobile must retain entered data and refresh on validation or conflict errors. Important conflicts include stale inventory revision and overlapping room/bed allocation.

### Discovery and owner collections

`GET properties/` and `GET homepage/` return:

- `rental_schema_version`
- `rental_summary.eligible_count`
- `rental_summary.scopes`
- `rental_summary.labels`
- `rental_summary.price`
- `rental_summary.price_period`
- `rental_summary.price_scope`
- `rental_summary.starting_from`

Use `rental_scope=entire_property|room|room_group|bed` to filter physical properties before pagination.

`GET properties/owned/` supports the same `rental_scope` filter and returns `rental_scopes` plus `manageable_offer_count`.

When eligible offers have mixed price periods, the backend returns no combined minimum. Mobile must ask the user to select an offer rather than comparing incompatible periods.

### Exact-offer favorites

Save:

```http
POST properties/{property_id}/save/
Content-Type: application/json

{"offer_id": "offer-id"}
```

Remove:

```http
DELETE properties/{property_id}/unsave/
Content-Type: application/json

{"offer_id": "offer-id"}
```

The response echoes `offer_id` and `is_saved`. Multiple offers under one property are independent. Saved results include exact `saved_offers` snapshots.

### Offer-aware visits

Send:

```json
{
  "visit_date": "2026-10-10",
  "visit_time": "11:00:00",
  "note": "Tenant note",
  "offer_id": "offer-id",
  "expected_offer_revision": 7
}
```

The backend validates current availability/revision and stores an immutable `offer_snapshot`. Viewing acceptance or rejection never changes rental availability or creates a lease.

### Availability freshness

Owners confirm current availability with:

```http
POST properties/{property_id}/confirm-availability/
```

Use the returned `availability_confirmed_at`. Do not substitute `updated_at`.

## 5. Lease and invoice offer context

For a property containing rental inventory, lease creation requires an available `offer_id`. The backend returns and preserves `offer_id` plus `offer_snapshot` on the lease and related invoices.

Do not derive lease rent or invoice amounts from the current listing price. Display the stored accounting amount returned by the lease/invoice API.

Only the invoice's tenant can create checkout. The backend ignores client-supplied amounts and returns its stored quote.

## 6. Chat message reliability

REST and WebSocket message creation accept an optional UUID `client_message_id`.

REST body:

```json
{"content": "Hello", "client_message_id": "client-generated-uuid"}
```

WebSocket body:

```json
{
  "type": "message.send",
  "conversation_id": "conversation-id",
  "content": "Hello",
  "client_message_id": "client-generated-uuid"
}
```

Generate the ID once per logical outgoing message and reuse it for every WebSocket/REST retry. The backend deduplicates by conversation, sender, and client ID. Reusing an ID with different content is rejected.

For sends containing the ID, WebSocket returns:

```json
{
  "type": "message.ack",
  "payload": {
    "id": "server-message-id",
    "client_message_id": "client-generated-uuid",
    "status": "sent"
  }
}
```

Replace the local pending message with the authoritative message using `client_message_id`. Other participants continue receiving `message.new`.

## 7. Mobile error handling

- `400`: malformed, missing, or general validation input.
- `401/403`: authentication, ownership, participant, or action permission failure.
- `404`: missing or invisible cross-account resource.
- `409`: request-key or revision conflict; retain local state and refresh.
- `422`: explicitly unsupported rental version or unavailable saved-offer selection where the endpoint distinguishes semantic validation.

Never treat ignored/missing offer identity as a successful rental operation. Confirm returned property, offer, lease, invoice, and subject IDs before showing success.

## 8. Keep disabled until staging/provider confirmation

The persistence/API foundations exist, but these capabilities are not production-ready yet:

- Real payment settlement and authenticated payment webhooks.
- Real digital-signature completion and authenticated signing webhooks.
- External AI provider execution; current backend behavior is a bounded facts-only fallback.
- Search-alert matching, quiet-hours, deduplication and push worker.
- Campaign expiry and impression-counting worker.
- Scheduled invoice generation.
- Signed analytics exports, lease documents and receipt URLs.
- Production Android App Links and iOS Universal Links hosting/configuration.
- Rental media-association capability until staging confirms foreign/deleted/private-media validation.

Do not enable a mobile capability merely because its route responds. Enable each operation only after its staging round trip and dependencies are confirmed.

## 9. Backend verification

Local backend verification completed:

- 484 tests passed.
- 3 tests skipped.
- Django system check passed.
- Migration drift check passed.
- WebSocket tests pass without Daphne; production remains Gunicorn with `UvicornWorker`.

For backend implementation details and outstanding production work, see `SOKOUN_ALL_FEATURES_BACKEND_DELIVERY.md` and `SOKOUN_ALL_FEATURES_BACKEND_PLAN.md`.
