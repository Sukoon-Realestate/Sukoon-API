# Visit Request Mobile API

All routes are under `/api/v1/properties/`. Authenticated routes use the
project's existing JWT authentication. Responses are wrapped by the shared
renderer as `{ "data": ... }` for GET requests and
`{ "message": "...", "data": ... }` for mutations.

Import [`Sukoon_Visit_Request_Flow.postman_collection.json`](postman/Sukoon_Visit_Request_Flow.postman_collection.json)
into Postman for executable requests and assertions.

## Screen-to-endpoint map

| Screen/action | Method and path |
|---|---|
| Booking days | `GET /<property_id>/available_dates/` |
| Times for one selected date | `GET /<property_id>/available_dates/?date=2026-09-15` |
| Submit a visit request | `POST /<property_id>/visits/` |
| Visit-request cards | `GET /visits/requests/` |
| Filter cards | `GET /visits/requests/?status=confirmed` |
| Visit details | `GET /visits/requests/<visit_id>/` |
| Cancel | `POST /visits/<visit_id>/cancel/` |
| Submit visit rating | `POST /visits/<visit_id>/review/` |

Supported status filters are `pending`, `confirmed`, `rejected`, and
`canceled`. List responses are paginated and accept `page` and `page_size`.

## Book a visit

```json
{
  "visit_date": "2026-09-15",
  "visit_time": "14:00:00",
  "note": "Optional note for the owner"
}
```

The selected time must be an enabled availability slot for that property. A
pending or confirmed booking blocks that property's slot. The `201` response
contains the complete visit summary used by the success screen.

`GET /<property_id>/available_dates/` returns only `days`. After a day is
chosen, call `GET /<property_id>/available_dates/?date=YYYY-MM-DD`; it returns
only that day's `times`.

## Visit card and details contract

The card response includes the property summary, owner name, raw date/time,
Arabic display labels, raw status, Arabic status label, and UI capabilities:

```json
{
  "id": "uuid",
  "property": {
    "id": "uuid",
    "title": "Furnished Apartment",
    "location": "Nasr City, Cairo",
    "price": "6500.00"
  },
  "owner": {"id": "uuid", "name": "Ahmed Mohamed"},
  "day_label": "الثلاثاء 15 سبتمبر",
  "time_label": "2:00 م",
  "status_label": "مقبول",
  "actions": {
    "can_cancel": true,
    "can_chat": true,
    "can_review": false,
    "can_find_alternative": false
  },
  "alternative_search_filters": null
}
```

Rejected cards return `alternative_search_filters` containing property type,
governorate, and city values that can be passed to the property search API.
Details additionally include raw `visit_date`, `visit_time`, `status`, `note`,
`review`, and owner contact fields.
`phone_number` and `masked_phone_number` are empty until the owner confirms
the request.

`can_chat` expresses whether the visit is eligible for owner chat. The
screens supplied for this feature did not define a chat/message contract, so
message storage and delivery are intentionally outside this API.

## Submit a rating

Only the visit's tenant can rate it. The visit must be confirmed, its scheduled
date/time must have passed, and it can be rated only once.

```json
{
  "overall_rating": 4,
  "cleanliness_rating": 4,
  "listing_accuracy_rating": 5,
  "owner_interaction_rating": 4,
  "comment": "The apartment matched the listing."
}
```

Every score is required and must be an integer from 1 through 5. `comment` is
optional. The overall score also updates the existing aggregate property
rating used by property cards and details.
