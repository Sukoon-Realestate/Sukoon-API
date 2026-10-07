# Rental offers: mobile implementation and proposed backend contract

**Accommodation form revision, 7 October 2026:** see [the backend implementation guide](rental_accommodation_forms_backend_changes.md). Room/group/bed fields now lead the first step, property context is separate, partial property totals are optional, and new detailed fields/media references are durable local draft data. These additions require an agreed contract extension and keep server publication gated. The guide supersedes earlier form/media descriptions below where they differ.

Date: 2026-10-07. Contract proposal: rental inventory v1.

**Backend implementation is absent from this checkout. None of the new fields, headers, query parameters, or endpoint extensions below is a deployed contract.** Every JSON example in this document describes **proposed** fields and semantics unless explicitly marked existing. The mobile implementation defaults all new server operations to disabled and never sends offer fields to the legacy service in that configuration. There are no new endpoint constants claiming an offer service exists.

## Baseline and repository findings

The available business baseline is [PROJECT_BUSINESS_DETAILS.md](../PROJECT_BUSINESS_DETAILS.md); the separately named `PROJECT_BUSINESS_DETAILS(2).md` attachment was not present. The agreed implementation uses the checked-in baseline. Verified paths include `apps/sokoun_app`, `packages/core`, [collection.json](../collection.json), [the current media handoff](../MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md), [owner status tabs](owner_property_status_tabs_backend.md), `design.md`, and the app's repository instructions. The root collection is wrapped under `collection`.

Existing property models combine physical structure with price, deposit, suitability, minimum rental months, and description. Existing favorites and viewing requests identify a property; chat creation identifies a recipient `user_id`. These are the indivisible-listing assumptions addressed by the client change. Existing API routes and moderation/media behavior are retained.

The client adds a small shared `rental_offers/data` domain with rooms, nested beds, offers, terms, inventory, an authoritative grouped-list projection, and immutable selected/historical accommodation snapshots. It uses existing AsyncCubits, CRUD/network/cache infrastructure, AppPagify collections, Go navigation, durable owner drafts, localization, and design tokens.

## Implemented journeys and operational boundary

Owners see “إيه الجزء اللي حابب تأجّره؟” early, retain their physical address/room count/media, define named rooms and beds, and create independent offers with separate prices and terms. A group selects two or more actual rooms for one combined price. Changing whole/partial mode parks the other mode in the local draft; parked offers never enter a request. Scope changes retain typed terms, clear incompatible room/bed and offer-photo selections, exclude irrelevant references from submission, and revalidate. Incomplete local room drafts stay recoverable when whole mode hides them, while existing room IDs remain in edits. Shared defaults and individual overrides are explicit. Existing unsaved-change and upload-recovery protection applies.

With default configuration, these are complete durable **local drafts**, labeled as local at every step and in review. The final action says “Save draft on this device”; it does not create a property, publish, or imply server persistence. The original property-only creation/editing path remains available. Offer reads can render server-supplied v1 data without enabling writes. Unknown/malformed schemas and scopes are displayed safely and cannot authorize a booking.

Tenant discovery is grouped by physical property. Cards use server-provided offer labels, count, scope, minimum eligible price and rent period. Details require choosing an offer and then pressing “Confirm accommodation”, including when there is only one offer. A deep link highlights its referenced offer without confirming it. Confirmation stores the exact snapshot and survives the sign-in return; changed terms or accommodation metadata require another confirmation. An unavailable choice stays selected and cannot start a viewing or chat. Favorites retain exact selections. Viewing summaries/review/confirmation carry the choice. Historical visits, owner requests/calendar, notifications, chat context, reviews, contracts, invoices and revenue models preserve supplied snapshots. A missing historical snapshot is identified as missing instead of filled from a current property price.

Offer availability/archive actions use the proposed extension of the existing property PATCH only when both configuration and fresh server action permissions permit them. The app verifies the response before applying success. Selecting “Mark rented” does not create a lease. Existing property-only digital lease creation is blocked for offer-based properties until a lease contract identifies the offer. Actual server payment/revenue amounts remain unchanged.

## Entities and stable identity (all additions proposed)

| Entity | Relationships and responsibilities |
| --- | --- |
| Property (existing ID preserved) | Owner, physical type, address/coordinates, total bedrooms/bathrooms/area, shared facilities, public property media, private ownership evidence, moderation/publication. |
| Room | Permanent server ID belonging to one property; owner-visible name/number, capacity, details, optional private/shared bathroom access, associated property media. |
| Bed | Permanent server ID nested under exactly one room; name/number and optional media. No resident identity. |
| Rental offer | Permanent server ID belonging to one property; scope, room references and optional bed reference, its own price/period/terms, availability, archive flag, revision, permissions and media references. |
| Shared defaults | Optional property inventory defaults for minimum months, deposit, suitability, description, smoking and rules. Price and price period always belong to an offer. |
| Selected/historical accommodation | Property ID + offer ID + immutable snapshot/revision. Preserves exact room/bed labels and terms for the relevant event. |

`property_type` is unchanged. `rental_scope` accepts exactly `entire_property`, `room`, `room_group`, `bed`. `mode` accepts `whole` or `partial`. A property's `bedrooms: 3` and an offer's `room_ids: [room_a, room_b]` retain both physical and offered counts.

Creation uses `client_key` only for draft references. The client generates local UUIDs for draft identities and uses them in intra-request references; they are **not** backend offer IDs. The server allocates permanent IDs, resolves references atomically, and echoes each creation `client_key` with its assigned ID in the full response. Existing IDs must remain stable across rename, edit, rent, archive and review. Never recycle them. Scope changes that would replace an existing accommodation identity require explicit server rules; the editor locks persisted whole/partial mode, scope, room and bed allocations. A server-verified transition contract is required to unlock these changes; price and permitted terms still follow the existing revision/review path.

A mode switch must be validated as an inventory transition. Omitted previously persisted offers are not instructions to hard-delete their requests/leases. Reject transitions with unresolved dependencies, or implement an explicitly documented archival policy with snapshots and audit records. Do not automatically cancel requests, end leases, or release occupancy.

## Proposed owner write extension of existing endpoints

Existing routes:

- `POST properties/create/` (multipart).
- `GET/PATCH properties/{property_id}/` (full property read/edit).
- `POST properties/{property_id}/images/` (existing photo upload).
- `GET properties/owned/?status=under_review|accepted|rejected` (existing status handoff).
- `DELETE properties/{property_id}/delete/` (existing whole-property deletion, with dependency checks).

**Proposed extensions, disabled by default:** owner POST/PATCH accept a multipart string field `rental_inventory` containing the following JSON. `X-Rental-Offers-Version: 1` selects the proposed write contract. New property creation additionally sends `Idempotency-Key` with a stable draft submission key. Property PATCH uses inventory `expected_revision` rather than reusing the creation idempotency key for different edits.

Illustrative proposed room-group creation JSON (physical fields/media remain on the parent multipart request):

```json
{
  "schema_version": 1,
  "mode": "partial",
  "expected_revision": 0,
  "rooms": [
    {"client_key": "draft-room-a", "name": "غرفة ١", "capacity": 2, "bathroom_access": "shared", "description": "غرفة مطلة على الشارع", "beds": []},
    {"client_key": "draft-room-b", "name": "غرفة ٢", "capacity": 1, "bathroom_access": "private", "description": "غرفة بحمام خاص", "beds": []}
  ],
  "shared_defaults": {
    "rental_period": 3,
    "deposit": "one_month",
    "suitable_for": "students",
    "description": "مرافق مشتركة تشمل المطبخ وغرفة المعيشة",
    "smoking_allowed": false,
    "rules": ["الهدوء مساءً"]
  },
  "offers": [
    {
      "client_key": "draft-group",
      "rental_scope": "room_group",
      "name": "الغرفتان معًا",
      "room_ids": ["draft-room-a", "draft-room-b"],
      "term_overrides": {"price": "5000.00", "price_period": "monthly", "description": "غرفتان معًا بسعر واحد"},
      "inherited_fields": ["rental_period", "deposit", "suitable_for", "smoking_allowed", "rules"],
      "availability": "available",
      "archived": false
    }
  ]
}
```

Two independent rooms instead produce **two offers**, each with a single distinct `room_ids` element and its own `term_overrides.price`, `price_period`, and availability. The client never divides a group/property price to invent them.

Proposed bed fragment:

```json
{
  "rooms": [{"id": "room_a", "name": "غرفة مشتركة", "capacity": 2, "bathroom_access": "shared", "description": "غرفة بسريرين", "beds": [{"id": "bed_a1", "name": "السرير قرب النافذة"}, {"id": "bed_a2", "name": "السرير الآخر"}]}],
  "offers": [{"id": "offer_a1", "rental_scope": "bed", "name": "سرير قرب النافذة", "room_ids": ["room_a"], "bed_id": "bed_a1", "term_overrides": {"price": "1500.00", "price_period": "monthly", "rental_period": 3, "deposit": "one_month", "suitable_for": "students", "description": "سرير محدد داخل غرفة مشتركة", "smoking_allowed": false, "rules": []}, "inherited_fields": [], "availability": "available", "archived": false}]
}
```

A second bed for independent rent needs a different offer ID referencing `bed_a2`; changing `offer_a1` to rented leaves that other non-overlapping offer's state intact.

`entire_property` contains no `room_ids` or `bed_id`; room/group contains no `bed_id`. `rental_period` remains a **minimum term in months**, separate from `price_period` (`daily`, `weekly`, `monthly`, `yearly`). New partial requests omit legacy root price/period/suitability/deposit/minimum months/smoking/offer description rather than submitting contradictory values. The proposed server must accept this distinction; legacy mandatory root pricing validation cannot be applied to a v1 partial property. Whole-mode submissions retain the existing full-property form and mirror its rental terms into the single offer.

`term_overrides` contains only explicit fields; `inherited_fields` names the permitted default fields. Reject unknown inherited fields and conflicting override/inheritance declarations. Return resolved `terms` plus `inherited_fields` so the editor and historical snapshots have a single effective meaning.

## Proposed full read response

Keep the existing response envelope, property IDs, physical fields, cover/captions and private evidence rules. Full responses add the following proposed inventory shape:

```json
{
  "id": "property_a",
  "property_type": "apartment",
  "bedrooms": 3,
  "status": "under_review",
  "rental_inventory": {
    "schema_version": 1,
    "mode": "partial",
    "revision": 12,
    "rooms": [{"id": "room_a", "client_key": "draft-room-a", "name": "غرفة مشتركة", "capacity": 2, "bathroom_access": "shared", "description": "غرفة بسريرين", "media_ids": ["image_room"], "beds": [{"id": "bed_a1", "name": "السرير قرب النافذة", "media_ids": []}]}],
    "shared_defaults": {"rental_period": 3, "deposit": "one_month", "suitable_for": "students", "description": "مرافق مشتركة", "smoking_allowed": false, "rules": []},
    "shared_media_ids": ["image_kitchen"],
    "offers": [{"id": "offer_a1", "client_key": "draft-offer-a1", "rental_scope": "bed", "name": "سرير قرب النافذة", "room_ids": ["room_a"], "bed_id": "bed_a1", "terms": {"price": "1500.00", "price_period": "monthly", "rental_period": 3, "deposit": "one_month", "suitable_for": "students", "description": "سرير محدد داخل غرفة مشتركة", "smoking_allowed": false, "rules": []}, "inherited_fields": [], "availability": "available", "archived": false, "revision": 7, "media_ids": ["image_bed"], "offer_link": "https://sokoun.app/properties/property_a/offers/offer_a1", "is_saved": false, "actions": {"can_archive": true, "can_set_availability": true}}]
  }
}
```

Owner write success must return the **full saved property**, real room/bed/offer IDs, echoed client keys for newly created entities, resolved terms, retained associations, and updated revisions. The client checks identity, scope, selections, names, room details, terms, availability and supported media fields. A missing inventory, ignored fields, substituted accommodation or contradictory price fails confirmation. A returned property ID is retained for recovery even if inventory confirmation fails; subsequent recovery uses PATCH. A response that only says “success” is insufficient.

Public read eligibility is authoritative. Do not return private `ownership_proof` to tenants, guests, favorites, chat, notifications or sharing. Owner responses may include archive/unavailable offers and permissions; public responses should retain an explicitly requested inaccessible/archived ID as a tombstone or return an understandable unavailable response without substituting another offer.

## Inventory, permission and concurrent validation

Authoritative validation belongs in a backend transaction with appropriate row locks/unique constraints and revision checks. Client validation is only assistance.

- `whole`: exactly one active entire-property offer; no simultaneous conflicting partial inventory.
- `partial`: room, room-group, or bed offers; at least two distinct rooms per group, exactly one room per room/bed offer. All selected rooms belong to this owner's property. A bed belongs to its referenced shared room. Shared-room capacity must be at least two, and identified beds cannot exceed capacity.
- No room in two non-archived room/group offers; no whole-room offer plus bed offers in that room; no duplicate bed offer. Rented/unavailable offers still retain their inventory identity until an explicit server transition releases it. Archived offers do not allocate new offers but dependencies remain retained.
- A room/bed/offer ID cannot be reassigned to another property or owner. Reject client keys that collide or resolve ambiguously. Never authorize ownership from the workspace UI or submitted IDs.
- Check action permissions, moderation/verification, existing requests and active leases on every write. The client requires `actions.can_archive` / `can_set_availability` from a fresh read; it does not invent permissions from an accepted review state.
- `expected_revision` must match the current inventory revision. Increment inventory revision and affected offer revision on relevant changes. Two concurrent owners/sessions cannot both allocate overlapping inventory or overwrite newer prices.
- Proposed `409` conflicts include `inventory_revision_conflict`, `inventory_overlap`, `offer_unavailable`, `active_lease_dependency`, `active_request_dependency`, and `mode_transition_blocked`. Proposed `422` validation errors identify invalid fields/room/bed references. Use the existing readable `message` failure envelope so current error UI handles these; a future structured detail may add `code`, `offer_id`, `room_ids`, `bed_id`, `current_revision`.
- On conflict, apply no partial inventory writes. Keep the local draft/selection and require a refresh/review; never remap a request to the property or another offer. Return `403` for ownership/permissions and `404` for invisible resources without disclosing private records.

Availability is `available`, `unavailable`, or `rented`; archive is a separate boolean. Unknown future values render as unconfirmed and cannot authorize a viewing. `rented` is a server-confirmed owner action with dependency/lease checks; this change does not build an occupancy or lease-creation engine. Do not compute current occupancy from capacity or expose residents' identities.

## Moderation and publication

The documented property PATCH returns the property to `under_review`. **Offer edits, associations and the currently proposed inventory actions use that same route and review policy.** The mobile implementation does not bypass review through a made-up offer endpoint. If the backend wants a separate availability-only policy, approve/document it first and adapt the client; it is not assumed here.

The exact relationship between accepted review, property verification, owner verification and public publication remains unresolved in the existing contract. Define public eligibility explicitly and use it consistently in search, details, favorites, share links and viewing submission. Review status, rental availability and viewing-slot availability are three independent dimensions. An accepted property with an unavailable offer is not rentable; an available offer on an unpublished property is not automatically public.

Owner status tabs/counts remain property counts. If inventory PATCH moves a property to review, include it in under-review and exclude it from accepted/rejected as appropriate. Return other non-overlapping offers' independent availability unchanged even when property-level moderation temporarily limits public visibility. Do not manufacture offer totals, revenue or occupancy from asking prices or accepted viewing counts.

## Grouped public discovery, filtering, sorting and pagination

**Decision: one result is one physical property, with explicit offer selection inside details.** Apply this to home sections, search, map markers, pagination/counts, comparisons and grouped favorites. Never page offers and then deduplicate client-side.

Existing `GET properties/` and `GET homepage/` gain a **proposed** `rental_offers_version=1` query parameter. Search adds **proposed** independent `rental_scope`; existing `property_type` continues to describe the physical property. Existing price/filter/order parameter names are retained with proposed v1 offer-aware semantics.

For a v1 query, derive eligible published, non-archived, available offers **before** price filters, sorting, property grouping and pagination. Suitability/smoking/terms evaluate the effective offer values, physical facilities/location/property type evaluate the parent. `bedrooms` remains the total property bedrooms, not included rooms. No client division, currency conversion or cross-period normalization supplies a price. Price ranges and price ordering require a selected `price_period`; the client blocks sending those v1 queries without it.

The proposed `rental_summary` below is authoritative for the **current query**. `price` is an actual eligible offer price in `price_period`; with multiple eligible offers in that period it is their minimum. If periods are mixed and the request has no rent period, the backend must either choose/document one explicit period projection (e.g. its monthly eligible subset) or omit a minimum and let the UI request offer selection. Never label a weekly/monthly mixed minimum as a uniform price.

```json
{
  "id": "property_a",
  "property_type": "apartment",
  "bedrooms": 3,
  "rental_schema_version": 1,
  "rental_summary": {
    "eligible_count": 2,
    "scopes": ["room", "bed"],
    "labels": ["غرفة بحمام خاص", "سرير قرب النافذة"],
    "price": "1500.00",
    "price_period": "monthly",
    "price_scope": "bed",
    "starting_from": true
  }
}
```

Both the outer schema marker and summary fields above are **proposed**. Full search results may instead include full `rental_inventory` plus the summary; short home/favorites models accept the projection. `starting_from` is server-supplied, not inferred from property price. Missing/invalid minimum prices render an explicit choose-offer message. Preserve the existing search response envelope `results`, `count`, `next`, `previous`; `count` and the requested `page_size` refer to eligible **properties**, with stable ordering and a property-ID tie-breaker. As in existing search, the client derives page totals from the server count and requested page size. Eligible-offer counts are labeled separately and never added to property totals. Public views/analytics need a documented property-versus-offer dimension if tracked.

### Home previews and photo context

When `RENTAL_OFFERS_API_VERSION=1` and `RENTAL_OFFERS_SEARCH=true` have both been verified, Home requests four bounded previews from the existing `GET properties/` endpoint: `rental_scope=entire_property|room|room_group|bed`, `price_period=monthly` initially, `page=1`, `page_size=2`, and `rental_offers_version=1`. The existing ordering parameter is retained. Choosing another rent period replaces each screen-owned query Cubit and isolates its cache; Home pull refresh reloads all four previews. Each preview labels the number shown against the returned property `count`. “View all” uses the existing search screen and `AppPagify`, retaining scope/period while restoring the normal search page size. Nothing categorizes the legacy Home first page into catalog sections.

Preview reads and their cached codecs reject missing/negative totals, duplicate or missing property IDs, inconsistent next-page metadata, and summaries that contradict the scope or price period. The same grouped-result validation applies to enabled v1 search reads. This assists integration verification; only the backend can guarantee grouping across pages, accurate eligible counts, publication permissions, and concurrent-update safety. Empty results use a contextual Lottie; an error remains retryable. Default builds preserve existing Home sections and issue no rental discovery requests.

Offer galleries distinguish selected accommodation, a bed's parent room, shared spaces, and general property photos. A partial offer excludes photos associated with unrelated accommodation. If no relevant accommodation photos exist, unassociated property photos are shown with an explicit general-property label. General photos do not prove room/bed inclusion. A bed summary names its parent room and room capacity; it never claims the whole room is included or interprets capacity as occupancy.

Local property-photo checks stream SHA-256 fingerprints before review, detecting identical file copies under different paths. These fingerprints survive local draft recovery and upload recovery, and never enter API payloads. Removing/replacing a photo clears dangling active and parked associations. The property-level requirement remains 10–25 unique photos and one 1–60-second video. Known video durations are checked for both local and remote media; existing remote media without duration metadata remains subject to backend validation. The media service must verify duration and content uniqueness for remote/uploaded files; no remote checksum field is assumed. Saving without a valid owning account/session fails instead of displaying an unpersisted local-save confirmation.

## Offer-specific favorites (proposed extensions)

Keep the existing route names:

- Proposed `POST properties/{property_id}/save/` body `{"offer_id":"offer_a1"}`.
- Proposed `DELETE properties/{property_id}/unsave/` body `{"offer_id":"offer_a1"}`. The server must support a DELETE body, or agree an alternate transport and update the client before enabling it.
- Proposed response adds `offer_id` and `is_saved`. The client requires the echoed ID and confirmed flag for success.
- Proposed `GET properties/saved/?rental_offers_version=1&...` uses grouped server filtering/counting/paging and returns a `saved_offers` array of exact offer snapshots per property, together with `rental_schema_version`/summary. This read requires the same v1 filter semantics even if public search is rolled out separately.

The key is `(user_id, property_id, offer_id)`. Preserve multiple saved offers under one grouped property. Removing one must not remove the others. Preserve an unavailable/archived saved offer or tombstone and its original label; never silently select an alternative. Define whether current terms and original saved terms are returned separately; the client uses supplied saved selections for identity and refreshes current terms for viewing. Legacy saved properties remain property-level until an explicit migration decision.

## Viewing references and historical snapshots (proposed extensions)

Existing routes and visit state/action rules stay intact. Proposed `POST properties/{property_id}/visits/` retains `visit_date`, `visit_time`, `note` and adds `offer_id`, `expected_offer_revision`. The client re-reads the exact property/offer over the existing GET, rejects offline-cache authorization, updates changed terms for another review, rechecks existing appointment slots, and submits the offer reference. The server must atomically revalidate publication, ownership/self-request policy, current offer availability/revision and slot permission. A GET alone cannot prevent a concurrent change. Proposed success echoes `offer_id`; ignoring it cannot report successful offer persistence.

Viewing **accept/reject/complete/cancel is appointment state only**. It must never decrement rooms/beds, mark rented, allocate a lease, or release inventory. Existing server `actions` continue to authorize tenant and owner visit actions. Schedules and owner calendars remain property-based; no new scheduling engine is introduced.

Tenant list/details, owner request list/details/dashboard/calendar, and related notifications need the same **proposed** fields:

```json
{
  "id": "visit_a",
  "property_id": "property_a",
  "offer_id": "offer_a1",
  "offer_snapshot": {
    "property_id": "property_a",
    "offer_id": "offer_a1",
    "offer_revision": 7,
    "rental_scope": "bed",
    "name": "سرير قرب النافذة",
    "room_ids": ["room_a"],
    "room_names": ["غرفة مشتركة"],
    "bed_id": "bed_a1",
    "bed_name": "السرير قرب النافذة",
    "terms": {"price": "1500.00", "price_period": "monthly", "rental_period": 3, "deposit": "one_month", "suitable_for": "students", "description": "سرير محدد داخل غرفة مشتركة", "smoking_allowed": false, "rules": []},
    "availability": "available",
    "archived": false,
    "capacity": 2,
    "bathroom_access": ["shared"],
    "offer_link": "https://sokoun.app/properties/property_a/offers/offer_a1"
  }
}
```

Snapshot creation is a server responsibility at request time, immutable thereafter. Retain exact scope/labels/rooms/bed, price/currency/period, minimum months, deposit and rules. `capacity` is accommodation capacity, not present occupancy. The snapshot shown records event-time availability; current availability must be supplied separately if needed. FCM data may encode `offer_snapshot` as a JSON string; the app parses that too.

Retain these snapshots after rename, price changes, renting, archival or moderation. Do not rebuild history from today's property values. Existing legacy visits with no offer fields remain readable with their current property relationship. A record containing an offer ID without its snapshot shows the reference and missing-details message. Unknown future scope remains unknown. Any contract/review/invoice/revenue/transaction that refers to this accommodation needs the same stable reference and appropriate event-time terms, while financial totals come from actual accounting records.

## Media associations and retry requirements

Existing documented requirements stay at the **property level**: 10–25 unique public photos for mobile submission/review and the current required 1–60 second video rule. Do not require ten photos/video again for each room or bed. The server media handoff permits incremental property draft upload before the minimum approval count; retain that sequence.

Optional **proposed** `media_ids` on rooms/beds/offers and `shared_media_ids` on inventory reference existing stable property image IDs only. Gate them independently. With that gate off the client omits all associations instead of assuming they persist. Owners can select uploaded offer-specific or shared-space photos after stable IDs exist. New file-only photos are uploaded through the original property flow, then associated in a subsequent supported property PATCH. No new media upload service is invented.

Omitted association fields on PATCH must preserve existing associations. An explicit empty array clears associations only under the supported media contract; omission must not erase them during a terms/availability edit. Fresh validation is also scoped to the original authenticated session, so switching accounts while a read is pending cannot authorize a write for the next account.

For a selected partial offer, public galleries use its explicit room/bed/offer associations plus explicitly shared media. They do not display unrelated room photos as that offer's photos. Before selection, the general gallery is labeled as property media with unconfirmed accommodation association. Captions distinguish offer media and shared spaces; the property-wide video is explicitly labeled because it can include other accommodation. Empty associations do not fabricate photographs. Whole-property media remains the existing property gallery.

Preserve `main_image_id`, cover promotion, cover-first response order, `retained_image_ids`, captions, removal flags and the existing image upload result. Deleted media must atomically validate/update associations or return a clear conflict; never leave dangling IDs or attach private ownership evidence. Provide idempotent upload handling (per-file upload token or deduplication guarantee) for a network failure after an upload reaches the server. This is a **proposed additional guarantee**; the client retains confirmed IDs and skips already confirmed files, but cannot establish deduplication for an unacknowledged upload on its own.

New property create idempotency must be scoped to the account and logical draft, validate a request fingerprint, replay the same complete result for retries, and avoid creating another property after a timeout/partial media failure. Conflicting reuse returns 409 and an explicit recoverable identity, not a second property. PATCH must not reuse a creation key for a different body. The client persists the submission key before creating and persists returned property IDs/confirmed image IDs during recovery. Idempotency retention/recovery policy and staging multipart uploads must be agreed before writes are enabled.

## Notifications, navigation, sharing and chat

Proposed notification data includes stable `property_id`, optional `offer_id`, and event-time `offer_snapshot`. Visit notifications continue navigating by their existing visit/request ID; property notifications retain the offer selection when supplied. Copy should name the actual room/group/bed using the snapshot, with a sensible existing title fallback. Do not emit “property rented” from viewing acceptance.

Old property links still open the property. Proposed canonical links are `/properties/{property_id}/offers/{offer_id}`; the client also accepts `/properties/{property_id}?offer_id={offer_id}`. It does not arbitrarily select the first offer for an old property link. Missing/archived requested offers retain their identity and show unavailability. Sharing uses a server-supplied `offer_link` when available, otherwise the old property link leads to explicit selection. Only `https://sokoun.app`, `https://www.sokoun.app`, or relative recognized property paths are accepted by the parser.

Android property intent routing is added. Production Android App Links still require hosted `assetlinks.json` with the real app identifier/certificate. iOS Universal Links still require an approved associated-domain entitlement, provisioning and hosted AASA file; these were absent and are not claimed as configured. The Dart startup queue waits for splash/account restoration and then opens tenant details with the selected offer. Real device link activation has not been verified.

Existing conversation creation remains recipient `user_id` only. The mobile app carries a transient accommodation context panel into the **same** participant conversation, with no extra thread and no unsupported chat field. Persistent message/conversation context is a separate **proposed backend extension**: attach validated property/offer references and snapshots to contextual messages or entry metadata while retaining existing conversation uniqueness/permissions. Do not silently persist the UI panel as chat history.

## Migration and staged rollout

1. Keep existing property/visit/favorite IDs and relationships. Absence of inventory is legacy; a present unsupported schema/scope is a future/invalid record and must not fall back to an entire-property assumption.
2. Audit legacy semantics, especially `property_type=room`. The app does not manufacture offer IDs or classify all existing rows as `entire_property`. Verified full-property listings may receive a server-generated entire-property offer; ambiguous room/shared listings require owner/operations clarification with an explicit migration rule. Do not infer an offered-room count or per-bed price from total bedrooms or asking price.
3. Preserve historical legacy representation and snapshots that actually exist. Any backfill must state its evidence and distinguish verified history from unknown terms. Old property-only clients must remain readable; do not expose new partial inventory to old clients as a whole-property price/booking. Agree a versioned exclusion/compatibility projection before rollout.
4. Implement schema, overlap/permission/dependency transactions, revisions, idempotency, property-level review/publication, media relations, grouped search and snapshots before enabling a client operation. Update the collection with confirmed examples only after deployment; this change deliberately leaves the legacy collection intact.
5. Verify each operation against staging, including ignored-field detection, 409 recovery, failed uploads, concurrent edits, guest/auth recovery, private evidence omission, multiple periods, unavailable favorites and historical retention. No live backend end-to-end verification is claimed by this implementation.

Release configuration in `rental_offer_capabilities.dart` (all disabled by default):

| Proposed rollout define | Enables only after contract version is exactly 1 |
| --- | --- |
| `RENTAL_OFFERS_API_VERSION=1` | Recognizes the agreed v1 operation contracts; alone enables no writes/queries. |
| `RENTAL_OFFERS_WRITES=true` | Owner create/edit inventory payloads on existing property endpoints. |
| `RENTAL_OFFERS_SEARCH=true` | Public home/search v1 grouped projections and scope/price semantics. |
| `RENTAL_OFFERS_FAVORITES=true` | Offer-specific saves/removals and grouped server favorite filtering. |
| `RENTAL_OFFERS_VIEWINGS=true` | Exact-offer viewing payloads with fresh read/revision validation. |
| `RENTAL_OFFERS_MEDIA=true` | Associations; also requires writes. |
| `RENTAL_OFFERS_ACTIONS=true` | Server-backed rented/available/archive actions; also requires writes and server permissions. |

These are compile-time release configuration, **not** automatic capability negotiation or proof of deployment. Keep them false until verified. Enabling some operations cannot compensate for an unsupported dependency, such as favorite filter semantics or lease references. If the backend settles on a different contract, update the typed serializers and tests before enabling it; the proposal is intentionally explicit rather than silently speculative.

## Client verification locations

- `test/rental_offers_domain_test.dart`: four scopes, groups vs independent offers, identities/overlap/defaults/payloads, legacy/unknown records, media/price meaning, stable history and links.
- `test/rental_offers_requests_test.dart`: disabled capabilities, confirmed/ignored/failed saves, creation recovery key, fresh reads, conflicts, precise favorites, independent availability and appointment-only acceptance.
- `test/rental_home_sections_test.dart`: capability gating, server property/offer counts, duplicate/context rejection, cache symmetry, period changes, “View all” filters, details context, empty/error/retry and late-response lifecycle.
- `test/tenant_property_details_screen_test.dart`: linked choices remain unconfirmed, changed terms require another confirmation, and exact bed/offer/filter context survives a simulated sign-in return.
- `test/owner_draft_recovery_test.dart`: storage recovery/failure and no false persistence after a missing/ended owning account.
- `test/owner_properties_flow_test.dart`: existing property-only creation/editing and concurrent upload retry, unique photo fixtures, copied-photo rejection without lost input, and a real device draft manifest plus local-save confirmation with zero publication requests. Unchanged photo rechecks preserve the saved form so an upload retry does not submit another property update.
- `test/rental_offers_ui_test.dart`: explicit selection, removed selection, field preservation, history, 288 owner/tenant/review/Home-card layout configurations at widths 320/390/600/768/1024/1366, scales 1/1.3/2, Arabic/English and light/dark. Test render captures can be generated with `SOKOUN_CAPTURE_RENTAL_UI=1`.

These use local fixtures and injected repositories. They establish client behavior and contract assumptions, not backend enforcement or production publication.

Verification recorded on 2026-10-07:

- The full Sokoun app suite passed **3,020 tests** with `flutter test --no-pub --reporter expanded`. After the final bed-ID and known-video-duration boundary checks, the domain, request and owner-flow suites passed **89 tests** together.
- The rental layout matrix passed all **288 configurations**. Rendered captures were reviewed at phone/tablet widths, including 320 pixels with doubled text size, Arabic/English, and light/dark themes. A long total-bedroom label was corrected to wrap within the card.
- Focused analysis of the changed feature directories and tests reported **no issues**. App-wide `flutter analyze --no-pub` reported six existing warnings/information findings in unrelated files, with no errors. Architecture checks, Dart formatting and `git diff --check` passed.
- These are Flutter widget/domain/integration fixtures. Physical-device behavior and the proposed backend operations have not been verified against a deployed service.
