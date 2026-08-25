# Mentor Backend API Instructions

This document defines the backend changes required by the Sokoun mobile app.

## General API rules

- Keep the project's existing response envelope and authentication behavior.
- Use `snake_case` JSON keys.
- Return real JSON booleans (`true` or `false`), not strings such as `"true"` or `"false"`.
- Keep response types stable, including when a list is empty or a user is not authenticated.
- Only return active/approved properties and valid future availability where applicable.

## 1. Add the `available_places` endpoint

Create this endpoint:

```http
GET /properties/available_places/?property_type_id={property_type_id}
```

### Request

`property_type_id` is required. Its value must be an `id` returned by the existing property-types endpoint:

```http
GET /properties/types
```

Example:

```http
GET /properties/available_places/?property_type_id=8d91d810-63fe-4e8d-9f7a-cdf20e518d32
```

### Response

Return the distinct places that currently contain at least one available property of the requested type. Do not return duplicate city/district combinations.

```json
{
  "data": {
    "places": [
      {
        "country": "Egypt",
        "city": "Cairo",
        "district": "Nasr City"
      },
      {
        "country": "Egypt",
        "city": "Cairo",
        "district": "Maadi"
      }
    ]
  }
}
```

Return `"places": []` when the property type is valid but has no available properties. Return the project's normal validation error when `property_type_id` is missing or invalid.

## 2. Replace property amenity booleans with one list

This applies to the property-details endpoint used by `apps/sokoun_app/lib/features/home/presentation/screens/tenant_property_details_screen.dart`:

```http
GET /properties/{property_id}/
```

Remove these keys from the details response:

```json
{
  "has_wifi": true,
  "has_elevator": true,
  "has_garage": true,
  "has_security": true,
  "has_balcony": false,
  "has_air_conditioning": true,
  "near_metro": true,
  "has_natural_gas": true,
  "has_electricity_meter": true,
  "has_water_meter": false
}
```

Replace them with a single `amenities` array:

```json
{
  "amenities": [
    "wifi",
    "elevator",
    "garage",
    "security",
    "air_conditioning",
    "near_metro",
    "natural_gas",
    "electricity_meter"
  ]
}
```

Rules:

- Include an amenity only when it is enabled for the property.
- Do not include false/disabled amenities. In the example above, `balcony` and `water_meter` are omitted.
- Use only these stable machine-readable values:
  - `wifi`
  - `elevator`
  - `garage`
  - `security`
  - `balcony`
  - `air_conditioning`
  - `near_metro`
  - `natural_gas`
  - `electricity_meter`
  - `water_meter`
- Return `"amenities": []` when the property has no amenities.
- Keep `is_furnished` as its existing top-level field; it is property metadata and is not part of this amenity migration.

## 3. Add favorite, saved, and rating fields to property details

Add these top-level keys to the same property-details response:

```json
{
  "is_fav": true,
  "is_saved": false,
  "rating": 4.7
}
```

Rules:

- `is_fav`: boolean indicating whether the authenticated tenant has marked this property as a favorite.
- `is_saved`: boolean indicating whether the authenticated tenant has saved/bookmarked this property.
- `rating`: JSON number containing the property's aggregate rating, using the same rating scale as the rest of the system.
- For an anonymous user, return `false` for both `is_fav` and `is_saved`.
- If the property has no ratings, return `0.0` so the field remains numeric and non-null.
- These three keys must always be present.

### Relevant property-details excerpt after the change

```json
{
  "id": "property-id",
  "title": "Furnished apartment",
  "amenities": [
    "wifi",
    "garage",
    "security"
  ],
  "is_fav": true,
  "is_saved": false,
  "rating": 4.7
}
```

## 4. Add the `available_dates` endpoint

Create a property-specific endpoint so the backend can resolve the property's owner and that owner's availability:

```http
GET /properties/{property_id}/available_dates/
```

The endpoint must use the owner of `{property_id}`. It must not use the authenticated tenant's availability.

An optional `date` query parameter selects which day's time slots are returned:

```http
GET /properties/{property_id}/available_dates/?date=2026-09-15
```

If `date` is omitted, return time slots for the first date in `days`. The `times` array must always correspond to either the requested date or that first returned date.

### Response

```json
{
  "data": {
    "days": [
      {
        "day": "sunday",
        "date": "15/9",
        "visit_date": "2026-09-15"
      },
      {
        "day": "monday",
        "date": "16/9",
        "visit_date": "2026-09-16"
      }
    ],
    "times": [
      {
        "time": "10:00 AM",
        "visit_time": "10:00:00",
        "is_available": true
      },
      {
        "time": "11:00 AM",
        "visit_time": "11:00:00",
        "is_available": false
      }
    ]
  }
}
```

Field rules:

- `day`: lowercase English weekday name, such as `sunday`.
- `date`: display value in `D/M` format, as requested by the app.
- `visit_date`: machine-readable value in `YYYY-MM-DD` format. The app sends this value as `visit_date` when creating a visit.
- `time`: display value in 12-hour format with `AM` or `PM`.
- `visit_time`: machine-readable 24-hour value in `HH:mm:ss` format. The app sends this value as `visit_time` when creating a visit.
- `is_available`: boolean. It is `false` when the owner did not enable the slot, the slot is already booked, or the slot is in the past.
- `days` must contain only bookable future dates configured by the property's owner.
- Return `"days": []` and `"times": []` when the owner has no future availability.
- Reject a `date` that does not belong to the returned owner schedule using the project's normal validation-error response.
- Calculate past/future status using the project's configured timezone and document that timezone in the API specification.

## Existing booking contract

The available-date response must be compatible with the existing booking request:

```http
POST /properties/{property_id}/visits/
Content-Type: application/json

{
  "visit_date": "2026-09-15",
  "visit_time": "10:00:00",
  "note": "Optional tenant note"
}
```

The backend must revalidate availability during booking. Do not trust an earlier `is_available: true` response, because another tenant may book the slot before this request arrives. Return a conflict/validation error when the slot is no longer available.

## Acceptance checklist

- [ ] `available_places` accepts a valid property-type ID and returns distinct places containing available properties of that type.
- [ ] Property details no longer contain the ten individual amenity boolean fields.
- [ ] Property details always contain an `amenities` array with only enabled values.
- [ ] Property details always contain typed `is_fav`, `is_saved`, and `rating` values.
- [ ] `available_dates` resolves availability from the property's owner.
- [ ] `available_dates` returns future days and time-slot availability in the documented shape.
- [ ] Empty results return empty arrays, not `null`.
- [ ] Booking rechecks the owner slot and prevents double booking.
- [ ] Automated API tests cover authenticated, anonymous, empty, invalid-ID, unavailable-slot, and already-booked cases.
