# Mobile Handoff: Owner Banner Advertisements

Date: 2026-10-10  
Backend scope: implemented locally under `/api/v1/advertising/v1/`

## Readiness

The Django API, migrations, seeded plans, protected media delivery, mock activation, public tenant-home feed, operation recovery, expiry maintenance, admin registration, and automated tests are implemented.

This handoff does **not** claim that the code is deployed. Before enabling the mobile capability in a shared environment, backend operations must deploy the revision, run both advertising migrations, configure durable shared media storage behind HTTPS, run Celery beat/workers (or the expiry command), and complete the two-account staging test described at the end.

No real payment occurs. The payment endpoint records `mock_succeeded`, activates the advertisement, and never creates a rent invoice, receipt, settlement, subscription, renewal, or card session.

## Base path and common behavior

```text
/api/v1/advertising/v1/
```

JSON successes use:

```json
{"key":"success","message":"...","data":{}}
```

JSON errors use:

```json
{"key":"error","message":"...","data":null,"errors":{"field":["stable_code"]}}
```

- Send `Accept-Language: ar` or `en`. The response includes `Content-Language` and `Vary: Accept-Language`.
- Private endpoints accept the existing bearer token or `access` cookie through the normal backend authentication class.
- Private JSON responses use `Cache-Control: no-store`.
- Public plans and feed responses use short revalidating cache headers.
- Advertisement and property IDs are UUID strings.
- All returned instants are RFC3339 UTC strings ending in `Z`.

## Endpoints

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `GET` | `plans/` | Public | Active purchasable plans |
| `POST` | `owner-advertisements/` | Required | Multipart create/upload |
| `GET` | `owner-advertisements/?page=1&page_size=20` | Required | Current owner's ads |
| `GET` | `owner-advertisements/{advertisement_id}/` | Required | Current owner's ad detail |
| `POST` | `owner-advertisements/{advertisement_id}/mock-payment/` | Required | Idempotent simulated activation |
| `GET` | `operations/{operation_id}/` | Required | Recover an unknown create outcome |
| `GET` | `placements/tenant-home/` | Public | Current public carousel window, maximum 20 |
| `GET` | `media/{advertisement_id}/` | Conditional | Owner-only while pending; public while active and eligible |

## 1. Plans

```http
GET /api/v1/advertising/v1/plans/
```

The server seeds these initial IDs and values:

| ID | Duration | Minor amount | Display amount |
| --- | --- | ---: | ---: |
| `weekly` | 1 `week` | `100000` | EGP 1,000 |
| `monthly` | 1 `calendar_month` | `300000` | EGP 3,000 |
| `yearly` | 1 `calendar_year` | `3000000` | EGP 30,000 |

Example data:

```json
{
  "results": [
    {
      "id": "weekly",
      "title": "Weekly",
      "duration_unit": "week",
      "duration_count": 1,
      "revision": "1",
      "active": true,
      "price": {"amount_minor": 100000, "currency": "EGP", "exponent": 2}
    }
  ]
}
```

Use the returned values as authoritative. Do not hard-code prices or infer display title from the ID. An empty `results` array is valid.

## 2. Create and upload

```http
POST /api/v1/advertising/v1/owner-advertisements/
Content-Type: multipart/form-data
```

Fields:

```text
operation_id: <stable client-generated ID, maximum 128 characters>
plan_id: weekly
plan_revision: 1
title: New accommodation in Maadi
description: Optional text
banner: <JPEG, PNG, or WebP bytes>
property_id: <optional UUID>
offer_id: <optional stable offer ID; requires property_id>
```

Validation:

- `title`: trimmed, required, maximum 150 characters.
- `description`: trimmed, optional, maximum 500 characters.
- `banner`: decoded content must be JPEG, PNG, or WebP; maximum 10 MiB. Filename and client MIME do not determine acceptance.
- Recommended `3:1` dimensions are presentation guidance, not a rejection rule.
- A linked property must belong to the caller and have backend status `verified`.
- A linked offer must exist in that property's current `rental_inventory`, be unarchived, and have `availability=available`.
- The plan must still be active and its current `revision` must equal `plan_revision`.

First success is HTTP `201`; an exact idempotent replay is HTTP `200`. Both return a full private advertisement with `status=pending_payment`, null dates, immutable `plan_snapshot`, and null `payment`.

The server fingerprints the normalized plan, revision, title, description, destination IDs, and image bytes. Reusing the same owner/`operation_id` with changed content returns HTTP `409` and `errors.operation_id=["idempotency_conflict"]`. Do not hide that conflict by generating a replacement ID.

Important media behavior: `banner_url` is an API URL. While the ad is pending, it requires the owning session. After valid activation it is public. For the pre-submit/review UI, continuing to render the local draft file avoids relying on authenticated image headers.

## 3. Simulated payment

```http
POST /api/v1/advertising/v1/owner-advertisements/{advertisement_id}/mock-payment/
Content-Type: application/json

{
  "operation_id": "<create-operation-id>-payment",
  "payment_mode": "mock"
}
```

On success, the response contains:

```json
{
  "status": "active",
  "starts_at": "2026-10-10T10:00:00Z",
  "ends_at": "2026-10-17T10:00:00Z",
  "payment": {
    "id": "<uuid>",
    "advertisement_id": "<uuid>",
    "operation_id": "<create-operation-id>-payment",
    "payment_mode": "mock",
    "status": "mock_succeeded"
  }
}
```

The transaction locks the advertisement, rechecks owner/destination/media eligibility, writes exactly one mock payment, and activates with dates. Retrying after success returns the same advertisement, payment ID, and dates, including after natural expiry. Never calculate or extend `ends_at` on the client.

Duration rules:

- `week`: exactly 604800 elapsed seconds per count.
- `calendar_month`: calendar addition in `Africa/Cairo`, clamped to the target month's last day.
- `calendar_year`: calendar addition in `Africa/Cairo`, with February 29 clamped to February 28 when needed.
- DST gaps move forward to the next valid local instant; overlaps use the later occurrence.

## 4. Owner list and detail

The list returns:

```json
{
  "count": 1,
  "results": ["<full private advertisement>"]
}
```

Ordering is `created_at DESC, id DESC`. `page_size` defaults to 20 and is capped at 100. Another owner's ID returns `404`; an expired/invalid session returns `401`. The API reports effective `expired` status immediately when `server_now >= ends_at`, even if the maintenance worker has not persisted the status yet.

## 5. Operation recovery

```http
GET /api/v1/advertising/v1/operations/{operation_id}/
```

Possible `data.state` values:

- `found`: `advertisement` is the full private object; never upload the image again.
- `processing`: `advertisement=null`, `retry_allowed=false`; wait and look up again.
- `not_found`: `advertisement=null`, `retry_allowed=true`; no committed advertisement exists for this owner/ID.
- `rejected`: `advertisement=null`, `retry_allowed=true`; correct the input, re-review the current plan, then resubmit.

The lookup is owner-scoped. The same text ID in another account cannot reveal the first account's operation.

## 6. Tenant-home placement

```http
GET /api/v1/advertising/v1/placements/tenant-home/
```

Data shape:

```json
{
  "server_now": "2026-10-10T10:00:30Z",
  "results": [
    {
      "id": "<uuid>",
      "title": "New accommodation in Maadi",
      "description": "Optional text",
      "banner_url": "https://<api-host>/api/v1/advertising/v1/media/<uuid>/",
      "property_id": "<optional uuid>",
      "offer_id": "<optional offer id>",
      "status": "active",
      "starts_at": "2026-10-10T10:00:00Z",
      "ends_at": "2026-10-17T10:00:00Z"
    }
  ]
}
```

The feed is public and shared across accounts. It returns at most 20 ads ordered by `starts_at DESC, id DESC`. It excludes pending, unpaid, expired, inactive-owner, missing-media, wrong-placement, and destination-ineligible ads. It never returns owner ID, operation ID, plan/price, or payment data.

Treat empty and failed feed reads as a hidden section, not a Home failure. Continue using `server_now` plus elapsed time for client-side removal until the next refresh. Use `property_id` and exact `offer_id` with the existing destination resolver; an informational banner with both null has no navigation action. Do not interpret `banner_url` as an external click destination.

## Stable error codes relevant to mobile

| HTTP | Code location | Meaning/action |
| --- | --- | --- |
| `400` | `property_id: not_eligible` | Keep draft; select an eligible owned property or remove destination |
| `400` | `offer_id: property_required` | Offer cannot be sent without a property |
| `400` | `offer_id: not_eligible` | Refresh property inventory and reselect |
| `400` | `plan_id: not_available` | Refresh plans |
| `400` | `operation_id: invalid_payment_operation` | Rebuild payment ID from the saved create operation |
| `409` | `plan_revision: plan_changed` | Refresh plan and require review before create retry |
| `409` | `operation_id: idempotency_conflict` | Reconcile; do not create a new ID automatically |
| `409` | `operation_id: operation_processing` | Poll operation lookup |
| `409` | `status: invalid_transition` | Refresh advertisement detail |
| `413` | `banner: too_large` | Choose an image at or below 10 MiB |
| `415` | `banner: invalid_image` / `unsupported_type` | Choose valid decoded JPEG/PNG/WebP bytes |

Also handle normal `401`, `403`, `404`, timeout, and `5xx` behavior. On an ambiguous create response, call operation lookup. On an ambiguous payment response, call advertisement detail first. Never infer success from HTTP `200` alone: validate `key`, IDs, operation IDs, status, payment mode/status, destination, snapshot, and dates as the current Flutter flow already does.

## Backend deployment checklist

1. Deploy the backend revision.
2. Run `python manage.py migrate`; confirm `advertising.0001` and `advertising.0002` are applied.
3. Confirm the three seeded plans and intended prices/revisions in admin.
4. Configure durable, shared `MEDIA_ROOT` storage and an HTTPS API origin. Local ephemeral disk is not sufficient for multiple production instances.
5. Run Celery beat/workers with `core_apps.advertising.tasks.expire_advertisements`, or schedule `python manage.py expire_advertisements`. Feed correctness does not depend on worker timing, but stored status maintenance does.
6. Confirm proxy scheme forwarding makes returned `banner_url` use HTTPS.
7. Do not enable the mobile capability until staging returns all endpoints and images successfully.

## Required staging acceptance

- Owner A creates an informational banner, loses/retries a response, recovers one record, activates it, and receives identical dates on payment retry.
- Guest and Tenant B fetch the public feed and image without Owner A's session.
- Repeat with Owner A's verified property and a specific available offer; tapping from Tenant B opens that exact offer.
- Owner B cannot read, pay, or fetch pending media for Owner A's ad.
- Changed-body reuse returns `idempotency_conflict`; bad/oversized/fake images and invalid destinations remain real errors.
- Move `ends_at` into the past without running the worker: feed omits the ad and owner detail reports `expired`.
- Repeat key responses in Arabic and English and confirm the mobile UI in RTL/LTR and both themes.

## Local verification completed

- Django system check: passed.
- Migration drift check: passed.
- Advertising tests: 9 passed.
- Complete backend suite: 568 passed, 6 skipped.
- New advertising package lint: passed. Existing shared settings lint warnings remain unchanged.
