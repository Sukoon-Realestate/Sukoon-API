# Mobile API Changes

This document summarizes the backend changes requested for the Sukoon mobile
application.

## 1. Available Places Endpoint

### New endpoint

```http
GET /api/v1/properties/available_places/?property_type_id=<property-type-uuid>
```

### Query parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `property_type_id` | Yes | UUID returned by `GET /api/v1/properties/types/` |

### Response

```json
{
  "data": {
    "places": [
      {
        "governorate": "Cairo",
        "city": "Cairo",
        "district": "Maadi"
      }
    ]
  }
}
```

The endpoint:

- Returns distinct governorate, city, and district combinations.
- Does not return duplicate locations.
- Returns `"places": []` when there are no matching properties.
- Returns `400` when `property_type_id` is missing or invalid.
- Requires authentication.
- Includes a property when `status="verified"` or the legacy
  `is_verified=true` flag is set.

The legacy approval fallback was added because the `status` field was introduced
after `is_verified` and defaulted existing properties to `under_review`.

## 2. Property Details Response

### Existing endpoint

```http
GET /api/v1/properties/{property_id}/
```

There are no request-body or query-parameter changes.

### Amenity response change

The following individual fields were removed from the property-details response:

```text
has_wifi
has_elevator
has_garage
has_security
has_balcony
has_air_conditioning
near_metro
has_natural_gas
has_electricity_meter
has_water_meter
```

They were replaced with one `amenities` array:

```json
{
  "amenities": [
    "wifi",
    "elevator",
    "garage",
    "security",
    "air_conditioning"
  ]
}
```

Only enabled amenities are included. When none are enabled, the API returns:

```json
{
  "amenities": []
}
```

Property create and update APIs continue to accept the existing amenity boolean
fields. The change applies only to the property-details response.

### Favorite, saved, and rating fields

The property-details response now always includes:

```json
{
  "is_fav": true,
  "is_saved": false,
  "rating": 4.5
}
```

- `is_fav` indicates whether the authenticated user favorited the property.
- `is_saved` indicates whether the authenticated user saved the property.
- Anonymous users receive `false` for both fields.
- `rating` is the aggregate property rating on a 1-to-5 scale.
- A property without ratings returns `0.0`.
- `is_furnished` remains a separate top-level property field.

## 3. Property Available Dates Endpoint

### New endpoint

```http
GET /api/v1/properties/{property_id}/available_dates/
```

An optional date can be selected:

```http
GET /api/v1/properties/{property_id}/available_dates/?date=2026-09-15
```

### Query parameters

| Parameter | Required | Description |
| --- | --- | --- |
| `date` | No | Schedule date in `YYYY-MM-DD` format |

### Response

```json
{
  "data": {
    "days": [
      {
        "day": "tuesday",
        "date": "15/9",
        "visit_date": "2026-09-15"
      }
    ],
    "times": [
      {
        "time": "10:00 AM",
        "visit_time": "10:00:00",
        "is_available": true
      }
    ]
  }
}
```

The endpoint:

- Uses the owner of the requested property.
- Does not use the authenticated tenant's availability.
- Returns only future owner schedule dates.
- Uses the first returned day when `date` is omitted.
- Returns disabled, booked, or expired slots with `is_available=false`.
- Returns empty `days` and `times` arrays when no future schedule exists.
- Returns `400` when the requested date is outside the owner's future schedule.
- Is publicly accessible.
- Uses the configured `Africa/Cairo` timezone.

The app should use `visit_date` and `visit_time` as the values sent when booking.

## 4. Visit Booking Validation

### Existing endpoint

```http
POST /api/v1/properties/{property_id}/visits/
Content-Type: application/json
```

The request body has not changed:

```json
{
  "visit_date": "2026-09-15",
  "visit_time": "10:00:00",
  "note": "Optional tenant note"
}
```

The backend now revalidates the owner slot transactionally during booking. A
booking is rejected when:

- The slot is not configured for the property owner.
- The slot is disabled.
- The slot is in the past.
- The same owner slot has already been booked for any of the owner's properties.

This prevents two tenants from booking the same owner time slot after both
previously received `is_available=true`.

## 5. New Data Models

The backend now includes persistence for:

- Owner availability slots.
- Property favorites.
- Saved properties.
- Property ratings.

These models are registered in Django admin.

## 6. Database Migration

The following migration was added:

```text
core_apps/properties/migrations/0010_property_engagement_and_availability.py
```

Apply it in the deployment environment:

```bash
python manage.py migrate
```

## 7. Automated Verification

Tests cover:

- Authenticated and anonymous property details.
- Enabled and empty amenity lists.
- Favorite, saved, and aggregate-rating values.
- Valid, missing, and invalid property-type IDs.
- Distinct available places and legacy property approval.
- Empty and invalid owner schedules.
- Enabled, disabled, expired, and already-booked slots.
- Booking-time availability revalidation.
- Owner-wide double-booking prevention.

The complete project test suite passes with 120 tests.
