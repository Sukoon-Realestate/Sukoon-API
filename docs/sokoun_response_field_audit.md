# Sokoun response field audit

Reviewed `collection.json` and the request/response models and consumers under `apps/sokoun_app/lib`. The collection contains 58 requests and 43 JSON response examples, with 561 distinct field paths counted per request. Sixteen requests have no saved JSON response. Testing uses those saved examples; it does not contact the backend.

## Changes

| Response fields | Where they are now used |
| --- | --- |
| Home `images_count`, `property_type` | Photo-count badge and property-type metadata on tenant home cards. Invalid star scores outside 0–5 display as unavailable. |
| Property `floor`, `suitable_for`, `smoking_allowed` | Rental details section with localized labels. Missing floor/smoking values stay unknown; an explicit ground floor or `false` is preserved. |
| Existing model `building_year`, `deposit` | Optional rows in the same rental details section when values are provided. These fields are modeled but are absent from the collection examples. |
| Property `images[].name`, `images[].description` | Gallery captions. One ordered gallery source aligns URLs, names, and descriptions, removes duplicate URLs and ignores images with no URL. |
| Owner request `tenant.avatar`, `property.district`, `subtitle`, `status_label` | Tenant avatars, property context and backend display copy in request cards. A schedule already included in the subtitle is not repeated. |
| Owner request `is_verified_tenant`, `verification_warning`, `actions.can_chat` | Verification badge/warning and the chat action. Explicit backend chat restrictions are respected. |
| Calendar `month_label`, `selected_date_label`, `time_formatted`, `status_label`, `tenant.avatar`, `tenant.initial` | Calendar header and visit cards, with existing localized fallbacks for sparse responses. |
| Calendar `days[].visit_count` | Existing visit markers plus accessible day labels with visit counts. Day selection remains accessible. |
| Reviews `tenant.avatar` | Reviewer avatar, retained in cache serialization with the existing name, verification and rating details. |
| Tenant account `menu_items.visit_requests.*`, `menu_items.verification.*` | Visit-request shortcut and verification title/subtitle in the profile menu. Visit requests open the existing visits screen. |

JSON parsing, defaults, equality and cache serialization remain in `data/`. Rental details, photo captions/viewer, verification warnings and tenant avatars are extracted presentation widgets. Screens retain orchestration and lifecycle ownership. New copy comes from `lang.json` and the existing translation generator. Styling follows `design.md`.

## Coverage and fields without additional UI

| Response area | Review result |
| --- | --- |
| Authentication and legacy profile endpoints | Identity, name, email, phone, gender, birth date, avatar and verification fields already support registration, account loading and profile editing. Account membership display uses the dedicated profile membership labels. |
| Tenant home, search, property details and location/type lookups | Existing title/media, prices/periods, rooms/area, furnishing, ratings, amenities, verification, maps and filtering remain in use. New rental details and media metadata are listed above. Lookup IDs, slugs, parent relationships and timestamps do not require extra display rows. |
| Owner dashboard and listings | Owner identity/verification, dashboard metrics, pending visit previews, listing status, views and visit counts already have consumers. Create/upload responses supply resource identities and retained media metadata. |
| Saved properties | Saved state, filters and sorting already consume property attributes and `saved_at`. Save/unsave acknowledgements support the existing state change. |
| Tenant visits and reviews | Scheduling, status labels, permitted actions, owner contact, notes, reviews and rating breakdowns already have consumers. Property location/price/bedroom details are shown on visit details rather than repeated in every list row. |
| Owner requests, calendar and availability | Permission/state changes, privacy notices, membership labels, notes, dates and slot states already have consumers. Newly surfaced request/calendar fields are listed above. Availability week boundaries overlap the day range already displayed. |
| Tenant/owner account and summary | Existing identity, membership, completion, verification, statistics, contracts/reviews counts, privacy and account details already have consumers. The newly connected menu fields are listed above. |
| Other app models | Chat online/verification state, queued messages and message metadata already have consumers. Notification appointment/action fields are consumed through presentation getters; revenue amounts/changes and formatted acceptance rates are also consumed through getters. These are not unused simply because a widget does not reference the underlying field directly. |

The following exclusions are intentional:

- Envelope status/messages and pagination fields belong to transport, errors and pagination. They are not new product attributes.
- IDs, lookup slugs and resource timestamps are retained or handled where needed for identity, requests, editing, cache or sorting. Public display does not require a row for each one.
- Identity image/selfie fields, national ID and ownership proof are verification inputs/internal documents. This change does not turn them into public property or participant media.
- `is_fav` is retained for compatibility; `is_saved` remains the state used by the documented save/unsave flow.
- `alternative_search_filters` is `null` in every saved example. The existing alternative-search action remains available; no filter structure or criteria are invented from a null sample.
- Testing-only profile enumeration, the testing login request and the deprecated calendar example do not create app features. Owner detail/accept/reject examples are saved with HTTP 404 despite containing example payloads; model tests verify the payload shapes, not live endpoint availability.
- Contracts counts are already visible, but the collection does not supply a contracts endpoint. No new contracts screen is fabricated.
- Empty arrays/null values and models for endpoints absent from the collection cannot establish a new response contract. Public-page format metadata and registration verification status are not rendered as raw technical strings.

## Verification

`response_fields_test.dart` covers real collection payloads, cache round-trips, sparse responses, unknown versus explicit rental terms, gallery alignment, reviewer avatars and backend chat restrictions. `response_ui_test.dart` exercises six affected UI sections in Arabic/English at 320, 390, 600, 768, 1024 and 1366 logical pixels and text scales 1, 1.3 and 2. It also checks missing rental information, stale warnings, chat permissions and calendar semantics. PNG export supports rendered phone/tablet review through `UI_REVIEW_DIR`.

Photo download/navigation, owner requests, profiles, property submission/details, pagination and backend handoff tests remain part of validation. Rendered review uses the saved examples; remote photos and live backend/device behavior are not verified by these widget tests.

Final validation: all 1,582 Sokoun tests pass, including 216 responsive response-UI combinations. Forty-eight PNGs were exported for phone/tablet rendering checks. Analysis reports no errors and the same two pre-existing warnings (generated assets import and the path dependency publishing warning). `git diff --check` passes.
