# Owner Visit Calendar and Availability API

All routes are under `/api/v1/properties/` and require the authenticated
owner's JWT cookie.

## Monthly visit calendar

`GET /owner/calendar/?year=2026&month=9&date=2026-09-15`

`year` and `month` are required. `date` is optional, but when present it must
belong to that month. The response includes only pending and confirmed visits:

```json
{
  "year": 2026,
  "month": 9,
  "days": [
    {"date": "2026-09-15", "day": 15, "visit_count": 2}
  ],
  "selected_date": "2026-09-15",
  "visits": [
    {
      "id": "uuid",
      "tenant": {"id": "uuid", "name": "Mohamed Ahmed"},
      "property": {"id": "uuid", "title": "Furnished Apartment"},
      "visit_time": "15:00:00",
      "status": "confirmed"
    }
  ]
}
```

Use `days` to render appointment indicators on the calendar and `visits` for
the selected-day cards.

## Seven-day availability grid

`GET /owner/properties/<property_id>/availability/?start_date=2026-09-14`

`start_date` is optional. Without it, the API checks the week starting on
Monday of the current week. It returns only dates that have at least one
bookable slot and only slots with `state: "available"`. Booked, disabled, and
unspecified times are intentionally omitted from this response.

## Save one date's slots

`PUT /owner/properties/<property_id>/availability/`

```json
{
  "availability_date": "2026-09-15",
  "slots": [
    {"time": "09:00:00", "is_enabled": true},
    {"time": "12:00:00", "is_enabled": true},
    {"time": "16:00:00", "is_enabled": false}
  ]
}
```

The authenticated user must own `<property_id>`. This is an atomic replacement
for that property's slots on `availability_date`:

- Included slots are created or updated.
- Omitted, non-booked slots are removed, becoming `unspecified`.
- Booked slots are preserved even if omitted.
- A booked slot cannot be submitted with `is_enabled: false`.
- Submitted times must be in the future.
