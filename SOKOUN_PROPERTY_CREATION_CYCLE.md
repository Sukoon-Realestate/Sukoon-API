# Sokoun — Property Creation Cycle

Prepared for GPT. Source: the Flutter implementation in `apps/sokoun_app`, reviewed on **2026-10-07**.

Use this document as context for **creating a new property only**: opening the owner form, completing its three steps, reviewing the draft, saving the listing, uploading its media, recovering interrupted submission, and receiving the moderation outcome. The behavior below comes from the mobile code. Backend requirements and unresolved integration details are identified separately; this document does not claim live backend verification.

## 1. Cycle overview

```text
Owner → My properties → Add property
  → Resume a local creation draft, or start a new one
  → Step 1: Basic details and map location
  → Step 2: Photos and required video
  → Step 3: Pricing, rental terms, description and optional details
  → Owner reviews the complete form
  → Create the property with its cover image, video and optional ownership proof
  → Store the returned property ID and media acknowledgements
  → Upload the remaining photos to that property
  → Clear the local draft after successful submission
  → Show the submitted / under-review screen
  → Backend moderation: accepted or rejected
```

Property creation is free. The authenticated account and server authorization determine which owner may create the listing.

## 2. Entry and navigation

- The main entry is the **Add** action in **My properties**, including its empty-state action.
- New creation opens `OwnerPropertyFlowScreen` without an existing property argument.
- The form has three steps and a separate success page. Step changes use the buttons; swiping between steps is disabled.
- Back moves to the previous step. Leaving an unfinished form offers **Stay**, **Save and exit**, or **Discard local draft**.
- During submission, form interaction and back navigation are blocked to prevent overlapping submissions.

## 3. Step 1 — Basic details and location

| Field | Mobile rule | Request field |
| --- | --- | --- |
| Property type | Required; select a backend-provided type | `property_type` uses the type slug |
| Listing title | Required, nonblank | `title` |
| Governorate | Required; select a real option | `governorate` uses its ID |
| City | Required; options depend on the governorate | `city` uses its ID |
| Address / street | Required, nonblank | `street`; also the initial `district` fallback |
| Bedrooms | Positive integer, at least 1 | `bedrooms` |
| Bathrooms | Positive integer, at least 1 | `bathrooms` |
| Area in square metres | Positive integer, at least 1 | `area` |
| Floor | Optional; if supplied, an integer, including 0 or a negative floor | `floor`; blank is sent as `""` |
| Map location | Required, explicitly confirmed valid coordinates | `latitude`, `longitude` |

Selecting a different governorate clears the selected city and map location. Changing the city or address also clears the map location, so the owner must confirm it again.

The location picker supports address search, selecting a point on the map, device location, and a satellite view. Confirmed coordinates are sent with six decimal places. Latitude must be between -90 and 90 and longitude between -180 and 180; both must be finite.

**Next: Photos** validates this step and directs the owner to the first invalid field when validation fails.

## 4. Step 2 — Photos and video

### Photos

- Require **10–25 photos**. The picker limits additions to the remaining capacity.
- The first photo is the **cover / main image**.
- Before submission, the owner can replace or remove photos, reorder them, and select a different cover. Selecting a cover moves it to the first position.
- Each photo may have an optional **name** and **description**.
- After an interrupted submission, acknowledged photos are represented by their saved server IDs and URLs; pending photos retain their local files.

The mobile readiness check counts photo entries and requires each to have a local file or existing URL. Unique-photo enforcement is a backend requirement in the existing handoff; the readiness check itself does not compare image contents.

### Video

- A property tour video is **required**.
- Its duration must be **1–60 seconds inclusive**.
- The owner can select a gallery video or record one. The app probes the selected file before accepting it and offers a preview.
- The next action is unavailable while the video is being prepared.
- A fresh creation must upload a local video file; an arbitrary video URL alone cannot satisfy the creation request.
- If the server already acknowledged the video during this same creation attempt, recovery can retain that saved video instead of uploading it again.

**Next: Pricing** validates the video and minimum photo count. Final submission also checks the maximum photo count and media readiness.

## 5. Step 3 — Pricing and rental details

| Field | Mobile rule | Request field |
| --- | --- | --- |
| Rent amount | Required, finite number greater than zero; decimal entry supported; displayed in EGP | `price`, sent as a trimmed string |
| Billing period | Required: `daily`, `weekly`, `monthly`, or `yearly` | `price_period` |
| Minimum stay | Required positive integer, displayed in **months** | `rental_period` |
| Suitable tenants | Required supported value | `suitable_for` |
| Amenities | Optional multiple selection; unsupported selected values block submission | `amenities` and boolean amenity fields |
| Property description | Required; at least **10 characters** after trimming | `description` |

**Billing period and minimum stay are separate.** For example, a monthly rent of `6500.50` with a minimum stay of 6 months sends `price="6500.50"`, `price_period="monthly"`, and `rental_period=6`.

Supported suitable-tenant values are:

```text
all, families, singles, students, female_students
```

The current supported amenity values are:

```text
wifi, elevator, garage, security, balcony, air_conditioning,
near_metro, natural_gas, electricity_meter, water_meter, furnished
```

Backend option labels are displayed in the selected language. Requests use stable API values rather than the displayed labels. Furnished is sent through `is_furnished` and excluded from the `amenities` array.

### Optional additional details

| Field | Behavior | Request field |
| --- | --- | --- |
| Area description | Optional text describing the space; separate from numeric area | `space` |
| Country | Starts as `Egypt`; editable and optional in mobile validation | `country` |
| Neighborhood | Optional; when supplied, becomes the district | `district` |
| Building year | Optional integer from 1800 through the current year | `building_year` |
| Deposit | Blank, a preset, or a finite custom amount of zero or more | `deposit` |
| Smoking | Allowed, not allowed, or unspecified | `smoking_allowed`: `true`, `false`, or `""` |
| Ownership proof | Optional image attachment for internal review | `ownership_proof` file |

Deposit presets are `none`, `half_month`, `one_month`, and `two_months`. For the initial creation request, an empty neighborhood makes `district` fall back to the address / street text.

An optional listing assistant can suggest a title and description. Applying a suggestion updates the local form, after which the owner still reviews and submits through the normal creation cycle.

## 6. Owner review before submission

The pricing step opens a review sheet only when all three readiness checks pass:

```text
isBasicsReady && isPhotosReady && isPricingReady
```

The sheet presents basic details and coordinates, photo count and captions, video presence, pricing and minimum stay, suitable tenants, amenities, description, and optional details. Each section can return the owner to the relevant form step to correct the draft.

A listing-quality card suggests a longer description of at least 40 characters, captions, deposit information, sufficient photos, a location, and a valid video. These suggestions are advisory; the mandatory description minimum remains 10 characters, and captions and deposit remain optional.

The owner explicitly selects **Submit for review** to start the network submission.

## 7. API calls used by this cycle

Paths are relative to the configured API base. Use the existing authenticated network client. Requests carry the active `Accept-Language: ar` or `en`; server messages and option labels are displayed directly.

| Method | Relative path | Purpose |
| --- | --- | --- |
| GET | `properties/types/` | Property type options |
| GET | `properties/governorates/` | Governorate options |
| GET | `properties/cities/?governorate={id}&search={text}` | Cities for the chosen governorate |
| GET | `properties/filter-options/` | Amenity, billing-period and suitable-tenant option labels |
| POST | `properties/create/` | Create the property using multipart form data |
| POST | `properties/{property_id}/images/` | Upload one remaining photo using multipart form data |
| PATCH | `properties/{property_id}/` | Save changed form data while retrying an already-created listing from this same creation attempt |
| GET | `properties/owned/?status=under_review&page=1&page_size=10` | Read the owner's under-review listings after returning to My properties |

The retry PATCH is part of recovering a partially completed creation. Normal management of existing listings is outside this document's scope.

### Initial creation request

The first POST sends the completed form, **one cover image**, the required video and its duration, and optional ownership proof. Other photos are uploaded after the property ID is known.

The following illustrates multipart field values; `<...>` entries represent selected IDs or binary file parts, not literal request strings:

```text
title: Furnished apartment in Nasr City
description: Two-bedroom apartment with a balcony near public transport.
property_type: <selected type slug>
governorate: <selected governorate ID>
city: <selected city ID>
district: <neighborhood, or street fallback>
street: <owner-entered address>
country: Egypt
latitude: 30.056100
longitude: 31.330000
bedrooms: 2
bathrooms: 1
area: 120
space: <optional area description>
floor: 3
price: 6500.50
price_period: monthly
rental_period: 6
suitable_for: families
building_year: <year, or empty string>
deposit: one_month
smoking_allowed: false
is_furnished: true
has_wifi: true
has_elevator: true
has_garage: false
has_security: false
has_balcony: true
has_air_conditioning: false
near_metro: false
has_natural_gas: false
has_electricity_meter: false
has_water_meter: false
amenities: ["wifi","elevator","balcony"]
main_image: <cover image file>
main_image_name: Living room
main_image_description: Bright living room with balcony access
video: <property tour video file>
video_duration: 35
ownership_proof: <optional proof image file; omitted if absent>
```

`amenities` is a **JSON-encoded array string** in the multipart request. Numeric form fields are parsed or retained as described in the field tables and serialized by the network layer. An empty optional floor is sent as `""`.

### Response and additional image uploads

1. The create response is mapped to `PropertyDetailsModel`. A **nonblank property ID** is mandatory; a response without it is rejected by the mapper.
2. The screen retains this property ID for the rest of the creation attempt.
3. The response should acknowledge the cover through `main_image`, `main_image_id`, cover caption fields, and its image record. The mobile uses this acknowledgement to mark the cover as already uploaded.
4. Returned `video`, `video_duration`, and `ownership_proof` acknowledge the uploaded files; acknowledged files become saved server references in the draft.
5. Remaining local photos upload concurrently to `properties/{property_id}/images/`, each with `image`, `name`, and `description`.
6. Each image response must contain a **nonblank `id` and `image` URL**. Its `name` and `description` should preserve the supplied captions.
7. Each acknowledged photo is recorded in the form and local draft even if another photo upload fails.
8. Only a successful save and successful completion of the remaining image uploads advance the mobile to the submitted page.

The mobile does **not** call a separate finalize, publish, or moderation-submission endpoint after the uploads.

## 8. Local drafts and interrupted submission

- Creation drafts are saved on the device per account, with a separate `new` creation slot.
- The draft includes the current form step, fields, coordinates, photo order and captions, video, proof attachment, saved property response, and acknowledged image references.
- Local media is copied into the app's private support directory. The draft manifest is written through a temporary file and rename.
- Changed forms autosave after a short debounce. The app also flushes pending writes when leaving the foreground and supports an explicit **Save draft** action.
- Reopening an unfinished creation offers **Resume draft** or **Discard local draft**.
- Missing local files are reported and removed from the restored media selection; required photos or video must be selected again before submission.
- Draft load failures present a retry screen. Save failures show a warning and retry action.

If creation succeeded but a later photo upload failed, the retry reuses the saved property ID and skips acknowledged images. If the form has not changed since its saved server snapshot, the property save is skipped. Otherwise, it PATCHes that same property before retrying pending uploads.

The local draft is cleared after successful completion. Discarding a local draft clears device storage only; it does not cancel a property already created on the server during a partial submission.

Local recovery cannot guarantee duplicate-free creation or uploads when the server applied a request but its response was lost. The current creation and image-upload bodies contain **no idempotency key**. Server idempotency or another reconciliation contract remains necessary for that case.

## 9. Submitted screen and moderation outcome

After successful submission, the creation flow shows **Under review**, the backend submission message, and a summary of type, location, price, photos, video, supplied captions, and the device-recorded submission time.

The owner can select:

- **View my properties**: return to the caller; the My properties entry refreshes its currently selected listing tab.
- **Add another property**: reset the form and begin a new creation cycle.

The My properties screen initially selects **Under review**. It also provides **Accepted** and **Rejected** tabs. The mobile understands `under_review` as a pending status and `accepted` / `rejected` as moderation outcomes. A rejected listing should include a real `rejection_reason` from the server.

The submitted screen currently says review takes **24–48 hours** and the outcome appears in notifications. This is existing UI copy, not a verified backend service guarantee. Acceptance, publication eligibility, and review notifications must be driven by the backend; proof attachment or a completed quality card does not grant verification.

## 10. Backend requirements to confirm for this cycle

These are integration requirements from the mobile flow and existing repository handoffs, not evidence that the server has delivered them:

1. Authorize the authenticated owner on creation and every subsequent media operation; validate location IDs, stable option values, fields, and file contents server-side.
2. Support the staged submission: the initial create request contains only the cover image, so the remaining minimum photo count cannot be required in that first POST. Keep an incomplete listing out of public results and confirm when it becomes eligible for moderation.
3. Enforce **10–25 unique photos** and a valid **1–60 second video** before publication. Enforce the maximum photo count safely during concurrent uploads.
4. Return stable property/image IDs, usable media URLs, captions, and the cover acknowledgement so recovery can reuse saved resources.
5. Define review scheduling and completion for staged uploads. The mobile currently sends no finalization request; introduce a new endpoint only through an explicit backend/mobile contract change.
6. Define idempotency or reconciliation for lost create/upload responses. A persisted local property ID protects acknowledged retries only.
7. Confirm persisted photo ordering. The mobile allows ordering before creation, but concurrent additional uploads send no explicit position field. Cover-first responses and arbitrary non-cover ordering require server agreement.
8. For recovery PATCHes, preserve omitted uploaded video/proof files. The serializer sends JSON-encoded `retained_image_ids` and `images_metadata` for acknowledged photos, and may send `main_image_id`; validate those IDs against this property and apply the update atomically.
9. Keep ownership proof private and distinct from public listing photos/video; proof attachment alone must not mark the owner or property verified.
10. Return an accurate moderation status, rejection reason when applicable, localized messages, and consistent owner-list results after creation and review decisions.

## 11. Source references

All paths below are relative to the repository root. The cycle is fully described above so this file can be shared without the repository.

- `apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_properties_screen.dart` — creation entry and list refresh.
- `apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_property_flow_screen.dart` — steps, review, submission, recovery and success handling.
- `apps/sokoun_app/lib/features/owner/home/data/models/owner_add_property_content.dart` — fields, readiness checks and multipart request mapping.
- `apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/` — step forms, video selection, owner review and submitted screen.
- `apps/sokoun_app/lib/features/owner/home/presentation/cubits/property_submission_cubit.dart` — initial POST and recovery PATCH.
- `apps/sokoun_app/lib/features/owner/home/presentation/cubits/upload_property_images_cubit.dart` — concurrent remaining-photo uploads and acknowledgements.
- `apps/sokoun_app/lib/features/owner/home/data/owner_draft_data.dart` and `presentation/cubits/owner_draft_cubit.dart` under the same feature — local persistence and recovery.
- `packages/core/lib/core/helpers/validators.dart` — numeric, coordinate, photo-count and video-duration rules.
- `packages/core/lib/core/network/api_endpoints.dart` — endpoint paths.
- `SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md`, section 4.3, and `docs/owner_property_status_tabs_backend.md` — creation-related backend requirements and moderation tabs.
