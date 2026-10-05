# Mobile Developer API Handoff: Property Media, Editing, and Deletion

**Date:** 2026-10-05  
**Version:** 1.0  
**Scope:** Property Creation, Full Property Editing, Image Retention & Captions, Video Tours, Ownership Proof, and Property Deletion.

All endpoints are relative to `/api/v1/`, retain trailing slashes, and use the existing authenticated session (JWT / Cookies).

---

## 1. Quick Route Summary

| Method | Path | Description | Key Changes |
| :--- | :--- | :--- | :--- |
| `POST` | `properties/create/` | Create property listing | Accepts cover captions, video, new fields, ownership proof. Returns full property. |
| `PATCH` | `properties/{property_id}/` | Full property update | Updates all writable fields, image retention, captions, cover promotion, video removal. Sets `status="under_review"`. |
| `POST` | `properties/{property_id}/images/` | Additional image upload | Optional `name` and `description`. Returns both. Max 25 images enforced transactionally. |
| `GET` | `properties/{property_id}/` | Property details | Unified complete property shape. Owners can view drafts; unapproved drafts hidden from public; `ownership_proof` omitted for non-owners. |
| `DELETE` | `properties/{property_id}/delete/` | Delete property | **New route:** Owner-only deletion. Returns HTTP 200. Returns HTTP 409 if active visits exist. |
| `GET` | `properties/owned/` | Owner's listing dashboard | Reflects edited content, cover, and `under_review` moderation status. Excludes deleted listings. |

---

## 2. Image Captions, Deduplication, and Cover Logic

### Captions on Images
- All images (cover photo and additional photos) accept optional `name` and `description`.
- Omitted, null, empty, or whitespace strings are trimmed and normalized to `""` in responses.
- Full Arabic Unicode text is supported.

### Cover Photo Identifiers
- `main_image`: Returns the absolute URL string of the cover photo.
- `main_image_id`: Stable UUID string of the cover `PropertyImage` record.
- `main_image_name`: Caption name of the cover photo.
- `main_image_description`: Caption description of the cover photo.
- `images`: Array of all property images, **with the selected cover always appearing as the first item**.
- The app sends the first selected photo as `main_image` on creation; subsequent photos are sent to `properties/{property_id}/images/`. The cover is included in `images` and not counted twice.

### Uploading Additional Photos (`POST properties/{property_id}/images/`)
Multipart request:
```text
image = <binary file>        # required
name = Living room           # optional
description = Bright room    # optional
```

Response (`HTTP 201 Created`):
```json
{
  "message": "Image uploaded successfully.",
  "data": {
    "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
    "image": "https://res.cloudinary.com/.../living-room.jpg",
    "name": "Living room",
    "description": "Bright room",
    "created_at": "2026-10-05T12:00:00+03:00",
    "updated_at": "2026-10-05T12:00:00+03:00"
  }
}
```

- **Image Limit:** Maximum 25 images per property. Exceeding this limit returns `HTTP 400 Bad Request`.
- **Publication Gate:** Properties must have at least 10 unique images before admin approval/publication. Drafts can be saved with fewer images during composition.

---

## 3. Video Tour Integration

Video tour fields are handled directly in `POST properties/create/` and `PATCH properties/{property_id}/` (no separate video endpoint).

| Multipart field | Type | Description |
| :--- | :--- | :--- |
| `video` | Binary file | MP4 video upload (H.264 compatible for iOS/Android). |
| `video_duration` | Integer | Media duration in seconds (must be between `1` and `60`). |
| `remove_video=true` | Boolean string | Clears the existing video and sets `video_duration` to `null`. |

- **Validation:** Uploading a new video file while simultaneously passing `remove_video=true` is rejected with `HTTP 400 Bad Request`.
- **Response:** When present, `video` is returned as an absolute playable HTTPS URL and `video_duration` as an integer. When absent or removed, both return `null`.

---

## 4. Property Create & Edit Field Reference

Both `POST properties/create/` and `PATCH properties/{property_id}/` accept multipart form data. String values for booleans and numbers are normalized server-side.

| Field | Type | Behavior / Constraints |
| :--- | :--- | :--- |
| `title` | String | Property title. |
| `description` | String | Full property description. |
| `price` | String / Decimal | Positive price (e.g. `"6500.00"`). Returned as a decimal string. |
| `price_period` | String | Period choices: `daily`, `weekly`, `monthly`, `yearly`. |
| `property_type` | String | Property type slug (e.g. `apartment`, `villa`, `studio`). |
| `bedrooms`, `bathrooms`, `area` | Integer | Room counts and area in sqm. |
| `space` | String | Optional display space string (e.g. `"120"`). |
| `floor` | Integer | Floor number. **Zero and negative values are permitted** (e.g. `0` for ground, `-1` for basement). Blank clears to `null`. |
| `rental_period` | Integer | Minimum rental period in months. |
| `suitable_for` | String | Allowed tenant type: `families`, `singles`, `students`, `female_students`, `all`. |
| `country` | String | Default: `"Egypt"`. Blank clears to `""`. |
| `governorate` | UUID string | Selected governorate ID. |
| `city` | UUID string | Selected city ID (must belong to the selected governorate). |
| `district` | String | Neighborhood / district. |
| `street` | String | Street address. Handled independently from `district`. *(On `create/`, if `district` is omitted, `street` is used as fallback).* |
| `latitude`, `longitude` | Decimal / String | Decimal coordinates (e.g. `"30.044400"`, `"31.235700"`). |
| `building_year` | Integer | Optional construction year between `1800` and current year. Blank clears to `null`. |
| `deposit` | String | Choices: `none`, `half_month`, `one_month`, `two_months` OR a non-negative numeric amount. Blank clears to `""`. |
| `smoking_allowed` | Boolean | `true`, `false`, or blank/null to clear to `null`. |
| `is_furnished` | Boolean | `true` or `false`. |
| `amenities` | JSON array string | JSON-encoded array of slugs, e.g. `'["wifi", "elevator", "security", "electricity_meter"]'`. Supported values: `wifi`, `elevator`, `garage`, `security`, `balcony`, `air_conditioning`, `near_metro`, `natural_gas`, `electricity_meter`, `water_meter`. |
| `main_image` | Binary file | Cover photo upload. Replaces existing cover on PATCH. |
| `main_image_id` | UUID string | Choose an existing retained image to promote to cover on PATCH. |
| `main_image_name` | String | Caption name for the cover photo. |
| `main_image_description`| String | Caption description for the cover photo. |
| `ownership_proof` | Binary file | JPG/PNG document proving ownership. Private to owner and admin. |
| `remove_ownership_proof`| Boolean string | `true` clears the document and resets `is_ownership_verified` to `false`. |

---

## 5. Existing Images Management on PATCH

On `PATCH properties/{property_id}/`, image retention, metadata updates, and cover promotion are handled atomically:

```text
retained_image_ids = ["image-uuid-1", "image-uuid-2"]
images_metadata = [{"id": "image-uuid-1", "name": "Living room", "description": ""}, {"id": "image-uuid-2", "name": "Bedroom", "description": "Garden view"}]
main_image_id = image-uuid-2
main_image_name = Living room
main_image_description =
```

- **`retained_image_ids`**: Any existing property image whose ID is not in this list is permanently deleted. Supplying an image ID belonging to another property raises a `400 Validation Error`.
- **`images_metadata`**: Matches images by ID and updates `name` and `description` independently.
- **`main_image_id`**: Promotes the specified retained image to cover. The promoted cover is automatically moved to the first position in `images`.
- **New Cover Upload (`main_image`)**: If a new file is uploaded on PATCH, it is stored as a new cover image and positioned first.

---

## 6. Complete Property Response Shape

Both `POST properties/create/`, `PATCH properties/{property_id}/`, and `GET properties/{property_id}/` return the complete unified property payload:

```json
{
  "message": "Property changes submitted for review.",
  "data": {
    "id": "c4d07375-a88f-4a2c-a027-3fa03e522415",
    "owner": {
      "id": "9569230f-eeb7-4d3a-a2dc-5ca624cc6040",
      "full_name": "Ahmed Mohamed",
      "name": "Ahmed Mohamed",
      "avatar": "https://res.cloudinary.com/.../avatar.jpg",
      "is_verified": true
    },
    "owner_is_verified": true,
    "is_ownership_verified": false,
    "main_image": "https://res.cloudinary.com/.../cover.jpg",
    "main_image_id": "cover-image-uuid",
    "main_image_name": "Living room",
    "main_image_description": "Natural light throughout the day",
    "video": "https://res.cloudinary.com/.../tour.mp4",
    "video_duration": 35,
    "property_link": "https://sokoun.app/properties/c4d07375-a88f-4a2c-a027-3fa03e522415",
    "title": "Furnished apartment",
    "description": "A comfortable apartment near the metro.",
    "price": "6500.00",
    "price_period": "monthly",
    "property_type": "apartment",
    "is_furnished": true,
    "is_verified": false,
    "status": "under_review",
    "bedrooms": 2,
    "bathrooms": 1,
    "area": 120,
    "space": "120",
    "floor": 3,
    "rental_period": 6,
    "suitable_for": "singles",
    "smoking_allowed": false,
    "country": "Egypt",
    "governorate": {
      "id": "e9772fe6-3833-44d6-b591-600fba6c163b",
      "name": "Cairo",
      "slug": "cairo",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    },
    "city": {
      "id": "f086c4d5-ad68-4bc1-8cf9-c05454267afe",
      "name": "Nasr City",
      "slug": "nasr-city",
      "governorate": "e9772fe6-3833-44d6-b591-600fba6c163b",
      "governorate_name": "Cairo",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-01-01T00:00:00Z"
    },
    "district": "Seventh district",
    "street": "Al Tayaran Street",
    "building_year": 2020,
    "deposit": "one_month",
    "ownership_proof": "https://res.cloudinary.com/.../ownership_document.jpg",
    "latitude": "30.044400",
    "longitude": "31.235700",
    "amenities": ["wifi", "elevator", "security", "electricity_meter"],
    "is_fav": false,
    "is_saved": false,
    "rating": 4.2,
    "images": [
      {
        "id": "cover-image-uuid",
        "image": "https://res.cloudinary.com/.../cover.jpg",
        "name": "Living room",
        "description": "Natural light throughout the day",
        "created_at": "2026-10-05T12:00:00+03:00",
        "updated_at": "2026-10-05T12:00:00+03:00"
      },
      {
        "id": "bedroom-image-uuid",
        "image": "https://res.cloudinary.com/.../bedroom.jpg",
        "name": "Master bedroom",
        "description": "",
        "created_at": "2026-10-05T12:00:00+03:00",
        "updated_at": "2026-10-05T12:00:00+03:00"
      }
    ],
    "created_at": "2026-10-01T10:00:00+03:00",
    "updated_at": "2026-10-05T12:00:00+03:00"
  }
}
```

> **Privacy Note:** `ownership_proof` is returned **only to the authenticated owner** and admins. For tenants and unauthenticated visitors, `ownership_proof` returns `null`.

---

## 7. Owner-Only Property Deletion

```http
DELETE /api/v1/properties/{property_id}/delete/
```

- **Authentication:** Required. Must be the owner of the listing.
- **Body:** None.

### Success Response (`HTTP 200 OK`)
```json
{
  "message": "Property deleted successfully.",
  "data": {
    "id": "c4d07375-a88f-4a2c-a027-3fa03e522415",
    "deleted": true
  }
}
```

### Error Responses
- `401 Unauthorized`: Not logged in.
- `403 Forbidden`: Authenticated user is not the listing owner.
- `404 Not Found`: Listing does not exist.
- `409 Conflict`: Cannot delete listing if active visit requests (`pending` or `confirmed`) or active leases exist:
  ```json
  {
    "message": "Cannot delete property with active or upcoming visit requests."
  }
  ```

---

## 8. Moderation & Draft Behavior

1. **Automatic Review Status:** Every owner edit via `PATCH properties/{property_id}/` automatically sets `status="under_review"`.
2. **Owner Draft Access:** The authenticated owner can always retrieve their pending or rejected draft via `GET properties/{property_id}/` to inspect or resume editing.
3. **Tenant Public Feed Isolation:** Unverified or under-review listings remain invisible to public search and feed endpoints until admin verification.
