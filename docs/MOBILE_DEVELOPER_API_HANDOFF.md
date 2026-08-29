# Mobile Developer API Handoff

This document contains the exact API changes that affect the Sukoon mobile app.

## Required Mobile Changes

The mobile app needs to:

1. Use the new available-places endpoint after selecting a property type.
2. Read property amenities from `amenities` instead of ten boolean fields.
3. Read `is_fav`, `is_saved`, and `rating` from property details.
4. Load visit dates and times from the property's new `available_dates` endpoint.
5. Send the returned `visit_date` and `visit_time` values when booking.
6. Handle booking failure if another tenant books the slot first.

All endpoints continue to use the existing API response envelope.

## 1. Get Property Types

This existing endpoint has not changed:

```http
GET {{base_url}}/api/v1/properties/types/
```

Use the returned `id` as `property_type_id` in the available-places request.

Example property type:

```json
{
  "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
  "name": "Apartment",
  "slug": "apartment",
  "description": ""
}
```

## 2. Get Available Places

This is a new endpoint:

```http
GET {{base_url}}/api/v1/properties/available_places/?property_type_id=e9772fe6-3833-44d6-b591-600fba6c163b
```

### Query parameter

| Name | Type | Required | Value |
| --- | --- | --- | --- |
| `property_type_id` | UUID string | Yes | An `id` returned by the property-types endpoint |

### Success response

```json
{
  "data": {
    "places": [
      {
        "governorate": "Cairo",
        "city": "Cairo",
        "district": "Maadi"
      },
      {
        "governorate": "Cairo",
        "city": "Cairo",
        "district": "Nasr City"
      }
    ]
  }
}
```

### Empty response

```json
{
  "data": {
    "places": []
  }
}
```

An empty array means there are currently no approved properties of that type in
an available location. It is not an API error.

The endpoint returns distinct locations, so the same governorate/city/district
combination will not appear twice.

Authentication is required.

## 3. Property Details

The endpoint URL and request have not changed:

```http
GET {{base_url}}/api/v1/properties/{property_id}/
```

### Removed response fields

Do not read these fields from the property-details response anymore:

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

### New amenities field

Read the new `amenities` array instead:

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

The only possible amenity values are:

```text
wifi
elevator
garage
security
balcony
air_conditioning
near_metro
natural_gas
electricity_meter
water_meter
```

Only enabled amenities are included. When no amenities are enabled:

```json
{
  "amenities": []
}
```

`is_furnished` is unchanged and remains a separate top-level field.

### New property-state fields

Property details now always contain:

```json
{
  "is_fav": true,
  "is_saved": false,
  "rating": 4.5
}
```

Client types:

| Field | JSON type | Behavior |
| --- | --- | --- |
| `is_fav` | Boolean | Whether the authenticated tenant favorited the property |
| `is_saved` | Boolean | Whether the authenticated tenant saved the property |
| `rating` | Number | Aggregate rating; `0.0` when the property has no ratings |

For anonymous requests, both `is_fav` and `is_saved` are `false`.

These values are real JSON booleans and numbers, not strings.

### Relevant response example

```json
{
  "data": {
    "id": "property-uuid",
    "title": "Furnished apartment",
    "is_furnished": true,
    "amenities": [
      "wifi",
      "garage",
      "security"
    ],
    "is_fav": true,
    "is_saved": false,
    "rating": 4.7
  }
}
```

## 4. Get Property Visit Dates and Times

This is a new endpoint:

```http
GET {{base_url}}/api/v1/properties/{property_id}/available_dates/
```

It returns availability belonging to the property's owner.

### Default request

```http
GET {{base_url}}/api/v1/properties/{property_id}/available_dates/
```

When no date is provided, `times` belongs to the first item in `days`.

### Request times for a selected date

```http
GET {{base_url}}/api/v1/properties/{property_id}/available_dates/?date=2026-09-15
```

| Name | Type | Required | Format |
| --- | --- | --- | --- |
| `date` | String | No | `YYYY-MM-DD` |

Use the `visit_date` value returned in `days` as this query parameter.

### Success response

```json
{
  "data": {
    "days": [
      {
        "day": "tuesday",
        "date": "15/9",
        "visit_date": "2026-09-15"
      },
      {
        "day": "wednesday",
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

### Field usage

| Field | Purpose |
| --- | --- |
| `day` | Lowercase English weekday name |
| `date` | Display label in `D/M` format |
| `visit_date` | Machine value used for date queries and booking |
| `time` | Display label in 12-hour format |
| `visit_time` | Machine value used for booking |
| `is_available` | Whether the slot can currently be selected |

The app should disable or hide time slots where `is_available` is `false`.

### Empty response

```json
{
  "data": {
    "days": [],
    "times": []
  }
}
```

The endpoint is publicly accessible. Future/past calculations use the
`Africa/Cairo` timezone.

## 5. Book a Property Visit

The endpoint and request body have not changed:

```http
POST {{base_url}}/api/v1/properties/{property_id}/visits/
Content-Type: application/json
```

```json
{
  "visit_date": "2026-09-15",
  "visit_time": "10:00:00",
  "note": "Optional tenant note"
}
```

Use the values returned by `available_dates`:

- Send `days[index].visit_date` as `visit_date`.
- Send `times[index].visit_time` as `visit_time`.
- Do not send the display-only `date` or `time` values.

Authentication is required.

### New booking behavior

The backend checks availability again during booking. A slot can become
unavailable after the app loads it if another tenant books it first.

The app must handle a `400` response and refresh `available_dates`:

```json
{
  "message": "The selected visit slot is already booked."
}
```

Other unavailable-slot errors use the same error envelope:

```json
{
  "message": "The selected visit slot is not available."
}
```

## Mobile Migration Checklist

- [ ] Load `property_type_id` from the property-types endpoint.
- [ ] Use `available_places` to populate location choices.
- [ ] Replace property-detail amenity booleans with `amenities` parsing.
- [ ] Add `is_fav`, `is_saved`, and numeric `rating` to the property model.
- [ ] Load `available_dates` before displaying the visit booking form.
- [ ] Reload `available_dates` when the selected day changes.
- [ ] Allow selection only when `is_available=true`.
- [ ] Book using `visit_date` and `visit_time`, not the display labels.
- [ ] On booking `400`, show an unavailable-slot message and refresh the schedule.
- [ ] Treat all empty lists as valid empty states, not `null` or errors.
