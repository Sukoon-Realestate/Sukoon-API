# Sokoun — all features backend implementation guide

Date: **2026-10-07**. Mobile project: `apps/sokoun_app`.

**Send this single file to the backend developer.** It consolidates the implementation details, backend handoff and backend response template previously split across the three paid-feature documents, together with every improvement in `SOKOUN_FREE_IMPROVEMENTS_IMPLEMENTATION.md` and the latest property/room/room-group/bed rental-offer changes. It also incorporates the accommodation-first forms and collection categories from [docs/rental_accommodation_forms_backend_changes.md](docs/rental_accommodation_forms_backend_changes.md). This is the authoritative backend delivery guide and supersedes the previous paid-feature requirements. New contracts are proposals for backend implementation and confirmation, not evidence of deployment. Section 4.8 includes rental-offer contracts, detailed form extensions, partial-property validation and collection requirements; [docs/rental_offers_backend_handoff.md](docs/rental_offers_backend_handoff.md) and the accommodation guide remain focused supporting references.

Backend must implement/confirm the contracts, deploy them to staging, then return **`SOKOUN_ALL_FEATURES_BACKEND_DELIVERY.md`** using the response format in section 7. The mobile developer will use that returned file to make final changes against the actual backend implementation.

## 1. Product decision and access rules

**Every feature is free to use. Actual rent checkout stays.** “Free” describes access to tools; a tenant still pays the rent owed on a real invoice.

- No owner/tenant subscriptions, purchase plans, feature checkout, store SKUs, native purchases/restores, promotion credits, paid alert allowances or paid AI tokens.
- Promotion, alerts, analytics, AI, lease creation/signing and rent management must not require proof of payment, an entitlement, or an upgrade. Configure and serve these tools for every eligible account in its appropriate workspace.
- Retain login, current-account KYC rules, object ownership, participant permissions, moderation, real slot availability, stale revision checks and normal operational rate limits. These are business/authorization rules, never a paid unlock.
- Rent checkout charges only the actual, server-authorized invoice/payment obligation. No feature-use surcharge, inferred commission, verification charge or invented fee is approved by this guide. Any genuinely applicable rent terms must be explicit and included in the confirmed server quote.
- Owner operations remain owner operations. Tenants can manage their own alerts and access/sign their own leases or pay their own invoices. A shared account/workspace selection never grants access to somebody else's data.
- Reading existing documents, campaign history, alerts and receipts remains available without an active subscription or credit balance.
- Promotion cannot buy verification or bypass moderation. Listing verification, owner identity verification and proof of ownership remain distinct.
- Existing listing validators remain **10–25 unique photos and a required, valid video of 1–60 seconds at property level**; do not repeat that requirement for every room or bed. Offer price period and minimum rental term in months remain separate concepts.
- Physical property type and rental scope are independent. Owners may offer the entire property or non-overlapping parts; rooms, room groups and beds use stable references under the same parent property. Whole and partial active modes are mutually exclusive under the proposed v1 contract.
- Viewing acceptance is an appointment transition only. It must never mark accommodation rented, reduce inventory, create a lease or derive revenue. Moderation/publication, rental availability and viewing slots remain separate dimensions.

The mobile subscription SDKs and purchase lifecycle have been removed. Feature destinations appear in the main owner/tenant journeys without a catalog, subscription or native-store request. The **Sokoun tools / أدوات سكون** shortcuts have been removed from both profiles; use the contextual entry points in section 2.1.

**Deployment boundary:** the six formerly paid client tools have no purchase gate. The new rental-offer domain, owner draft/editor and tenant selection/context flows are implemented, but new server operations remain disabled by default behind explicit capability configuration. Owners can save labeled local offer drafts; the existing property-only flow remains available. This Flutter workspace contains no backend implementation of rental inventory, the new feature APIs, alert workers, AI provider, signing service or rent payment service. Making tools free does not deploy these services. Configure real services and respond with honest empty/error states while work is incomplete; do not fabricate persistence, success, balances, matches, signatures or payments.

## 2. Mobile architecture and integration map

The implementation follows `.agents/skills/sokoun-feature-architecture/SKILL.md` and `apps/sokoun_app/AGENTS.md`:

| Mobile area | Responsibility |
|---|---|
| `features/tenant/decision_tools/data/` and `presentation/` | Account-scoped comparison, costs, notebook, private lists/notes, manual saved searches and explained matches |
| Existing tenant home/search and visits features | Real map results, property availability, booking review, calendar export, visit/review permissions |
| Existing owner home/properties features | Accommodation-first create/edit forms, durable scoped drafts, supporting property context, image order/cover, quality checks, rejection reasons and owner listing categories |
| Existing tenant favorites and shared rental collection widgets | Categories based on exact saved offers, one card per physical property, accurate saved prices and preserved raw pagination/cache |
| Existing shared chat/support features | Encrypted local recovery, conversation eligibility, socket lifecycle and durable support receipts |
| `features/shared/rental_offers/data/` and `presentation/` | Physical room/bed inventory, independent offers/terms, overlap validation, exact selected/historical snapshots, capability gates, server-confirmed mutations and property/offer link routing |
| `features/shared/premium/data/` | Shared feature API constants, typed free configuration, exact rent money, JSON/cache helpers and hosted-session validation |
| `features/shared/premium/presentation/` | Free tools hub, workspace-only guard, configuration Cubit, typed remote views, confirmation/feedback/empty states and property selection |
| `features/owner/promotions/` | Free campaign composition and history |
| `features/tenant/premium_alerts/` | Free persisted alerts, management and notification navigation |
| `features/owner/advanced_analytics/`, `features/owner/ai_assistant/` | Measured analytics and consent-based listing suggestions |
| `features/shared/digital_leases/`, `features/shared/rent_management/` | Participant documents/signing, invoice history, real rent checkout and receipts |

Some internal folders/classes/translation keys retain their earlier `premium`/`paid` names for source compatibility. They do **not** implement paid access. New service paths use **`features/v1/`**. The client does not call the former `premium/v1/catalog/`, `entitlements/`, `purchase-orders/` or `purchases/verify/` routes. Backend must remove payment requirements from feature handlers and supply the final path mapping if it uses different routes.

Ordinary remote operations use `AsyncCubit`, typed data helpers and `BaseCrudUseCase`. Collections use `AppPagify` and its existing cache contract. Initial requests run from lifecycle initialization; screens compose extracted widgets. Account/resource/query dimensions scope GET caches, with symmetric serializers. Mutations are not cached. Cached visit slots, lease configuration/documents and invoices cannot authorize booking, signing or payment; obtain current server data and enforce rules again during the mutation.

Promotion/alert configuration is owned by a stable content Cubit. Paginated history remains accessible independently of configuration loading/failure. AI, analytics, lease reads and invoice reads have no configuration/subscription prerequisite.

Translations originate in `packages/core/assets/translations/lang.json`. Arabic, English and `LocaleKeys` are generated. Navigation uses `Go` and existing workspace routing. Native billing packages are absent. The recorded free-feature verification used **Flutter 3.35.1 / Dart 3.9.0**; the recorded rental-offer and navigation checks used the workspace SDK **Flutter 3.44.7 / Dart 3.12.2** (section 8).

### 2.1 Main app journeys and resource context

The tools now use the main app journeys as their entry points. The duplicate Profile → Sokoun tools shortcuts have been removed; existing bottom tabs remain in place.

| Journey | Mobile wiring | Backend responsibility |
|---|---|---|
| Owner writes a listing | Add/edit → description section → AI → review/edit → explicitly apply to the local form | Return a suggestion for the supplied facts/property; normal submission and moderation still publish the listing |
| Owner defines rental accommodation | Add/edit → “إيه الجزء اللي حابب تأجّره؟” → scope-specific accommodation details → separate property/shared-facility context → media → terms → review; local-only save until supported | Persist the supported inventory and agreed detailed-field extensions, assign permanent IDs, validate partial forms without hidden whole-property requirements, enforce ownership/overlap/dependencies/revisions and retain moderation; sections 4.8.3 and 4.8.13 |
| Tenant chooses accommodation | Grouped property card → details → explicit offer choice → exact accommodation/price/terms → favorite or viewing | Return authoritative eligible-offer summaries and exact IDs/snapshots; proposed save/viewing extensions must confirm the selected offer; unavailable selections never substitute another offer |
| Owner/tenant browses listing categories | Owner listings and Favorites → All/Entire property/Room/Room group/Bed/Type not specified; search/map use supported scope queries | Apply verified scope filters before property counts/pagination; favorites match saved offers, owner categories compose with review status; section 4.8.14 |
| Owner promotes a published listing | Properties → accepted/verified listing card → Promote listing; listing action sheet also retains access | Authorize the actual `property_id`; enforce publication, availability and campaign eligibility |
| Owner reviews performance | Home → Manage your rentals → Advanced analytics → select listing; listing card opens its own analytics | Authorize property and return real period-specific measurements |
| Tenant resumes a search | Home → Saved searches and decisions; Home → Search alerts; results/saved search → alert with its full filters | Persist authorized alerts and match the complete filter set; opening saved searches alone does not create an alert |
| Parties manage a lease | Tenant Home/owner dashboard → Contracts → Digital leases; owner listing → Digital leases for that property → Create lease | Filter `GET leases/` by optional `property_id`; draft keeps that property selected and requires an eligible tenant from `lease-tenants/` |
| Tenant reviews due rent | Signed-in tenant Home → real earliest due/overdue invoice → invoice details → optional real checkout | Return the due-invoice preview query described in section 5.6; fresh detail/mutation authorizes payment |
| Parties review lease invoices | A server-reported signed/active lease → Rent invoices for this lease | Filter `GET rent-invoices/` by `lease_id` and current workspace before pagination |
| Owner tracks rent | Home → Manage your rentals → Rent management | Read authorized invoice history; client does not invent income totals or collect a feature fee |

Existing `profiles/contracts/` document items may include an optional **`lease_id`** pointing to the actual `features/v1/leases/{id}/` resource. The app then offers “View digital lease”. Existing document IDs are never treated as lease IDs. Items without this field keep their existing document viewer, and the Contracts header still opens the digital lease collection.

**ho rent.** The app never changes rental inventory or creates a lease/invoice automatically from visit acceptance. Backend must define an explicit agreed-tenancy/participant-eligibility process, restrict tenant selection accordingly, and create rent obligations from approved lease/ledger rules. The legacy lease draft identifies the property and an explicitly selected eligible tenant; it does not identify a rental offer or establish agreement from a viewing. New lease creation is blocked for offer-based properties until the lease contract identifies the selected accommodation and the mobile form/serializer is integrated with that contract; section 5.5 describes this boundary.

The Home rent preview owns one lifecycle-managed Cubit outside the paginated discovery header, so feed rebuilds do not restart invoice loading. It loads independently of discovery, refreshes on Home pull-to-refresh and after returning from invoice details, and is not requested for guest users. Property-scoped lease and lease-scoped invoice caches include account, workspace and resource IDs. Invalid mixed-resource responses are rejected rather than shown as the selected resource's data.

## 3. Shared API conventions and endpoint inventory

All paths below are relative to the configured API base. Preserve current authentication/session handling; document the actual staging/production base, prefixes and environment differences in the backend delivery file.

Detail/mutation success envelope:

```json
{"key":"success","msg":"","data":{"id":"resource-id"}}
```

New feature collection envelope; collection screens send `page` and `page_size=20`. The single-invoice Home preview uses `page_size=1`:

```json
{"key":"success","msg":"","data":{"results":[],"count":0,"per_page":20,"total_pages":1,"next":null,"previous":null}}
```

Use the existing non-success HTTP/envelope behavior for failures with a useful localized message. Document field validation, 401/403, not-found, revision/slot conflicts, rate limits and provider failures. A declined operation must not be wrapped as success. Mutations expecting a resource/receipt need JSON data rather than an empty `204` response. Existing endpoints keep their established pagination/envelopes unless the delivery explicitly maps a change.

IDs are opaque strings; booleans are JSON booleans; counts/revisions are integers. Missing measurements are `null`, distinct from zero. Instants use ISO 8601 with a time zone, preferably UTC. Visit appointments use the **Africa/Cairo** time zone with daylight-saving rules; lease calendar dates are `YYYY-MM-DD`.

Lease/invoice/payment monetary objects use integer minor units, never floating point:

```json
{"amount_minor":1200000,"currency":"EGP","exponent":2}
```

All figures/identifiers in examples are illustrative, not approved commercial terms or real performance. The current lease rent form supports EGP with two decimals. The server owns invoice totals and any applicable rent terms.

Existing listing prices and proposed rental-offer `terms.price` retain decimal-string serialization. Do not interpret those strings as minor-unit integers or derive lease/invoice obligations from asking prices. Document the currency and decimal mapping when turning explicitly agreed terms into accounting records.

### 3.1 New free feature services — 20 method/path contracts

These are **proposed contracts already wired in the client**, not proof of deployment. Constants are centralized in `features/shared/premium/data/premium_api_constants.dart`.

| Method | Relative path | Inputs | Response data |
|---|---|---|---|
| GET | `features/v1/configuration/` | `workspace=owner\|tenant`, `lang=ar\|en` | Free operational configuration |
| GET | `features/v1/boost-campaigns/` | Paging, authenticated owner | Campaign page |
| POST | `features/v1/boost-campaigns/` | `property_id`, `option_id`, `request_key` | Action receipt |
| GET | `features/v1/search-alerts/` | Paging, authenticated tenant | Alert page |
| POST | `features/v1/search-alerts/` | Name, cadence, complete filters, request key | Action receipt |
| GET | `features/v1/search-alerts/{id}/` | Authorized alert ID | Alert |
| PATCH | `features/v1/search-alerts/{id}/` | `enabled`, `revision`, `request_key` | Action receipt |
| DELETE | `features/v1/search-alerts/{id}/` | `revision`, `request_key` in JSON body | Action receipt |
| GET | `features/v1/owner-analytics/{property_id}/` | `period_days=7\|30\|90`, `lang=ar\|en` | Measured analytics |
| POST | `features/v1/listing-suggestions/` | Property ID/public facts, language, request key | Suggestion |
| GET | `features/v1/lease-configuration/` | `lang=ar\|en` | Creation permission and approved templates |
| GET | `features/v1/lease-tenants/` | Owned `property_id`, paging | Eligible tenant page |
| GET | `features/v1/leases/` | `workspace`, optional `property_id`, paging | Authorized, filtered lease page |
| POST | `features/v1/leases/` | Lease draft body | Created lease |
| GET | `features/v1/leases/{id}/` | Authorized lease ID | Lease |
| POST | `features/v1/leases/{id}/signing-session/` | `revision`, `request_key` | Hosted signing receipt |
| POST | `features/v1/leases/{id}/cancel/` | `revision`, `request_key` | Action receipt |
| GET | `features/v1/rent-invoices/` | `workspace`, optional `lease_id`, `status`, `ordering`, paging | Authorized, filtered invoice page or Home due preview |
| GET | `features/v1/rent-invoices/{id}/` | Authorized invoice ID | Invoice |
| POST | `features/v1/rent-invoices/{id}/checkout/` | `invoice_id`, `request_key` | Hosted rent receipt and quote |

Configuration example:

```json
{
  "workspace":"owner",
  "boost_options":[{"id":"week","title":"Free promotion for 7 days","duration_days":7}],
  "alert_cadences":["instant","daily"]
}
```

The server owns actual option IDs, positive durations and localized titles. Cadences currently understood by the composer are `instant` and `daily`. Provide supported operational options for the appropriate workspace; report unsupported delivery workers in the delivery file. No `products`, `store_product_id`, `credit_cost`, `grants`, `remaining`, subscription expiry or purchase token is required. Absent operational configuration cannot become a prompt to pay. Configuration identity must match the requested workspace.

### 3.2 Existing services used by the original free improvements

These routes already exist in client code; backend must confirm deployed behavior and supply the needed fields. Constants are in `packages/core/lib/core/network/api_endpoints.dart`. Rental-offer additions to these routes are **proposed extensions**, gated off by default and detailed in section 4.8. They add no separate offer endpoint and do not change the 20 free-service method/path contracts in section 3.1.

| Method | Relative path | Backend responsibility |
|---|---|---|
| GET | `properties/` | Full search semantics, honest paging, actual coordinates/availability/verification and promotion labels |
| GET | `homepage/` | Existing discovery sections; proposed v1 grouped property projections and eligible offer summaries |
| GET | `properties/{property_id}/` | Current comparable details, rental terms, verification distinctions, freshness and stable media IDs |
| GET | `properties/saved/` | Existing saved-property collection; proposed grouped results with exact `saved_offers` snapshots and server filtering/pagination |
| POST / DELETE | `properties/{property_id}/save/` / `properties/{property_id}/unsave/` | Existing property favorites; proposed offer-specific body and echoed `offer_id`/`is_saved`, including DELETE-body support |
| GET | `properties/{property_id}/available_dates/` | Real days; add `date=YYYY-MM-DD` for that day's slots |
| POST | `properties/{property_id}/visits/` | Atomic slot validation and pending viewing request |
| GET | `properties/visits/` and `properties/visits/requests/` | Current account's visits/requests with exact appointment and action permissions |
| GET | `properties/visits/requests/{visit_id}/` | Authorized visit detail used by calendar/review flows |
| PATCH | `properties/visits/{visit_id}/update/` | Authorized cancellation; current body uses `{"status":"canceled"}` |
| POST | `properties/visits/{visit_id}/review/` | Eligibility and unique review validation |
| GET | `properties/owner/visits/requests/` and `properties/owner/visits/requests/{id}/` | Owner request history/details, eligibility and appointment truth |
| POST | `properties/owner/visits/requests/{id}/accept/` and `reject/` | Authorized, atomic request transitions and notifications |
| GET / PUT | `properties/owner/properties/{property_id}/availability/` | Existing viewing schedule management; confirm final schedule schema; this is not rental inventory or occupancy |
| POST | `properties/create/` | Listing validation, stable created ID and moderation state |
| PATCH | `properties/{property_id}/` | Authorized fields, retained media/captions/cover and moderation re-review |
| POST | `properties/{property_id}/images/` | Additional uploads, stable image acknowledgement and maximum count |
| DELETE | `properties/{property_id}/delete/` | Authorized existing listing deletion |
| GET | `properties/owned/` | Honest listing statuses and actual rejection reasons |
| GET | `properties/owner/dashboard/`, `properties/owner/profile/`, `properties/owner/revenues/` | Real counts, acceptance rate and existing operational statistics |
| GET | `chat/conversations/` and `chat/conversations/{id}/messages/` | Participant privacy, history and current-account sending permission |
| POST | `chat/conversations/create/` | Authorized conversation creation (`user_id` body in current client) |
| POST | `chat/conversations/{id}/messages/create/` | Message creation/acknowledgement, sharing deduplication semantics with sockets |
| POST | `chat/conversations/{id}/read/` | Existing authorized read receipts |
| POST / GET | `support/tickets/` | Durable contextual reports and private ticket listing |
| GET | `support/tickets/{id}/` | Private ticket detail and saved message thread |
| POST | `support/tickets/{id}/replies/` | Authorized reply; current JSON body is `{"body":"reply text"}` |

Do not implement these as feature-charged endpoints. Saved private notes/drafts/manual searches and calendar export do not require new server storage to work on the device. Extensions that are not yet wired are explicitly separated in section 4.7.

## 4. Original free improvements — complete feature inventory

| Feature and in-app entry | Client behavior | Backend work/confirmation |
|---|---|---|
| Property details → Compare; search/Favorites → My decision tools | Compare up to 3 current listings; missing entries remain identifiable/removable; cached details are labeled | Stable property IDs, authorized current detail, real verification and availability fields |
| Property details/comparison → costs | Listed rent, stated deposit and known subtotal; missing other terms stay unknown | Accurate `price`, `price_period`, `deposit`; return explicit additional terms if supported |
| My decision tools → private lists/notes | Account/device-scoped named groups and notes; removing a comparison preserves notes | No new API required for local behavior; optional private sync requires a separate delivered contract |
| Property/visit details → viewing checklist | Private property-associated notes for water, light, noise, maintenance, internet, costs and safety | No server endpoint required for local notes; never expose notes to owners/other users |
| Search results → Save search; decision tools → Saved searches | Persist every chosen filter locally; duplicate criteria update its name; manual reopening uses normal search | Preserve search semantics; automatic free alerts use section 5.2, not silent uploading of local saved searches |
| Search results → Map and list | Actual coordinates from loaded results; viewport filter, clear-area action and additional pages | Actual permitted coordinates; whole-catalog area search is a separate extension |
| Filtered result/map → property explanation | Explain matches only from actual selected criteria/listing data | Consistent price period/type/amenities/bedrooms/verification; no invented commute/neighborhood/AI score |
| Property details → availability transparency | Show true `availability_confirmed_at` or explicitly unknown | Owner confirmation metadata and an authorized confirmation action |
| Property details → Book visit | Real dates/slots, Egypt time validation, clear time when date changes, fresh recheck | Atomic scheduling/booking and conflict response; section 4.2 |
| Book visit → request review/confirmation | Review property/day/time/note; success means sent/pending; failures retain form | Return real request/state; no guaranteed acceptance or 24-hour promise |
| Accepted visit → Export to calendar | Share `.ics`, exact Cairo appointment converted to UTC, stable visit ID, one-hour reminder | Exact appointment fields; OS import remains local and is not cloud calendar synchronization |
| Visit/review notification → detail/review | Prefer explicit action permissions; otherwise require past accepted or completed visit; suppress duplicates | Accurate `actions`, appointment/status, existing review and authorized real notification targets |
| Owner editor → draft resume/save/discard | Atomic account-scoped autosave of fields/step/media/metadata and acknowledged IDs; private file copies; missing files visible | Stable IDs/acknowledgements and server idempotency for ambiguous creation/upload |
| Owner photos → move/select cover | Preserve order, file/remote identity and captions across drafts | Confirm ordered retention and atomic media update; section 4.3 |
| Owner review → listing quality checklist | Suggestions for images, location, description, deposit, captions and video | Keep validators/moderation authoritative; suggestions are not verification |
| Owner rejected listing → reason | Actual reason or honest missing-reason fallback | Return `rejection_reason`; provide recoverable moderation workflow |
| Owner profile → Statistics | Missing acceptance rate differs from explicit 0%; cached values preserve the distinction | Real measurements, nullable fields and definitions; section 5.3 extends these freely |
| Chat composer → durable recovery | Encrypt local drafts/uncertain messages by account/conversation; save before send; explicit restart recovery, no automatic replay | Shared REST/socket message identity and durable acknowledgement; section 4.4 |
| Chat entry/history/composer → permissions | Peer verification badge does not decide current user's access; history stays open; explicit `can_send=false` disables sending | Enforce current-account KYC/participation and return current-account permission |
| Chat menu → Report a problem | Send context/reason/details, require durable receipt, preserve failed form, keep chat accessible | Private support ticket and moderation pipeline; section 4.5 |
| Owner editor/management → rental offers | Named room/bed inventory, groups versus independent offers, explicit defaults/overrides, durable local drafts and gated server actions | Proposed create/edit/read/availability/archive contract, overlap/ownership/dependency/revision validation and moderation; section 4.8 |
| Tenant discovery/details/Favorites → chosen accommodation | Grouped property results, explicit offer selection, actual offer prices/periods, scoped media and preserved unavailable selections | Proposed grouped queries, authoritative summaries, offer-specific favorites and publication rules; section 4.8 |
| Viewing/history/notifications/chat/contracts → accommodation context | Exact offer reference and supplied historical snapshot; review links retain that offer; no automatic occupancy or new chat thread | Server snapshots and stable references throughout the record lifecycle; lease creation extension remains required; sections 4.8 and 5.5 |

### 4.1 Comparable properties, rent terms and freshness

Return `is_verified`, `owner_is_verified` (or the supported owner object equivalent) and `is_ownership_verified` as distinct facts. Do not substitute promotion for any of them. Missing/removed listings must return the established unavailable/not-found response rather than an invented alternative listing.

`deposit` currently supports `none`, `half_month`, `one_month`, `two_months`, or a supplied non-negative amount. Month-based deposits can be calculated only when `price_period=monthly` and rent is known. A blank deposit is unknown, not zero. Utilities, services and brokerage are not assumed included. The known subtotal is rent plus a known deposit, not a promise that all move-in costs are covered.

For offer-based properties, comparisons retain the property as their result unit and require explicit accommodation selection. Cost calculations use the selected offer's effective price, price period and deposit; never fall back to the parent's legacy asking price or divide that price by rooms/beds. Supplied unknown scopes remain unknown; section 4.8 defines legacy handling.

`availability_confirmed_at` is an owner-confirmed instant. Never fill it with `updated_at` merely because content changed. Backend must provide a genuinely authorized owner confirmation operation and document its actual path/body/response for final mobile wiring. Define stale-listing duration and availability status explicitly.

### 4.2 Viewing availability, requests, calendar and reviews

Availability data example, wrapped in the normal success envelope:

```json
{
  "days":[{"day":"Saturday","date":"10/10","visit_date":"2026-10-10"}],
  "times":[{"time":"11:00 AM","visit_time":"11:00:00","is_available":true}]
}
```

The dated request sends `?date=2026-10-10`. Display labels cannot replace exact `visit_date`/`visit_time`. Reject impossible dates, past slots and invalid Cairo wall-clock appointments. Handle daylight-saving transitions with the business's chosen slot policy and document it. A cached slot response can be displayed but never authorize a booking.

Existing legacy request body (the gated proposed offer extension is in section 4.8):

```json
{"visit_date":"2026-10-10","visit_time":"11:00:00","note":"Tenant supplied note"}
```

Within a transaction, authorize the account/property, revalidate the appointment slot and selected offer when applicable, and create the request according to the actual appointment policy. Reserving a viewing slot must not reserve rooms/beds or change rental availability. Prevent concurrent duplicate bookings and return a useful slot-conflict response. The mobile recheck cannot replace server concurrency protection. Creation currently sends no `request_key`; if the backend adds a booking idempotency token, return its exact schema so the mobile can adopt it.

Visit responses must include a stable ID, property/participant IDs, `status`, exact `visit_date`, exact `visit_time`, existing review information and:

```json
{"actions":{"can_cancel":true,"can_chat":true,"can_review":false,"can_find_alternative":false}}
```

Compute all actions for the authenticated account. Review POST fields are `cleanliness_rating`, `listing_accuracy_rating`, `owner_interaction_rating` (1–5) and `comment`. Enforce eligibility and unique review per eligible visit/reviewer on the server. Calendar export requires an accepted appointment with exact fields; the `.ics` UID derives from the stable visit ID. Notify participants of acceptance/rejection/cancellation and return real visit IDs for review navigation.

Rescheduling, completion recording, automatic calendar update/cancellation and server reminders require a defined lifecycle/notification contract before additional mobile integration. Existing `.ics` sharing is not an automatic calendar sync service.

### 4.3 Owner drafts, media order and publication

Local draft storage does not need a backend draft endpoint. It persists form step, fields, photo/video/proof private copies, captions, existing property ID and acknowledged image IDs. The backend must acknowledge stable IDs immediately so retries update the same listing instead of creating another. Define server idempotency for ambiguous create/upload responses; local recovery alone cannot guarantee a server-side upload was applied only once.

Rental drafts additionally retain rooms/beds, offers, terms, parked mode-specific offers and a stable creation submission key. Parked offers are local only and omitted from requests. Proposed owner POST/PATCH fields, create idempotency and media associations are in section 4.8; they never imply a deployed server-draft endpoint.

Existing multipart fields include `main_image`, `main_image_id`, `main_image_name`, `main_image_description`, `retained_image_ids`, `images_metadata`, video/removal fields and ownership proof. Additional image uploads support `image`, `name` and `description`.

```json
{
  "retained_image_ids":["cover-id","photo-id"],
  "main_image_id":"cover-id",
  "images_metadata":[
    {"id":"cover-id","name":"Living room","description":""},
    {"id":"photo-id","name":"Bedroom","description":"Garden view"}
  ]
}
```

Confirm multipart encoding of these arrays. On PATCH, validate that retained/image/cover IDs belong to this listing. Media retention, deletions, caption changes and cover selection must be atomic; failed validation must not partially delete images. Omitted retention data must not accidentally mean “delete all”; document omission versus an explicit empty list. Cover must be retained and returned first in `images`.

**Additional ordering agreement needed:** persist the order of `retained_image_ids`, or deliver the explicit ordering field/mobile adaptation you require. Returning cover first is already supported; arbitrary non-cover ordering still needs server confirmation. Return `main_image_id`, cover captions and each image's stable `id`, URL, `name` and `description` after create/edit/upload.

Enforce maximum 25 photos transactionally and the 10-photo publication requirement plus required valid 1–60 second video at property level. Edits retain moderation/re-review behavior; return real `rejection_reason` when rejected. Offer edits and proposed availability/archive actions currently use the same property PATCH/re-review policy. Private proof files need appropriate access controls and must never enter offer/public galleries. Quality suggestions do not weaken validators.

### 4.4 Chat eligibility, acknowledgements and recovery

Authorize history/send/read using the current authenticated participant. Return `can_send` in conversation data and enforce that permission on socket and REST writes. A peer's `is_verified` flag is display information, not the caller's sending permission.

Current REST send body is `{"content":"message"}`. Current socket body is `{"conversation_id":"conversation-id","content":"message"}`. These client bodies **do not yet carry a shared server-recognized `client_message_id`**. Local uncertain outgoing messages are encrypted and recovered for explicit review/send; automatic replay is intentionally absent.

Backend must deliver a shared REST/socket idempotency and acknowledgement contract, including `client_message_id`, authoritative message ID/time, current status, retry/conflict behavior and acknowledgement/lookup after timeout. Scope uniqueness to the sender/conversation and deduplicate a socket send followed by REST fallback. Include exact schema/event changes in the delivery file so final mobile work can send/consume them. No duplicate-delivery guarantee is claimed before that integration.

Rental-offer chat entries display transient accommodation context in the existing participant conversation. Creation still sends recipient `user_id` only. Persistent offer context requires the explicit backend extension in section 4.8; no offer-specific thread or unsupported chat payload is introduced.

Persist acknowledgements and read state consistently, isolate conversations/accounts, and return permission failures without discarding recoverable client drafts. Pause/resume/disconnect behavior must preserve existing socket ownership.

### 4.5 Reports, support receipts and moderation

Chat reports use the existing ticket endpoint, not a pretend local block. Body fields:

```json
{
  "workspace":"tenant",
  "category":"report_owner",
  "subject":"Selected reason",
  "description":"Selected reason\nConversation: conversation-id\nParticipant: participant-id\nProperty: property-context\nUser supplied details"
}
```

Owners reporting tenants send `category=report_tenant`. Other existing support fields/attachment multipart behavior remain supported. Context currently travels in `description`; return structured report fields if you need them, with the precise mobile adaptation. Validate authorization against the conversation/participants rather than trusting copied IDs in text.

Create a durable ticket and return non-empty ticket `id`, `reference` and a saved initial message in `messages`:

```json
{
  "id":"ticket-id","reference":"SUP-001","subject":"Selected reason",
  "status":"open","created_at":"2026-10-06T10:00:00Z",
  "messages":[{"id":"message-id","sender":"user","body":"Saved report details","created_at":"2026-10-06T10:00:00Z","attachments":[]}]
}
```

Do not return success before durable storage. Restrict ticket visibility to the account and authorized support/moderation staff, maintain a moderation audit trail, and define outcomes. Incomplete receipt/failure leaves report details available for retry. A successful report closes its sheet and preserves access to chat. Server-side user blocking is a separate extension; no block action is simulated by submitting a ticket.

### 4.6 Existing owner statistics

Return genuine counts and documented measurement windows. Missing/invalid acceptance rate is unknown; explicit `0` is a measured zero. Never turn absent data into income, activity or a positive rate. Preserve the existing dashboard/profile/revenue semantics while adding the free advanced metrics in section 5.3.

Count physical properties separately from offers. One property with two independent room offers remains one property; a two-room group is one offer. Supply offer counts only when measured and labeled explicitly. Revenue comes from actual accounting, not asking prices, capacity or accepted appointments. Related financial rows may include the stable offer snapshot from section 4.8 without changing their authorized amounts.

### 4.7 Remaining free backend extensions and current mobile boundaries

These were listed as remaining work in the original free implementation document. Backend should define/implement the server contracts and identify the final mobile work in its delivery. They must remain free, but their additional screens/actions are **not yet wired** merely because they appear here.

| Extension | Backend should deliver | Current mobile boundary |
|---|---|---|
| Whole-catalog map search | Bounding-box/radius queries, paging, coordinate privacy and authoritative geographic fields | Viewport filtering currently applies only to loaded search results; no undeclared `bbox` request is sent |
| Nearby services/routes | Real data source, permission/privacy handling, route/service schema and attribution | No fabricated nearby facilities, route or commute score |
| Owner availability confirmation | Authorized confirmation operation, true timestamp and freshness/stale policy | Reads the timestamp; new mutation path awaits backend agreement |
| Listing lifecycle | Pause, renew/reactivate and stale transitions with ownership/moderation rules; define offer availability/archive dependencies separately | Existing statuses/rejection remain; new listing lifecycle endpoints are not invented. Rental-offer rented/available/archive actions are wired only behind the proposed existing-PATCH capability/permission gates in section 4.8 |
| Visit reschedule/completion/reminders | Exact status transitions, conflict checks, real notification targets and reminder worker | Existing request/cancel/review and local calendar export remain available |
| Cross-device manual saved searches | Account-owned CRUD, full filters, revisions and conflict/deletion rules | Current manual searches are local; free automatic alerts are separate server records in section 5.2 |
| Optional private notebook/checklist sync | Explicit opt-in, account-private CRUD/revisions, privacy and deletion semantics | Local notes/groups/checklists work without server sync; never upload automatically |
| Server-side blocking | Separate authorized action, existing conversation/history policy and enforcement | Report submission is not a block |

Return actual API/schema proposals for requested extensions rather than marking them delivered from existing list endpoints. Optional cloud synchronization is not a prerequisite for existing local features. Partial rent payments/refund requests, analytics time series and historical notified-match lists likewise need explicit additional contracts; rental-offer requirements follow in section 4.8 and the free-service flows in section 5.

### 4.8 Rental offers — physical property and offered accommodation

**Latest implemented client change; every added server field, header, query parameter and operation in this section is proposed and disabled by default until supported.** Backend source is absent from this checkout. Extend the existing property services; do not treat the proposal as a deployed offer API or silently ignore new fields. These rules cover create/edit/read, owner management, public search, favorites, viewings, historical records and rollout without adding a scheduling, payment or lease-creation engine.

The business baseline is the checked-in [PROJECT_BUSINESS_DETAILS.md](PROJECT_BUSINESS_DETAILS.md); the separately named `PROJECT_BUSINESS_DETAILS(2).md` attachment was unavailable, and use of the checked-in baseline was agreed. Existing contracts were checked against [collection.json](collection.json), [MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md](MOBILE_PROPERTY_MEDIA_EDITING_DELETION_HANDOFF.md), [owner property status tabs](docs/owner_property_status_tabs_backend.md), repository instructions and `design.md`. The dedicated [rental-offer handoff](docs/rental_offers_backend_handoff.md) and [accommodation forms guide](docs/rental_accommodation_forms_backend_changes.md) are supporting references. Their delivery requirements are consolidated here, including the detailed-field extensions and category behavior in sections 4.8.13–4.8.14.

#### 4.8.1 Implemented journeys and operational boundary

Owners see “إيه الجزء اللي حابب تأجّره؟” early. The selected scope determines the primary form, fields, validation, review and edit experience; partial offers lead with accommodation details and keep parent-property information in a separate supporting section. Named rooms/beds and independent offers retain their own terms. A group selects two or more actual rooms for one combined price. Changing whole/partial mode parks the other mode in the local draft; parked offers never enter a request. Scope changes retain compatible shared data, exclude irrelevant references from submission, and revalidate. Shared defaults and individual overrides are explicit. Existing unsaved-change and upload-recovery protection applies; section 4.8.13 defines the new detailed fields and their contract status.

With default configuration, these are complete durable **local drafts**, labeled as local at every step and in review. The final action says **“Save draft on this device”**; it does not create a property, publish, or imply server persistence. The original property-only creation/editing path remains available. Even when the proposed v1 write flag is enabled, entered local-only detailed fields block server submission until a compatible schema, reader, serializer and persistence confirmation exist. Do not remove that guard to make publication appear available. Offer reads can render server-supplied v1 data without enabling writes. Unknown/malformed schemas and scopes are displayed safely and cannot authorize a booking.

Tenant discovery is grouped by physical property. Cards use server-provided offer labels, count, scope, minimum eligible price and rent period. Details require choosing an offer and then explicitly confirming the accommodation, including when there is only one offer. Deep links highlight an offer without confirming it; sign-in retains the exact confirmed snapshot, and changed terms require another confirmation. Favorites retain exact saved selections and use their own price context rather than an unsaved discovery minimum. Viewing summaries/review/confirmation carry the choice. Historical visits, owner requests/calendar, notifications, chat context, reviews, contracts, invoices and revenue models preserve supplied snapshots. A missing historical snapshot is identified as missing instead of filled from a current property price.

Offer availability/archive actions use the proposed extension of the existing property PATCH only when both configuration and fresh server action permissions permit them. The app verifies the response before applying success. Selecting “Mark rented” does not create a lease. Existing property-only digital lease creation is blocked for offer-based properties until a lease contract identifies the offer. Actual server payment/revenue amounts remain unchanged.

#### 4.8.2 Entities and stable identity (all additions proposed)

| Entity | Relationships and responsibilities |
| --- | --- |
| Property (existing ID preserved) | Owner, physical type, address/coordinates, total bedrooms/bathrooms/area, shared facilities, public property media, private ownership evidence, moderation/publication. |
| Room | Permanent server ID belonging to one property; owner-visible name/number, capacity, details, optional private/shared bathroom access, associated property media. |
| Bed | Permanent server ID nested under exactly one room; name/number and optional media. No resident identity. |
| Rental offer | Permanent server ID belonging to one property; scope, room references and optional bed reference, its own price/period/terms, availability, archive flag, revision, permissions and media references. |
| Shared defaults | Optional property inventory defaults for minimum months, deposit, suitability, description, smoking and rules. Price and price period always belong to an offer. |
| Selected/historical accommodation | Property ID + offer ID + immutable snapshot/revision. Preserves exact room/bed labels and terms for the relevant event. |

`property_type` is unchanged. `rental_scope` accepts exactly `entire_property`, `room`, `room_group`, `bed`. `mode` accepts `whole` or `partial`. A property's `bedrooms: 3` and an offer's `room_ids: [room_a, room_b]` retain both physical and offered counts.

Creation uses `client_key` only for draft references. The client generates local UUIDs for draft identities and uses them in intra-request references; they are **not** backend offer IDs. The server allocates permanent IDs, resolves references atomically, and echoes each creation `client_key` with its assigned ID in the full response. Existing IDs must remain stable across rename, edit, rent, archive and review. Never recycle them. Scope changes that would replace an existing accommodation identity require explicit server rules; the editor locks persisted whole/partial mode, scope, room and bed allocations until a verified transition checks existing requests and leases.

A mode switch must be validated as an inventory transition. Omitted previously persisted offers are not instructions to hard-delete their requests/leases. Reject transitions with unresolved dependencies, or implement an explicitly documented archival policy with snapshots and audit records. Do not automatically cancel requests, end leases, or release occupancy.

#### 4.8.3 Proposed owner write extension of existing endpoints

Existing routes:

- `POST properties/create/` (multipart).
- `GET/PATCH properties/{property_id}/` (full property read/edit).
- `POST properties/{property_id}/images/` (existing photo upload).
- `GET properties/owned/?status=under_review|accepted|rejected` (existing status handoff).
- `DELETE properties/{property_id}/delete/` (existing whole-property deletion, with dependency checks).

**Proposed extensions, disabled by default:** owner POST/PATCH accept a multipart string field `rental_inventory` containing the following JSON. `X-Rental-Offers-Version: 1` selects the proposed write contract. New property creation additionally sends `Idempotency-Key` with a stable draft submission key. Property PATCH uses inventory `expected_revision` rather than reusing the creation idempotency key for different edits.

Illustrative proposed room-group creation JSON (physical fields/media remain on the parent multipart request). This example covers the fields represented by the current proposed v1 adapter; detailed room/bed/shared-facility extensions in section 4.8.13 are not emitted by that adapter today:

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

#### 4.8.4 Proposed full read response

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

#### 4.8.5 Inventory, permission and concurrent validation

Authoritative validation belongs in a backend transaction with appropriate row locks/unique constraints and revision checks. Client validation is only assistance.

- `whole`: exactly one active entire-property offer; no simultaneous conflicting partial inventory.
- `partial`: room, room-group, or bed offers; at least two distinct rooms per group, exactly one room per room/bed offer. All selected rooms belong to this owner's property. A bed belongs to its referenced shared room. Shared-room capacity must be at least two, and identified beds cannot exceed capacity.
- No room in two non-archived room/group offers; no whole-room offer plus bed offers in that room; no duplicate bed offer. Rented/unavailable offers still retain their inventory identity until an explicit server transition releases it. Archived offers do not allocate new offers but dependencies remain retained.
- A room/bed/offer ID cannot be reassigned to another property or owner. Reject client keys that collide or resolve ambiguously. Never authorize ownership from the workspace UI or submitted IDs.
- Check action permissions, moderation/verification, existing requests and active leases on every write. The client requires `actions.can_archive` / `can_set_availability` from a fresh read; it does not invent permissions from an accepted review state.
- `expected_revision` must match the current inventory revision. Increment inventory revision and affected offer revision on relevant changes. Two concurrent owners/sessions cannot both allocate overlapping inventory or overwrite newer prices.
- Proposed `409` conflicts include `inventory_revision_conflict`, `inventory_overlap`, `offer_unavailable`, `active_lease_dependency`, `active_request_dependency`, and `mode_transition_blocked`. Proposed `422` validation errors identify invalid fields/room/bed references. Use the existing readable `message` failure envelope so current error UI handles these; a future structured detail may add `code`, `offer_id`, `room_ids`, `bed_id`, `current_revision`.
- On conflict, apply no partial inventory writes. Keep the local draft/selection and require a refresh/review; never remap a request to the property or another offer. Return `403` for ownership/permissions and `404` for invisible resources without disclosing private records.
- Treat shared address/floor/building/facility edits as parent-property changes that may affect multiple offers. Authorize and validate that shared change explicitly rather than disguising it as an edit to one room or bed.

Availability is `available`, `unavailable`, or `rented`; archive is a separate boolean. Unknown future values render as unconfirmed and cannot authorize a viewing. `rented` is a server-confirmed owner action with dependency/lease checks; this change does not build an occupancy or lease-creation engine. Do not compute current occupancy from capacity or expose residents' identities.

#### 4.8.6 Moderation and publication

The documented property PATCH returns the property to `under_review`. **Offer edits, associations and the currently proposed inventory actions use that same route and review policy.** The mobile implementation does not bypass review through a made-up offer endpoint. If the backend wants a separate availability-only policy, approve/document it first and adapt the client; it is not assumed here.

The exact relationship between accepted review, property verification, owner verification and public publication remains unresolved in the existing contract. Define public eligibility explicitly and use it consistently in search, details, favorites, share links and viewing submission. Review status, rental availability and viewing-slot availability are three independent dimensions. An accepted property with an unavailable offer is not rentable; an available offer on an unpublished property is not automatically public.

Owner status tabs/counts remain property counts. If inventory PATCH moves a property to review, include it in under-review and exclude it from accepted/rejected as appropriate. Return other non-overlapping offers' independent availability unchanged even when property-level moderation temporarily limits public visibility. Do not manufacture offer totals, revenue or occupancy from asking prices or accepted viewing counts.

#### 4.8.7 Grouped public discovery, filtering, sorting and pagination

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

Both the outer schema marker and summary fields above are **proposed**. Full search results may instead include full `rental_inventory` plus the summary; short home models accept the projection, and favorites may retain it as supporting property data. A discovery summary cannot replace the exact `saved_offers` snapshots or determine favorite category/price membership (section 4.8.14). `starting_from` is server-supplied, not inferred from property price. Missing/invalid minimum prices render an explicit choose-offer message. Preserve current pagination envelope `results`, `count`, `per_page`, `total_pages`; `count` and page size refer to eligible **properties**, with stable ordering and a property-ID tie-breaker. Eligible-offer counts are labeled separately and never added to property totals. Public views/analytics need a documented property-versus-offer dimension if tracked.

#### 4.8.8 Offer-specific favorites (proposed extensions)

Keep the existing route names:

- Proposed `POST properties/{property_id}/save/` body `{"offer_id":"offer_a1"}`.
- Proposed `DELETE properties/{property_id}/unsave/` body `{"offer_id":"offer_a1"}`. The server must support a DELETE body, or agree an alternate transport and update the client before enabling it.
- Proposed response adds `offer_id` and `is_saved`. The client requires the echoed ID and confirmed flag for success.
- Proposed `GET properties/saved/?rental_offers_version=1&...` uses grouped server filtering/counting/paging and returns a `saved_offers` array of exact offer snapshots per property, together with `rental_schema_version`/summary. This read requires the same v1 filter semantics even if public search is rolled out separately.

The key is `(user_id, property_id, offer_id)`. Preserve multiple saved offers under one grouped property. Removing one must not remove the others. Preserve an unavailable/archived saved offer or tombstone and its original label; never silently select an alternative. Define whether current terms and original saved terms are returned separately; the client uses supplied saved selections for identity and refreshes current terms for viewing. Legacy saved properties remain property-level until an explicit migration decision.

#### 4.8.9 Viewing references and historical snapshots (proposed extensions)

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

#### 4.8.10 Media associations and retry requirements

Existing documented requirements stay at the **property level**: 10–25 unique public photos for mobile submission/review and the current required 1–60 second video rule. Do not require ten photos/video again for each room or bed. The server media handoff permits incremental property draft upload before the minimum approval count; retain that sequence.

Optional **proposed** `media_ids` on rooms/beds/offers and `shared_media_ids` on inventory reference existing stable property image IDs only. Gate them independently. With that gate off the client omits all associations instead of assuming they persist. Owners can select uploaded offer-specific or shared-space photos after stable IDs exist. New file-only photos are uploaded through the original property flow, then associated in a subsequent supported property PATCH. No new media upload service is invented.

Omitted association fields on PATCH must preserve existing associations. An explicit empty array clears associations only under the supported media contract; omission must not erase them during a terms/availability edit. Fresh validation is also scoped to the original authenticated session, so switching accounts while a read is pending cannot authorize a write for the next account.

For a selected partial offer, public galleries use its explicit room/bed/offer associations plus explicitly shared media. They do not display unrelated room photos as that offer's photos. Before selection, the general gallery is labeled as property media with unconfirmed accommodation association. Captions distinguish offer media and shared spaces; the property-wide video is explicitly labeled because it can include other accommodation. Empty associations do not fabricate photographs. Whole-property media remains the existing property gallery.

Preserve `main_image_id`, cover promotion, cover-first response order, `retained_image_ids`, captions, removal flags and the existing image upload result. Deleted media must atomically validate/update associations or return a clear conflict; never leave dangling IDs or attach private ownership evidence. Provide idempotent upload handling (per-file upload token or deduplication guarantee) for a network failure after an upload reaches the server. This is a **proposed additional guarantee**; the client retains confirmed IDs and skips already confirmed files, but cannot establish deduplication for an unacknowledged upload on its own.

New property create idempotency must be scoped to the account and logical draft, validate a request fingerprint, replay the same complete result for retries, and avoid creating another property after a timeout/partial media failure. Conflicting reuse returns 409 and an explicit recoverable identity, not a second property. PATCH must not reuse a creation key for a different body. The client persists the submission key before creating and persists returned property IDs/confirmed image IDs during recovery. Idempotency retention/recovery policy and staging multipart uploads must be agreed before writes are enabled.

#### 4.8.11 Notifications, navigation, sharing and chat

Proposed notification data includes stable `property_id`, optional `offer_id`, and event-time `offer_snapshot`. Visit notifications continue navigating by their existing visit/request ID; property notifications retain the offer selection when supplied. Copy should name the actual room/group/bed using the snapshot, with a sensible existing title fallback. Do not emit “property rented” from viewing acceptance.

Old property links still open the property. Proposed canonical links are `/properties/{property_id}/offers/{offer_id}`; the client also accepts `/properties/{property_id}?offer_id={offer_id}`. It does not arbitrarily select the first offer for an old property link. Missing/archived requested offers retain their identity and show unavailability. Sharing uses a server-supplied `offer_link` when available, otherwise the old property link leads to explicit selection. Only `https://sokoun.app`, `https://www.sokoun.app`, or relative recognized property paths are accepted by the parser.

Opening a property from a supplied historical review also retains its exact `offer_id`. Missing or archived selected accommodation must remain identifiable when current details are opened; never redirect that reference to a different room or the entire property. Legacy reviews without an offer reference keep the existing property destination.

Android property intent routing is added. Production Android App Links still require hosted `assetlinks.json` with the real app identifier/certificate. iOS Universal Links still require an approved associated-domain entitlement, provisioning and hosted AASA file; these were absent and are not claimed as configured. The Dart startup queue waits for splash/account restoration and then opens tenant details with the selected offer. Real device link activation has not been verified.

Existing conversation creation remains recipient `user_id` only. The mobile app carries a transient accommodation context panel into the **same** participant conversation, with no extra thread and no unsupported chat field. Persistent message/conversation context is a separate **proposed backend extension**: attach validated property/offer references and snapshots to contextual messages or entry metadata while retaining existing conversation uniqueness/permissions. Do not silently persist the UI panel as chat history.

#### 4.8.12 Migration and staged rollout

1. Keep existing property/visit/favorite IDs and relationships. Absence of inventory is legacy; a present unsupported schema/scope is a future/invalid record and must not fall back to an entire-property assumption.
2. Audit legacy semantics, especially `property_type=room`. The app does not manufacture offer IDs or classify all existing rows as `entire_property`. Verified full-property listings may receive a server-generated entire-property offer; ambiguous room/shared listings require owner/operations clarification with an explicit migration rule. Do not infer an offered-room count or per-bed price from total bedrooms or asking price.
3. Preserve historical legacy representation and snapshots that actually exist. Any backfill must state its evidence and distinguish verified history from unknown terms. Old property-only clients must remain readable; do not expose new partial inventory to old clients as a whole-property price/booking. Agree a versioned exclusion/compatibility projection before rollout.
4. Implement schema, overlap/permission/dependency transactions, revisions, idempotency, property-level review/publication, media relations, grouped search and snapshots before enabling a client operation. Agree the detailed fields and partial-property validation in section 4.8.13 and the owner/favorite collection semantics in section 4.8.14. Update the collection with confirmed examples only after deployment; this change deliberately leaves the legacy collection intact.
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

The current adapter recognizes contract version 1 only. Do not set a new version or enable all flags to bypass local-only fields. Agree any schema/capability extension, update mobile readers, serializers and confirmation together, and verify complete persistence before recommending rollout. Public search support does not establish an owner collection scope-filter contract or selected-offer lease support.

#### 4.8.13 Accommodation-first forms and required contract extensions

The selected rental scope changes what the owner fills in and what the tenant sees. The physical property remains the shared parent; its internal model must not force every scope through a full-property form.

| Form | Primary accommodation fields/sections | Supporting property context | Price covers |
| --- | --- | --- | --- |
| Entire property | Physical type, title, total area/bedrooms/bathrooms, furnishing/contents, facilities and property description | Address/map, floor and relevant building/ownership details | Entire property |
| Room | One identified room; name, area, capacity, furnishing, contents, private facilities, bathroom access, room description and relevant photos | Parent type/name, address/map, floor, elevator/building access, shared kitchen/living/bathroom spaces and property-wide rules; physical totals optional when unknown | Selected room as a whole |
| Room group | At least two distinct rooms in the same property; editable details/photos for every included room, names/count, group description and shared/exclusive group facilities | The same parent context, collected once | All included rooms together, one combined price |
| Bed | Identified bed, type/size, personal storage/provisions and description/photos; separate shared-room identity, area when known, capacity/physical beds, bathroom access and room facilities | Separate parent-property location, floor, building access, shared facilities and rules | Selected individual bed |

Room capacity is a physical specification, not current occupancy or available-bed count. An actual physical bed count comes from identified beds, not a capacity-derived availability estimate. Do not expose residents' identities. Room area never falls back to total property area; a bed has no invented area. Show combined room-group area only when every included room has a valid known area, and label it as the included rooms' combined area. Two rooms together remain one offer; independent rooms remain separate offers with independent terms and availability.

**Contract status must be reported separately for each field:**

| Status | Current mobile behavior | Backend delivery requirement |
| --- | --- | --- |
| Existing property-only fields | Uses the existing physical property/location/floor/media/amenity flow | Confirm deployed mappings and preserve legacy required fields |
| Fields represented by the proposed rental v1 adapter | Rooms: identity/name/capacity/bathroom/description; beds: identity/name; offers: allocation/effective terms/defaults/overrides; optional stable media IDs | Verify the full contract in sections 4.8.3–4.8.4 against staging; representation in mobile is not deployment evidence |
| New detailed accommodation fields | Typed durable local drafts; excluded from current API serialization; entered unsupported details prevent server submission | Agree public request/read fields, validation, version/capability support and mobile persistence confirmation before publication |

The following names are **proposed extensions to agree**, not keys currently sent or read by the mobile v1 adapter:

| Entity | Proposed extension | Required behavior |
| --- | --- | --- |
| Room | `area` | Nullable positive numeric square metres with decimals; unknown is null/omitted, never zero or property area |
| Room | `is_furnished` | Nullable room-specific boolean; no silent inheritance from property furnishing |
| Room | `contents` | Bed, wardrobe, desk, AC and similar contents; agree free text versus stable catalog IDs and localized labels |
| Room | `features` | Private room facilities, distinct from shared property amenities |
| Bed | `type` | Optional type/size with an agreed text or option contract |
| Bed | `storage` | Optional personal storage/provisions, without resident data |
| Bed | `description` | Bed-specific description, separate from parent-room and offer descriptions |
| Offer | `group_facilities` | Explicit facilities available to the group, including exclusive access only when verified |
| Property/inventory | `shared_facilities` | Explicit shared kitchen/living/bathroom and other spaces, preserving existing physical amenity/access values independently |
| Property/inventory | `property_rules` | Property-wide rules and an agreed relationship to inherited/overridden offer terms |
| Room/bed/offer/inventory | Stable media associations | Map relevant public property-image IDs to units and shared spaces under section 4.8.10; no private proof or local file references |

Elevator/building access and physical amenities use their verified existing property mappings where supported. If a needed access/facility field is absent, report the exact extension and client adaptation in the delivery file rather than inventing a request key or treating it as supported.

On device, detailed fields live in `RentalRoomDraftDetails`, `RentalBedDraftDetails`, `RentalOfferDraftDetails` and `RentalSharedDraftDetails`. Their `local_details` objects and `photo_refs` are **private draft format**, not API keys to accept accidentally. Agree the public entity placement, JSON types, nullability, omission/clear behavior, catalog/text choices, units, permissions and versioning. Return complete persisted details so the client can detect ignored fields or substituted accommodation, including fixtures with unknown optional values for every scope.

Partial-property validation must differ from legacy whole-property validation:

1. Keep the existing property-only flow's required title/type, address/location, physical totals and rent fields. For partial offers, require shared identity/location context and valid selected accommodation instead of hidden full-property requirements.
2. Allow physical property area, bedroom totals and bathroom totals to be omitted when unknown. Preserve existing values on PATCH; omission is not zero or deletion. If a known total conflicts with an allocation, identify the parent-property total and affected rooms in a readable validation error.
3. Do not apply mandatory legacy root price, period, deposit, minimum term, suitability, smoking or offer-description validation to partial offers. Price and `price_period` belong to each offer; `rental_period` remains the separate minimum term in months.
4. Validate required unit fields only for the selected scope. Require one identified room, at least two distinct group rooms, or an identified bed inside its selected shared room as appropriate. Hidden/incompatible room/bed selections must not block a valid different scope or enter its request.
5. Validate agreed detailed fields at their entity level. Nullable room area/furnishing remain unknown when omitted; do not populate them from the property. Keep private room facilities, shared property facilities and group-specific access distinct.
6. Use the established readable error envelope. Any new structured field/entity error schema must be agreed; permission, conflict and validation failures must allow entered data to remain recoverable, without partial mutation or apparent success for ignored fields.

Creation/editing share the same accommodation-first composition. Editing restores the exact offer, room/bed IDs, detailed values and media associations. Compatible shared data survives scope switches; incompatible selections are explained, retained locally where useful and excluded from submission. Shared address/floor/building/facility edits are explicit parent-property edits that may affect other offers. Existing requests/leases restrict published mode/scope/allocation transitions; the current mobile editor keeps persisted selections locked until that transition contract is verified.

Before save, the review identifies the parent property, exact accommodation, included room names/count or bed and parent room, price/basis/period, minimum term/deposit/rules and shared facilities. Details lead with the selected unit's facts and description, then show property and shared-space context. Changing the offer changes the primary details, terms, availability and relevant gallery; missing unit data stays unknown instead of borrowing unrelated property values. Extend immutable historical snapshots with agreed unit facts when needed, retaining event-time meaning.

Media requirements remain **10–25 unique public property photos and one required 1–60 second video**, collected once. Associate relevant room/bed/offer/shared photos after stable server IDs exist; durable local photo keys are not server IDs. Confirm associations in the saved response, label general property/shared-space media and exclude unrelated rooms from the selected offer's gallery. Section 4.8.10 owns the upload/retry/privacy rules; no extra ten-photo/video requirement applies to a unit.

Mobile coordination points: `rental_offer_capabilities.dart`, `rental_room.dart`, `rental_offer.dart`, `rental_inventory.dart`, `rental_inventory_validation.dart`, `rental_inventory_confirmation.dart`, `rental_accommodation_draft_details.dart`, `owner_add_property_content.dart`, `owner_accommodation_draft_data.dart`, `owner_property_draft.dart`, `property_submission_cubit.dart`, and the existing discovery/gallery data helpers. Backend delivery must identify exact reader/serializer/confirmation changes, not only a flag to enable.

#### 4.8.14 Owner, favorite, search and map collection categories

Owner listings and Favorites provide **All types, Entire property, Room, Room group, Bed and Type not specified**. Category controls use shared presentation logic, while one result remains one physical property. A property with several matching offers appears once in a category and may appear in another category for other eligible accommodation. Offer counts and property counts remain separate.

| Collection | Implemented mobile behavior | Required backend contract/delivery |
| --- | --- | --- |
| Owner listings | Review-status tabs compose with categories. Matches loaded `rental_inventory.offers[].rental_scope`, or confirmed `rental_summary.scopes` when full inventory is absent. Rented/unavailable/archived offers remain manageable. The inspected request sends `status`, `page`, `page_size`; no verified owner scope query exists | Agree a scope filter on the existing `GET properties/owned/` contract, composing with status and ownership. Filter properties before count/pagination; include manageable offers rather than applying public available-only discovery rules. Return the actual query/version/capability mapping for mobile integration |
| Favorites | Membership uses **saved** offer snapshots, never unsaved offers or discovery summary scopes. Matching saved offers are projected under one property without changing the raw cache. Unavailable/archived saved offers retain identity. Missing snapshots stay Type not specified | Supply complete `saved_offers` with exact property/offer IDs, scope, terms and availability. Verify the proposed favorite `rental_scope` and term filters against saved offers before grouping/counting/paging and before enabling `RENTAL_OFFERS_FAVORITES` |
| Public Home/search/map | Existing `RENTAL_OFFERS_SEARCH` gates real property-grouped scope queries. Section/“View all” context preserves scope and price period; detail still requires explicit final accommodation confirmation. Search/map scope controls are disabled with an explanation when unsupported | Use the existing versioned discovery contract in section 4.8.7. Apply scope, price-period and eligible availability filters before property grouping/pagination; counts and map markers stay property-based. Do not present a locally categorized first page as a complete catalog |
| Legacy/unknown type | All types and Type not specified keep ambiguous legacy records and missing/unknown saved snapshots accessible | Migrate only with reliable evidence. Do not infer rental scope from physical `property_type`; Type not specified is a UI fallback, **not** a new API `rental_scope` value |

Until compatible collection filters are verified, owner/favorite category filtering explicitly describes **matching loaded properties** and retains the original pages/cache and Load more/retry behavior. It cannot supply a fabricated category-wide count or new pagination service. An empty filtered first page is not evidence that the entire category is empty. Public search capability does not automatically authorize a new owner query parameter.

Favorites also use their saved price context: one matching saved offer with valid terms shows that offer's price, price period and scope basis; several saved offers keep separate prices and require selection rather than a client-derived minimum. Missing terms are unknown. Do not reuse a property's discovery minimum for unsaved accommodation or compare weekly/monthly prices as one minimum. Define any distinction between saved-time and current terms explicitly, and revalidate current terms/availability before actions. Exact saved offer IDs survive opening details/authentication; unavailable saved offers never substitute another offer.

Return fixtures and observed collection results for: two saved beds under one property yielding one Bed card; an unavailable saved bed remaining in Bed; a non-overlapping bed and room-group property appearing once in each matching owner category; status and scope composing; a first page with no loaded match followed by a matching property on page two; one saved group alongside a cheaper unsaved bed; same-scope saved offers with different price periods; missing saved snapshots remaining unspecified; and category switching retaining exact offer actions and raw cached data. Section 7 requires these collection capabilities to be reported separately from public search and basic inventory persistence.

## 5. Formerly paid features — free service contracts

All six capabilities below are available in the client without subscriptions or feature charges. Backend must make their operations free and enforce only the real rules in section 1. This does not remove unsupported-contract gates: lease creation for offer-based properties remains blocked until selected accommodation can be identified (section 5.5).

| Feature | In-app entry |
|---|---|
| Promotion | Published owner listing card → Promote a listing; listing action sheet |
| Search alerts | Tenant Home → Search alerts; saved search/results → create alert using all filters |
| Advanced analytics | Owner dashboard → Advanced analytics; owner listing card/action sheet |
| AI listing assistant | Owner editor → description section → assistant → review and apply |
| Digital leases/signing | Home/dashboard → Contracts → Digital leases; owner listing → property-specific leases and draft |
| Rent management | Tenant Home due-invoice preview; signed/active lease → its invoices; owner dashboard → invoice history |

All six are accessible through the main-flow entry points above. The placement reuses the same feature screens and request contracts, with contextual IDs and filters and no feature payment gate. Profile no longer links to the tools hub.

### 5.1 Free listing promotion

Promotion body:

```json
{"property_id":"owned-property-id","option_id":"approved-option-id","request_key":"client-generated-uuid"}
```

Only publishable, accepted, available owned properties may be promoted. Check ownership, moderation, availability and campaign conflicts on the server. Resolve duration from the server-defined free option; do not accept a price or ranking strength from the client.

Campaign identity remains the physical `property_id`. For a property with offers, use the agreed publication predicate and eligible available offers from section 4.8; accepted moderation status alone does not prove publication. Promotion must not revive a rented/archived offer or display a parent's price as a bed's price. Offer-specific campaign targeting is not part of the current request body.

Create campaigns atomically and return the same result for repeated `request_key` submissions. Do not reserve/debit credits or create a charge. Define cancellation, moderation removal and failure behavior. Campaign scheduling/ranking/expiry and impression counting are backend responsibilities. The app makes no position, lead or conversion guarantee.

Create response data is an action receipt with campaign `id`, `subject_id` equal to the property ID, and `status=active|pending`. Campaign page items contain `id`, `property_id`, `property_title`, `status`, `duration_days`, `starts_at`, `ends_at`, and nullable `impressions`. Supported history states include `pending`, `active`, `paused`, `completed`, `cancelled`, `expired`, `failed`.

Return `is_sponsored: true` in sponsored home/search property payloads for placements where the backend applies promotion. Existing mobile property models preserve this flag and display a sponsorship label independently of `is_verified`. Define the allowed sponsored placements and labeling contract. Promotion must not change verification flags or conceal preferential placement. The public label is “Promoted listing”; the existing wire field remains `is_sponsored` for compatibility.

### 5.2 Free saved-search alerts

Alert body:

```json
{"name":"Near work","cadence":"daily","filters":{"search":"Maadi","city":"","district":"","ordering":"-created_at","page":1,"page_size":10,"price_min":"10000","price_max":"18000","property_type":"apartment","price_period":"monthly","suitable_for":"family","is_furnished":"true","is_verified":"","smoking_allowed":"","bedrooms":"2","bathrooms":"1","amenities":["wifi"]},"request_key":"client-generated-uuid"}
```

Use the existing `PropertySearchFilters` wire semantics exactly, including empty strings and string-valued filter flags. Validate price range and use the same interpretation as ordinary search. The full canonical schema is in `features/tenant/home/data/models/property_search_model.dart`; do not drop dimensions when persisting a search. The client normalizes the alert's page to 1.

The latest filter model also preserves **proposed** `filters.rental_scope` (`""`, `entire_property`, `room`, `room_group`, `bed`) in manual searches and alert JSON. For offer-aware alerts, matching must use the same eligible-offer/price-period semantics as section 4.8, then group/count physical properties. `bedrooms` stays the property's total bedroom count. Reject unsupported scopes or missing periods for price filters/sorting instead of silently dropping them. The alert body currently carries no separate rental-offer contract-version marker; agree any needed alert versioning and exact mobile adaptation in the delivery file. Enabling the public search flag alone does not establish support in alert persistence/workers.

Configuration `alert_cadences` enables supported choices: currently `instant` and `daily`. Provide both when the corresponding delivery worker is supported. Document operational delivery limits and what qualifies as a meaningful change; do not introduce a paid alert allowance or a purchase requirement. Implement worker matching for published, eligible, available listings; handle duplicates, batching, quiet hours, notification preferences and revoked permissions. Pausing/deleting must stop future delivery. Manual searches saved on the device remain free and are not automatically uploaded or enabled for alerts.

Alert response/page item fields: `id`, `name`, `cadence`, `enabled`, `can_manage`, positive `revision`, nullable `last_matched_at`, and complete `filters`. Create receipt has the alert `id` and `status=active|paused`. PATCH receipt has `subject_id=alert-id` and the resulting `active|paused` status. DELETE uses revision/idempotency JSON and returns `subject_id=alert-id`, `status=cancelled`; exclude deleted alerts from normal results.

Notification center payload should include:

```json
{"notification_type":"search_alert_match","title":"New matching homes","body":"Open your search","actions":{"primary":{"label":"View matches","action_type":"open_search_alert","target_id":"alert-id"}}}
```

For FCM, send string fields `notification_id`, `notification_type`, `title`, `body`, `action_label`, `action_type=open_search_alert`, and `target_id=alert-id`. The client switches to the tenant workspace and GETs the authorized alert before opening current search results with its stored filters. Push is not the source of truth. A separate historical list of specifically notified matches is not implemented; document it if your product contract requires that instead of current matching results.

### 5.3 Free advanced owner analytics

Response data:

```json
{"property_id":"owned-property-id","period_days":30,"measured_at":"2026-10-06T10:00:00Z","methodology":"Localized definition of included events","metrics":[{"key":"unique_views","label":"Unique visitors","value":128,"unit":"count","definition":"Distinct eligible visitors during the selected period"},{"key":"viewing_conversion","label":"Viewing request rate","value":3.25,"unit":"percent","definition":"Describe the numerator denominator and attribution window"}],"export_url":"https://authorized-expiring-report-url"}
```

Counts above are example payload values, not actual performance. Compute real measurements for the authenticated owner's property and requested 7/30/90-day interval. Deduplicate events, define bot/self-view treatment, privacy rules, source attribution, measurement window/time zone and empty/insufficient-data behavior. A percentage uses percentage points: `3.25` displays as `3.25%`. Missing metrics are `null`; unknown values display as a dash.

The first client implementation renders server-defined metric cards, definitions, methodology and report download. It does not invent market rents, recommendation scores or comparative trends, and it does not yet contain a time-series chart contract. Keep basic existing owner analytics available. Exports must authorize ownership and use bounded-life HTTPS URLs.

The analytics resource remains property-scoped. If offer-level events/metrics are delivered, return explicit property-versus-offer definitions and stable IDs; do not count the same property once per offer in property totals. An accepted viewing is not a rental conversion or revenue event. Related revenue/transaction displays preserve supplied offer snapshots while continuing to use actual server accounting amounts.

### 5.4 Free AI listing assistance

AI body:

```json
{"property_id":"owned-property-id-or-empty-for-draft","facts":{"title":"Owner title","description":"Owner description","property_type":"apartment","price":"12000","price_period":"monthly","deposit":"one_month","bedrooms":2,"bathrooms":1,"space":"120","governorate":"Cairo","district":"Maadi","amenities":["wifi"]},"language":"ar","request_key":"client-generated-uuid"}
```

Response data:

```json
{"id":"suggestion-id","property_id":"same-property-id-or-empty-for-draft","suggested_title":"Localized suggested title","suggested_description":"Localized suggested description","warnings":["Any factual review note"]}
```

The client sends an explicit whitelist of public listing facts after consent. It does not send ownership proof files, identity documents, email/phone fields, coordinates or chat contents as separate AI inputs. Empty fields and zero values in a partial existing-property summary mean information has not been supplied; do not manufacture those facts. For a persisted property, authorize the ID and use authoritative property data as appropriate.

Keep provider credentials and prompt execution on the backend. Support `ar|en`, enforce operational rate limits, bound execution and input/output sizes, and make retries idempotent. Generation is free to users; provider cost belongs to the service, with no paid token allowance or user charge. Validate the result before returning it; mobile currently limits title to 150 characters and description to 5000. Return factual cautions where needed and document retention/provider handling.

The assistant produces a suggestion only. It never publishes, verifies or changes a live listing. Owners review/edit it; applying changes the local draft's title/description and leaves normal listing validation/moderation intact. The owner still needs the normal submission flow to publish.

The editor entry supplies the actual persisted property ID when editing or resuming a saved property. An unsaved new draft supplies an empty ID. In both cases `facts` come from the current form, including edits that have not yet been submitted; authorize the property ID without discarding those owner-provided draft facts. Suggestions remain local until the owner applies and submits them through the normal editor.

The existing AI facts whitelist is property-level and does not identify a selected room, bed or offer. Do not infer offer prices/terms from parked legacy form values or claim that an assistant response persisted inventory. Offer-aware AI facts and application to individual offer descriptions require an explicit whitelist/identity contract and final mobile wiring; ownership evidence and resident identities remain excluded.

### 5.5 Free digital lease drafts and signing

Configuration data:

```json
{"can_create":true,"templates":[{"id":"approved-template-id","title":"Residential lease","jurisdiction":"EG","language":"ar","version":"approved-version"}]}
```

Tenant option page items: `{"id":"eligible-tenant-account-id","display_name":"Tenant name"}`. Scope the query to the owned `property_id` and participants eligible under the agreed-tenancy process. Do not infer agreement from an accepted viewing or expose an unrestricted user directory. The mobile form selects names and sends the selected opaque ID; it does not ask users to enter internal IDs. Empty eligible-tenant results must remain a real empty response rather than a fabricated tenant.

`GET leases/?workspace=owner&property_id=...&page=1&page_size=20` returns only that authorized property's leases. Apply resource filtering before computing count/pagination. The unfiltered Contracts/tools entry still requests all authorized leases in the selected workspace. Document any actual filter naming changes in the returned delivery file.

Existing property-only lease draft body:

```json
{"property_id":"owned-property-id","tenant_id":"eligible-tenant-id","template_id":"approved-template-id","template_version":"approved-version","start_date":"2026-10-10","end_date":"2027-10-10","rent":{"amount_minor":1200000,"currency":"EGP","exponent":2},"request_key":"client-generated-uuid"}
```

Validate ownership, participant eligibility/consent requirements, approved template/version, real dates, positive rent and end after start. Generate the full legal document from approved template data. Template approval, jurisdiction-specific requirements and signature validity are responsibilities of the business/backend/signing provider; the app does not generate legal clauses or declare a browser return legally signed.

**Rental-offer lease boundary:** that body cannot identify one room/group/bed. The mobile form and a fresh property read before creation block new leases for properties containing rental inventory, including an unsupported inventory schema. They reject cached/wrong-resource authorization and account changes during validation. Existing legacy property-only leases remain readable and creatable under their established rules. The proposed rental inventory flags do not enable offer lease creation.

Before enabling this additional lease capability, deliver a **proposed** stable `offer_id` plus an immutable agreed-accommodation/terms snapshot, explicit participant eligibility for that offer, inventory/lease dependency and concurrent-change rules, and exact create/read/collection response mappings. This extension is not currently sent by the client. Retain property IDs and historical lease IDs; do not reinterpret legacy documents as whole-property offers. Return the supplied `offer_id`/`offer_snapshot` on related lease, contract, invoice and revenue records where applicable; current read models preserve them. Rent obligations must come from explicit agreement and the actual lease/ledger, never the latest asking price or a viewing acceptance.

Completing the offer-based rental cycle also requires mobile integration after this contract is agreed: exact-offer selection in the lease form/body, eligible participants for that accommodation, review of agreed terms, and confirmation of the returned offer identity/snapshot. Backend must define which explicit agreement/lease transition changes availability and creates rental obligations, with transactional allocation checks. Existing rental flags cannot enable this missing lease integration, and no separate rental-application endpoint is assumed.

Lease response/page item fields: `id`, `property_id`, `property_title`, `owner_name`, `tenant_name`, `start_date`, `end_date`, `rent`, `status`, positive `revision`, `document_url`, `can_sign`, `can_cancel`. Creation must return `status=draft` and the requested property ID. Define the full lifecycle using supported states such as `draft`, `pending`, `signed`, `active`, `cancelled`, `expired`; document amendments, rejected signatures and provider failures if additional states are needed.

Signing session and cancellation bodies are `{"revision":2,"request_key":"client-generated-uuid"}`. Reject stale revisions. A signing-session receipt has `status=pending`, `subject_id=lease-id`, an HTTPS `hosted_url` and a future `expires_at`. Authorize the current signer and use the provider to present/review the exact document and capture an auditable signature. Webhooks must be authenticated, deduplicated and reconciled; update signing state only from authoritative provider evidence.

Mobile refreshes after returning to the app and supports manual refresh. It never marks a lease signed locally. Draft cancellation is shown only for a draft with `can_cancel=true`; return `subject_id=lease-id`, `status=cancelled`. Define participant invitation, decline, countersigning, recovery and notification delivery on the backend. Keep existing free contract viewing compatible with these completed documents.

Only server-reported `signed`/`active` leases offer the contextual invoice shortcut. The shortcut reads existing authorized invoices for the actual lease ID; it does not generate them. Supply `lease_id` in legacy contract document items when those documents have a corresponding digital lease, and specify the mapping in the backend delivery.

### 5.6 Free rent management with real rent checkout

Invoice response/page item:

```json
{"id":"invoice-id","lease_id":"lease-id","property_title":"Property title","reference":"INV-2026-001","due_date":"2026-11-01","amount":{"amount_minor":1200000,"currency":"EGP","exponent":2},"status":"due","receipt_url":"","can_pay":true}
```

Owners read their invoices; tenants read/pay only invoices where they are an authorized party. Generate immutable references and amounts from approved lease/ledger rules. Define scheduling, late payments, cancellations, refunds, fees, partial payments and settlements. The implemented client currently pays a complete invoice; partial-payment and refund request flows require additional contracts/UI.

For invoices referring to offer-based accommodation, return the **proposed** stable `offer_id` and event-time `offer_snapshot` described in section 4.8. Existing invoice details/cards and rent summaries can display that supplied context. Do not reconstruct historical price/identity from current offers or change authorized invoice amounts because asking prices changed. This read extension adds no payment or invoice-creation flow.

The collection endpoint supports these main-flow reads using the same envelope:

```text
# All authorized invoices for a lease, filtered before pagination:
GET features/v1/rent-invoices/?workspace=tenant&lease_id=lease-id&page=1&page_size=20

# Tenant Home preview: status is an OR filter, sorted earliest due date first:
GET features/v1/rent-invoices/?workspace=tenant&status=due,overdue&ordering=due_date&page=1&page_size=1
```

Support the lease filter for both owner and tenant workspaces and authorize the lease participants. The Home response must contain `results` with zero or one invoice and a nonnegative integer `count` for **all matching authorized due/overdue invoices**. Return `results:[], count:0` only when none are due; use a real error for unsupported queries or service failures. Do not return paid/cancelled invoices for this query, silently ignore the filter, or manufacture zero/amounts. Use deterministic ordering for invoices with the same due date and document the time zone for determining overdue status.

Home displays the actual invoice's amount/status/date and offers “View invoice”. It does not treat the first page as a total balance, collect rent directly from cached preview data, or show an income forecast. Unknown amounts remain unknown. Invoice details fetch the real ID and refresh payment permission before checkout; returning to Home refreshes the preview after a payment or other invoice change.

Checkout body: `{"invoice_id":"same-id-as-path","request_key":"client-generated-uuid"}`. Resolve the actual payable amount, fees, recipient and currency on the server; never accept an amount from the client. Receipt example:

```json
{"id":"checkout-session-id","subject_id":"invoice-id","status":"pending","hosted_url":"https://approved-provider/session","expires_at":"2026-10-06T12:15:00Z","amount":{"amount_minor":1200000,"currency":"EGP","exponent":2},"message":""}
```

The mobile app checks invoice identity, pending status, positive known quote amount, HTTPS URL and future expiry, then displays the server quote for confirmation before opening the provider. Unknown invoice states cannot initiate payment. Use one idempotent active checkout per invoice/payment attempt, including retries after application restart. The provider session must charge the confirmed quote; do not silently change its amount after confirmation.

Do not return `paid` merely because a checkout/session exists or the browser redirects back. Validate provider signatures, amount, currency, invoice identity and settled status, then update the ledger atomically. Deduplicate webhook replay and prevent payment against an already paid/cancelled invoice. Reconcile delayed events. The client refreshes the invoice on resume/manual refresh; a receipt button is available only after backend `status=paid`.

Hosted URLs must be HTTPS, scoped to the authorized transaction/provider, expire, and avoid embedded login credentials. Document the actual redirect/return URL and supported deep-link configuration in the delivery file. The current return behavior relies on app resume/manual refresh; no specific provider callback route has been invented. No card data, payment secrets, wallet ledger or payout secrets are stored in the app.

## 6. Shared receipts, retries, authorization and delivery order

Action receipt shape:

```json
{"id":"resource-or-session-id","subject_id":"target-resource-id","status":"pending","message":"Localized outcome","hosted_url":"","expires_at":null,"amount":{"amount_minor":null,"currency":"","exponent":2}}
```

For non-financial/non-hosted operations, money/URL fields may be omitted. Use each operation's required status/subject identity in section 5; a generic success ID does not authorize rent checkout or signing.

Persist a unique `(account, operation, request_key)` record and request fingerprint for new mutations. Identical retries return the original result; different payloads with the same key conflict. Use database transactions/uniqueness for campaigns, alert revisions/deletion, lease revisions, invoice checkout/settlement and media edits. Rate limits prevent abuse but cannot become a paid unlock. Local caches never authorize somebody else's resources.

The free-service `request_key` convention does not invent that field on existing property routes. Proposed rental owner creation uses the persisted `Idempotency-Key` header and request fingerprint; inventory PATCH uses `expected_revision` and atomic overlap/dependency checks (section 4.8). Viewing requests still need an agreed idempotency extension if desired. Fresh offer/permission validation is tied to the originating authenticated session; an account switch cannot authorize a write for the next account, and reconnect must not replay an unreviewed inventory mutation.

Signing/payment webhooks require authenticated provider evidence, durable event IDs, deduplication, retry handling and reconciliation. Never update `signed` or `paid` from the client returning to the app. Keep private credentials and provider execution on the backend. Signed document/export/receipt URLs must be HTTPS, participant/owner authorized and expire appropriately.

Suggested delivery order:

1. Confirm existing authentication, account/workspaces and free property/visit/media/chat/support contracts. Remove legacy feature-payment checks and implement free configuration.
2. Resolve atomic slot booking, media identity/order, truthful availability/permissions/rejections/statistics and chat acknowledgement/idempotency gaps.
3. Confirm rental v1/property-only compatibility and fixtures for all four scopes. Implement stable inventory IDs/client-key mapping, migration, transactional overlap/dependency/revision checks, create/upload idempotency and publication policy. Agree and implement the detailed unit fields and partial-property validation in section 4.8.13; retain the mobile local-only-data guard until readers, serializers and persistence confirmation support them.
4. Deliver complete accommodation/media reads, grouped discovery, owner status-plus-scope filtering, exact saved-offer categories/prices, viewing references/historical snapshots and notification/link behavior. Verify the distinct collection contracts in section 4.8.14, filters before property counts/pagination, and per-operation staging round trips before enabling the corresponding rental capability.
5. Deploy free campaigns, offer-aware alert persistence/matching/push, measured analytics/export and AI generation with their precise supported context and operational monitoring.
6. Configure approved lease templates and explicit eligible participants, then deploy document access/signing and reconciled provider events. Extend lease creation to selected offers before enabling it for offer-based properties.
7. Deploy invoice generation, real rent quote/checkout, settlement reconciliation and durable receipts; preserve supplied historical accommodation without changing ledger semantics.
8. Deliver extension contracts from section 4.7 with explicit implementation/integration status. Provide sanitized fixtures and staging evidence for every required feature/path.
9. Return the completed delivery MD below. Mobile then applies real endpoint/schema differences, callbacks and remaining integration work and verifies staging/device flows.

Required backend checks: unauthenticated/wrong-account reads/writes, workspace/ownership/participant checks, empty/missing resources, fresh versus stale/cached authorization, simultaneous slot bookings, invalid and reordered media IDs, ambiguous create/upload retries, duplicate review prevention, REST/socket duplicate sends, durable report receipts, nullable metrics, unsupported configuration, repeated keys/payload conflicts, ineligible promotion, campaign expiry, alert pause/delete/deduplication, AI failure/retry without user charges, signing revision/participant/expiry checks, expired/declined/delayed checkout, webhook replay and paid-invoice replay. Confirm each free feature works without any subscription, entitlement or credit record.

Also verify all four rental scopes; grouped rooms versus independent room offers; bed parent/identity/capacity; simultaneous overlapping allocations; whole/partial transitions with active requests/leases; rented/unavailable allocation retention; one rented offer leaving other non-overlapping availability unchanged; PATCH moderation/status-tab counts; eligible same-period summary/filter/sort/pagination; exact favorites/removal echoes; ignored-field/failed-write handling; viewing acceptance leaving inventory untouched; historical identity after edits/archive; private proof omission; media deletion/association conflicts; missing versus unknown legacy fields; account switches; and old/offer-specific links. Capability enablement requires actual staging evidence for that operation and its dependencies.

For detailed forms, include known/unknown decimal room areas, optional unknown property totals, room-specific furnishing/contents/private facilities, bed details/shared-room context, group/shared facilities and rules, omitted-versus-cleared PATCH values, shared-property edits, full returned persistence and stable media association round trips. Include readable errors that preserve entered data; a successful response that ignores a requested field is a failed contract check.

For collections, verify every case in section 4.8.14, including non-overlapping categories, composed owner status/scope, saved-only membership and price basis, unavailable exact selections, missing snapshots, mixed price periods and a matching property reached after an initially empty filtered page. Report these separately from public search and inventory writes.

## 7. Backend return file — required response format

Backend: create **`SOKOUN_ALL_FEATURES_BACKEND_DELIVERY.md`** and return it to the mobile developer. Populate the following format with **actual delivered behavior**; placeholders are not completion evidence. Include incomplete features and exact mobile work. Share credentials/passwords separately through the established secure channel.

### 7.1 Delivery identity

- Delivery date: `<actual date>`
- Backend repository/commit/release: `<reference>`
- Deployment environment/version: `<actual values>`
- Staging API base/prefix and production rollout: `<actual values/status>`
- Authentication/session changes: `<details or unchanged>`
- OpenAPI/Postman/schema/fixture locations: `<links or delivered files>`
- Account role and eligible property/room/bed/offer/tenant/visit/lease/invoice fixture IDs and revisions: `<sanitized IDs, including all four scopes and legacy/unknown records>`
- Free feature policy: `<evidence that no subscription, feature charge, entitlement or credit is required>`
- Real rent checkout retained: `<provider/environment/status>`
- Rental-offer contract version and supported operations: `<deployed create/edit/read/search/favorites/viewing/media/action support; exact mappings and gaps>`
- Detailed accommodation fields and partial-property validation: `<per-field public mappings/version/status, persisted read-back evidence and missing fields from section 4.8.13>`
- Collection category support: `<owner status-plus-scope, saved-offer favorite filters and public search reported separately; actual query/capability mappings and property-based counts/pages>`
- Rental migration/publication decision: `<legacy semantics audit, old-client compatibility and actual eligibility predicate>`
- Client rollout recommendation: `<per-flag enable/keep disabled with staging evidence; not automatic capability negotiation>`

### 7.2 Complete feature delivery matrix

Use `deployed and verified`, `implemented but not deployed`, `blocked`, `not implemented`, or `client-only; dependencies confirmed` with evidence. Copy **every feature row in sections 4 and 5**, plus extension rows from 4.7. Include the rental areas below separately so one supported operation does not imply that all rental flags can be enabled. Do not mark the whole project done because a route exists.

| Feature | Actual status | Scope/permissions | Evidence | Remaining backend/mobile work |
|---|---|---|---|---|
| `<each feature>` | `<status>` | `<workspace/ownership>` | `<reference>` | `<exact gaps>` |
| Rental inventory create/edit/read and stable room/bed/offer IDs | `<status>` | `<ownership, revisions, all four scopes>` | `<reference>` | `<exact gaps>` |
| Detailed room/bed/group/shared fields and media associations | `<status>` | `<entity permissions, optional unknowns, complete persistence>` | `<per-field mapping and round-trip fixtures>` | `<serializer/reader/confirmation gaps>` |
| Partial-property versus legacy whole-property validation | `<status>` | `<shared identity/location, scope fields, omitted PATCH totals>` | `<success/error fixtures for every scope>` | `<exact gaps>` |
| Rental availability/archive and mode/dependency transitions | `<status>` | `<action permissions, overlap, requests/leases>` | `<reference>` | `<exact gaps>` |
| Grouped discovery/filtering/sorting/counts | `<status>` | `<publication, eligible offers, exact price period>` | `<reference>` | `<exact gaps>` |
| Owner status-plus-scope collection categories | `<status>` | `<owned manageable offers, property-based filtering/counts/pages>` | `<query and multi-page fixtures>` | `<agreed owner filter/client wiring>` |
| Exact-offer favorites and unavailable saved selections | `<status>` | `<account, property, offer>` | `<reference>` | `<exact gaps>` |
| Saved-offer favorite categories and price context | `<status>` | `<saved-only scope/terms, unavailable selections, unknown snapshots>` | `<category/price/pagination fixtures>` | `<exact gaps>` |
| Offer viewing references and immutable historical snapshots | `<status>` | `<participants, revisions, appointment-only transitions>` | `<reference>` | `<exact gaps>` |
| Offer media associations and create/upload recovery | `<status>` | `<stable public IDs, private proof, idempotency>` | `<reference>` | `<exact gaps>` |
| Offer notifications/deep links/transient versus persistent chat context | `<status>` | `<visibility, participants, native link deployment>` | `<reference>` | `<exact gaps>` |
| Legacy migration, compatibility and per-operation rollout | `<status>` | `<ambiguous room records, future enums, supported version>` | `<reference>` | `<exact gaps>` |
| Selected-offer lease creation and financial record context | `<status>` | `<explicit agreement, immutable snapshot, ledger amounts>` | `<reference>` | `<exact gaps; creation remains blocked until supported>` |

### 7.3 Final method/path and schema mapping

Fill one row for **all 20 new method/path contracts**, every existing endpoint affected in section 3.2 and each extension delivered. Include unchanged and unavailable endpoints. For rental offers, report the proposed extension of each existing method/path separately: owner POST/PATCH/full GET/owned reads, home/search, favorites GET/POST/DELETE, viewing create and both parties' request/history/calendar reads. Include detailed field placement and scope-aware validation, the agreed owner status/scope query, and favorite saved-offer filtering/grouping/pagination. Document notification/snapshot response mappings and any proposed lease extension. No new offer endpoint is assumed by this request.

| Requested method/path | Actual method/path | Query/body differences | Response/envelope/status differences | Deployed | Exact mobile adaptation |
|---|---|---|---|---|---|
| `<requested>` | `<actual>` | `<unchanged or exact schema>` | `<types/nullability/permissions>` | `<yes/no>` | `<specific work>` |

Provide sanitized actual success, empty, validation, permission, conflict and provider failure payloads for each applicable route. Include JSON types, dates/time zone, revisions, currencies, paging, translation behavior and all supported status values. Confirm DELETE JSON-body handling for alerts and offer favorites, multipart `rental_inventory` encoding, `X-Rental-Offers-Version`/create `Idempotency-Key`, ID/client-key resolution and media array encoding/order. Confirm full saved-inventory responses and exact offer/flag echoes; ignored fields must never produce apparent successful persistence.

#### 7.3.1 Detailed accommodation field delivery matrix

Provide one row for **every extension in section 4.8.13**, plus the actual existing or extended elevator/building-access and media mappings. List unsupported fields explicitly. Proposed names are requirements to resolve, not an instruction to expose private `local_details` or `photo_refs` as API fields.

| Proposed requirement | Actual public entity/key/type | Required, null, omitted/clear and inheritance semantics | Contract version/capability/status | Persisted read-back/error evidence | Exact mobile adaptation |
| --- | --- | --- | --- | --- | --- |
| `<each room/bed/group/shared field or media mapping>` | `<actual mapping, units or catalog/text choice>` | `<create/PATCH/read rules>` | `<verified support or exact gap>` | `<sanitized fixtures/run reference>` | `<typed models, reader, serializer, confirmation>` |

Include unknown optional values, decimal area units, catalog IDs/localized labels where used, preserved known property totals on omitted PATCH fields, and errors for invalid/foreign allocations. Agree any version extension with mobile: the current adapter accepts version 1 only. A deployed field without compatible mobile serialization/read-back confirmation does not authorize removal of the local-only-data submission guard.

### 7.4 Feature-specific delivered details

| Area | Required actual details |
|---|---|
| Configuration/promotion | Free option IDs/durations/titles, no credit debit/feature charge, eligibility/conflicts, placements, `is_sponsored`, campaign expiry and real impression definition |
| Rental inventory/owner writes | Permanent room/bed/offer IDs, client-key mapping, four scopes, whole/partial exclusivity, defaults/overrides, exact scope payloads, capacities/parent refs, overlap/lease/request dependencies, revision/conflict behavior, full response confirmation and availability/archive permissions |
| Detailed accommodation forms | All field mappings in section 4.8.13, supported versus local-only data, partial/whole required-field differences, unknown physical totals, create/PATCH omission/clear rules, explicit shared-property edits, persisted detailed responses and field errors |
| Collection categories | Owner status-plus-scope contract and manageable-offer predicate; saved-only favorite membership/terms/availability; property filters before counts/pages; unknown legacy/snapshot fallback; distinct public/owner/favorite capability recommendations and section 4.8.14 fixtures |
| Rental discovery/favorites | Publication predicate, grouped property result unit/counts, eligible same-period discovery minimum, scope versus property-type filters, actual offer price sorting, saved exact references/tombstones and their separate price context, removal echoes and unsupported query behavior |
| Rental history/migration/rollout | Immutable accommodation/price snapshots, missing/future-field handling, ambiguous legacy room decisions, old IDs/clients, mode-change dependencies and operation-specific capability recommendations with staging evidence |
| Alerts/saved search | Full canonical filters including proposed rental scope/offer-aware price semantics and any alert versioning, supported cadences, workers/meaningful changes, preferences/quiet hours, pause/delete, delivery/deduplication and exact notification/FCM payload |
| Comparison/costs/map/freshness | Property/verification and selected-offer rent/deposit mapping, explicit selection, location privacy, map scope/query support, owner confirmation operation and lifecycle policy |
| Visits/calendar/reviews | Slot/time-zone policy, atomic offer-revision/slot validation, exact IDs/immutable snapshots, appointment-only actions without occupancy changes, exact appointments, review uniqueness, reschedule/completion/reminder support |
| Owner drafts/media | Created/uploaded IDs, create-header/upload idempotency, retained IDs/cover/captions/order, offer/shared associations, omitted versus explicit-empty semantics, private proof, deletion conflicts, property-level validators and PATCH moderation rules |
| Chat/support/notifications/links | Caller `can_send`, KYC, recipient-only conversation creation, transient versus proposed persistent offer context, REST/socket deduplication, private report receipts, offer snapshots/targets, canonical/legacy links, assetlinks/AASA/native requirements and moderation/block policy |
| Analytics | Actual property-versus-offer metrics/definitions/windows/time zone, real accounting revenue, null versus zero, aggregation evidence and authorized export format/expiry |
| AI | Provider/model, facts whitelist, ownership lookup, ar/en support, consent/retention, output limits, factual validation, operational rate limits, retries and no user charge |
| Leases/signing | Approved template IDs/versions/jurisdiction, explicit agreed-tenancy and eligible tenant source, selected-offer create/read extension and its outstanding mobile gate, `property_id` collection filter, legacy contract `lease_id` mapping, immutable accommodation snapshot, participant invitations/consent, document access, states/revisions, provider and reconciled signing events |
| Rent | `lease_id` filtering and Home `status=due,overdue&ordering=due_date&page_size=1` query with honest count/empty/error behavior, stable offer context when supplied, invoice schedule/ownership/ledger amounts/references, quote calculation, no feature-use surcharge, checkout idempotency, provider/settlement evidence, receipts and any partial/refund/settlement gaps |
| Local/private extensions | Which optional sync/lifecycle/map/blocked-user contracts exist, exact privacy/authorization, and remaining client wiring |

Provide actual hosted signing/payment/export/document domains, expiry, return URLs, deep-link requirements and environment differences. Identify any new native configuration needed for real rent/signing integrations; no native subscription/IAP setup is requested.

### 7.5 Concurrency and operational evidence

Document object authorization, idempotency-key scope/fingerprint/retention, room/bed allocation and inventory revision transactions, mode/lease/request dependency transitions, booking/campaign/media/signing/invoice locks, REST/socket message identity, verified webhook deduplication/reconciliation, worker monitoring/rate limits and signed URL permissions. Include observed simultaneous overlap/edit tests, unchanged inventory after viewing acceptance, independent availability after renting one offer, and retained history after archival. Include actual test evidence, not a checklist of intended behavior.

| Scenario | Environment | Observed response/state | Evidence reference | Pass/fail/gap |
|---|---|---|---|---|
| `<scenario from section 6>` | `<actual>` | `<actual result>` | `<test/run reference>` | `<result>` |

Distinguish backend tests from mobile/native-device checks still required.

### 7.6 Exact mobile work after backend delivery

| Mobile feature/file | Required adaptation | Delivered contract/evidence | Acceptance check |
|---|---|---|---|
| `<feature/path>` | `<endpoint/field/status/callback/native changes>` | `<reference>` | `<test/staging/device check>` |

List unsupported statuses, schema/pagination changes, remaining notification routes, provider callbacks, new extension screens/actions and blockers. This table is the implementation input for the final mobile integration; a reply containing only “done” is insufficient.

For rental offers, list exact typed-model, detailed-draft-to-public-schema, reader, serializer and persistence-confirmation changes; agreed owner collection query wiring; saved-offer category/price mappings; and changes for every compile-time define in section 4.8.12. Include the selected-offer lease form/body/confirmation work in section 5.5, remaining AI/alert context extensions and Android/iOS hosted/native link work. Recommend enabling a flag only with evidence for its operation and dependencies; unsupported capabilities keep honest local/disabled behavior. No backend-side deployment changes these compile-time flags automatically.

## 8. Mobile verification and remaining integration checks

Initial free-feature verification on **2026-10-07** used **Flutter 3.35.1 / Dart 3.9.0**. The table records that earlier run; later SDK/rental-offer results are recorded separately below.

| Check | Result |
|---|---|
| Dependency compatibility | Previously resolved successfully; no new dependency for main-flow placement and no `in_app_purchase` or `in_app_purchase_android` dependency |
| Complete Sokoun app tests, including architecture and all three feature matrices | **2,931 passed, 0 failed** |
| Free tool contract/flow/architecture coverage within the passing suite | 11 contract tests, 22 flow tests and 8 architecture tests |
| Main-journey contracts and behavior | **18 passed**; actual property/lease/invoice IDs, workspace routing, eligible-tenant selection, filter/cache isolation, invalid response rejection, explicit AI apply, guest privacy, independent Home loading and refresh |
| Main-journey rendered review | 72 configurations × 8 panels = **576 layouts**, plus 2 keyboard/landscape/split-view input scenarios; **256 PNGs** in `/tmp/sokoun-main-flow-after` |
| Owner dashboard before/after comparison | **8 PNGs** using the original committed widget and updated widget with identical fixture data, Arabic/English at 390/1024, in `/tmp/sokoun-main-flow-comparison` |
| Feature tools rendered review | 72 matrix configurations × 10 panels = 720 layouts, plus 4 keyboard/landscape/split-view scenarios; **320 PNGs** |
| Original free feature rendered review | 72 configurations × 7 panels = 504 layouts; **56 PNGs** in `/tmp/sokoun-free-tools-free-final` |
| App analysis | **0 errors**; 2 existing unused-import warnings in `lib/generated/assets.dart` and `lib/shared_widgets/sokoun_refresh_indicator.dart` |
| Formatting, translation JSON and whitespace | Checked successfully |

Follow-up Profile/Home verification on **2026-10-07** used the workspace's current **Flutter 3.44.7 / Dart 3.12.2**. **502 focused tests passed** across `main_journey_features_test.dart`, `tenant_home_pagination_test.dart`, `profile_flow_test.dart`, `profile_settings_support_test.dart` and `feature_architecture_test.dart`, including **19 main-journey tests**. Both profiles omit the tools shortcut, and the actual tenant Home screen's greeting, search, tools, rent preview and listings move together in one scroll area without a fixed AppBar. Focused analysis found no issues; formatting and whitespace checks passed. This follow-up changes no backend contracts.

Earlier rental-offer verification on **2026-10-07** used **Flutter 3.44.7 / Dart 3.12.2**; the recorded counts below precede the accommodation-form and collection-category follow-up:

| Rental-offer check | Observed result |
|---|---|
| Complete Sokoun app regression suite, before the final historical-review link adjustment | **2,997 passed, 0 failed** |
| Final routing/domain/architecture verification after retaining the review's offer reference | **48 passed, 0 failed**, including both exact-offer and legacy review navigation |
| Focused save/favorites/details/lifecycle checks | **51 passed**, covering failed/ignored saves, exact favorites and preserved legacy concurrent saves |
| Rental editor, tenant selection and review layout matrix | **216 configurations**: widths 320/390/600/768/1024/1366, scales 1/1.3/2, Arabic/English and light/dark; actual Tajawal/MaterialIcons loaded |
| Full app analysis with the current SDK | **0 errors, no new issues**; the same baseline 2 unused-import warnings and 4 existing deprecation infos |
| Changed core and final routing analysis | **No issues found** |
| Formatting and whitespace | **126 changed Dart files checked, 0 formatting changes**; `git diff --check` passed |

Meaningful rental coverage is in `test/rental_offers_domain_test.dart`, `test/rental_offers_requests_test.dart`, `test/rental_offers_ui_test.dart` and the final review-navigation test in `test/tenant_property_details_screen_test.dart`. It covers entire/room/group/bed offers, groups versus independent offers, room/bed overlap, scope-dependent payloads/defaults, exact price/period/media meaning, failed and unsupported persistence, creation recovery, current-session/revision validation, exact favorites/viewings, independent rented availability, appointment-only acceptance, missing/unknown legacy fields, historical snapshots and retained unavailable selections. These tests use fixtures/injected repositories and do not establish backend enforcement or deployment.

For the detailed forms and collection categories in sections 4.8.13–4.8.14, also run `test/rental_accommodation_forms_test.dart` and `test/rental_listing_categories_test.dart` after adapting the agreed backend contract. Keep fixture-based client checks separate from staging persistence, filtering and concurrency evidence requested in section 7.

Relevant commands are:

```sh
cd apps/sokoun_app
make featureToolsCheck
make featureToolsUiReview TOOLS_REVIEW_DIR=/tmp/sokoun-tools-final
make mainJourneyCheck
make mainJourneyUiReview JOURNEY_REVIEW_DIR=/tmp/sokoun-main-flow-after
make freeFeaturesCheck

# Rental-offer/domain/request/UI and final routing/architecture checks:
flutter test --no-pub test/rental_offers_domain_test.dart test/rental_offers_requests_test.dart test/rental_offers_ui_test.dart test/tenant_property_details_screen_test.dart test/feature_architecture_test.dart
# Detailed accommodation forms and collection categories:
flutter test --no-pub test/rental_accommodation_forms_test.dart test/rental_listing_categories_test.dart
# Optional rental UI render captures:
SOKOUN_CAPTURE_RENTAL_UI=1 flutter test --no-pub test/rental_offers_ui_test.dart
```

Use the project SDK on PATH when running these Make targets. They cover free owner/tenant destinations, AI consent/generation without purchase allowances, promotion creation without credits/charges, independent alert history during configuration failures, cache isolation/serialization, mutation retries, real lease/invoice access, authoritative signing/rent statuses and the existing architecture contracts.

Rendered review covers Arabic/English, light/dark, widths 320/390/600/768/1024/1366, scales 1/1.3/2 and additional keyboard/landscape/split-view flows. The feature-tools fixtures render 720 panel cases plus four interaction/layout scenarios; representative PNGs are in `/tmp/sokoun-tools-final`. Original free-feature fixtures also exercise 504 panel layouts.

Main-journey fixtures cover the owner dashboard, owner listing cards, tenant Home header with a real-shaped due invoice, explicit rent empty and cached/unknown-money states, Contracts/document links, a property-specific draft and an active lease's invoice entry. Decimal rent input now preserves the decimal separator (for example `6500.50`) across keyboard/viewport changes; rent card dates use the app's language and listing titles have room for two lines. Existing bottom tabs, listing moderation/rejection/resubmission and real rent checkout are preserved. The duplicate Profile tools shortcuts have been removed. Tenant Home keeps its greeting toolbar, search, rent preview and property results in one scroll area.

Automated client checks do not prove backend deployment, actual provider webhook/settlement/signature behavior, native map rendering, calendar import, picker permissions, device process-kill recovery or a native release build. Complete those integration/device checks after the backend returns its actual delivery file. No backend completion is asserted by this guide.
