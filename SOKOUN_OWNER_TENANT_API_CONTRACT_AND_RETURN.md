# Sokoun owner–tenant API contract and backend return template

Prepared **2026-10-12** against the Flutter working tree after baseline `0e122774433b42e16a6643f33e886bdd29d897c9`. Read alongside [the Django implementation/verification guide](SOKOUN_OWNER_TENANT_DJANGO_IMPLEMENTATION_AND_VERIFICATION.md) and [the cycle specification](../../SOKOUN_OWNER_TENANT_CYCLES_EXPLAINED_EN.md).

This is the **client-compatible target contract**, not a declaration that all routes are deployed. Legacy/advertising contracts have earlier backend handoffs; structured rental has a local-backend return; planning remains a proposed client integration with historical 404 observations. The backend engineer must fill section 12 with the actual deployed contract, examples, deviations and evidence. “Correct” means demonstrated conformance for the tested version and cases; an unverified endpoint cannot be called 100% correct.

## 1. Protocol and compatibility boundaries

All paths are relative to `/api/v1/` unless a section explicitly says otherwise. Preserve trailing slashes, method, content type and query/body placement. URL-encode opaque resource IDs. Use actual server IDs from previous responses; sample aliases such as `lease-example` are explanatory and are not valid production UUIDs. Request-key examples are synthetic stable UUIDs; reuse a key only for the same logical intention.

| Family | Prefix / body convention | Success `data` shape | Compatibility rule |
| --- | --- | --- | --- |
| Property/visit/chat | Existing `properties/`, `homepage/`, `chat/`; some multipart; visit bodies have no generic revision/key | Existing resource/collection schema | Do not add a required `expected_revision`/`request_key` to these clients without a coordinated migration. |
| Legacy features/invitations | `features/v1/`; `request_key`, action-specific `revision` | Direct resource, not canonical wrapper | Invitation response and legacy draft/cancel must remain accepted. |
| Structured rental | `features/v1/`; `request_key`, `expected_revision` plus source revisions | `{resource,operation_receipt}` for most writes | Reads are direct resources; payment-attempt reconciliation is a direct resource exception. |
| Planning | `features/v1/`; typed action body with `request_key`, `expected_revision` | `{resource,operation_receipt}` for writes | Invite preview is a read-only POST returning a direct resource; no mutation receipt. |
| Banner advertising | `advertising/v1/`; `operation_id`, multipart create, mock activation | Advertising resource/receipt fields | Do not substitute rental request keys/quotes or claim real PSP capture. |

Headers: `Accept: application/json`, `Accept-Language: ar` or `en`, `Content-Type: application/json` for JSON. Multipart uploads must use the generated boundary and real bytes. Current transport persists access/refresh cookies and can derive `Authorization: Bearer …` from the access cookie; return the exact installed Django auth/refresh behavior. Do not publish tokens in this return document. Private responses must avoid shared/public caching; locale-dependent public responses need appropriate language variation.

`workspace=owner|tenant` controls presentation/filtering. The server must derive identity and permissions from authentication and database relationships, never from workspace or a supplied participant ID.

## 2. Shared JSON shapes and types

### 2.1 Envelope, pagination and canonical receipt

Feature successes use `key=success`, `msg` and `data`; advertising handoff uses `message`. Preserve the family's documented message field and HTTP status. An HTML proxy error, login page or malformed 200 is not a successful resource.

<!-- contract: empty-page -->
```json
{"key":"success","msg":"","data":{"results":[],"count":0,"per_page":20,"total_pages":1,"next":null,"previous":null}}
```

Collections request `page` (one-based) and, in shared feature pagination, `page_size=20`. Return stable deterministic ordering, correct filtered count/page metadata and no duplicate IDs across pages. Parent-scoped pages must not contain other requests' offers or other leases' reports/transitions. A fresh empty page is authoritative. Return an empty collection rather than a placeholder object with an empty ID.

<!-- contract: decision-request -->
```json
{"expected_revision":3,"request_key":"c2a15b57-1376-44e0-af2e-355086934ab1","decision":"accept_review","note":"Reviewed the current terms."}
```

`Decision` in later tables means exactly the above shape with the action's decision token. `effective_on`, `requested_date`, `item_ids` are included only when nonempty/applicable. `note` is emitted even when empty. The URL action is not always identical to the decision token: `/review/` receives `accept_review` or `request_changes`.

Canonical writes return an operation receipt **inside `data` alongside `resource`**. Receipt fields are `id`, `subject_id`, `request_key`, positive `revision`, `status=confirmed`. The receipt subject is the returned resource identity. A new resource can have a different subject than the source used for capability/recovery lookup. For an existing aggregate its revision must advance beyond the reviewed revision. For artifacts such as quotes, receipt revision belongs to the artifact; do not compare it to the source invoice's revision.

### 2.2 Money, dates, nullability and permissions

| Value | Exact convention |
| --- | --- |
| Accounting Money | `{amount_minor: integer, currency: "EGP", exponent: 2}`; no floating-point major-unit accounting. Unknown values must not become zero. Refund/deposit/fees stay separate. |
| Listing price | `RentalSelection.terms.price` is a decimal **string** in the listing contract, with `price_period`; it is not a Money object. Convert/validate on the server, never confuse it with accounting rent. |
| Revision | Integer; create target normally 0, saved resource positive. `offer_revision`, `invitation_revision`, `request_revision`, `lease_revision`, `roster_revision`, `item_revision` refer to different resources. |
| Civil dates | `YYYY-MM-DD`; `starts_on`/`ends_on_exclusive` are not UTC instants. Preserve inclusive/exclusive semantics and `Africa/Cairo` calendar policy. Legacy `start_date`/`end_date` must be returned exactly as accepted. |
| Instants | Timezone-aware ISO 8601; UTC `Z` recommended for responses. Expiry is server-authoritative; client-visible TTL is not authorization. |
| Permissions | Root `allowed_actions: string[]`, `blocking_reasons: string[]`; legacy invitation also uses `actions.can_respond`. Unknown status tokens must not enable actions. |
| Optional vs null | Follow each serializer. Example: empty legacy `offer_id` is omitted; housing `end_on` is null when unspecified; response `lease_id` may be null/empty before consumption. Do not replace all empty strings with null globally. |
| IDs | Opaque stable strings; never use display labels as IDs. Return `user_id` for chat participants, resource ID for an invitation/connection, and retain the distinction. |

### 2.3 Exact accommodation snapshot

<!-- contract: rental-selection -->
```json
{
  "property_id":"property-example","offer_id":"offer-example","offer_revision":7,
  "rental_scope":"bed","name":"Bed A1","room_ids":["room-a"],"room_names":["Room A"],
  "bed_id":"bed-a1","bed_name":"Bed A1",
  "terms":{"price":"10000","price_period":"monthly","rental_period":3,"deposit":"one_month","suitable_for":"students","description":"Shared accommodation close to campus.","smoking_allowed":false,"rules":["Keep shared spaces clean"]},
  "availability":"available","archived":false,"capacity":2,"bathroom_access":["shared"],
  "offer_link":"https://sokoun.app/properties/property-example/offers/offer-example"
}
```

`entire_property`, `room`, `room_group`, `bed` are distinct scopes. Room has one room ID; room group has at least two distinct room IDs; bed has one room and a bed ID/name, with shared-room capacity at least two. Supply matching room labels and resolved terms. Historical snapshots retain original terms after listing edits. Server must reconstruct/validate the canonical snapshot instead of trusting a submitted price. The client now compares structured creation against the accepted invitation snapshot, including names, room/bed identity, capacity, bathroom access and terms; locale-dependent labels must stay consistent through this round trip.

## 3. Capabilities and operation recovery

`GET features/v1/rental-capabilities/?subject_id={source_or_resource}&action={action}` returns account-bound `account_id`, `account_verified`, `enabled_capabilities`, `policy_version`, `allowed_actions`, `blocking_reasons`. Supported client capability names: `rental_center`, `rental_interests`, `rental_agreements`, `rent_checkout`, `rental_handovers`, `condition_reports`, `rental_deposits`, `rental_maintenance`, `rental_changes`, `rental_settlement`, `rental_disputes`, `owner_payouts`, `signed_documents`, `rental_reviews`.

`GET features/v1/planning-capabilities/?capability=housing_offers&action=read` optionally includes `subject_id` for scoped commands/reads. Collection authorization currently omits the subject; the actual collection route still must enforce its parent scope.

<!-- contract: planning-access -->
```json
{"key":"success","msg":"","data":{"account_id":"tenant-example","account_verified":true,"policy_version":"planning-policy-v1","enabled_capabilities":["housing_offers"],"verified_services":["housing_offers"],"allowed_actions":["read"],"expires_at":"2027-01-01T12:05:00Z"}}
```

This is a shape example, not a live/future permission grant. Return a short real expiry and only services verified in that environment. Planning names: `lifestyle`, `roommates`, `housing_groups`, `group_visits`, `group_applications`, `housing_requests`, `housing_offers`, `commute`, `tenant_assistant`, `condition_reports`, `move_out_notices`, `replacements`. Mobile build flags and server grants are both required. Empty capabilities/actions or 404 keep the service unavailable.

`GET features/v1/rental-operations/{request_key}/?subject_id={original_request_subject}` is a fresh authorized lookup, not a new command. Preserve the original request subject even if the operation created a new resource.

<!-- contract: operation-confirmed -->
```json
{"key":"success","msg":"","data":{"request_key":"161f3a2b-b1ee-4f73-8994-20e4abf35744","request_subject_id":"invitation-example","status":"confirmed","operation_receipt":{"id":"operation-example","subject_id":"lease-example","request_key":"161f3a2b-b1ee-4f73-8994-20e4abf35744","revision":1,"status":"confirmed"}}}
```

**Current generic client accepts only `confirmed`, `pending`, `unknown`. It rejects `absent_final` because the current backend has no agreed permanent tombstone guarantee.** Older proposal text mentioning final absence is a future requirement, not currently supported behavior. Do not unlock a replacement write with a 404. Any future final-absence support needs a durable server guarantee and coordinated mobile change. Payment lookup's separate `absence_confirmed` contract is described below; it also requires permanent absence, never a temporarily empty list.

Sources: [rental API constants](../../apps/sokoun_app/lib/features/shared/premium/data/rental_api_constants.dart), [rental capability enum](../../apps/sokoun_app/lib/features/shared/premium/data/enums/rental_capability.dart), [planning access](../../apps/sokoun_app/lib/features/shared/premium/data/models/planning_access.dart), [operation lookup](../../apps/sokoun_app/lib/features/shared/premium/data/rental_operation_data.dart).

## 4. C01/C02/S01 — property, visits and communication

| Method / path | Current client input | Response and critical rule |
| --- | --- | --- |
| GET `homepage/`, `properties/` | Catalog search/scope/filter/paging query | Public published discovery with `rental_schema_version`, `rental_summary` count/scopes/labels/price/period/scope/starting_from; exact filters before pagination |
| GET `properties/types/`, `properties/filter-options/`, `properties/governorates/`, `properties/cities/` | Existing catalog query | Stable catalog IDs and localized labels; do not invent missing district IDs |
| POST `properties/create/`; GET/PATCH `properties/{id}/` | Existing property multipart fields, inventory JSON when enabled | Full saved property, stable room/bed/offer IDs, echoed client keys, revisions, moderation/actions |
| GET `properties/owned/` | Owner filters/pagination, optional `rental_scope` | Owned property inventory, `rental_scopes`, `manageable_offer_count`; no other owner's private drafts |
| POST `properties/{id}/confirm-availability/` | Existing action body | Authoritative `availability_confirmed_at`; `updated_at` is not equivalent |
| POST `properties/{id}/save/`; DELETE `properties/{id}/unsave/` | `{offer_id}` for exact offer; existing legacy property mode when no offer | Echo `offer_id`, `is_saved`; multiple offers under one property independent |
| GET `properties/{id}/available_dates/` | Existing date/availability query | Real selectable dates/slots, consistent with owner calendar |
| GET `properties/owner/properties/{id}/availability/` | `week_start=YYYY-MM-DD` | Owned weekly schedule, editable/locked slot states |
| PUT `properties/owner/properties/{id}/availability/` | `availability_date`, `slots:[{time,is_enabled}]` | Updated schedule; booked/locked slots cannot be silently cleared |
| GET `properties/owner/calendar/` | `year`, `month`, `date=YYYY-MM-DD` | Owner calendar days/visits for the selected month/date |
| POST `properties/{id}/visits/` | `BookVisitBody` below | Saved visit with exact `offer_id`/`offer_snapshot`; validate slot and current offer |
| GET `properties/visits/`, `properties/visits/requests/` | Tenant `page`, optional `status` | Tenant-scoped visits/requests with localized labels/actions and correct page metadata |
| GET `properties/owner/visits/requests/`, `properties/visits/received/` | Owner pagination | Owner-scoped request/received views, including tabs and status labels |
| GET `properties/visits/{id}/`, `properties/visits/requests/{id}/`, `properties/owner/visits/requests/{id}/` | Respective actor resource ID | Authorized detail, current actions, history and contact grant |
| POST `properties/owner/visits/requests/{id}/accept/` | No business fields in current accept command | Updated accepted request; no lease/allocation |
| POST `properties/owner/visits/requests/{id}/reject/` | `reason`, `custom_reason` | Rejected request; reason policy enforced |
| PATCH `properties/visits/{id}/update/` | `{status:"canceled"}` for current tenant cancel | Cancellation result; preserve accepted contact history according to policy |
| POST `properties/visits/{id}/review/` | `cleanliness_rating`, `listing_accuracy_rating`, `owner_interaction_rating`, `comment` | Authorized eligible review, ratings 1..5; no fabricated completion |
| GET `properties/{id}/reviews/` | Pagination | Published reviews with safe author projection |
| POST `chat/conversations/create/` | `{user_id}` of allowed counterparty | Canonical conversation; independent relationship authorization |
| GET `chat/conversations/`, `chat/conversations/{id}/`, `chat/conversations/{id}/messages/` | Actor pagination/cursor according to current chat DTO | Participant-scoped thread/messages, persisted IDs and ordering |
| POST `chat/conversations/{id}/messages/create/` | `{content,client_message_id}` | Canonical persisted message with same client ID; socket retry must not duplicate it |
| POST `chat/conversations/{id}/read/` | Existing read action | Authorized read/unread state; never another participant's thread |

Full listing fields and inventory nesting are in [the current serializer matrix](../qa/SOKOUN_SERIALIZER_MATRIX.md), [owner draft implementation](../../apps/sokoun_app/lib/features/owner/home/data/owner_draft_data.dart) and [inventory handoff](../../MOBILE_ALL_FEATURES_BACKEND_HANDOFF.md#4-rental-inventory-integration). For inventory creation preserve `X-Rental-Offers-Version: 1` and `Idempotency-Key: <stable draft UUID>`; `rental_inventory` is a multipart JSON string with `schema_version`, `mode`, `expected_revision`, rooms/beds/shared defaults/media/offers. This is not the structured lease JSON body.

<!-- contract: visit-request -->
```json
{"offer_id":"offer-example","expected_offer_revision":7,"visit_date":"2027-01-15","visit_time":"11:00:00","note":"Please confirm the selected bed can be viewed."}
```

Legacy visit requests omit both offer fields. Current `BookVisitBody` does **not** emit a request key, target revision or timezone. Do not silently require those fields; return any proposed versioned upgrade. Available-date and owner-availability DTOs remain defined by [visit models](../../apps/sokoun_app/lib/features/owner/visits/data/models/). Socket send includes `conversation_id`, `content`, `client_message_id`; REST send omits `conversation_id` because it is in the path. ACK, persistence and counterpart broadcast are three independently tested facts.

## 5. C03 — legacy invitation and draft contract

### 5.1 Invitation create, read and tenant response

All routes here start `features/v1/`:

| Route | Input | Output |
| --- | --- | --- |
| POST `tenancy-invitations/` | Legacy body below | Direct `TenancyInvitation` in `data`; owner/source checked |
| GET `tenancy-invitations/` | `workspace`, optional `property_id`, paging | Participant-scoped paginated invitations |
| GET `tenancy-invitations/{id}/` | ID | Direct invitation |
| POST `tenancy-invitations/{id}/respond/` | `decision=accepted|rejected`, **`revision`**, `request_key` | Direct updated invitation |
| GET `lease-tenants/` | `property_id` | Eligible accepted unconsumed tenants as `id`, `display_name` |
| GET `lease-configuration/` | Actor | Approved templates/versions and `can_create`; structured policy extension if supported |

<!-- contract: legacy-invitation-request -->
```json
{"property_id":"property-example","tenant_id":"tenant-example","offer_id":"offer-example","expected_offer_revision":7,"request_key":"fb12f8a4-c4f6-423e-ae14-f8bcb6655dab"}
```

If no rental inventory is selected, omit `offer_id` **and** `expected_offer_revision`. The source visit is resolved by the backend; the current legacy body does not send a `visit_id`.

<!-- contract: legacy-invitation-response -->
```json
{"key":"success","msg":"Invitation created.","data":{"id":"invitation-legacy","property_id":"property-legacy","property_title":"Legacy apartment","owner_id":"owner-example","owner_name":"Owner","tenant_id":"tenant-example","tenant_name":"Tenant","offer_id":null,"offer_snapshot":null,"status":"pending","revision":1,"created_at":"2027-01-01T12:00:00Z","expires_at":"2027-01-08T12:00:00Z","accepted_at":null,"rejected_at":null,"revoked_at":null,"lease_id":null,"eligible_for_lease":false,"actions":{"can_respond":true},"allowed_actions":[],"blocking_reasons":[]}}
```

This example is a **tenant projection for a separate property without inventory**. For the offer-aware create example, return its same property/offer and the complete snapshot from §2.3. `actions.can_respond` is actor-specific: false for owner, true only for the intended tenant while eligible to respond. After accept, increment revision, set `accepted_at`, set `eligible_for_lease` according to current expiry/source/consumption, and remove respond permission. Seven-day validity still applies after acceptance. New draft consumes consent permanently; cancel never restores it.

<!-- contract: legacy-invitation-accept -->
```json
{"decision":"accepted","revision":1,"request_key":"eed8a613-a642-4bce-9a5b-d9c5658d9b98"}
```

### 5.2 Legacy draft creation and cancellation

`POST features/v1/leases/` accepts the existing `LeaseDraftBody`. This route also supports the structured body in §6; distinguish the schemas deliberately on the server.

<!-- contract: legacy-draft-request -->
```json
{"property_id":"property-legacy","tenant_id":"tenant-example","template_id":"eg-residential-v1","template_version":"1","start_date":"2027-01-15","end_date":"2027-07-15","rent":{"amount_minor":500000,"currency":"EGP","exponent":2},"request_key":"60c6c290-e532-4e7f-899a-b1dc1d0630a2"}
```

<!-- contract: legacy-draft-response -->
```json
{"key":"success","msg":"Draft created.","data":{"id":"lease-legacy","property_id":"property-legacy","property_title":"Legacy apartment","invitation_id":"invitation-legacy","owner_name":"Owner","tenant_name":"Tenant","start_date":"2027-01-15","end_date":"2027-07-15","rent":{"amount_minor":500000,"currency":"EGP","exponent":2},"offer_snapshot":null,"status":"draft","revision":1,"can_sign":false,"can_cancel":true,"legacy_read_only":false,"allowed_actions":[],"blocking_reasons":[]}}
```

This owner projection deliberately demonstrates existing compatibility when `owner_id`/`tenant_id` are omitted. If present, they must match the authenticated owner and selected tenant. Dates and rent must match the accepted body. Offer-aware draft adds **only** `offer_id` to this body and returns its exact stored `offer_snapshot`; the body does not send `invitation_id`, `expected_offer_revision`, `rentalSelection` or `hasRentalOffers`. Django must resolve and consume the unique accepted source atomically, validating current inventory; reject ambiguous/stale sources.

`POST features/v1/leases/{id}/cancel/` legacy body is `{revision,request_key}`; return the direct cancelled lease with advanced revision. Same-key replay must return the saved cancellation even though the original revision is now stale. New key on a stale revision must conflict. A cancelled draft has no possession to return and creates no rental invoice. Old read-only history and new cancellable drafts are separate classifications.

Legacy signing's historical body `{revision,request_key}` does not authorize structured signing. Keep signing disabled unless the appropriate service/contract is verified. The old checkout handoff likewise does not replace the current quote-based payment flow.

Sources: [invitation backend return](../../TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md), [legacy draft body](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/lease_draft_body.dart), [draft Cubit](../../apps/sokoun_app/lib/features/shared/digital_leases/presentation/cubits/lease_draft_cubit.dart).

## 6. C04–C06 — structured rental endpoint and body registry

All routes in this section start `features/v1/`. `Mutation<T>` means the canonical resource/receipt wrapper in §2. DTO fields, including request field inventories, are in §13 and linked directly to Dart. Do not send a field inventory as an object with every value null: use each serializer's actual types and omission rules.

### Readiness, interest, invitation and agreement

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET `rental-capabilities/` | `subject_id`, `action` | `RentalCapabilities`; fresh authenticated verification and scoped actions |
| GET `rental-operations/{request_key}/` | `subject_id` | `RentalOperationLookup`; current client accepts confirmed/pending/unknown only; see section 3 |
| GET `owner-payment-profile/` | Current owner | `OwnerPaymentProfile`; masked beneficiary, required policies, KYC requirements and actions |
| POST `owner-payment-profile/onboarding-session/` | `OwnerOnboardingBody` | `Mutation<OwnerOnboardingSession>`; hosted KYC URL with TTL, subject/revision/key and operation identity |
| GET `rental-interests/` | `workspace`, pagination | `RentalInterest[]`; participant-scoped offer snapshots |
| POST `rental-interests/` | `RentalInterestBody` | `Mutation<RentalInterest>`; verify available exact offer/revision, capacity, desired dates, duration and tenant |
| GET `rental-interests/{id}/` | Interest UUID | `RentalInterest`, including server-derived `source_eligible`, `tenant_id`, `proposal_id`, `invitation_id` |
| POST `rental-interests/{id}/respond/` | `Decision` | `Mutation<RentalInterest>`; reject/other explicitly allowed decisions |
| GET `terms-proposals/` | `workspace`, pagination | `TermsProposal[]` |
| POST `terms-proposals/` | `TermsProposalBody` | `Mutation<TermsProposal>`; source interest and offer revisions, full policy-bound terms |
| GET `terms-proposals/{id}/` | Proposal UUID | `TermsProposal`; immutable current/previous terms and exact offer snapshot |
| PATCH `terms-proposals/{id}/` | `TermsProposalBody` with current target revision | `Mutation<TermsProposal>`; editing invalidates prior approvals |
| POST `terms-proposals/{id}/respond/` | `Decision`: accept/reject/request_changes | `Mutation<TermsProposal>`; both parties act on the same revision |
| GET `tenancy-invitations/` | Existing workspace/property filters | Existing compatible invitation list; extend with scoped actions |
| POST `tenancy-invitations/` | Legacy `CreateTenancyInvitationBody` **or** new `RentalInvitationBody` | Preserve legacy response; use `Mutation<TenancyInvitation>` for interest-sourced body |
| GET `tenancy-invitations/{id}/` | Existing detail route | `TenancyInvitation` with owner/tenant/offer/revision, timestamps and eligibility |
| POST `tenancy-invitations/{id}/respond/` | Existing `{decision,revision,request_key}` | Preserve existing agreed raw invitation response; enforce expiry and current participant |
| POST `tenancy-invitations/{id}/revoke/` | `Decision`: revoke_invitation | `Mutation<TenancyInvitation>`; owner only, before consumption |
| GET `lease-configuration/` | Current actor | `RentalAgreementConfiguration`: approved templates, versions, policy, can_create and permissions |
| GET `leases/` | `workspace`, `period`, `search`, pagination | Extended `DigitalLease[]` for My Rentals; filters all/current/upcoming/ended/pending_settlement |
| POST `leases/` | `RentalAgreementDraftBody` | `Mutation<DigitalLease>`; consume accepted eligible invitation atomically |
| GET `leases/{id}/` | Lease UUID | Extended `DigitalLease`; agreement details, including `legacy_read_only` |
| GET `leases/{id}/rental-center/` | Lease UUID | Fresh participant-scoped `RentalCenter` aggregate; independent states, balances and next actions |
| PATCH `leases/{id}/` | Full draft body with current `expected_revision` | `Mutation<DigitalLease>`; permitted draft edit, same participants/accommodation; invalidate reviews/document signatures |
| POST `leases/{id}/review/` | `Decision`: accept_review/request_changes | `Mutation<DigitalLease>`; review the current exact document/terms revision |
| POST `leases/{id}/submit-for-signature/` | `Decision`: submit_for_signature | `Mutation<DigitalLease>`; readiness, mutual review and inventory hold checks |
| POST `leases/{id}/signing-session/` | `RentalSigningBody` | `Mutation<RentalSigningSession>`; exact document ID/hash, revision, request key and TTL |
| POST `leases/{id}/cancel/` | Existing legacy body or new Decision: cancel_draft | Legacy compatibility or `Mutation<DigitalLease>`; cancel permitted drafts only |
| GET `leases/{id}/timeline/` | `workspace`, pagination | `RentalTimelineEvent[]`; actual immutable events with dates/actors represented by authorized labels |
| GET `leases/{id}/billing-schedule/` | `workspace`, pagination | `BillingPeriod[]`; full server-calculated schedule, issued invoice IDs only when present |

Invitation eligibility: pending/confirmed visits for the same owner, tenant and property, or an eligible interest path. Completed visits remain unsupported until the backend eligibility change is explicitly accepted. Invitation lifetime is seven days, including accepted invitations. Creating a draft consumes an invitation once; cancelling the draft never restores it. Do not silently create a lease by property and tenant alone when an exact room/bed offer is selected.

Owner readiness includes verified identity, listing ownership, beneficiary/KYC, payout readiness and explicit acceptance of the **required** policy versions and complete policy summary. Do not infer acceptance from a previously accepted version. Collect full bank/KYC data through the hosted provider, not mobile fields or logs.

### Invoices and payment

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET `rent-invoices/` | Existing workspace/lease filters, pagination | Extended `RentInvoice[]`; real billing periods and independent balances |
| GET `rent-invoices/{id}/` | Invoice UUID | Extended `RentInvoice`; exact state/revision/balance/allowed_actions/active attempt |
| POST `rent-invoices/{id}/quote/` | `Decision` with current invoice revision and request key | `Mutation<PaymentQuote>`; short-lived SHA-256 fingerprint, payer total and zero tenant service fee |
| POST `rent-invoices/{id}/checkout/` | `RentCheckoutBody`: invoice_id, quote_id, expected_revision, request_key | `Mutation<RentalCheckoutSession>`; one server-recorded attempt before PSP session creation |
| GET `payment-attempts/` | **Required recovery mode:** invoice_id + request_key | `PaymentAttemptLookup`; at most one matching attempt, absence_confirmed, optional active_session |
| GET `payment-attempts/{id}/` | Attempt UUID | `PaymentAttempt`; exact invoice/key/amount, confirmed capture time, receipt, PSP settlement and owner payout states |
| POST `payment-attempts/{id}/reconcile/` | `Decision`: reconcile, current attempt revision and UUID | Direct authoritative `PaymentAttempt`; server-rate-limited PSP reconciliation; never create a charge |

The invoice response exposes `invoice_status`, `balance`, `revision`, `can_pay` and `allowed_actions` containing `quote` and `checkout` when currently permitted. `payment_attempt_id` identifies a live/existing attempt. Without the new quote/permission/revision contract, the app keeps a legacy invoice readable and disables checkout.

Quote DTO (`data.resource`; return the canonical receipt alongside it):

```json
{
  "quote_id":"quote-uuid","invoice_id":"invoice-uuid","invoice_revision":3,
  "payer_amount":{"amount_minor":1000000,"currency":"EGP","exponent":2},
  "tenant_service_fee":{"amount_minor":0,"currency":"EGP","exponent":2},
  "policy_version":"rental-policy-v1","fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "expires_at":"2026-10-09T10:05:00Z"
}
```

The nested Money objects above are the implemented DTO. The illustrative fingerprint is a placeholder, not a calculated quote. Return the actual immutable lowercase SHA-256 fingerprint, `rental-policy-v1` and a five-minute expiry. Quote receipt revision belongs to the quote; `invoice_revision` still pins the invoice.

Checkout DTO (`data.resource`; return the canonical receipt alongside it):

```json
{
  "session_id":"session-uuid","payment_attempt_id":"attempt-uuid",
  "invoice_id":"invoice-uuid","quote_id":"quote-uuid","invoice_revision":3,
  "request_key":"request-uuid","status":"created",
  "amount":{"amount_minor":1000000,"currency":"EGP","exponent":2},
  "checkout_url":"https://approved-psp.example/checkout/opaque-session",
  "expires_at":"2026-10-09T10:15:00Z","operation_receipt_id":"operation-uuid",
  "navigation":{
    "allowed_origins":["https://approved-psp.example","https://approved-3ds.example"],
    "return_url":"https://sokoun.example/payments/return?invoice_id=invoice-uuid",
    "return_state":"unpredictable-attempt-bound-nonce",
    "external_schemes":["approved-bank-app"]
  }
}
```

These domains are documentation placeholders; backend configuration must supply real approved PSP/3DS origins. Allowlist exact HTTPS origins, not suffixes or arbitrary redirects. Return callbacks must echo one `state` and one `payment_attempt_id`, match the exact configured return path/query, and be bound to the authenticated attempt. The mobile app does not treat `success=true` as a financial outcome. Restrict native bank app schemes; omit them when unsupported. Never put card details or reusable PSP credentials in API responses.

Recovery lookup example:

```json
{"invoice_id":"invoice-uuid","request_key":"request-uuid","results":[{"payment_attempt_id":"attempt-uuid","lease_id":"lease-uuid","invoice_id":"invoice-uuid","revision":4,"request_key":"request-uuid","quote_id":"quote-uuid","invoice_revision":3,"policy_version":"rental-policy-v1","quote_fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","payment_status":"pending","invoice_status":"due","amount":{"amount_minor":1000000,"currency":"EGP","exponent":2},"confirmed_at":null,"receipt_id":"","settlement_status":"pending","payout_status":"held"}],"absence_confirmed":false,"active_session":null}
```

Only expose a reusable `active_session` if it is still valid and matches the original invoice, quote, revision, request key and amount. An empty lookup does not unlock a second charge. `absence_confirmed=true` requires a permanent tombstone; generic `absent_final` is not currently accepted by the client. Captured success requires an authoritative `payment_status=captured` plus `confirmed_at`. Authorization, capture, PSP settlement and owner payout remain four separate facts. Receipt production may lag a confirmed capture; expose its pending state without inventing a receipt URL.

### Stay operations, change agreements and final closure

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET/POST `leases/{id}/handovers/` | workspace + pagination / `HandoverBody` | `RentalHandover[]` / `Mutation<RentalHandover>`; move_in or move_out |
| GET/PATCH `handovers/{id}/` | UUID / complete HandoverBody at current revision | `RentalHandover` / `Mutation<RentalHandover>`; edit invalidates approvals |
| POST `handovers/{id}/respond/` | Decision: accept/dispute | `Mutation<RentalHandover>`; mutual acceptance on exact condition, keys, meters, inventory and evidence |
| POST `rental-attachments/` | Multipart lease_id, file, mime_type, sha256, request_key | Canonical resource + operation receipt; `RentalEvidence` metadata only |
| GET `rental-attachments/{id}/` | Attachment UUID | Fresh participant-authorized `RentalEvidence` metadata, immutable digest and revision; needed to reconcile an unknown upload |
| GET `rental-attachments/{id}/download/` | Attachment UUID | `RentalEvidenceLink`: id, subject_id=lease UUID, URL, expires_at; participant authorization |
| GET `leases/{id}/deposit/` | Lease UUID | `RentalDeposit`; agreed/due/collected/returned/applied/disputed/remaining balances and separate `invoice_type=deposit` invoice ID |
| GET/POST `leases/{id}/maintenance-requests/` | workspace + pagination / `MaintenanceBody` | List / `Mutation<MaintenanceRequest>`; category, priority, access preferences and evidence |
| GET `maintenance-requests/{id}/` | Request UUID | `MaintenanceRequest`; events, appointment, proposed cost and payer |
| POST `maintenance-requests/{id}/actions/` | `MaintenanceActionBody` | `Mutation<MaintenanceRequest>`; explicitly allowed response/work/cost actions |
| GET/POST `leases/{id}/payment-extension-requests/` | workspace + pagination / `RentalChangeBody` with invoice_id | List / `Mutation<RentalChange>`; original due date remains immutable |
| GET/POST `leases/{id}/amendments/` | workspace + pagination / RentalChangeBody | List / Mutation; effective date and full proposed terms |
| GET/POST `leases/{id}/renewals/` | workspace + pagination / RentalChangeBody | List / Mutation; same tenancy root, no repeated commission or automatic renewal |
| GET/POST `leases/{id}/termination-requests/` | workspace + pagination / RentalChangeBody | List / Mutation; reason and proposed exit date |
| POST `rent-invoices/{id}/external-payment-claims/` | RentalChangeBody with invoice_id, amount, method, evidence | Mutation; a claim is not a PSP capture or an automatic invoice adjustment |
| GET `leases/{id}/external-payment-claims/` | workspace + pagination | Related claim list for rental history |
| GET `payment-extension-requests/{id}/`, `amendments/{id}/`, `renewals/{id}/`, `termination-requests/{id}/`, `external-payment-claims/{id}/` | Change UUID | RentalChange; kind, previous/current terms, dates, permissions |
| POST each change detail's `respond/` | Decision: accept/reject/request_changes; propose_end includes effective_on | Mutation; exact reviewed version and role |
| POST `amendments/{id}/submit-for-signature/`, `renewals/{id}/submit-for-signature/` | Decision: submit_for_signature | Mutation<RentalChange>; freeze document version and validate both reviews |
| POST `amendments/{id}/signing-session/`, `renewals/{id}/signing-session/` | RentalSigningBody | Mutation<RentalSigningSession>; pins change ID, revision, document ID/hash |
| GET `leases/{id}/final-settlement/` | Lease UUID | FinalSettlement; server totals, item IDs/evidence, acceptance/dispute status |
| POST `leases/{id}/final-settlement/propose/` | SettlementBody | Mutation<FinalSettlement>; only permitted lines, validated evidence, server recomputes balances |
| POST `leases/{id}/final-settlement/respond/` | Decision: accept/dispute, optional disputed item_ids | Mutation<FinalSettlement>; neither acceptance nor submission directly returns money |
| GET/POST `refund-requests/` | workspace/lease filters + pagination / RefundBody | List / Mutation<RentalRefund>; request only, operations controls PSP execution |
| GET `refund-requests/{id}/` | Refund UUID | RentalRefund; requested amount, actual refundable balance, provider tracking state |
| POST `refund-requests/{id}/respond/` | Decision if explicitly allowed | Mutation; do not grant ordinary users financial execution/operations approval |
| GET/POST `disputes/` | workspace/lease filters + pagination / DisputeBody | List / Mutation<RentalDispute>; subject identity, reason and authorized evidence |
| GET `disputes/{id}/` | Dispute UUID | RentalDispute; responses and operations resolution |
| POST `disputes/{id}/respond/` | Decision: reply, note | Mutation<RentalDispute>; append-only party reply |
| GET `leases/{id}/documents/` | Pagination | RentalDocument[]; metadata/status only, including contracts, signed changes, receipts and statements |
| GET `rental-documents/{id}/download/` | Document UUID | PrivateDocumentLink: id, subject_id=lease UUID, URL and TTL |
| POST `rental-statements/` | RentalStatementBody: lease_id, starts_on, ends_on_exclusive, target revision/key | Mutation<RentalDocument>; queued statement resource with revision, type=statement and generation status |
| GET/POST `leases/{id}/reviews/` | Pagination / RentalReviewBody | List / Mutation<RentalReview>; one actual tenancy review per permitted author, rating 1..5 |

Maintenance actions currently exposed: `acknowledge`, `reply`, `propose_appointment`, `accept_appointment`, `start_work`, `report_resolved`, `confirm_resolved`, `reopen`, `cancel`, `propose_cost`, `approve_cost`, `reject_cost`. Cost payer is `owner` or `tenant`; unexpected responsibility values are invalid. A proposed cost must not create a charge until the responsible party approves the exact version and amount. Emergency reporting includes contextual support, not a promise of emergency service.

Attachments: V1 UI accepts up to five PNG images, each at most 5 MiB after normalization. The client re-encodes photos to remove metadata and deletes its temporary file after upload. Backend must still verify actual MIME/magic bytes, size, digest, participant/lease ownership, malware status, retention and download permissions. Scanning transitions `pending` to `ready` or `unsafe`; only ready evidence may be attached or downloaded. A parent draft stores approved attachment **metadata/IDs**, never bytes, raw paths or download URLs. Before transmission, the client protects an intent containing `lease_id`, `request_key` and `sha256`. After a confirmed pending response, it also protects the returned `resource_id` and `minimum_revision`; future checks read that ID without another upload. Unknown uploads use scoped operation lookup and then authorized metadata. A wrong digest/lease, regressed revision, unknown status or missing operation never unlocks a new transmission. Durable completion of a ready/unsafe scan clears its upload record; unsafe media never enters a parent form. Generic permanent tombstones are unsupported. Never require the client to retransmit an unknown file to discover its result. Revalidate restored IDs before attachment use. Physical-device camera/gallery permission and upload recovery remain integration checks.

### Owner finance and contextual support

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET `owner-payables/` | workspace=owner, optional lease_id, pagination | OwnerPayable[]: gross, commission, processing_fee, net, settlement/payout states and blocking reasons |
| GET `payouts/` | workspace, optional lease_id, pagination | RentalPayout[]; authorized owner view only |
| GET `payouts/{id}/` | Payout UUID | RentalPayout; actual tracking state, masked beneficiary, payable IDs and failure/hold reason |

The mobile client has no endpoint to force payout execution. It never infers owner payout success from a paid invoice. Extend the existing support ticket body with optional `rental_context` containing `lease_id`, `invoice_id`, `payment_attempt_id`, `subject_kind`, `subject_id`. It is context for support routing, not financial permission; validate every supplied ID. Existing tickets without this field remain compatible. Lease responses may supply `chat_thread_id` for the existing authorized chat thread; do not create another messaging transport.

A payment-attempt detail must also include the original `quote_id`, `invoice_revision`, `policy_version` and `quote_fingerprint`. This binds recovery on another app session or device to the same intention. For an unfinished attempt, its lookup may include the existing unexpired `active_session`; return the same attempt/key and authorized checkout session, never create a second charge during a GET. If no active session can safely be resumed, keep status checking and support available.

### Complete structured agreement example

POST `features/v1/leases/` (owner, accepted current invitation):

<!-- contract: structured-draft-request -->
```json
{
  "invitation_id": "invitation-example",
  "invitation_revision": 2,
  "property_id": "property-example",
  "offer_id": "offer-example",
  "offer_revision": 7,
  "tenant_id": "tenant-example",
  "terms": {
    "starts_on": "2027-01-31",
    "ends_on_exclusive": "2028-01-31",
    "handover_on": "2027-01-31",
    "monthly_rent": {
      "amount_minor": 1000000,
      "currency": "EGP",
      "exponent": 2
    },
    "deposit": {
      "amount_minor": 1000000,
      "currency": "EGP",
      "exponent": 2
    },
    "deposit_holder": "platform",
    "included_services": [],
    "excluded_services": [],
    "termination_policy": "notice-v1",
    "renewal_policy": "mutual-v1",
    "policy_version": "rental-policy-v1",
    "template_id": "eg-residential-v1",
    "template_version": "1",
    "timezone": "Africa/Cairo",
    "occupants": 1,
    "billing_anchor_day": 31,
    "commission_rate_bps": 1000,
    "commission_payer": "owner",
    "commission_basis": "first_period_base_rent",
    "processing_fee_payer": "platform",
    "renewal_commission_rate_bps": 0
  },
  "request_key": "161f3a2b-b1ee-4f73-8994-20e4abf35744",
  "expected_revision": 0
}
```

Canonical response, owner projection:

<!-- contract: structured-draft-response -->
```json
{
  "key": "success",
  "msg": "",
  "data": {
    "resource": {
      "id": "lease-example",
      "revision": 1,
      "owner_id": "owner-example",
      "tenant_id": "tenant-example",
      "invitation_id": "invitation-example",
      "property_id": "property-example",
      "property_title": "Example shared apartment",
      "owner_name": "Owner",
      "tenant_name": "Tenant",
      "status": "draft",
      "lease_status": "draft",
      "legacy_read_only": false,
      "can_sign": false,
      "can_cancel": false,
      "terms": {
        "starts_on": "2027-01-31",
        "ends_on_exclusive": "2028-01-31",
        "handover_on": "2027-01-31",
        "monthly_rent": {
          "amount_minor": 1000000,
          "currency": "EGP",
          "exponent": 2
        },
        "deposit": {
          "amount_minor": 1000000,
          "currency": "EGP",
          "exponent": 2
        },
        "deposit_holder": "platform",
        "included_services": [],
        "excluded_services": [],
        "termination_policy": "notice-v1",
        "renewal_policy": "mutual-v1",
        "policy_version": "rental-policy-v1",
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "timezone": "Africa/Cairo",
        "occupants": 1,
        "billing_anchor_day": 31,
        "commission_rate_bps": 1000,
        "commission_payer": "owner",
        "commission_basis": "first_period_base_rent",
        "processing_fee_payer": "platform",
        "renewal_commission_rate_bps": 0
      },
      "offer_snapshot": {
        "property_id": "property-example",
        "offer_id": "offer-example",
        "offer_revision": 7,
        "rental_scope": "bed",
        "name": "Bed A1",
        "room_ids": [
          "room-a"
        ],
        "room_names": [
          "Room A"
        ],
        "bed_id": "bed-a1",
        "bed_name": "Bed A1",
        "terms": {
          "price": "10000",
          "price_period": "monthly",
          "rental_period": 3,
          "deposit": "one_month",
          "suitable_for": "students",
          "description": "Shared accommodation close to campus.",
          "smoking_allowed": false,
          "rules": [
            "Keep shared spaces clean"
          ]
        },
        "availability": "available",
        "archived": false,
        "capacity": 2,
        "bathroom_access": [
          "shared"
        ],
        "offer_link": "https://sokoun.app/properties/property-example/offers/offer-example"
      },
      "reviewed_by": [],
      "allowed_actions": [
        "edit_lease",
        "cancel_draft"
      ],
      "blocking_reasons": []
    },
    "operation_receipt": {
      "id": "operation-example",
      "subject_id": "lease-example",
      "request_key": "161f3a2b-b1ee-4f73-8994-20e4abf35744",
      "revision": 1,
      "status": "confirmed"
    }
  }
}
```

The create response must match the authenticated owner, tenant, invitation, property, accepted invitation snapshot and submitted terms, with `status=draft` and `legacy_read_only=false`. A server 200 with mismatched facts remains unresolved in the client. Do not “fix” this by echoing unvalidated request data; derive the response from saved authorized rows.

For edits, preserve participants/accommodation and use current target revision. A terms change invalidates prior reviews/signatures and generates a new document version. Return real `document_id`/`document_hash` only when the artifact exists. Terms policy currently expects owner-funded commission 1000 basis points once on first-period base rent, platform processing fees, renewal commission 0; taxes/refund treatment require an approved policy rather than invented defaults.

### Payment and hosted-session contract cautions

Quote request is a `Decision` with `decision=quote`, current invoice revision and a stable quote-operation key. Checkout request is **only** `invoice_id`, `quote_id`, `expected_revision`, `request_key`; client sends no amount or card details. The returned quote/checkout must match the invoice, quote, key, amount, fingerprint and expiry. Quote and checkout are separate intentions and keys.

<!-- contract: checkout-request -->
```json
{"invoice_id":"invoice-example","quote_id":"quote-example","expected_revision":3,"request_key":"d0a0f1d2-4053-4c67-945a-499b9cae2267"}
```

`GET payment-attempts/?invoice_id=...&request_key=...` is a lookup envelope with `results` (zero or one exact attempt), `absence_confirmed` and optional `active_session`, not an ordinary broad payment history page. Return `absence_confirmed=false` for unresolved absence. Only set true when the original operation is permanently prevented from committing. Reject contradictory true + nonempty results. Reconcile is a direct `PaymentAttempt` response and must never create a charge. Capture requires `payment_status=captured` and authoritative `confirmed_at`; receipt generation, PSP settlement and payout may still be pending.

Hosted checkout navigation contains exact HTTPS `allowed_origins`, `return_url`, unpredictable attempt-bound `return_state` and approved `external_schemes`. Examples using `.example` hosts are placeholders, never a production allowlist. Bind return state/attempt, verify provider signatures on the backend, and use fresh resource readback; URL success text is not financial confirmation. Signing likewise pins document ID/hash/revision with a private expiring session.

## 7. C08/C09/S02/C06 — planning contracts

Planning endpoints require fresh build + server capability + verified service + action grants. They are not proven deployed by this document. All paths below start `features/v1/`. Unless stated otherwise, POST writes return `Mutation<T>` and GET detail returns direct `T`; lists use §2 pagination.

### 7.1 Lifestyle, roommates and groups

| Method / route | Request body / response |
| --- | --- |
| GET/POST `lifestyle-profile/` | Read `LifestyleProfile`; save `discoverable`, `habits`, `preferences`, `disclosed`, `expected_revision`, `request_key`; no input `id` or `revision` |
| GET `roommate-candidates/`, `roommate-connections/` | Paged `RoommateRecord` |
| POST `roommate-candidates/{id}/{decision}/` | `decision`, `note`, `candidate_revision`, `expected_revision=0`, `request_key`; candidate operation can create a different relationship resource |
| POST `roommate-connections/{id}/{decision}/` | `decision`, `note`, current `expected_revision`, `request_key`; permitted actor only |
| GET/POST `housing-groups/`; GET `housing-groups/{id}/` | Group list/create/detail; create uses `GroupActionBody(action=create)` |
| POST `housing-groups/{id}/{action}/` | `GroupActionBody`, returning updated **HousingGroup** and receipt for group ID/revision |
| POST `housing-groups/{id}/invitations/` | `group_id`, `group_revision`, `expected_revision=0`, `request_key`; returns new `GroupInvite` receipt |
| GET `group-invitations/{id}/` | Admin-authorized `GroupInvite` |
| POST `group-invitations/preview/` | `{token}`; read-only direct `GroupInvite`, no receipt, no token consumption |
| POST `group-invitations/join/` | `token`, `group_id`, `group_revision`, `expected_revision=group_revision`, `request_key`; updated group + receipt |

Roommate decisions must be taken from current actions/UI (`request`, `accept`, `decline`, `withdraw`, `block` as applicable); `candidate` and connection IDs are distinct. `RoommateRecord` fields: `id`, `user_id`, `display_name`, `status`, `revision`, `reasons`, `disclosures`, `chat_granted`, `allowed_actions`, `blocking_reasons`. Match reasons/disclosures must not leak undisclosed profile answers. Lifestyle answer tokens come from [the actual enums/models](../../apps/sokoun_app/lib/features/tenant/roommates/data/); do not translate enum values.

`GroupActionBody` always sends `expected_revision`, `request_key`, `roster_revision`, `action`, `consent`. Create/edit additionally sends `name`, `visibility`, `capacity`, `criteria` (write schema). Nonempty `member_id`, `item_id` + `item_revision`, `note`, `appointment_at` are conditional. `selection` and `proposal` are sent when supplied. `request_visit`/`apply` send `participant_ids` from the current active roster. Do not use their presence as everyone else's consent.

Group actions: `edit`, `transfer_admin`, `remove_member`, `leave`, `archive`, `revoke_invites`, `add_shortlist`, `remove_shortlist`, `vote`, `comment`, `propose_costs`, `approve_costs`; `request_visit`, `consent_visit`, `withdraw_visit_consent` require `group_visits`; `apply`, `consent_application`, `withdraw_application_consent` require `group_applications`.

Group response: `id,name,status,visibility,revision,roster_revision,capacity,criteria,members,shortlist,proposals,visits,applications,allowed_actions,blocking_reasons`. Member: `user_id,name,role,status`. Proposal request: `id,revision,roster_revision,offer_id,offer_revision,start_on,end_on,period,total,contributions`; contributions map user IDs to integer minor amounts; `approved_by` is response-only. Process response: `id,revision,roster_revision,status,selection,participant_ids,consented_ids,appointment_at,qualifying_visit_id,allowed_actions`. All consent is versioned and actor-owned.

GroupInvite returns `id,group_id,group_name,status,link,revision,group_revision,member_count,capacity,expires_at`. Private join link format is `https://sokoun.app/housing-groups/join#<base64url-token>`; do not log/store raw tokens in analytics. Preview and join bodies remain private. Sources: [group data and models](../../apps/sokoun_app/lib/features/shared/housing_groups/data/).

### 7.2 Housing requests and owner responses

| Method / route | Input | Resource |
| --- | --- | --- |
| GET `housing-requests/`; GET `housing-demand/` | Tenant own list / eligible owner feed, paging | `HousingRequest[]` |
| GET `housing-requests/{id}/` | Authorized actor | `HousingRequest` |
| POST `housing-requests/` | `HousingRequestBody(action=publish)` | New `HousingRequest` |
| POST `housing-requests/{id}/{action}/` | Same full body, current revision; `edit`, `pause`, `publish`, `close`, `fulfill` | Updated request |
| GET/POST `housing-requests/{id}/offers/` | Page / `HousingOfferBody` | Scoped offer list / new offer |
| POST `housing-offers/{id}/{decision}/` | `Decision`: `shortlist`, `decline`, `withdraw` | Updated offer |

Criteria **write** fields: `city_id`, `district_ids` (currently empty list), `rental_scope`, `property_type`, `budget_min`, `budget_max`, `price_period`, `start_on`, `end_on` nullable, `people`, `amenities`, `furnished` bool/null. Criteria **read** fields: `city` object, `filters` as `PropertySearchFilters`, `start_on`, `end_on`, `people`, `area_note`. Echoing the write shape as the read shape loses the client's editable city/filter state. `area_note` currently is not sent by `toRequest`; do not claim it is applied as a district filter.

<!-- contract: housing-request-create -->
```json
{
  "expected_revision": 0,
  "request_key": "04c372ed-f263-4dd2-83a8-1a4fa03b974e",
  "action": "publish",
  "title": "Bed close to campus",
  "note": "Move-in at the end of January.",
  "criteria": {
    "city_id": "city-example",
    "district_ids": [],
    "rental_scope": "bed",
    "property_type": "apartment",
    "budget_min": {
      "amount_minor": 500000,
      "currency": "EGP",
      "exponent": 2
    },
    "budget_max": {
      "amount_minor": 1200000,
      "currency": "EGP",
      "exponent": 2
    },
    "price_period": "monthly",
    "start_on": "2027-01-31",
    "end_on": null,
    "people": 1,
    "amenities": [],
    "furnished": true
  },
  "visibility": "eligible_owners"
}
```

Response reconstructs the read criteria (catalog values here are synthetic):

<!-- contract: housing-request-response -->
```json
{
  "key": "success",
  "msg": "",
  "data": {
    "resource": {
      "id": "request-example",
      "user_id": "tenant-example",
      "title": "Bed close to campus",
      "note": "Move-in at the end of January.",
      "status": "published",
      "revision": 1,
      "criteria": {
        "city": {
          "id": "city-example",
          "name": "Example City",
          "slug": "example-city"
        },
        "filters": {
          "search": "",
          "city": "city-example",
          "district": "",
          "ordering": "-created_at",
          "page": 1,
          "page_size": 20,
          "price_min": "5000",
          "price_max": "12000",
          "rental_scope": "bed",
          "property_type": "apartment",
          "price_period": "monthly",
          "suitable_for": "",
          "is_furnished": "true",
          "is_verified": "",
          "smoking_allowed": "",
          "bedrooms": "",
          "bathrooms": "",
          "amenities": []
        },
        "start_on": "2027-01-31",
        "end_on": "",
        "people": 1,
        "area_note": ""
      },
      "expires_at": "2027-02-01T00:00:00Z",
      "allowed_actions": [
        "edit",
        "pause",
        "close"
      ],
      "blocking_reasons": []
    },
    "operation_receipt": {
      "id": "operation-request",
      "subject_id": "request-example",
      "request_key": "04c372ed-f263-4dd2-83a8-1a4fa03b974e",
      "revision": 1,
      "status": "confirmed"
    }
  }
}
```

Owner offer POST body:

<!-- contract: housing-offer-request -->
```json
{
  "expected_revision": 0,
  "request_key": "78f8e5bc-2d9a-4a58-b317-d6f152de5b60",
  "request_id": "request-example",
  "request_revision": 1,
  "selection": {
    "property_id": "property-example",
    "offer_id": "offer-example",
    "offer_revision": 7,
    "rental_scope": "bed",
    "name": "Bed A1",
    "room_ids": [
      "room-a"
    ],
    "room_names": [
      "Room A"
    ],
    "bed_id": "bed-a1",
    "bed_name": "Bed A1",
    "terms": {
      "price": "10000",
      "price_period": "monthly",
      "rental_period": 3,
      "deposit": "one_month",
      "suitable_for": "students",
      "description": "Shared accommodation close to campus.",
      "smoking_allowed": false,
      "rules": [
        "Keep shared spaces clean"
      ]
    },
    "availability": "available",
    "archived": false,
    "capacity": 2,
    "bathroom_access": [
      "shared"
    ],
    "offer_link": "https://sokoun.app/properties/property-example/offers/offer-example"
  },
  "note": "This is the exact bed available for review."
}
```

Tenant detail/list item projection of the new offer (the immediate owner POST response must instead return owner actions such as `withdraw`):

<!-- contract: housing-offer-resource -->
```json
{
  "id": "response-example",
  "request_id": "request-example",
  "owner_user_id": "owner-example",
  "status": "sent",
  "note": "This is the exact bed available for review.",
  "revision": 1,
  "request_revision": 1,
  "selection": {
    "property_id": "property-example",
    "offer_id": "offer-example",
    "offer_revision": 7,
    "rental_scope": "bed",
    "name": "Bed A1",
    "room_ids": [
      "room-a"
    ],
    "room_names": [
      "Room A"
    ],
    "bed_id": "bed-a1",
    "bed_name": "Bed A1",
    "terms": {
      "price": "10000",
      "price_period": "monthly",
      "rental_period": 3,
      "deposit": "one_month",
      "suitable_for": "students",
      "description": "Shared accommodation close to campus.",
      "smoking_allowed": false,
      "rules": [
        "Keep shared spaces clean"
      ]
    },
    "availability": "available",
    "archived": false,
    "capacity": 2,
    "bathroom_access": [
      "shared"
    ],
    "offer_link": "https://sokoun.app/properties/property-example/offers/offer-example"
  },
  "rent": {
    "amount_minor": 1000000,
    "currency": "EGP",
    "exponent": 2
  },
  "deposit": {
    "amount_minor": 1000000,
    "currency": "EGP",
    "exponent": 2
  },
  "price_period": "monthly",
  "allowed_actions": [
    "shortlist",
    "decline"
  ],
  "blocking_reasons": []
}
```

`HousingRequest` returns `id,user_id,title,note,status,revision,criteria,expires_at,allowed_actions,blocking_reasons`. Known statuses: `draft,published,paused,closed,fulfilled,expired`.

`HousingOfferBody` sends `expected_revision=0`, `request_key`, `request_id`, `request_revision`, complete `selection`, `note`. Return `id,request_id,owner_user_id,status,note,revision,request_revision,selection,rent,deposit,price_period,allowed_actions,blocking_reasons`. `rent` and `deposit` are Money. Known statuses: `sent,viewed,shortlisted,declined,withdrawn,expired`. Every returned offer must belong to the parent request; this is now validated before the page is displayed. Two to three **offers** may be compared, including different offers on one property.

### 7.3 Commute, assistant and alerts

| Method / route | Request | Response |
| --- | --- | --- |
| POST `commute-searches/` | `destinations` 1..2, `local_time`, `time_kind=depart_at|arrive_by`, `timezone`, `balance`, `hard_limits=true`, `filters`, key/rev0 | `Mutation<CommuteSearch>` |
| GET `commute-searches/{id}/` | Own opaque search ID | `CommuteSearch` |
| GET `commute-searches/{id}/results/` | Paging; no private coordinates in query | `CommuteMatch[]` |
| POST `tenant-assistant/turns/` | `text`, `session_id`, `language`, `previous_turn_id` null when empty, `retain_history=false`, key/rev0 | `Mutation<TenantAssistantReply>` |
| GET `configuration/` | `workspace=tenant`, `lang` | Supported alert cadences/configuration |
| GET/POST `search-alerts/`; GET `search-alerts/{id}/` | Create `name,cadence,filters,request_key`; read own alerts | Legacy direct alert / paginated alerts |
| PATCH `search-alerts/{id}/` | `enabled,revision,request_key` | Direct updated alert |
| DELETE `search-alerts/{id}/` | JSON `revision,request_key` | Cancellation receipt under existing alert contract |

Destination has `label`, `location` using existing PropertyLocation JSON, `mode=driving|walking|transit|cycling`, `limit_minutes`. CommuteSearch: `id,revision,coverage,provider,resolved_at,expires_at,unknown_count`. CommuteMatch: `property_id,title,offer_ids,estimates`; estimate: `destination_label,duration_seconds` nullable, `limit_seconds,status,explanation`. Only `status=ok` and a nonnegative known duration prove a route. Provider timeout/uncovered route is not zero minutes. Apply hard limits and sorting to the full declared catalog before pagination.

Assistant reply: `id,revision,text,filters,unresolved_requirements,grounded_property_ids,actions,costs`. Action kinds: `search,requestDraft,commute,group,property,compare,messageDraft,visitReview`; fields include `title,property_id,offer_id,property_ids`. References must be authorized grounded IDs; unsupported filters belong in unresolved requirements. Cost fields: `label,kind=recurring|deposit|one_time,period,money`. The user reviews every action; do not return executable API paths. Local saved search has no server create endpoint and does not establish alert delivery.

Sources: [commute models](../../apps/sokoun_app/lib/features/tenant/commute/data/models/), [assistant models](../../apps/sokoun_app/lib/features/tenant/ai_assistant/data/models/), [alert body](../../apps/sokoun_app/lib/features/tenant/premium_alerts/data/models/premium_alert_body.dart).

### 7.4 Condition reports, move-out notices and replacement

| Method / route | Body / response |
| --- | --- |
| GET `leases/{lease_id}/condition-report-context/` | Direct unsaved ConditionReport template: empty ID, actual lease selection, stable items, permitted baseline; action `create` |
| GET/POST `leases/{lease_id}/condition-reports/` | Scoped list / `ConditionReportBody` → new report + receipt |
| GET `condition-reports/{id}/` | Authorized report |
| POST `condition-reports/{id}/{action}/` | Full `ConditionReportBody`; `submit`, `acknowledge`, `object`, `finalize` |
| GET/POST `leases/{lease_id}/move-out-notices/` | Scoped list / `TransitionBody(kind=moveOutNotice,action=submit)` |
| GET `move-out-notices/{id}/`; POST `move-out-notices/{id}/{action}/` | Read / `acknowledge`, `withdraw` using TransitionBody |
| GET/POST `leases/{lease_id}/replacement-requests/` | Scoped list / `TransitionBody(kind=replacement,action=submit)` |
| GET `replacement-requests/{id}/`; POST `replacement-requests/{id}/{action}/` | Read / `nominate`, `approve_availability`, `approve_candidate`, `withdraw`, `decline`, `cancel` as allowed |
| GET `leases/{lease_id}/replacement-candidates/` | Authorized candidates: `id,display_name,source,revision,consented` |

`ConditionReportBody` always emits `request_key,expected_revision,lease_id,action,kind,inspected_on,selection,items,evidence_ids,baseline_id,baseline_revision`; `baseline_id=null` if absent; `objection` only when nonempty. Kind is `move_in|move_out`. Item: `id,space,label,kind,condition,note,reading,unit,quantity,evidence_ids`; kind `surface|inventory|meter|key`, condition `notInspected|unknown|good|worn|damaged|missing`. Reading is decimal string/null, quantity integer/null. Evidence IDs refer to confirmed private uploads of that lease.

Response adds `id,status,revision,evidence,acknowledgements,baseline_items,history,allowed_actions,blocking_reasons`. Acknowledgment: `user_id,name,status,revision,note`. Known report statuses: `draft,submitted,changes_requested,acknowledged,final,superseded`. Report finalization does not accept handover or charge damage. These routes deliberately do not reuse `handovers/{id}/respond/`.

<!-- contract: move-out-request -->
```json
{"lease_id":"lease-example","kind":"moveOutNotice","action":"submit","request_key":"4bbd8cef-a3f1-4940-9d3e-9952a866ef59","expected_revision":0,"requested_on":"2027-07-31","reason":"Moving after the agreed notice period."}
```

<!-- contract: move-out-response -->
```json
{"key":"success","msg":"Notice received.","data":{"resource":{"id":"notice-example","lease_id":"lease-example","kind":"moveOutNotice","status":"submitted","revision":1,"requested_on":"2027-07-31","received_at":"2027-06-30T12:00:00Z","effective_on":"","reason":"Moving after the agreed notice period.","candidate_id":"","candidate_revision":0,"outgoing_release_status":"","incoming_agreement_status":"","future_availability_status":"","history":[],"allowed_actions":["withdraw"],"blocking_reasons":[]},"operation_receipt":{"id":"operation-notice","subject_id":"notice-example","request_key":"4bbd8cef-a3f1-4940-9d3e-9952a866ef59","revision":1,"status":"confirmed"}}}
```

`TransitionBody` emits the same fields for replacement, plus `candidate_id,candidate_revision` only when candidate ID is nonempty. Response fields are illustrated above. `received_at` is not `effective_on`; empty effective date is intentional until policy makes it effective. Known transition statuses: `draft,submitted,received,acknowledged,review_required,approved,candidate_pending,candidate_consented,signatures_pending,activation_pending,effective,withdrawn,declined,cancelled,expired`. Unknown kinds lose actions; never emit a new kind as if the app understands it.

Sources: [ConditionReport and body](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report.dart), [transition and body](../../apps/sokoun_app/lib/features/shared/rental_changes/data/models/tenancy_transition.dart), [planning handoff](../sokoun_new_features_backend_handoff.md).

## 8. C07 — banner contract

All paths below start `advertising/v1/`. Preserve the existing [banner backend handoff](../../MOBILE_OWNER_BANNER_ADS_API_HANDOFF.md) and [current banner data/models](../../apps/sokoun_app/lib/features/shared/banner_ads/data/).

| Method / path | Request | Response / access |
| --- | --- | --- |
| GET `plans/` | Locale | Public `results` with id/title/duration_unit/duration_count/revision/active/price Money |
| POST `owner-advertisements/` | Multipart fields below | Owner ad, server quote/status and durable original artwork reference |
| GET `owner-advertisements/`; GET `owner-advertisements/{id}/` | Own paging / ID | Actor-scoped ad list/detail |
| POST `owner-advertisements/{id}/mock-payment/` | Existing mock-payment body below | Same ad's activation and simulation receipt |
| GET `operations/{operation_id}/` | Original operation ID | Authoritative create/activation recovery, same advertisement |
| GET `placements/tenant-home/` | Locale | Public eligible active carousel, maximum 20 |
| GET `media/{advertisement_id}/` | Owner auth while pending | Original bytes; public only while active/eligible according to policy |

Create multipart fields: `operation_id` (stable ID, max128), `plan_id`, `plan_revision`, `title`, `description`, **`banner` bytes** (JPEG/PNG/WebP); optional `property_id`, optional `offer_id` requiring property. Do not submit a local path or base64 string as a replacement for the multipart file. Backend validates owned target and saved bytes before activation. Plans/revision/price/duration must come from GET, not these docs' historical seed values.

<!-- contract: banner-mock-request -->
```json
{
  "operation_id": "banner-example-payment",
  "payment_mode": "mock"
}
```

Activation response must retain the same advertisement ID and include `status=active`, server `starts_at`/`ends_at`, and `payment` with `id,advertisement_id,operation_id,payment_mode=mock,status=mock_succeeded`. Repeat activation returns the same dates/payment even after natural expiry. Week duration is elapsed time; calendar month/year use the agreed Cairo calendar/clamping/DST policy from the banner handoff.

Keep the original ad/operation on media failure or timeout. Historical pending media 404 is a blocker for the existing operation, not a reason to create a second ad. Return stable error codes, localized `message`, correct `Content-Language` and safe cache headers. Banner mock activation must remain distinct from rental payment capture and from provider sandbox/live evidence.

## 9. Errors, replay and client reaction

Return the documented HTTP status plus a readable localized message and machine-readable field/domain codes. Exact deployed error code names must be listed in the backend return; names below express required semantics rather than falsely claiming every server already emits them.

| Situation | Required HTTP/result semantics | Client/retest behavior |
| --- | --- | --- |
| Invalid field/type/catalog/date/MIME | 400 or the explicitly agreed 422; field errors | Preserve input; correct fields; changed intention uses a new key only after prior outcome is resolved |
| Missing/expired authentication | 401 under actual auth contract | Refresh/login through existing transport; no silent actor substitution |
| Authenticated but forbidden | 403, or documented non-disclosing 404 for private existence | No mutation; disable invalid action after fresh resource read |
| Missing resource | 404 | Not a successful empty resource and not proof an unknown operation never committed |
| Stale revision/source/offer/slot | 409 with domain code/current authorized context | Refresh and ask user to review changed facts; never silently resubmit new terms |
| Same key, different semantic payload | 409 idempotency conflict | Keep original operation; do not overwrite its payload |
| Expired invitation/session/token | Document 409/410 contract | New reviewed source/session only after original operation reconciled |
| Rate limit | 429 with `Retry-After` where supported | Preserve draft/key; bounded retry, no charge duplication |
| Service/provider unavailable | 503 or documented domain failure; capability unavailable | Read/reconcile existing work remains available as authorized |
| Timeout/connection lost/5xx after write | Outcome unknown until reconciled | Same identity lookup; do not show success or create replacement mutation |
| Malformed/mismatched 2xx resource/receipt | Contract failure, possibly committed | Preserve operation and investigate/reconcile; never infer rejection from parse failure |

Example **proposed** normalized error (backend must confirm its exact codes and exception adapter; do not emit a success envelope for this):

<!-- contract: revision-error -->
```json
{"key":"error","message":"This record changed. Refresh it before trying again.","code":"revision_conflict","errors":{"expected_revision":["stale_revision"]},"data":null}
```

Server replay must check a saved key/body match before ordinary stale-revision checks, return the same committed resource/receipt identity and avoid repeating outbox/ledger effects. Some reads may now reflect newer revisions; recovery must still prove the original operation. State which response is the immutable replay snapshot and which is current detail. Legacy draft cancellation's historical same-key replay is a required regression.

## 10. Contract conformance checklist for each endpoint

For every row in this file, backend must provide: implemented method/path; auth and object scope; schema with required/optional/nullable fields; enums; content type; normal/error statuses; request and response example; idempotency namespace/replay policy; target and source revisions; mutation side effects; counterpart read endpoint; worker/provider dependencies; deployed evidence.

Schema acceptance tests must compare the **actual Dart serialization**, not manually renamed equivalents. Required traps to test:

1. `revision` vs `expected_revision`; `expected_offer_revision` vs `offer_revision`; `terms_proposal_id` spelling; `ends_on_exclusive` vs legacy `end_date`.
2. Direct legacy `data` vs canonical `data.resource`; root-level `allowed_actions`; invitation `actions.can_respond`; artifact receipt revision vs invoice revision.
3. Accounting minor units vs listing decimal strings; unknown amounts vs zero; deposit vs recurring rent; price period compatibility.
4. Housing criteria write vs read; omission vs null; participant ID vs resource ID; typed body fields always emitted even for a decision-only action.
5. Same-key retries, pending lookup, malformed success, scope-mixed lists, account changes, unknown enum values and stale provider callbacks.
6. Owner and tenant views after every transition, plus a stranger/unverified actor. No private document/media/token exposure through collections, deep links or operation lookups.

Publish a versioned OpenAPI document (or equivalent exact schema) for the implemented deployment. Include multipart schemas and error responses, not just successful JSON. If current deployment differs, put each difference in the deviation table before changing mobile calls. Do not fill missing evidence with hypothetical payloads.

## 11. Local verification record

The examples marked `contract:` are synthetic fixtures. Local tests parse every JSON fence and round-trip representative request DTOs and response/receipt relationships. They do not contact Django, validate real provider credentials or prove remote deployment.

Executed on 2026-10-12 with Flutter **3.44.7** / Dart **3.12.2**:

```bash
cd apps/sokoun_app
make ownerTenantCyclesCheck FLUTTER=/Users/aait/Downloads/flutter_3.44_7/bin/flutter
```

| Check | Result | Scope / limits |
| --- | --- | --- |
| Focused Flutter analysis | No issues found | Changed feature areas and new/affected tests listed in Makefile |
| Default build-gate suite | **263 passed, 23 skipped** | 17 test files; skipped cases require enabled planning gates |
| Enabled planning-gate suite | **39 passed, 4 skipped** | Four planning test files, including Arabic/English offer comparison; four skipped cases assert disabled-build behavior already exercised in the default run |
| Documentation samples | **10 tests passed** within the default suite | All **25 JSON blocks** parse; representative request serializers, legacy/structured responses, criteria mapping and receipts checked |
| Markdown local links / diff whitespace | Passed | Relative file/directory targets exist; `git diff --check` clean |
| Django tests / staging / signing / PSP / deployed workers / physical devices | **Not run in this phase** | Requires backend checkout/returned deployment and authorized integration fixtures |

The two suite counts are separate runs and include shared cases; they are not 302 distinct business journeys. Some existing pure-data fixtures emit localization-key warnings without a mounted localization host; the asserted test results pass. No warning is treated as backend or provider evidence.

The reproducible target is [ownerTenantCyclesCheck in the app Makefile](../../apps/sokoun_app/Makefile). Existing capability defaults remain unchanged; planning flags are enabled only in the fake-transport test invocation. Live owner/tenant integration follows the backend return, not this local result.

## 12. Backend return form

Copy this section into **`SOKOUN_OWNER_TENANT_BACKEND_RETURN.md`** and send that file back with the schema/evidence bundle. Fill every row; use `not implemented`, `not deployed`, `not verified` or a concrete blocker instead of leaving ambiguous blanks. Keep credentials, personal data, private token links and raw payment/KYC data out of the bundle.

### A. Release identity and environment

| Field | Backend answer |
| --- | --- |
| Backend repository / commit / PR | TO FILL |
| Deployment ID, UTC time, environment and HTTPS API base URL | TO FILL |
| Python / Django / DRF / database versions | TO FILL |
| Web / worker / scheduler / WebSocket release versions | TO FILL |
| Applied migration names; backfill counts; `migrate --check` result | TO FILL |
| Auth classes, access/refresh transport, CSRF/cookie behavior | TO FILL |
| OpenAPI/schema version and artifact path/hash | TO FILL |
| Approved rental/template/privacy policy versions | TO FILL |
| Provider environments and verified service families | TO FILL |
| Server capability/action grants by actor; mobile build requirements | TO FILL |
| Operator, rollback procedure, unresolved-operation recovery owner | TO FILL |

### B. Endpoint contract confirmation (one row per endpoint/action)

| Method / full path | Implemented and deployed SHA | Request schema/example | Response schema/example and HTTP status | Actor/object rules | Revision/key/replay behavior | Errors | Evidence artifact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TO FILL | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |

For each JSON/multipart example, supply a sanitized **actual** request and response with UTC timestamp, locale and actor alias. Preserve field names, types and relationships while replacing identifiers consistently. Include a counterpart read, stale conflict, forbidden actor, duplicate replay and lost-response recovery for writes. Include receipt/operation lookup and linked source revisions. Do not return only endpoint names or Swagger screenshots.

### C. Cycle acceptance

| Cycle | Implemented / deployed / verified separately | Test IDs and command/result | Both-actor evidence | Provider/job/storage proof | Remaining blocker |
| --- | --- | --- | --- | --- | --- |
| C01 listing/discovery/visit | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C02 rejection/cancel/resubmit | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C03 invitation/legacy draft | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C04 structured agreement/payment/move-in | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C05 active stay/recurring operations | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C06 exit/settlement/replacement | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C07 banner/mock activation/placement | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C08 roommates/groups | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C09 request/offer/compare/handoff | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| S01 exact accommodation | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| S02 alerts/commute/assistant | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| S03 recovery/account isolation | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |

### D. Conflict resolution and approved policy

| Question | Approved answer / version / test |
| --- | --- |
| Public guest discovery permissions (BE001) | TO FILL |
| Original banner media/operation repair (BE002), no replacement ad | TO FILL |
| English visit labels and cache variation (BE003) | TO FILL |
| Cancelled never-occupied draft Rental Center applicability (GAP001) | TO FILL |
| Planning deployment and actual grants (DEP001) | TO FILL |
| Active fixture and signing/payment/payout readiness (DEP002) | TO FILL |
| Counterpart chat broadcast/persistence/reconnect (OBS001) | TO FILL |
| Activation ordering, inventory holds, payment/deposit requirements | TO FILL |
| Studio zero-bedroom rules, partial-period rounding, taxes, refund/commission policy | TO FILL |
| Invitation source eligibility, expiry, ambiguity handling and consumption | TO FILL |
| Financial closure vs legal end/possession; notice/replacement effective boundary | TO FILL |
| Deletion, retention, private group history and provider data retention | TO FILL |
| Generic operation statuses and permanent payment absence guarantees | TO FILL |

### E. Deviations requiring mobile coordination

| Current Dart contract | Deployed/proposed difference | Reason and migration/version strategy | Affected cycles | Fixture/example and owner |
| --- | --- | --- | --- | --- |
| TO FILL (or explicitly “none”) | TO FILL | TO FILL | TO FILL | TO FILL |

### F. Next integration-test prerequisites

- Dedicated nonproduction environment, allowlisted test identities (owner A/B, tenant A/B/C, unverified, guest), reset/cleanup policy and authorization scope.
- Credentials delivered through the agreed private mechanism; account aliases and resource fixture IDs only in the Markdown.
- Published whole/room/group/bed fixtures, eligible visits/invitations, active lease/invoice/payment fixtures, groups/requests/reports/transitions, media and documents.
- Exact build flags and server capability grants for **passed** families; verification bypass disabled.
- Signing/PSP sandbox details, event delivery/reconciliation instructions, worker/scheduler/storage health evidence, stable operation journal and correlation IDs.
- Reproducible backend test commands/output, deployment and migration evidence, unresolved issue list and designated observer for logs during integration.

After this file is returned, mobile integration tests will validate the deployed examples against the Dart models, then exercise the journeys and failures with separate owner/tenant sessions. They will report local parsing, remote API, provider and device results separately.

## 13. Structured DTO field appendix

The following field inventory is synchronized from the existing rental handoff and links to actual Dart models. It is a navigation aid for exact serialization, not a generic all-fields-writable Django serializer. Resource permissions add root `allowed_actions` and `blocking_reasons`. Local recovery DTOs are explicitly not API request bodies. Inspect nested linked models for field types and conditional omissions.

| Client model | Purpose | Wire fields |
| --- | --- | --- |
| [RentalAgreementConfiguration](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_configuration.dart) | Resource/read DTO | `templates`, `policy`, `can_create` |
| [RentalAgreementDraftBody](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_draft_body.dart) | Request | `invitation_id`, `invitation_revision`, `property_id`, `offer_id`, `offer_revision`, `tenant_id`, `terms`, `request_key`, `expected_revision` |
| [RentalAgreementTerms](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_terms.dart) | Resource/read DTO | `starts_on`, `ends_on_exclusive`, `handover_on`, `monthly_rent`, `deposit`, `deposit_holder`, `included_services`, `excluded_services`, `termination_policy`, `renewal_policy`, `policy_version`, `template_id`, `template_version`, `timezone`, `occupants`, `billing_anchor_day`, `commission_rate_bps`, `commission_payer`, `commission_basis`, `processing_fee_payer`, `renewal_commission_rate_bps` |
| [RentalCommercialPolicy](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_commercial_policy.dart) | Resource/read DTO | `version`, `commission_rate_bps`, `commission_payer`, `commission_basis`, `processing_fee_payer`, `renewal_commission_rate_bps`, `timezone`, `billing_cycle`, `currency`, `exponent` |
| [RentalSigningBody](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_signing_body.dart) | Request | `document_id`, `document_hash`, `expected_revision`, `request_key` |
| [RentalSigningSession](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_signing_session.dart) | Resource/read DTO | `session_id`, `subject_id`, `request_key`, `revision`, `document_id`, `document_hash`, `hosted_url`, `expires_at`, `operation_receipt_id` |
| [RentalNotificationContext](../../apps/sokoun_app/lib/features/shared/notifications/data/models/rental_notification_context.dart) | Resource/read DTO | `lease_id`, `invoice_id`, `payment_attempt_id`, `handover_id`, `maintenance_request_id`, `payout_id`, `dispute_id`, `rental_interest_id`, `terms_proposal_id`, `rental_change_id`, `rental_change_kind` |
| [RentalDecisionBody](../../apps/sokoun_app/lib/features/shared/premium/data/models/rental_action_body.dart) | Request | `expected_revision`, `request_key`, `decision`, `note`, `effective_on`, `requested_date`, `item_ids` |
| [RentalCapabilities](../../apps/sokoun_app/lib/features/shared/premium/data/models/rental_capabilities.dart) | Resource/read DTO | `account_id`, `account_verified`, `enabled_capabilities`, `policy_version` |
| [RentalOperationLookup](../../apps/sokoun_app/lib/features/shared/premium/data/models/rental_operation_lookup.dart) | Resource/read DTO | `request_key`, `request_subject_id`, `status`, `operation_receipt` |
| [RentalOperationReceipt](../../apps/sokoun_app/lib/features/shared/premium/data/models/rental_operation_receipt.dart) | Resource/read DTO | `id`, `subject_id`, `request_key`, `revision`, `status` |
| [RentalPermissions](../../apps/sokoun_app/lib/features/shared/premium/data/models/rental_permissions.dart) | Resource/read DTO | `allowed_actions`, `blocking_reasons` |
| [BillingPeriod](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/billing_period.dart) | Resource/read DTO | `id`, `start`, `end_exclusive`, `issue_at`, `due_at`, `invoice_id`, `amount`, `status` |
| [CheckoutNavigationRules](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/checkout_navigation_rules.dart) | Resource/read DTO | `allowed_origins`, `return_url`, `return_state`, `external_schemes` |
| [InvoiceLine](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/invoice_line.dart) | Resource/read DTO | `id`, `type`, `description`, `amount` |
| [PaymentAttempt](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_attempt.dart) | Resource/read DTO | `refundable_balance`, `revision`, `lease_id`, `payment_attempt_id`, `invoice_id`, `request_key`, `quote_id`, `invoice_revision`, `policy_version`, `quote_fingerprint`, `payment_status`, `invoice_status`, `amount`, `confirmed_at`, `receipt_id`, `payout_status`, `settlement_status`, `updated_at` |
| [PaymentAttemptLookup](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_attempt_lookup.dart) | Resource/read DTO | `invoice_id`, `request_key`, `results`, `absence_confirmed`, `active_session` |
| [PaymentQuote](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_quote.dart) | Resource/read DTO | `quote_id`, `invoice_id`, `invoice_revision`, `payer_amount`, `tenant_service_fee`, `policy_version`, `expires_at`, `fingerprint` |
| [PaymentRecoveryIntent](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_recovery_intent.dart) | Local/query DTO; not a server resource | `invoice_id`, `request_key`, `quote_id`, `invoice_revision`, `quote_fingerprint`, `payment_attempt_id`, `created_at`, `policy_version`, `amount` |
| [RentPaymentState](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_payment_state.dart) | Resource/read DTO |  |
| [RentalCheckoutSession](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/rental_checkout_session.dart) | Resource/read DTO | `session_id`, `payment_attempt_id`, `invoice_id`, `quote_id`, `request_key`, `invoice_revision`, `status`, `amount`, `checkout_url`, `expires_at`, `operation_receipt_id`, `navigation` |
| [MyRentalsFilter](../../apps/sokoun_app/lib/features/shared/rental_center/data/models/my_rentals_filter.dart) | Local/query DTO; not a server resource | `period`, `search` |
| [RentalCenter](../../apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_center.dart) | Resource/read DTO | `id`, `tenancy_root_id`, `revision`, `property_title`, `lease_status`, `status`, `occupancy_status`, `financial_closure_status`, `terms`, `balance`, `next_action`, `timeline`, `billing_schedule`, `chat_thread_id`, `last_updated_at`, `legacy_read_only`, `offer_snapshot` |
| [RentalNextAction](../../apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_next_action.dart) | Resource/read DTO | `action`, `resource_id`, `description`, `kind` |
| [RentalTimelineEvent](../../apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_timeline_event.dart) | Resource/read DTO | `id`, `label`, `description`, `occurred_at`, `kind`, `resource_id` |
| [RentalChange](../../apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change.dart) | Resource/read DTO | `document_hash`, `document_id`, `id`, `lease_id`, `invoice_id`, `revision`, `kind`, `status`, `reason`, `requested_date`, `original_due_at`, `deferred_until`, `effective_on`, `amount`, `terms`, `previous_terms`, `signature_document_id` |
| [RentalChangeBody](../../apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change_body.dart) | Request | `invoice_id`, `reason`, `requested_date`, `effective_on`, `method`, `amount`, `terms`, `evidence_ids`, `lease_revision`, `request_key`, `expected_revision` |
| [RentalDeposit](../../apps/sokoun_app/lib/features/shared/rental_deposits/data/models/rental_deposit.dart) | Resource/read DTO | `id`, `lease_id`, `revision`, `holder`, `invoice_id`, `status`, `agreed`, `due`, `collected`, `returned`, `applied`, `disputed`, `remaining` |
| [DisputeBody](../../apps/sokoun_app/lib/features/shared/rental_disputes/data/models/dispute_body.dart) | Request | `lease_id`, `subject_kind`, `subject_id`, `reason`, `evidence_ids`, `request_key`, `expected_revision` |
| [RentalDispute](../../apps/sokoun_app/lib/features/shared/rental_disputes/data/models/rental_dispute.dart) | Resource/read DTO | `id`, `lease_id`, `subject_kind`, `subject_id`, `revision`, `status`, `reason`, `resolution`, `responses`, `evidence` |
| [EvidenceUploadBody](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/evidence_upload_body.dart) | Request | `lease_id`, `file`, `mime_type`, `sha256`, `request_key` |
| [HandoverBody](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_body.dart) | Request | `kind`, `possession_on`, `condition`, `keys`, `meters`, `inventory`, `evidence_ids`, `request_key`, `expected_revision` |
| [HandoverItem](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_item.dart) | Resource/read DTO | `id`, `label`, `condition`, `reading`, `evidence_ids` |
| [RentalEvidence](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart) | Resource/read DTO | `id`, `lease_id`, `name`, `mime_type`, `size_bytes`, `status`, `sha256`, `revision` |
| [RentalEvidenceLink](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence_link.dart) | Resource/read DTO | `id`, `subject_id`, `url`, `expires_at` |
| [RentalHandover](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_handover.dart) | Resource/read DTO | `id`, `lease_id`, `revision`, `kind`, `status`, `possession_on`, `condition`, `keys`, `meters`, `inventory`, `evidence`, `accepted_by` |
| [RentalInterest](../../apps/sokoun_app/lib/features/shared/rental_interests/data/models/rental_interest.dart) | Resource/read DTO | `source_eligible`, `tenant_id`, `id`, `property_id`, `offer_id`, `revision`, `tenant_name`, `desired_start`, `months`, `occupants`, `message`, `status`, `proposal_id`, `invitation_id`, `offer_snapshot` |
| [RentalInterestBody](../../apps/sokoun_app/lib/features/shared/rental_interests/data/models/rental_interest_body.dart) | Request | `property_id`, `offer_id`, `offer_revision`, `desired_start`, `months`, `occupants`, `message`, `request_key`, `expected_revision` |
| [TermsProposal](../../apps/sokoun_app/lib/features/shared/rental_interests/data/models/terms_proposal.dart) | Resource/read DTO | `id`, `interest_id`, `invitation_id`, `revision`, `status`, `terms`, `previous_terms`, `offer_snapshot` |
| [TermsProposalBody](../../apps/sokoun_app/lib/features/shared/rental_interests/data/models/terms_proposal_body.dart) | Request | `interest_id`, `offer_id`, `terms`, `interest_revision`, `offer_revision`, `request_key`, `expected_revision` |
| [MaintenanceActionBody](../../apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_action_body.dart) | Request | `action`, `note`, `appointment_at`, `cost`, `cost_payer`, `evidence_ids`, `request_key`, `expected_revision` |
| [MaintenanceBody](../../apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_body.dart) | Request | `title`, `description`, `category`, `priority`, `access_times`, `evidence_ids`, `request_key`, `expected_revision` |
| [MaintenanceEvent](../../apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_event.dart) | Resource/read DTO | `id`, `label`, `note`, `at`, `appointment_at`, `cost` |
| [MaintenanceRequest](../../apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_request.dart) | Resource/read DTO | `id`, `lease_id`, `revision`, `title`, `description`, `category`, `priority`, `access_times`, `status`, `appointment_at`, `proposed_cost`, `cost_payer`, `events`, `evidence` |
| [OwnerOnboardingBody](../../apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_onboarding_body.dart) | Request | `expected_revision`, `request_key`, `accepted_policy_versions` |
| [OwnerOnboardingSession](../../apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_onboarding_session.dart) | Resource/read DTO | `session_id`, `subject_id`, `request_key`, `revision`, `hosted_url`, `expires_at`, `operation_receipt_id` |
| [OwnerPayable](../../apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_payable.dart) | Resource/read DTO | `id`, `lease_id`, `invoice_id`, `period`, `revision`, `gross`, `commission`, `net`, `processing_fee`, `settlement_status`, `payout_status`, `payout_id`, `blocking_reasons` |
| [OwnerPaymentProfile](../../apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_payment_profile.dart) | Resource/read DTO | `policy_summary`, `required_policy_versions`, `id`, `revision`, `status`, `masked_beneficiary`, `provider`, `requirements`, `accepted_policy_versions` |
| [RentalPayout](../../apps/sokoun_app/lib/features/shared/rental_payouts/data/models/rental_payout.dart) | Resource/read DTO | `id`, `lease_id`, `revision`, `status`, `amount`, `masked_beneficiary`, `reason`, `submitted_at`, `succeeded_at`, `payable_ids` |
| [FinalSettlement](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/final_settlement.dart) | Resource/read DTO | `id`, `lease_id`, `revision`, `status`, `lines`, `rent_balance`, `deposit_to_return`, `refund_due`, `total_due`, `accepted_by` |
| [PrivateDocumentLink](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/private_document_link.dart) | Resource/read DTO | `id`, `subject_id`, `url`, `expires_at` |
| [RefundBody](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/refund_body.dart) | Request | `lease_id`, `payment_attempt_id`, `amount`, `reason`, `payment_revision`, `request_key`, `expected_revision` |
| [RentalDocument](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_document.dart) | Resource/read DTO | `id`, `lease_id`, `type`, `title`, `status`, `created_at`, `revision` |
| [RentalRefund](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_refund.dart) | Resource/read DTO | `id`, `lease_id`, `payment_attempt_id`, `revision`, `status`, `amount`, `refundable_balance`, `reason`, `method` |
| [RentalReview](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_review.dart) | Resource/read DTO | `id`, `lease_id`, `revision`, `rating`, `comment`, `status` |
| [RentalReviewBody](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_review_body.dart) | Request | `rating`, `comment`, `request_key`, `expected_revision` |
| [RentalStatementBody](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_statement_body.dart) | Request | `lease_id`, `starts_on`, `ends_on_exclusive`, `request_key`, `expected_revision` |
| [SettlementBody](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_body.dart) | Request | `lines`, `note`, `request_key`, `expected_revision` |
| [SettlementLine](../../apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_line.dart) | Resource/read DTO | `id`, `type`, `description`, `amount`, `evidence_ids`, `disputed` |
| [RentalSupportContext](../../apps/sokoun_app/lib/features/shared/support/data/models/rental_support_context.dart) | Resource/read DTO | `lease_id`, `invoice_id`, `payment_attempt_id`, `subject_kind`, `subject_id` |
| [RentalInvitationBody](../../apps/sokoun_app/lib/features/shared/tenancy_invitations/data/models/rental_invitation_body.dart) | Request | `interest_id`, `interest_revision`, `property_id`, `offer_id`, `offer_revision`, `tenant_id`, `terms_proposal_id`, `expected_revision`, `request_key` |
| [DigitalLease](../../apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease.dart) | Resource/read DTO | `owner_id`, `tenant_id`, `invitation_id`, `id`, `property_id`, `property_title`, `owner_name`, `tenant_name`, `start_date`, `end_date`, `rent`, `status`, `revision`, `document_url`, `can_sign`, `can_cancel`, `tenancy_root_id`, `lease_status`, `occupancy_status`, `financial_closure_status`, `legacy_read_only`, `terms`, `reviewed_by`, `document_id`, `document_hash`, `hold_expires_at`, `offer_snapshot` |
| [RentInvoice](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_invoice.dart) | Resource/read DTO | `id`, `lease_id`, `property_title`, `reference`, `due_date`, `amount`, `status`, `receipt_url`, `can_pay`, `revision`, `invoice_type` (legacy `type` read fallback), `billing_period_id`, `period_start`, `period_end_exclusive`, `due_at`, `deferred_until`, `charges`, `credits`, `applied`, `balance`, `lines`, `payment_attempt_id`, `receipt_id`, `invoice_status`, `offer_snapshot` |
| [EvidenceUploadIntent](../../apps/sokoun_app/lib/features/shared/rental_handovers/data/models/evidence_upload_intent.dart) | Protected local recovery DTO; never submitted as a server resource | `lease_id`, `request_key`, `sha256`, optional confirmed `resource_id`, `minimum_revision`; no bytes, paths or URLs |
| [RentCheckoutBody](../../apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_checkout_body.dart) | Request | `invoice_id`, `quote_id`, `expected_revision`, `request_key` |
