# Sokoun — all features backend implementation guide

Date: **2026-10-07**. Mobile project: `apps/sokoun_app`.

**Send this single file to the backend developer.** It consolidates the implementation details, backend handoff and backend response template previously split across the three paid-feature documents, together with every improvement in `SOKOUN_FREE_IMPROVEMENTS_IMPLEMENTATION.md`. This guide is the current integration contract and supersedes the previous paid-feature requirements.

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
- Existing listing validators remain **10–25 unique photos and a required, valid video of 1–60 seconds**. Listing billing period and minimum stay remain separate concepts.

The mobile subscription SDKs and purchase lifecycle have been removed. Feature destinations appear in the main owner/tenant journeys without a catalog, subscription or native-store request. The **Sokoun tools / أدوات سكون** shortcuts have been removed from both profiles; use the contextual entry points in section 2.1.

**Deployment boundary:** client flows are implemented and unlocked. This Flutter workspace contains no backend implementation of the new feature APIs, alert workers, AI provider, signing service or rent payment service. Making the client free does not deploy these services. Configure real services and respond with honest empty/error states while work is incomplete; do not fabricate success, balances, matches, signatures or payments.

## 2. Mobile architecture and integration map

The implementation follows `.agents/skills/sokoun-feature-architecture/SKILL.md` and `apps/sokoun_app/AGENTS.md`:

| Mobile area | Responsibility |
|---|---|
| `features/tenant/decision_tools/data/` and `presentation/` | Account-scoped comparison, costs, notebook, private lists/notes, manual saved searches and explained matches |
| Existing tenant home/search and visits features | Real map results, property availability, booking review, calendar export, visit/review permissions |
| Existing owner home/properties features | Durable editor drafts, image order/cover, quality checks and rejection reasons |
| Existing shared chat/support features | Encrypted local recovery, conversation eligibility, socket lifecycle and durable support receipts |
| `features/shared/premium/data/` | Shared feature API constants, typed free configuration, exact rent money, JSON/cache helpers and hosted-session validation |
| `features/shared/premium/presentation/` | Free tools hub, workspace-only guard, configuration Cubit, typed remote views, confirmation/feedback/empty states and property selection |
| `features/owner/promotions/` | Free campaign composition and history |
| `features/tenant/premium_alerts/` | Free persisted alerts, management and notification navigation |
| `features/owner/advanced_analytics/`, `features/owner/ai_assistant/` | Measured analytics and consent-based listing suggestions |
| `features/shared/digital_leases/`, `features/shared/rent_management/` | Participant documents/signing, invoice history, real rent checkout and receipts |

Some internal folders/classes/translation keys retain their earlier `premium`/`paid` names for source compatibility. They do **not** implement paid access. New service paths use **`features/v1/`**. The client does not call the former `premium/v1/catalog/`, `entitlements/`, `purchase-orders/` or `purchases/verify/` routes. Backend must remove payment requirements from feature handlers and supply the final path mapping if it uses different routes.

Ordinary remote operations use `AsyncCubit`, typed data helpers and `BaseCrudUseCase`. Collections use `AppPagify` and its existing cache contract. Initial requests run from lifecycle initialization; screens compose extracted widgets. Account/resource/query dimensions scope GET caches, with symmetric serializers. Mutations are not cached. Cached visit slots, lease configuration/documents and invoices cannot authorize booking, signing or payment; obtain current server data and enforce rules again during the mutation.

Promotion/alert configuration is owned by a stable content Cubit. Paginated history remains accessible independently of configuration loading/failure. AI, analytics, lease reads and invoice reads have no configuration/subscription prerequisite.

Translations originate in `packages/core/assets/translations/lang.json`. Arabic, English and `LocaleKeys` are generated. Navigation uses `Go` and existing workspace routing. Native billing packages are absent; the updated app resolves with **Flutter 3.35.1 / Dart 3.9.0**.

### 2.1 Main app journeys and resource context

The tools now use the main app journeys as their entry points. The duplicate Profile → Sokoun tools shortcuts have been removed; existing bottom tabs remain in place.

| Journey | Mobile wiring | Backend responsibility |
|---|---|---|
| Owner writes a listing | Add/edit → description section → AI → review/edit → explicitly apply to the local form | Return a suggestion for the supplied facts/property; normal submission and moderation still publish the listing |
| Owner promotes a published listing | Properties → accepted/verified listing card → Promote listing; listing action sheet also retains access | Authorize the actual `property_id`; enforce publication, availability and campaign eligibility |
| Owner reviews performance | Home → Manage your rentals → Advanced analytics → select listing; listing card opens its own analytics | Authorize property and return real period-specific measurements |
| Tenant resumes a search | Home → Saved searches and decisions; Home → Search alerts; results/saved search → alert with its full filters | Persist authorized alerts and match the complete filter set; opening saved searches alone does not create an alert |
| Parties manage a lease | Tenant Home/owner dashboard → Contracts → Digital leases; owner listing → Digital leases for that property → Create lease | Filter `GET leases/` by optional `property_id`; draft keeps that property selected and requires an eligible tenant from `lease-tenants/` |
| Tenant reviews due rent | Signed-in tenant Home → real earliest due/overdue invoice → invoice details → optional real checkout | Return the due-invoice preview query described in section 5.6; fresh detail/mutation authorizes payment |
| Parties review lease invoices | A server-reported signed/active lease → Rent invoices for this lease | Filter `GET rent-invoices/` by `lease_id` and current workspace before pagination |
| Owner tracks rent | Home → Manage your rentals → Rent management | Read authorized invoice history; client does not invent income totals or collect a feature fee |

Existing `profiles/contracts/` document items may include an optional **`lease_id`** pointing to the actual `features/v1/leases/{id}/` resource. The app then offers “View digital lease”. Existing document IDs are never treated as lease IDs. Items without this field keep their existing document viewer, and the Contracts header still opens the digital lease collection.

**Accepting a viewing is not agreement to rent.** The app never creates a lease or invoice automatically from visit acceptance. Backend must define an explicit agreed-tenancy/participant-eligibility process, restrict tenant selection accordingly, and create rent obligations from approved lease/ledger rules. Opening a listing's lease flow supplies a property ID only; it does not select a tenant or confirm eligibility.

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

Rent amounts use integer minor units, never floating point:

```json
{"amount_minor":1200000,"currency":"EGP","exponent":2}
```

All figures/identifiers in examples are illustrative, not approved commercial terms or real performance. The current lease rent form supports EGP with two decimals. The server owns invoice totals and any applicable rent terms.

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

These routes already exist in client code; backend must confirm deployed behavior and supply the needed fields. Constants are in `packages/core/lib/core/network/api_endpoints.dart`.

| Method | Relative path | Backend responsibility |
|---|---|---|
| GET | `properties/` | Full search semantics, honest paging, actual coordinates/availability/verification and promotion labels |
| GET | `properties/{property_id}/` | Current comparable details, rental terms, verification distinctions, freshness and stable media IDs |
| GET | `properties/{property_id}/available_dates/` | Real days; add `date=YYYY-MM-DD` for that day's slots |
| POST | `properties/{property_id}/visits/` | Atomic slot validation and pending viewing request |
| GET | `properties/visits/` and `properties/visits/requests/` | Current account's visits/requests with exact appointment and action permissions |
| GET | `properties/visits/requests/{visit_id}/` | Authorized visit detail used by calendar/review flows |
| PATCH | `properties/visits/{visit_id}/update/` | Authorized cancellation; current body uses `{"status":"canceled"}` |
| POST | `properties/visits/{visit_id}/review/` | Eligibility and unique review validation |
| GET | `properties/owner/visits/requests/` and `properties/owner/visits/requests/{id}/` | Owner request history/details, eligibility and appointment truth |
| POST | `properties/owner/visits/requests/{id}/accept/` and `reject/` | Authorized, atomic request transitions and notifications |
| GET / PUT | `properties/owner/properties/{property_id}/availability/` | Existing owner availability management; confirm final schedule schema |
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

### 4.1 Comparable properties, rent terms and freshness

Return `is_verified`, `owner_is_verified` (or the supported owner object equivalent) and `is_ownership_verified` as distinct facts. Do not substitute promotion for any of them. Missing/removed listings must return the established unavailable/not-found response rather than an invented alternative listing.

`deposit` currently supports `none`, `half_month`, `one_month`, `two_months`, or a supplied non-negative amount. Month-based deposits can be calculated only when `price_period=monthly` and rent is known. A blank deposit is unknown, not zero. Utilities, services and brokerage are not assumed included. The known subtotal is rent plus a known deposit, not a promise that all move-in costs are covered.

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

Current request body:

```json
{"visit_date":"2026-10-10","visit_time":"11:00:00","note":"Tenant supplied note"}
```

Within a transaction, authorize the account/property, revalidate current availability and reserve/create the request according to the actual business policy. Prevent concurrent duplicate bookings and return a useful slot-conflict response. The mobile recheck cannot replace server concurrency protection. Creation currently sends no `request_key`; if the backend adds a booking idempotency token, return its exact schema so the mobile can adopt it.

Visit responses must include a stable ID, property/participant IDs, `status`, exact `visit_date`, exact `visit_time`, existing review information and:

```json
{"actions":{"can_cancel":true,"can_chat":true,"can_review":false,"can_find_alternative":false}}
```

Compute all actions for the authenticated account. Review POST fields are `cleanliness_rating`, `listing_accuracy_rating`, `owner_interaction_rating` (1–5) and `comment`. Enforce eligibility and unique review per eligible visit/reviewer on the server. Calendar export requires an accepted appointment with exact fields; the `.ics` UID derives from the stable visit ID. Notify participants of acceptance/rejection/cancellation and return real visit IDs for review navigation.

Rescheduling, completion recording, automatic calendar update/cancellation and server reminders require a defined lifecycle/notification contract before additional mobile integration. Existing `.ics` sharing is not an automatic calendar sync service.

### 4.3 Owner drafts, media order and publication

Local draft storage does not need a backend draft endpoint. It persists form step, fields, photo/video/proof private copies, captions, existing property ID and acknowledged image IDs. The backend must acknowledge stable IDs immediately so retries update the same listing instead of creating another. Define server idempotency for ambiguous create/upload responses; local recovery alone cannot guarantee a server-side upload was applied only once.

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

Enforce maximum 25 photos transactionally and the 10-photo publication requirement plus required valid 1–60 second video. Edits retain moderation/re-review behavior; return real `rejection_reason` when rejected. Private proof files need appropriate access controls. Quality suggestions do not weaken validators.

### 4.4 Chat eligibility, acknowledgements and recovery

Authorize history/send/read using the current authenticated participant. Return `can_send` in conversation data and enforce that permission on socket and REST writes. A peer's `is_verified` flag is display information, not the caller's sending permission.

Current REST send body is `{"content":"message"}`. Current socket body is `{"conversation_id":"conversation-id","content":"message"}`. These client bodies **do not yet carry a shared server-recognized `client_message_id`**. Local uncertain outgoing messages are encrypted and recovered for explicit review/send; automatic replay is intentionally absent.

Backend must deliver a shared REST/socket idempotency and acknowledgement contract, including `client_message_id`, authoritative message ID/time, current status, retry/conflict behavior and acknowledgement/lookup after timeout. Scope uniqueness to the sender/conversation and deduplicate a socket send followed by REST fallback. Include exact schema/event changes in the delivery file so final mobile work can send/consume them. No duplicate-delivery guarantee is claimed before that integration.

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

### 4.7 Remaining free backend extensions and current mobile boundaries

These were listed as remaining work in the original free implementation document. Backend should define/implement the server contracts and identify the final mobile work in its delivery. They must remain free, but their additional screens/actions are **not yet wired** merely because they appear here.

| Extension | Backend should deliver | Current mobile boundary |
|---|---|---|
| Whole-catalog map search | Bounding-box/radius queries, paging, coordinate privacy and authoritative geographic fields | Viewport filtering currently applies only to loaded search results; no undeclared `bbox` request is sent |
| Nearby services/routes | Real data source, permission/privacy handling, route/service schema and attribution | No fabricated nearby facilities, route or commute score |
| Owner availability confirmation | Authorized confirmation operation, true timestamp and freshness/stale policy | Reads the timestamp; new mutation path awaits backend agreement |
| Listing lifecycle | Pause, rented/unavailable, renew/reactivate and stale transitions with ownership/moderation rules | Shows existing statuses/rejection; new lifecycle mutation endpoints are not invented in the client |
| Visit reschedule/completion/reminders | Exact status transitions, conflict checks, real notification targets and reminder worker | Existing request/cancel/review and local calendar export remain available |
| Cross-device manual saved searches | Account-owned CRUD, full filters, revisions and conflict/deletion rules | Current manual searches are local; free automatic alerts are separate server records in section 5.2 |
| Optional private notebook/checklist sync | Explicit opt-in, account-private CRUD/revisions, privacy and deletion semantics | Local notes/groups/checklists work without server sync; never upload automatically |
| Server-side blocking | Separate authorized action, existing conversation/history policy and enforcement | Report submission is not a block |

Return actual API/schema proposals for requested extensions rather than marking them delivered from existing list endpoints. Optional cloud synchronization is not a prerequisite for existing local features. Partial rent payments/refund requests, analytics time series and historical notified-match lists likewise need explicit additional contracts; the current new flows are described next.

## 5. Formerly paid features — free service contracts

All six capabilities below are available in the client without subscriptions or feature charges. Backend must make their operations free and enforce only the real rules in section 1.

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

Create campaigns atomically and return the same result for repeated `request_key` submissions. Do not reserve/debit credits or create a charge. Define cancellation, moderation removal and failure behavior. Campaign scheduling/ranking/expiry and impression counting are backend responsibilities. The app makes no position, lead or conversion guarantee.

Create response data is an action receipt with campaign `id`, `subject_id` equal to the property ID, and `status=active|pending`. Campaign page items contain `id`, `property_id`, `property_title`, `status`, `duration_days`, `starts_at`, `ends_at`, and nullable `impressions`. Supported history states include `pending`, `active`, `paused`, `completed`, `cancelled`, `expired`, `failed`.

Return `is_sponsored: true` in sponsored home/search property payloads for placements where the backend applies promotion. Existing mobile property models preserve this flag and display a sponsorship label independently of `is_verified`. Define the allowed sponsored placements and labeling contract. Promotion must not change verification flags or conceal preferential placement. The public label is “Promoted listing”; the existing wire field remains `is_sponsored` for compatibility.

### 5.2 Free saved-search alerts

Alert body:

```json
{"name":"Near work","cadence":"daily","filters":{"search":"Maadi","city":"","district":"","ordering":"-created_at","page":1,"page_size":10,"price_min":"10000","price_max":"18000","property_type":"apartment","price_period":"monthly","suitable_for":"family","is_furnished":"true","is_verified":"","smoking_allowed":"","bedrooms":"2","bathrooms":"1","amenities":["wifi"]},"request_key":"client-generated-uuid"}
```

Use the existing `PropertySearchFilters` wire semantics exactly, including empty strings and string-valued filter flags. Validate price range and use the same interpretation as ordinary search. The full canonical schema is in `features/tenant/home/data/models/property_search_model.dart`; do not drop dimensions when persisting a search. The client normalizes the alert's page to 1.

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

### 5.5 Free digital lease drafts and signing

Configuration data:

```json
{"can_create":true,"templates":[{"id":"approved-template-id","title":"Residential lease","jurisdiction":"EG","language":"ar","version":"approved-version"}]}
```

Tenant option page items: `{"id":"eligible-tenant-account-id","display_name":"Tenant name"}`. Scope the query to the owned `property_id` and participants eligible under the agreed-tenancy process. Do not infer agreement from an accepted viewing or expose an unrestricted user directory. The mobile form selects names and sends the selected opaque ID; it does not ask users to enter internal IDs. Empty eligible-tenant results must remain a real empty response rather than a fabricated tenant.

`GET leases/?workspace=owner&property_id=...&page=1&page_size=20` returns only that authorized property's leases. Apply resource filtering before computing count/pagination. The unfiltered Contracts/tools entry still requests all authorized leases in the selected workspace. Document any actual filter naming changes in the returned delivery file.

Lease draft body:

```json
{"property_id":"owned-property-id","tenant_id":"eligible-tenant-id","template_id":"approved-template-id","template_version":"approved-version","start_date":"2026-10-10","end_date":"2027-10-10","rent":{"amount_minor":1200000,"currency":"EGP","exponent":2},"request_key":"client-generated-uuid"}
```

Validate ownership, participant eligibility/consent requirements, approved template/version, real dates, positive rent and end after start. Generate the full legal document from approved template data. Template approval, jurisdiction-specific requirements and signature validity are responsibilities of the business/backend/signing provider; the app does not generate legal clauses or declare a browser return legally signed.

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

Signing/payment webhooks require authenticated provider evidence, durable event IDs, deduplication, retry handling and reconciliation. Never update `signed` or `paid` from the client returning to the app. Keep private credentials and provider execution on the backend. Signed document/export/receipt URLs must be HTTPS, participant/owner authorized and expire appropriately.

Suggested delivery order:

1. Confirm existing authentication, account/workspaces and free property/visit/media/chat/support contracts. Remove legacy feature-payment checks and implement free configuration.
2. Resolve atomic slot booking, media identity/order, truthful availability/permissions/rejections/statistics and chat acknowledgement/idempotency gaps.
3. Deploy free campaigns, alert persistence/matching/push, analytics aggregation/export and AI generation with operational monitoring.
4. Configure approved lease templates and eligible participant selection, then deploy document access, signing sessions and reconciled provider events.
5. Deploy invoice generation, real rent quote/checkout, settlement reconciliation and durable receipts.
6. Deliver extension contracts from section 4.7 with explicit implementation/integration status. Provide sanitized fixtures and staging evidence for every required feature/path.
7. Return the completed delivery MD below. Mobile then applies real endpoint/schema differences, callbacks and remaining integration work and verifies staging/device flows.

Required backend checks: unauthenticated/wrong-account reads/writes, workspace/ownership/participant checks, empty/missing resources, fresh versus stale/cached authorization, simultaneous slot bookings, invalid and reordered media IDs, ambiguous create/upload retries, duplicate review prevention, REST/socket duplicate sends, durable report receipts, nullable metrics, unsupported configuration, repeated keys/payload conflicts, ineligible promotion, campaign expiry, alert pause/delete/deduplication, AI failure/retry without user charges, signing revision/participant/expiry checks, expired/declined/delayed checkout, webhook replay and paid-invoice replay. Confirm each free feature works without any subscription, entitlement or credit record.

## 7. Backend return file — required response format

Backend: create **`SOKOUN_ALL_FEATURES_BACKEND_DELIVERY.md`** and return it to the mobile developer. Populate the following format with **actual delivered behavior**; placeholders are not completion evidence. Include incomplete features and exact mobile work. Share credentials/passwords separately through the established secure channel.

### 7.1 Delivery identity

- Delivery date: `<actual date>`
- Backend repository/commit/release: `<reference>`
- Deployment environment/version: `<actual values>`
- Staging API base/prefix and production rollout: `<actual values/status>`
- Authentication/session changes: `<details or unchanged>`
- OpenAPI/Postman/schema/fixture locations: `<links or delivered files>`
- Account role and eligible property/tenant/visit/lease/invoice fixture IDs: `<sanitized IDs>`
- Free feature policy: `<evidence that no subscription, feature charge, entitlement or credit is required>`
- Real rent checkout retained: `<provider/environment/status>`

### 7.2 Complete feature delivery matrix

Use `deployed and verified`, `implemented but not deployed`, `blocked`, `not implemented`, or `client-only; dependencies confirmed` with evidence. Copy **every feature row in sections 4 and 5**, plus extension rows from 4.7. Do not mark the whole project done because a route exists.

| Feature | Actual status | Scope/permissions | Evidence | Remaining backend/mobile work |
|---|---|---|---|---|
| `<each feature>` | `<status>` | `<workspace/ownership>` | `<reference>` | `<exact gaps>` |

### 7.3 Final method/path and schema mapping

Fill one row for **all 20 new method/path contracts**, every existing endpoint affected in section 3.2 and each extension delivered. Include unchanged and unavailable endpoints.

| Requested method/path | Actual method/path | Query/body differences | Response/envelope/status differences | Deployed | Exact mobile adaptation |
|---|---|---|---|---|---|
| `<requested>` | `<actual>` | `<unchanged or exact schema>` | `<types/nullability/permissions>` | `<yes/no>` | `<specific work>` |

Provide sanitized actual success, empty, validation, permission, conflict and provider failure payloads for each applicable route. Include JSON types, dates/time zone, revisions, currencies, paging, translation behavior and all supported status values. Confirm DELETE JSON-body handling for alerts and multipart array encoding/order for media.

### 7.4 Feature-specific delivered details

| Area | Required actual details |
|---|---|
| Configuration/promotion | Free option IDs/durations/titles, no credit debit/feature charge, eligibility/conflicts, placements, `is_sponsored`, campaign expiry and real impression definition |
| Alerts/saved search | Full canonical filters, supported cadences, workers/meaningful changes, preferences/quiet hours, pause/delete, delivery/deduplication and exact notification/FCM payload |
| Comparison/costs/map/freshness | Property/verification/rent/deposit field mapping, location privacy, map scope/query support, owner confirmation operation and lifecycle policy |
| Visits/calendar/reviews | Slot/time-zone policy, atomic booking/conflicts, action permissions, exact appointments, review uniqueness, reschedule/completion/reminder support |
| Owner drafts/media | Created/uploaded IDs, ambiguous-retry handling, retention/omission semantics, persisted order, cover/caption metadata and moderation rules |
| Chat/support | Caller `can_send`, KYC enforcement, REST/socket client ID/ack/status schema, deduplication, durable ticket receipts, moderation/block policy |
| Analytics | Actual metrics/definitions/windows/time zone, null versus zero, aggregation evidence and authorized export format/expiry |
| AI | Provider/model, facts whitelist, ownership lookup, ar/en support, consent/retention, output limits, factual validation, operational rate limits, retries and no user charge |
| Leases/signing | Approved template IDs/versions/jurisdiction, explicit agreed-tenancy and eligible tenant source, `property_id` collection filter, legacy contract `lease_id` mapping, participant invitations/consent, document access, states/revisions, provider and reconciled signing events |
| Rent | `lease_id` filtering and Home `status=due,overdue&ordering=due_date&page_size=1` query with honest count/empty/error behavior, invoice schedule/ownership/amounts/references, quote calculation, no feature-use surcharge, checkout idempotency, provider/settlement evidence, receipts and any partial/refund/settlement gaps |
| Local/private extensions | Which optional sync/lifecycle/map/blocked-user contracts exist, exact privacy/authorization, and remaining client wiring |

Provide actual hosted signing/payment/export/document domains, expiry, return URLs, deep-link requirements and environment differences. Identify any new native configuration needed for real rent/signing integrations; no native subscription/IAP setup is requested.

### 7.5 Concurrency and operational evidence

Document object authorization, idempotency-key scope/fingerprint/retention, booking/campaign/media/signing/invoice locks, REST/socket message identity, verified webhook deduplication/reconciliation, worker monitoring/rate limits and signed URL permissions. Include actual test evidence, not a checklist of intended behavior.

| Scenario | Environment | Observed response/state | Evidence reference | Pass/fail/gap |
|---|---|---|---|---|
| `<scenario from section 6>` | `<actual>` | `<actual result>` | `<test/run reference>` | `<result>` |

Distinguish backend tests from mobile/native-device checks still required.

### 7.6 Exact mobile work after backend delivery

| Mobile feature/file | Required adaptation | Delivered contract/evidence | Acceptance check |
|---|---|---|---|
| `<feature/path>` | `<endpoint/field/status/callback/native changes>` | `<reference>` | `<test/staging/device check>` |

List unsupported statuses, schema/pagination changes, remaining notification routes, provider callbacks, new extension screens/actions and blockers. This table is the implementation input for the final mobile integration; a reply containing only “done” is insufficient.

## 8. Mobile verification and remaining integration checks

Verified on **2026-10-07** using **Flutter 3.35.1 / Dart 3.9.0**.

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

Relevant commands are:

```sh
cd apps/sokoun_app
make featureToolsCheck
make featureToolsUiReview TOOLS_REVIEW_DIR=/tmp/sokoun-tools-final
make mainJourneyCheck
make mainJourneyUiReview JOURNEY_REVIEW_DIR=/tmp/sokoun-main-flow-after
make freeFeaturesCheck
```

Use the project SDK on PATH when running these Make targets. They cover free owner/tenant destinations, AI consent/generation without purchase allowances, promotion creation without credits/charges, independent alert history during configuration failures, cache isolation/serialization, mutation retries, real lease/invoice access, authoritative signing/rent statuses and the existing architecture contracts.

Rendered review covers Arabic/English, light/dark, widths 320/390/600/768/1024/1366, scales 1/1.3/2 and additional keyboard/landscape/split-view flows. The feature-tools fixtures render 720 panel cases plus four interaction/layout scenarios; representative PNGs are in `/tmp/sokoun-tools-final`. Original free-feature fixtures also exercise 504 panel layouts.

Main-journey fixtures cover the owner dashboard, owner listing cards, tenant Home header with a real-shaped due invoice, explicit rent empty and cached/unknown-money states, Contracts/document links, a property-specific draft and an active lease's invoice entry. Decimal rent input now preserves the decimal separator (for example `6500.50`) across keyboard/viewport changes; rent card dates use the app's language and listing titles have room for two lines. Existing bottom tabs, listing moderation/rejection/resubmission and real rent checkout are preserved. The duplicate Profile tools shortcuts have been removed. Tenant Home keeps its greeting toolbar, search, rent preview and property results in one scroll area.

Automated client checks do not prove backend deployment, actual provider webhook/settlement/signature behavior, native map rendering, calendar import, picker permissions, device process-kill recovery or a native release build. Complete those integration/device checks after the backend returns its actual delivery file. No backend completion is asserted by this guide.
