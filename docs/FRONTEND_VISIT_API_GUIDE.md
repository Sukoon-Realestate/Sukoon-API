# Frontend Visit API Guide

This is the integration reference for the visit-request, tenant booking, and
owner availability screens. Every endpoint is under
`/api/v1/properties/`.

Authenticated endpoints use the app's existing cookie-based JWT session. The
shared response envelope is:

- `GET`: `{ "data": ... }`
- `POST` / `PUT` / `PATCH`: `{ "message": "...", "data": ... }`
- Errors: `{ "message": "..." }`

An executable Postman collection is available at
[`postman/Sukoon_Visit_Request_Flow.postman_collection.json`](postman/Sukoon_Visit_Request_Flow.postman_collection.json).

## Tenant booking flow

### 1. Load bookable days

`GET /<property_id>/available_dates/`

Authentication is optional. This returns only days with enabled future slots.

```json
{
  "data": {
    "days": [
      {
        "day": "monday",
        "date": "7/9",
        "visit_date": "2026-09-07"
      }
    ]
  }
}
```

Use `visit_date` in the next request.

### 2. Load times for the selected day

`GET /<property_id>/available_dates/?date=2026-09-07`

```json
{
  "data": {
    "times": [
      {
        "time": "9:00 AM",
        "visit_time": "09:00:00",
        "is_available": true
      }
    ]
  }
}
```

Only submit a time where `is_available` is `true`. Use `visit_time` in the
booking payload.

### 3. Create a visit request

`POST /<property_id>/visits/`

```json
{
  "visit_date": "2026-09-07",
  "visit_time": "09:00:00",
  "note": "Optional note to the owner"
}
```

Requires authentication. A `201` response contains the visit summary used by
the success screen. Booking is rejected if the selected slot is no longer
available.

## Tenant visit requests

### List request cards

`GET /visits/requests/`

Optional filter: `?status=pending`, `confirmed`, `rejected`, or `canceled`.
The response is paginated.

```json
{
  "data": {
    "per_page": 10,
    "total_pages": 1,
    "results": [
      {
        "id": "visit-uuid",
        "property": {
          "id": "property-uuid",
          "title": "Cozy Studio Near Metro Station",
          "location": "Maadi, Cairo",
          "price": "7000.00"
        },
        "owner": {"id": "owner-uuid", "name": "Zeyad Mohammed"},
        "day_label": "الإثنين 7 سبتمبر",
        "time_label": "9:00 ص",
        "status_label": "بانتظار رد المالك",
        "actions": {
          "can_cancel": true,
          "can_chat": false,
          "can_review": false,
          "can_find_alternative": false
        },
        "alternative_search_filters": null
      }
    ]
  }
}
```

Use `actions` to decide which buttons to show. If a rejected request has
`alternative_search_filters`, pass its values to the property-search API.

### Request details

`GET /visits/requests/<visit_id>/`

This contains the list-card fields plus raw `visit_date`, `visit_time`,
`status`, `note`, `review`, and owner contact details. Owner phone fields are
empty until the request is confirmed.

### Cancel a request

`POST /visits/<visit_id>/cancel/`

Body: `{}`

Only the tenant who owns the request can cancel it.

### Rate a completed visit

`POST /visits/<visit_id>/review/`

```json
{
  "overall_rating": 4,
  "cleanliness_rating": 4,
  "listing_accuracy_rating": 5,
  "owner_interaction_rating": 4,
  "comment": "Optional feedback"
}
```

Only the tenant can submit this once, after a confirmed visit's scheduled time
has passed. Every rating is an integer from 1 to 5.

## Owner availability per property

Availability is scoped to a property. The owner must use an ID from their
owned-property list; one property's slots never affect another property's
slots.

### Show bookable slots in a seven-day window

`GET /owner/properties/<property_id>/availability/?start_date=2026-09-07`

`start_date` is optional. The API returns only dates with bookable slots and
only slots with `state: "available"`.

```json
{
  "data": {
    "week_start": "2026-09-07",
    "week_end": "2026-09-13",
    "days": [
      {
        "date": "2026-09-07",
        "day": "monday",
        "slots": [
          {
            "id": "slot-uuid",
            "time": "09:00:00",
            "is_enabled": true,
            "state": "available",
            "visit": null
          }
        ]
      }
    ]
  }
}
```

### Save one date's slots

`PUT /owner/properties/<property_id>/availability/`

```json
{
  "availability_date": "2026-09-07",
  "slots": [
    {"time": "09:00:00", "is_enabled": true},
    {"time": "12:00:00", "is_enabled": true},
    {"time": "16:00:00", "is_enabled": false}
  ]
}
```

This atomically replaces that property's unbooked slots for
`availability_date`:

- Included times are created or updated.
- Omitted unbooked times are removed.
- Booked times remain unchanged and cannot be disabled.
- Submitted times must be future times.

## Owner visit calendar

`GET /owner/calendar/?year=2026&month=9&date=2026-09-07`

`year` and `month` are required; `date` is optional and must be inside the
selected month. This endpoint shows actual pending or confirmed visit requests,
not availability slots.

```json
{
  "data": {
    "year": 2026,
    "month": 9,
    "days": [
      {"date": "2026-09-07", "day": 7, "visit_count": 2}
    ],
    "selected_date": "2026-09-07",
    "visits": [
      {
        "id": "visit-uuid",
        "tenant": {"id": "tenant-uuid", "name": "Mohamed Ahmed"},
        "property": {"id": "property-uuid", "title": "Cozy Studio"},
        "visit_time": "09:00:00",
        "status": "pending"
      }
    ]
  }
}
```
