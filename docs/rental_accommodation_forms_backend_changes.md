# Sokoun accommodation forms: backend implementation guide

Updated 7 October 2026. This handoff describes the accommodation-first mobile implementation and the service work needed to publish it. It is an implementation proposal, **not a claim that these services or new fields exist in production**.

Read this with [the rental-offers contract handoff](rental_offers_backend_handoff.md) and [the existing property creation cycle](../SOKOUN_PROPERTY_CREATION_CYCLE.md). Keep existing property-only clients and ambiguous historical listings working.

## 1. The model the service must preserve

A **property** is the physical apartment, villa, studio or other supported property type. It owns address, coordinates, floor/building access, shared amenities, public property media and private ownership evidence.

A **rental offer** identifies exactly what is rented and owns price, price period, minimum rental term, deposit, description, rules, suitability and availability. `property_type` does not become a room or bed because the offer rents part of an apartment.

The mobile rental v1 discriminator already uses these proposed values:

| Scope | Allocation | Price covers |
| --- | --- | --- |
| `entire_property` | The whole property; no room/bed selection | Entire property |
| `room` | Exactly one identifiable room in that property | That room as a whole |
| `room_group` | At least two distinct identifiable rooms in that property | All included rooms together, one combined price |
| `bed` | One identifiable bed within one identifiable shared room | That individual bed |

Two independently rented rooms are **two offers**. A two-room group is **one offer**. Property bedroom count and included-room count remain different facts. Never derive room/bed prices from a property price, or occupancy/available-bed counts from room capacity.

## 2. What the mobile UI now collects

| Form | Primary fields and sections | Supporting property context | Pricing |
| --- | --- | --- | --- |
| Entire property | Physical type, title, total area/bedrooms/bathrooms, facilities/furnishing, property description | Address, map, floor, optional building/ownership details | Whole-property price and terms |
| Room | Select/define identified room; name, area, capacity, furnishing, contents, bathroom access, private facilities, descriptions | Parent type/name, address/map, floor, building access/amenities, shared spaces/rules; optional physical totals | Whole-room price and terms |
| Room group | Select/define at least two rooms; editable details for every included room; group description/facilities; named-room summary | Same supporting context, collected once | One combined group price and terms |
| Bed | Shared-room selection, bed selection/name/type/storage/description; separate shared-room identity, area, capacity, bathroom and facilities | Same supporting context, collected once | Individual-bed price and terms |

Photos/video are collected once for the property. The owner can associate relevant property photos with rooms, beds and shared spaces. There is no additional ten-photo/video requirement per unit.

Editing opens the selected offer's form immediately. A device draft remembers the active offer, all room/bed identities, scoped details and media references. The mobile client keeps unused local data recoverable while excluding incompatible allocations from submission.

## 3. Contract status: do not enable publication prematurely

The repository contains a property API and a **proposed** rental v1 adapter. There is no deployed backend implementation or verified server schema in this workspace.

`RentalOfferCapabilities.configured` defaults all new write/search/favorite/viewing/media/inventory-action flags off. Completing the UI does not enable them. The client currently says **“Save draft on this device”**, preserves entered fields, and explicitly confirms that the draft was not published or saved to the server.

Even with the existing v1 write flag enabled, the client blocks a write when the advertised accommodation contains new local-only details. Removing this guard would lose entered data. Backend support must be agreed, followed by an explicit versioned mobile serializer/reader and persistence-confirmation update.

These are the existing compile-time mobile configuration names, not server capability discovery:

| Configuration | Service behavior that must be verified first |
| --- | --- |
| `RENTAL_OFFERS_API_VERSION` | Agreed request/read schema version. The current adapter accepts version 1 only. |
| `RENTAL_OFFERS_WRITES` | Confirmed inventory persistence through the existing property create/edit API. |
| `RENTAL_OFFERS_SEARCH` | Scope filtering before property grouping, counting and pagination. |
| `RENTAL_OFFERS_FAVORITES` | Exact property/offer save and reopen behavior. |
| `RENTAL_OFFERS_VIEWINGS` | Exact offer identity, fresh availability checks and viewing-only appointment transitions. |
| `RENTAL_OFFERS_MEDIA` | Stable image associations returned after save. Requires compatible writes. |
| `RENTAL_OFFERS_ACTIONS` | Authorized availability/archive transitions with revision checks. Requires compatible writes. |

Do not set a new API version without updating the mobile capability checks, readers, serializers and confirmation logic together. Do not enable every flag simply because one operation works.

### Already represented by the proposed v1 adapter

- Inventory schema/mode/revision; rooms, nested beds, offers and shared term defaults.
- Stable room/bed/offer IDs, echoed creation client keys, offer scope/name/allocation, permissions and availability.
- Room name, capacity, bathroom access and description; bed name and identity.
- Effective offer terms and explicit inherited/overridden fields.
- Optional stable property-image associations, behind the independent media capability.
- Grouped discovery projection, exact saved-offer/viewing identity and event-time snapshots.

These still require service verification; being represented in mobile code does not establish production support.

### Extensions required for the detailed forms

The following **proposed public contract fields** must be agreed with the mobile developer before implementation. They are **not currently emitted in API requests or read as supported server fields**:

| Entity | Proposed extension | Required behavior |
| --- | --- | --- |
| Room | `area` | Nullable positive numeric square metres, allowing decimals. Unknown is null/omitted, not zero and not property area. |
| Room | `is_furnished` | Nullable boolean specific to this room; do not inherit silently from the property. |
| Room | `contents` | Items such as bed, desk, wardrobe or AC. Agree free text versus stable option IDs; return localized option labels if using a catalog. |
| Room | `features` | Facilities inside that room, separate from shared property amenities. |
| Bed | `type` | Optional bed type/size, with an agreed text or option contract. |
| Bed | `storage` | Optional personal storage/provisions, without resident identity information. |
| Bed | `description` | Optional bed-specific description, distinct from shared-room description and offer description. |
| Offer | `group_facilities` | Optional facilities available to the group, including explicitly exclusive access when verified; must not imply exclusive access from property amenities. |
| Property/inventory | `shared_facilities` | Explicit shared kitchen, living spaces, bathrooms and other spaces; preserve existing amenity/access values independently. |
| Property/inventory | `property_rules` | Explicit rules that apply across offers. Define their relationship with inherited and overridden offer terms. |
| Room/bed/offer/inventory | Media associations | Stable property image IDs for the selected unit, its parent room, and shared spaces. Never expose private proof/document media here. |

On the device these fields live in typed `RentalRoomDraftDetails`, `RentalBedDraftDetails`, `RentalOfferDraftDetails` and `RentalSharedDraftDetails`. Their `local_details` objects and `photo_refs` are **private draft format**, not wire keys to accept accidentally.

Extend the versioned response/request schema and advertise compatible capabilities. Add normal domain parsing/serialization on mobile only after agreement. Return complete persisted details so the client can detect ignored fields or substituted accommodation. Include a fixture for each scope, including unknown optional values.

## 4. Update property validation for partial offers

The legacy full-property request still requires its original title, type, address/location, area, bedrooms/bathrooms and rent fields.

For a v1 partial property:

1. Require the shared identity/location context and a valid room/bed allocation.
2. Allow physical area, bedroom totals and bathroom totals to be omitted when unknown. The partial form does not require inventing them to save a room/bed. Preserve existing known values on PATCH. Treat omitted fields as unchanged, never as zero or a delete.
3. Keep numeric physical totals separate from included-room/bed identities. If a known total is incompatible, return a readable field error identifying the **property** total and affected room allocation.
4. Do not apply legacy required root price, price period, minimum term, suitability, deposit or listing description validation to partial offers. These values belong to the offer.
5. Distinguish `price_period` from the minimum term `rental_period` in months. Daily/weekly pricing is not a daily/weekly minimum lease length.
6. Validate the new unit fields only where relevant. A bed has no invented area; its parent room may have a known area.

## 5. Inventory, permissions and concurrency

Enforce allocation and permissions in a transaction. Client validation is only assistance.

- Whole-property and partial active modes cannot conflict.
- A room cannot be allocated to overlapping individual-room/group offers.
- Whole-room/group allocation cannot coexist with bed offers inside that room.
- A bed cannot be allocated twice.
- Rented/unavailable offers retain their allocation until an explicit permitted transition releases it.
- Renting one independent offer changes that offer only.
- Verify owner/property/room/bed relationships; reject foreign IDs and ambiguous client keys.
- Use expected inventory revisions and idempotency for creation/retry. Return authoritative current revisions and stable identities.
- Published scope/allocation changes must check active requests/leases. Return explicit permitted transitions/actions; the current mobile UI locks persisted allocations.
- A shared address/floor/facility edit affects the parent property and potentially all its offers. Authorize and validate it as such.

Use the existing readable server-error envelope. Add structured field/entity errors and conflict codes only through an agreed schema. Preserve entered client data on validation, permission and revision failures. Do not report an ignored field as successfully persisted.

## 6. Reads, discovery, favorites and history

Return accommodation facts with property details, so selecting a different offer can replace the primary details and its gallery. A room's area/contents must not be filled from property totals. Optional missing facts should remain unknown.

Discovery remains **property grouped**: apply scope, availability, price period, suitability and price filters before grouping and pagination. One property appears once per section; counts, pages and map markers count properties. Offer counts are separate. The server-confirmed minimum must use eligible available offers in the selected scope and a single price period. Keep the existing documented search endpoint/envelope; do not introduce a second pagination service.

Favorites, deep links and actions must preserve property ID **and exact offer ID**. An unavailable offer is shown as unavailable, not replaced with the cheapest/first offer. Keep old property URLs working and do not classify ambiguous historical `property_type=room` records automatically.

### Collection categories implemented on mobile

Favorites and owner listings now provide All types, Entire property, Room, Room group, Bed and Type not specified. A property with multiple matching offers appears once in a category. Owner review-status tabs remain independent of these categories; rented, unavailable and archived offers remain manageable under their actual type.

- **Owner collection:** the inspected `ownedProperties` request supports `status`, `page` and `page_size`, with no verified rental-scope filter. Mobile categorizes loaded properties using `rental_inventory.offers[].rental_scope` or confirmed `rental_summary.scopes`. It retains the original page boundaries/cache and offers Load more. Extend the existing owner collection contract with an explicitly agreed scope filter that composes with status, and return property-based filtered totals/pages. Do not enable that request field merely because the UI exists.
- **Favorites:** return complete `saved_offers` snapshots with the exact offer ID, scope, terms and availability. Category membership is determined by the **saved offers**, not by other offers on the property or a discovery minimum. A card with one matching saved offer shows that snapshot's price, period and scope basis. Several saved offers keep their individual prices; mobile does not compute a minimum from them or reuse a discovery minimum for unsaved accommodation. A missing saved snapshot belongs to Type not specified. The proposed v1 favorite search already uses the existing `rental_scope` filter under `RENTAL_OFFERS_FAVORITES`; verify filtering/grouping/counts against saved snapshots before enabling it. Without that capability, mobile clearly reports matching loaded properties rather than a fabricated category total.
- **Search and map:** category controls use the existing `RENTAL_OFFERS_SEARCH` gate and versioned property-grouped search contract. Scope filtering must happen before server pagination and map results must still represent physical properties. Controls are disabled with an explanation when this service is unavailable. No locally categorized first page is presented as the complete search catalog.
- **Legacy:** provide a migrated explicit offer scope only after a reliable migration. Do not derive it from `property_type`. The mobile Type not specified category is a presentation fallback, not a new API `rental_scope` value.

Acceptance cases for these collection reads: two saved beds in one property yield one Bed card; a saved unavailable bed stays in Bed; a property with non-overlapping bed and room-group offers appears once in each relevant owner category; review status and scope compose; page one with no matches does not prevent reaching a matching property on page two; price ranges compare the selected price period and relevant offer terms only; category switching preserves exact offer actions and raw cache data.

Historical viewing, lease, invoice, notification and chat contexts must retain event-time accommodation and terms when those services support snapshots. Include new unit facts in a versioned snapshot extension where the business needs them; do not reconstruct history from today's room description or rent.

**Accepting a viewing request changes appointment status only.** It must not rent/reserve accommodation, create a lease or generate an invoice.

## 7. Media workflow

Retain the existing property upload/retry sequence and stable image IDs. Enforce the property-level submission requirement of **10–25 unique photos and one required 1–60 second video**. Do not require these again for every offer. Private proof remains private.

Agree how associations to newly uploaded photos are finalized after stable server image IDs exist. The mobile device uses durable local photo keys across draft copying/recovery, but does not send those keys as server image IDs. A confirmed association must be returned by the server before the public gallery can claim that a photo depicts the selected accommodation. Label general property/shared-room/shared-space media explicitly; exclude unrelated rooms from a selected offer's gallery.

## 8. Suggested implementation order and acceptance evidence

1. Confirm the rental v1/property-only compatibility contract and create/read fixtures.
2. Implement transactional allocations, stable ID/client-key mapping, revisions, idempotency and dependency permissions.
3. Agree and implement the detailed unit-field extensions and partial-property validation.
4. Implement media association persistence and complete read/confirmation responses.
5. Implement property-grouped discovery, exact favorites/viewings and immutable snapshots.
6. Run contract tests with the mobile developer. Enable each mobile capability separately after its service behavior is verified.

Required cases: all four scopes; two rooms together versus independent offers; known/unknown room area; bed in a shared room without occupancy inference; optional unknown property totals; duplicate room/bed allocation including rented offers; shared-property edits; active-request/lease restrictions; stale revision; field-error input recovery; upload retry; unavailable saved offer; exact offer through authentication/links; viewing acceptance with no rental/financial side effects; legacy ambiguous room records.

Mobile files to coordinate: `rental_offer_capabilities.dart`, `rental_room.dart`, `rental_offer.dart`, `rental_inventory.dart`, `rental_inventory_validation.dart`, `rental_inventory_confirmation.dart`, `owner_add_property_content.dart`, `owner_accommodation_draft_data.dart`, `owner_property_draft.dart`, `property_submission_cubit.dart` and the grouped discovery/gallery data helpers.
