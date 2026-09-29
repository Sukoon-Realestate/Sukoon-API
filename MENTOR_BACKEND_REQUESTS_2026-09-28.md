# Mentor Backend Handoff — Sokoun — 28 September 2026

Implement the backend work requested by Emara on 28 September 2026. This document covers the new requests and supplements [the earlier backend instructions](MENTOR_BACKEND_API_INSTRUCTIONS.md).

**Contract status:** Existing routes and field names below were checked against the Flutter repository, not a running backend. Routes marked **proposed** and the explicitly listed product assumptions need agreement before implementation. Example IDs, URLs, timestamps, and counts are illustrative.

## Request overview

| Request | Endpoint / backend work | Status |
| --- | --- | --- |
| Property video | `POST /properties/create/` and `GET /properties/{property_id}/` | Extend existing contracts |
| Property sharing / deep linking | Return `property_link`; serve an agreed public property URL | New response field and link configuration |
| Time on received visits | `GET /properties/visits/received/` | Extend every list item |
| Owner badge counts | `GET /profiles/owner/unread-counts/` | Proposed new endpoint |
| Tenant badge counts | `GET /profiles/tenant/unread-counts/` | Proposed new endpoint |
| View all properties from tenant home | `GET /properties/` with pagination | Reuse and verify existing collection |
| Tenant “My rates” | `GET /profiles/my-rates/` | Proposed new endpoint |
| About us, privacy policy, terms | Three public content endpoints under `/pages/` | Proposed new endpoints |
| Complete registration | `POST /auth/complete-register/` | Proposed new endpoint |

Keep the existing authentication, response envelope, and validation-error conventions. The JSON examples show the relevant payload, not a replacement envelope. Use stable `snake_case` keys, integer counts, JSON booleans, and empty arrays for empty collections.

## 1. Add video to property creation and details

### Create a property

```http
POST /properties/create/
Content-Type: multipart/form-data
```

Retain the current property fields and add support for:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `video` | Uploaded file | No | One property walkthrough video |
| `video_duration` | Integer, seconds | When video is supplied by the current client | Client-reported duration; verify against the actual file |

The Flutter create flow already sends these exact keys. Video is optional because the flow permits skipping it. The current client permits a maximum duration of **60 seconds**; enforce the same limit server-side and publish supported file types and maximum upload size.

Persist the upload against the created property. Validate it before reporting successful creation; do not silently accept and discard the file. Requests without a video must continue to work.

### Return the video

Return the following fields from `GET /properties/{property_id}/` and the successful create response:

```json
{
  "id": "property-id",
  "video": "https://media.example.com/properties/property-id/walkthrough.mp4",
  "video_duration": 42
}
```

- `video` is a playable HTTPS URL, not a server filesystem path or upload filename.
- Return `video: null` and `video_duration: null` when no video exists.
- Preserve the existing photos and other property fields.
- If media URLs expire, document their lifetime and how fetching details obtains a fresh URL.

**Acceptance:** Create with a valid video, fetch the same property, and play the returned URL. Also cover creation without video, an invalid file, and a video exceeding 60 seconds.

## 2. Provide a property link for sharing and deep linking

Add a canonical `property_link` field to property details and the successful create response:

```json
{
  "id": "property-id",
  "property_link": "https://example.com/properties/property-id"
}
```

The example domain is a placeholder; use the agreed production web domain. This is a public sharing URL, distinct from the API URL.

Backend/web responsibilities:

- Keep the link stable and resolve it using the property's real ID.
- Provide a web fallback when the app is unavailable, and an unavailable/not-found result for a property that cannot be shown publicly.
- Configure the link host to support Android App Links and iOS Universal Links, using application identifiers and verification details supplied by the mobile team.
- Do not put authentication credentials or private owner details in the link.

Mobile responsibilities: configure link handling and open the identified property on both a cold start and an already running app. Returning a URL alone does not complete deep-link support.

**Acceptance:** The shared URL opens the correct property with the app installed, falls back to the web otherwise, and handles invalid or unavailable properties predictably. Deferred navigation after app installation is not assumed by this request; confirm separately if required.

## 3. Include time in every received visit request

```http
GET /properties/visits/received/
```

Each returned visit must include its scheduled time alongside its date. Do not expose the time only on the visit-details endpoint or at the outer response level.

Example list item, showing the relevant fields:

```json
{
  "id": "visit-id",
  "property_id": "property-id",
  "visit_date": "2026-10-01",
  "visit_time": "14:30:00",
  "time": "2:30 PM",
  "status": "pending"
}
```

- `visit_date`: `YYYY-MM-DD`.
- `visit_time`: canonical 24-hour `HH:mm:ss`, matching the value accepted by the existing booking endpoint.
- `time`: display value for the same scheduled time, consistent with the earlier availability contract.
- Use and document the same schedule timezone as booking and availability.
- Preserve current fields and pagination. Apply this to every item on every page.
- Do not substitute request creation time for the scheduled visit time. If old records have no schedule time, document that case explicitly rather than inventing one.

**Acceptance:** The time on a received request matches the submitted booking and visit details, including after a schedule update.

## 4. Add owner and tenant count endpoints

Create two authenticated endpoints. The proposed paths are:

```http
GET /profiles/owner/unread-counts/
GET /profiles/tenant/unread-counts/
```

### Owner response

```json
{
  "visit_requests_count": 4,
  "unread_chat_messages_count": 7,
  "unread_notifications_count": 3
}
```

### Tenant response

```json
{
  "favorites_count": 6,
  "unread_chat_messages_count": 7,
  "unread_notifications_count": 3,
  "visit_requests_count": 2
}
```

### Counting rules

| Field | Required meaning / decision |
| --- | --- |
| Owner `visit_requests_count` | Requests received for properties belonging to the authenticated account. **Proposed badge rule:** pending requests awaiting an owner decision. Confirm whether all requests were intended instead. |
| Tenant `visit_requests_count` | Requests created by the authenticated account. **Proposed badge rule:** active requests, with the backend's existing pending/accepted statuses. Confirm the status set before implementation. |
| `favorites_count` | Total items in the tenant's Favorites collection, across all pages. That screen currently uses `/properties/saved/`; confirm whether this is the intended collection, because property details distinguish `is_fav` and `is_saved`. |
| `unread_chat_messages_count` | Number of unread incoming messages, not the number of conversations. Exclude messages sent by the authenticated account. |
| `unread_notifications_count` | Number of unread notifications, consistent with the existing `/notifications/unread-count/` endpoint. |

All keys must always be present and contain non-negative integers; return zero when no matching records exist. Reading these endpoints must not mark anything as read.

One account can use both workspaces. Chat and notifications are shared account-wide, so their counts must be identical in both responses for the same underlying state. Do not introduce a server role-switch requirement or split those inboxes by the active workspace. Follow [the workspace account contract](WORKSPACE_ACCOUNT_HANDOFF.md).

Calculate counts over the complete authorized dataset, not just the first page. The current chat client derives its count from a page of conversations; the new endpoint should remove that limitation. Counts must reflect message-read, notification-read, favorite removal, and visit-status changes on the next fetch.

**Acceptance:** Verify zero-data accounts, accounts using both workspaces, more than one page of conversations, read operations, favorite changes, and transitions into/out of the agreed visit statuses.

## 5. Support “View all properties” from tenant home

Use the existing property collection rather than introduce a second unfiltered listing API:

```http
GET /properties/?page=1&page_size=10&ordering=-created_at
```

The current client expects this pagination payload:

```json
{
  "count": 0,
  "next": null,
  "previous": null,
  "results": []
}
```

- Without optional filters, return all properties eligible for public tenant browsing, across pages; do not restrict results to a home preview or the signed-in account's own properties.
- Each item must use the existing property-card/list schema, including identity, title, media, price, location, rating, and applicable favorite/saved state.
- Retain existing search and filter query parameters. The client already sends `search`, `property_type`, `price_min`, `price_max`, and other property filters.
- Return accurate `count`, `next`, and `previous` values with stable ordering across pages.
- The existing `homepage` endpoint already has a paginated client consumer; preserve its response when making this change.

The mobile team must wire the “View all” action to the full collection. If `/properties/` already satisfies these rules, the backend deliverable is verification and documentation of that contract.

**Acceptance:** A dataset larger than one page can be browsed completely, with no preview-only cap, duplicate page items, or leaked unpublished listings.

## 6. Add the tenant “My rates” endpoint

```http
GET /profiles/my-rates/?page=1&page_size=10
```

**Proposed interpretation:** return ratings/reviews submitted by the signed-in tenant. Confirm whether the request instead means ratings received by the tenant before finalizing the schema.

Use the existing pagination structure. Each item should identify the review, property, and visit, and expose the rating, comment, and submission time:

```json
{
  "id": "review-id",
  "property_id": "property-id",
  "property_title": "Apartment in Cairo",
  "property_image": "https://media.example.com/properties/property-id/main.jpg",
  "visit_id": "visit-id",
  "rating": 4,
  "comment": "The property matched the listing.",
  "created_at": "2026-09-28T14:13:00Z"
}
```

- Return only reviews belonging to the authenticated tenant under the agreed interpretation.
- Use a numeric rating on the existing rating scale; the current mobile rating UI uses five stars.
- Return the stored comment, including an empty string if no comment was entered, and an ISO 8601 timestamp with timezone.
- Sort newest first, with a stable tie-breaker, and return an empty paginated collection when appropriate.
- Reuse existing review records and IDs. Document any criterion ratings already stored by the backend instead of inventing a second scoring system.

**Integration dependency:** the current `VisitRatingSheet` is presentation UI; no rating submission endpoint was found in its flow. Provide the existing submission contract, or flag submission as a separate missing dependency. This request specifically asks for the “My rates” read endpoint.

**Acceptance:** Two tenants cannot read one another's private review history; an account's stored reviews appear with correct pagination and property references.

## 7. Add About us, privacy policy, and terms content

Provide these proposed public read endpoints:

```http
GET /pages/about-us/
GET /pages/privacy-policy/
GET /pages/terms/
```

Use a consistent payload for all three:

```json
{
  "slug": "about-us",
  "title": "About us",
  "content": "Approved page content supplied by the product team.",
  "content_format": "plain_text",
  "language": "en",
  "updated_at": "2026-09-28T00:00:00Z"
}
```

- Serve Arabic and English through the project's existing language-selection convention; document the request mechanism and fallback behavior.
- Agree on one content format with mobile. The proposed format above is plain text with paragraph breaks; if existing content is HTML, declare that format explicitly before integration.
- Return the approved content from backend-managed storage so updates do not require an app release.
- Allow access before login and from either workspace.
- Do not treat the sample sentence above as actual About us, privacy, or terms copy. The product team supplies the approved text.

**Acceptance:** Each page is available without login, returns the requested supported language, and exposes content updates through the same stable URL.

## 8. Add “Complete register” for missing identity documents

```http
POST /auth/complete-register/
Content-Type: multipart/form-data
```

Authenticate the existing account and fill in its missing registration/KYC fields. Do not create another account or require the user to repeat their password and basic registration data.

Reuse the field names already sent by `RegisterBody`:

| Field | Type | Behavior |
| --- | --- | --- |
| `national_id` | String | National ID number; preserve string representation. Current mobile validation expects 14 characters; enforce the agreed ID format server-side. |
| `front_id_image` | Uploaded image | Front of the national ID |
| `back_id_image` | Uploaded image | Back of the national ID |
| `selfie_image` | Uploaded image | Existing registration/KYC field; confirm whether required for this completion endpoint |

The requested minimum is the national ID number plus front/back images. The current KYC screen also requires a selfie, so resolve that requirement explicitly with mobile.

Implementation behavior:

- Resolve the account from the authenticated session; do not accept a target user ID to select another account.
- Allow omission of valid fields already stored. Omitted fields must not erase existing data. Validate the combined existing and submitted data before marking completion.
- Preserve the existing verification workflow. Uploading documents may move the account to review; it must not automatically mark identity as verified.
- Validate image type, size, and readability, and return field-specific errors for invalid or still-missing required fields.
- Retrying the same submission must not create duplicate accounts or duplicate verification requests. Document how rejected documents may be replaced and how pending/approved submissions are handled.
- Return completion state and remaining requirements. Keep uploaded identity files out of public property/media responses.
- Reflect the updated state in `GET /auth/users/me/` and the account/profile endpoints used by the app.

Proposed success payload; map these names/statuses to existing verification fields where available:

```json
{
  "registration_complete": true,
  "verification_status": "pending",
  "missing_fields": []
}
```

Here `registration_complete` means the required registration data was supplied. It does not mean identity review was approved.

**Acceptance:** An account with missing documents can complete them without re-registering; already supplied data is preserved; invalid files produce field errors; repeat submissions do not duplicate records; and verification status remains accurate.

## Decisions and delivery

Resolve these points when returning the API contract:

1. Final paths for the proposed endpoints, property-link host, and the mobile/web link configuration owners.
2. The included visit statuses for each count and whether Favorites means the current saved-property collection.
3. Whether “My rates” means submitted or received reviews, and the available rating-submission contract.
4. Whether selfie upload is required to complete registration, plus the existing verification status values.
5. Media limits, schedule timezone, and the content language/format convention.

Deliver the implemented routes in the project's API documentation or Postman collection, including request fields, response envelopes, pagination, errors, and sample records. Provide staging evidence for each section's acceptance criteria and identify any mobile integration still required.

### Repository references

- [Endpoint constants](packages/core/lib/core/network/api_endpoints.dart)
- [Property creation fields](apps/sokoun_app/lib/features/owner/home/data/models/owner_add_property_content.dart)
- [Received visit parser](apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_request_content.dart)
- [Property listing filters and pagination](apps/sokoun_app/lib/features/tenant/home/data/models/property_search_model.dart)
- [Favorites data source](apps/sokoun_app/lib/features/tenant/favorites/data/favorites_data.dart)
- [Registration upload fields](apps/sokoun_app/lib/features/shared/auth/data/models/register.dart)
- [KYC completion validation](apps/sokoun_app/lib/features/shared/auth/data/models/kyc_upload_documents_data.dart)
