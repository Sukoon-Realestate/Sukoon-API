# Sokoun property media, editing, and deletion — backend handoff

Date: 2026-10-05.

The Flutter client is wired to the contracts below. New fields and the delete route are **proposed server changes**, not evidence that they are deployed. This repository contains the mobile app and checked-in API examples (`collection.json`), but no backend server implementation. Implement these changes in the backend repository, then update the authoritative API collection with real responses.

## Routes

All paths are relative to `/api/v1/`, keep trailing slashes, and reuse the existing authenticated session.

| Method | Path | Required change |
| --- | --- | --- |
| POST | `properties/create/` | Accept cover captions, optional video, additional details, and ownership document in the same multipart property request. Return the complete property. |
| PATCH | `properties/{property_id}/` | Update every owner-editable field, cover, existing image captions/retention, video, and ownership document. Submit edits for review and return the complete updated property. |
| POST | `properties/{property_id}/images/` | Keep the current additional-image upload route. Make `name` and `description` optional and return both. |
| GET | `properties/{property_id}/` | Return the same complete property shape with captions, video, location, terms, amenities, and review status. Owners must be able to fetch their pending/rejected property for editing. |
| DELETE | `properties/{property_id}/delete/` | **New route:** delete the authenticated owner's property. |
| GET | `properties/owned/` | Continue returning the owner's listings; reflect updated content, cover, and `under_review` status, and exclude deleted properties. |

Creation/update/image/deletion operations must verify that the authenticated account owns the property. Do not accept an owner ID from the client. Tenant details must return approved public content only.

## Optional photo name and description

Apply optional captions to every image, including the cover. Both may be omitted, empty, whitespace, or null. Trim strings and normalize missing captions to `""` in responses. Captions are recommended in the app, but neither is a validation requirement. Persist supplied captions and return them consistently from upload, create, update, and details serializers.

Additional photo upload remains multipart:

```text
POST properties/{property_id}/images/
image = <binary photo>          # required
name = Living room             # optional
description = Bright room      # optional
```

```json
{
  "message": "Image uploaded successfully.",
  "data": {
    "id": "image-id",
    "image": "https://media.example.com/living-room.jpg",
    "name": "Living room",
    "description": "Bright room",
    "created_at": "2026-10-05T12:00:00+03:00",
    "updated_at": "2026-10-05T12:00:00+03:00"
  }
}
```

Give the cover a stable image ID too. Return `main_image_id`, `main_image_name`, and `main_image_description`, and include the cover record in `images`. `main_image` stays a URL string for compatibility. When the same cover URL appears in `images`, the app deduplicates it and preserves its captions.

The app sends the first selected photo as `main_image` in the property request. If the save response includes its URL, the app records it as already uploaded and sends only the remaining new photos to `/images/`. Do not create a duplicate cover image or count the cover twice.

The client requires 10–25 photos to submit. Property saving happens before additional uploads; accept the cover-only draft and temporarily incomplete edit image sets, but gate moderation/publication until the property has at least 10 unique images. Enforce the maximum transactionally when concurrent image uploads arrive. A failed upload is retried against the already-created property, and successfully uploaded images are retained.

## Video in the existing property endpoint

The app selects or records one optional video. It validates duration from the selected file: 1–60 seconds. Accept it on `POST properties/create/` and `PATCH properties/{property_id}/`, alongside the other property fields; do not require a separate video endpoint.

| Multipart field | Semantics |
| --- | --- |
| `video` | Binary video file; store/replace the property's video. |
| `video_duration` | Integer seconds supplied by the app; independently validate/probe the actual media duration server-side. |
| `remove_video=true` | Clear the existing video and duration. |
| No video fields | Preserve the video on PATCH; create without a video on POST. |

Return `video` as an absolute playable HTTP(S) URL and `video_duration` as integer seconds. Return both as `null` when no video exists. Serve a format supported on Android/iOS (for example MP4/H.264), with correct content type and byte-range support. A replacement upload and `remove_video=true` must not be accepted together. Validate uploaded content and return normal API errors for unsupported or invalid media.

## Create and edit request fields

Use multipart parsers on both POST and PATCH. Form fields arrive as strings; normalize numeric and boolean values instead of treating `"false"` as truthy. The following are the fields sent by `OwnerAddPropertyFormState.toJson()`:

| Fields | Type / behavior |
| --- | --- |
| `title`, `description` | Property text. |
| `price`, `price_period` | Positive price; period from filter options (`daily`, `weekly`, `monthly`, `yearly`). |
| `property_type` | Slug/value from the property-type endpoint. |
| `bedrooms`, `bathrooms`, `area`, `space`, `floor` | Property measurements and floor; zero/negative floors are permitted. |
| `rental_period`, `suitable_for` | Rental duration and intended residents from filter options. |
| `governorate`, `city` | Region IDs; validate that the city belongs to the selected governorate. |
| `district`, `street`, `country` | Neighborhood, street, and country; keep neighborhood and street separate in responses. |
| `latitude`, `longitude` | Selected valid geographic coordinates. |
| `building_year` | Optional integer (client supports 1800 through the current year); blank clears it. |
| `deposit` | Optional non-negative EGP amount, or existing choices `none`, `half_month`, `one_month`, `two_months`; blank clears it. Return the persisted value. |
| `smoking_allowed` | `true`, `false`, or blank to clear to `null`. |
| `is_furnished` | Boolean. |
| `has_wifi`, `has_elevator`, `has_garage`, `has_security`, `has_balcony`, `has_air_conditioning`, `near_metro`, `has_natural_gas`, `has_electricity_meter`, `has_water_meter` | Existing amenity booleans; retain compatibility. |
| `amenities` | JSON-encoded array of amenity API values, including supported values returned by the filter-options endpoint. Excludes `furnished`, which uses `is_furnished`. Validate supported values and return the complete amenity array. |
| `main_image` | Optional binary cover file. Required for the normal creation flow; replace the cover on PATCH when supplied. |
| `main_image_id` | Choose an existing retained image as the cover. Must belong to this property. |
| `main_image_name`, `main_image_description` | Optional cover captions; blank clears old captions. |
| `ownership_proof` | Optional binary JPG/PNG ownership document, for internal review only. |
| `remove_ownership_proof=true` | Clear the ownership document and its verification state. |
| `video`, `video_duration`, `remove_video` | See video semantics above. |

Do not clear an existing video/document merely because the binary field is absent. Explicit clear flags are used. Reject contradictory replacement/clear flags. Changing or removing ownership proof must reset proof verification for review.

Blank optional country, neighborhood (`district`), building year, and deposit values clear those fields on PATCH. For compatibility with the old creation contract, the client uses the street as `district` on POST when no separate neighborhood is entered; PATCH keeps the two fields independent.

### Existing images on PATCH

These two multipart text fields contain JSON:

```text
retained_image_ids = ["cover-id", "bedroom-id"]
images_metadata = [{"id":"cover-id","name":"Entrance","description":""},{"id":"bedroom-id","name":"","description":"Room overlooking the garden"}]
main_image_id = cover-id
main_image_name = Entrance
main_image_description =
```

The real request contains every retained image, not only the two shown here.

- If `retained_image_ids` is absent, leave image membership unchanged. If present, remove existing image records not listed. Verify every supplied ID belongs to this property, including the selected cover.
- Apply `images_metadata` by image ID, allowing either caption to be cleared independently. Never match metadata by response order or localized image name.
- The client implements replacement by removing the old ID and uploading the replacement. A new first photo is sent as the binary `main_image` during PATCH; other new files follow through `/images/`.
- Preserve retained images in the order given by `retained_image_ids`. Keep the selected cover first in the response. Return stable IDs, URLs, captions, and timestamps for every image.
- Handle removals, cover selection/replacement, captions, and scalar edits atomically within the property PATCH. Do not delete a promoted cover while cleaning up the previous cover's storage.
- Validate references and the maximum photo count. As with creation, additional uploads can be pending; prevent publication/moderation approval of an incomplete set.

## Complete property response

Reuse one property serializer for create, update, and details instead of returning only an ID or returning raw location IDs on writes. Example shape below shows two images for brevity; actual details include every persisted image.

```json
{
  "message": "Property changes submitted for review.",
  "data": {
    "id": "property-id",
    "owner": {"id": "owner-id", "full_name": "Ahmed Mohamed", "is_verified": true},
    "main_image": "https://media.example.com/cover.jpg",
    "main_image_id": "cover-id",
    "main_image_name": "Living room",
    "main_image_description": "Natural light throughout the day",
    "video": "https://media.example.com/property.mp4",
    "video_duration": 35,
    "property_link": "https://sokoun.app/properties/property-id",
    "title": "Furnished apartment",
    "description": "A comfortable apartment near the metro.",
    "price": "6500.00",
    "price_period": "monthly",
    "property_type": "apartment",
    "is_furnished": true,
    "is_verified": false,
    "is_ownership_verified": false,
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
      "id": "governorate-id", "name": "Cairo", "slug": "cairo",
      "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
    },
    "city": {
      "id": "city-id", "name": "Nasr City", "slug": "nasr-city",
      "governorate": "governorate-id", "governorate_name": "Cairo",
      "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"
    },
    "district": "Seventh district",
    "street": "Main street",
    "building_year": 2020,
    "deposit": "one_month",
    "ownership_proof": "https://private-media.example.com/owner-document.jpg",
    "latitude": "30.044400",
    "longitude": "31.235700",
    "amenities": ["wifi", "elevator", "security", "electricity_meter"],
    "is_fav": false,
    "is_saved": false,
    "rating": 4.2,
    "images": [
      {
        "id": "cover-id", "image": "https://media.example.com/cover.jpg",
        "name": "Living room", "description": "Natural light throughout the day",
        "created_at": "2026-10-05T12:00:00+03:00", "updated_at": "2026-10-05T12:00:00+03:00"
      },
      {
        "id": "bedroom-id", "image": "https://media.example.com/bedroom.jpg",
        "name": "", "description": "",
        "created_at": "2026-10-05T12:00:00+03:00", "updated_at": "2026-10-05T12:00:00+03:00"
      }
    ],
    "created_at": "2026-10-01T10:00:00+03:00",
    "updated_at": "2026-10-05T12:00:00+03:00"
  }
}
```

This is the owner's response. Omit `ownership_proof` for tenants and guests, or return null. The existing app treats the document as private; tenant details show verification status, not the underlying ownership document. Under-review draft values must not become public before approval. Server-owned IDs, timestamps, rating, save flags, owner identity, verification flags, and status are read-only; listing content and media are editable.

The app maps older raw `city`/`governorate` IDs and amenity booleans for compatibility, but the target contract uses nested region objects and the complete amenity array. Return decimal prices as strings, counts/durations as numbers, flags as booleans, and timestamps as ISO 8601. Keep missing optional fields present as null or empty strings consistently.

## Editing and moderation

On every accepted owner edit, persist draft changes and set `status="under_review"`. Return that actual status in PATCH, owner details, and the owned-property list. The app shows an edit-review bottom sheet after saving and uploading all selected media, and updates the property card's status from the response.

Do not accept client-supplied status/verification fields. Preserve or withdraw the last approved public version according to the existing moderation policy; expose only the approved version to tenants. Owners need access to the pending draft so reopening Edit loads their submitted values and media. Media replacement/removal must follow the same review policy as text edits.

## New owner-only deletion endpoint

```text
DELETE /api/v1/properties/{property_id}/delete/
```

No request body. Recommended success response:

```json
{
  "message": "Property deleted successfully.",
  "data": {"id": "property-id", "deleted": true}
}
```

Return 200 only after deletion commits. Use the normal error envelope and HTTP 401/403/404 for unauthenticated, unauthorized, and missing properties. If existing leases or protected records prevent deletion, return a meaningful 409 error and keep the listing intact.

Remove the property from public search, owner lists, favorites/saved references, and future visit availability. Clean up media and pending moderation records while respecting existing visit/contract history rules. The Flutter confirmation sheet disables duplicate requests, keeps the property card after an error/cancel, and removes it only after API success. Relevant owner/detail caches are invalidated on success.

## Backend acceptance checks

1. Upload photos with neither caption, only a name, only a description, and both captions. Verify persistence and GET/write response equality, including blank/null normalization and Arabic text.
2. Create with a video using the property multipart endpoint. Verify its returned URL/duration and actual tenant playback after approval. Create without video; replace, remove, and leave a video unchanged on PATCH.
3. Rename an existing image, clear its description, delete/replace it, and choose a retained image as cover. Verify stable IDs, ordering, deduplication, ownership checks, and concurrency-safe limits.
4. Edit every writable field and reopen Edit. Verify country, separate neighborhood/street, region IDs, zero floor, deposit, smoking false/null, all supported amenities, document replacement/removal, and draft media survive.
5. Confirm each edit returns `under_review`, appears in the owner's list as pending, and cannot leak unapproved content to tenants.
6. Delete as the owner and verify the property disappears; attempt deletion as another account and ensure nothing changes. Check missing IDs and any lease conflict.
7. Capture real create/PATCH/GET/image/delete responses in `collection.json` once deployed and run a staging owner-to-tenant flow. Client fixture tests do not verify the remote deployment.
