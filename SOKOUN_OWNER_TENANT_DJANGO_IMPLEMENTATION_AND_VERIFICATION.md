# Sokoun owner–tenant cycles: Django implementation and verification guide

Prepared: **2026-10-12**. Audience: backend engineer, QA, release operator, mobile integrator.

This guide translates [the owner–tenant cycle specification](../../SOKOUN_OWNER_TENANT_CYCLES_EXPLAINED_EN.md) into backend work and acceptance criteria, checked against the Flutter implementation. Use it with [the API contract and backend return template](SOKOUN_OWNER_TENANT_API_CONTRACT_AND_RETURN.md). Complete that return template before the next live integration phase.

## 1. What is verified, and what still needs evidence

The repository contains the Flutter clients, typed API models, local tests, handoffs and earlier sanitized server observations. It does **not** contain the Django project, production database, worker configuration or provider dashboards. Backend implementation details below are requirements and recommended designs, not claims that those components already exist. Map the concepts to your actual Django apps and return the mapping; do not create a parallel rental subsystem merely to match these names.

Evidence levels used here:

| Label | Meaning |
| --- | --- |
| Client implemented | A reachable Flutter flow and typed request/response handling exist. Build/server/provider gates can still prevent use. |
| Locally verified | A test exercised client behavior using fixtures or fake transport. This does not prove deployed API behavior. |
| Historical server observation | A dated response in the previous audit; it must be rechecked against the release being delivered. |
| Backend required | A rule the Django service must implement and prove. Its current implementation is unknown without server evidence. |
| Policy decision | A business choice that code and tests cannot safely invent. Return the approved answer and version. |

The baseline mobile commit is `0e122774433b42e16a6643f33e886bdd29d897c9`; this guide and the companion client fixes are working-tree changes after it. The prior audit targeted **TEST-DO**, with observations on 2026-10-11 UTC (some reports dated October 12 local time). Its backend commit was not supplied. No new remote mutations or provider operations were run for this handoff.

Historical sources: [backend findings](SOKOUN_BACKEND_REQUIRED_FIXES.md), [audit report](../qa/SOKOUN_AUDIT_REPORT.md), [flow matrix](../qa/SOKOUN_FLOW_TEST_MATRIX.md), [captured evidence](../qa/evidence/run-2026-10-11/). Preserve their timestamps and original outcomes when adding new evidence.

## 2. Cycle-to-implementation map

Paths below are relative to `apps/sokoun_app/lib/features/`. The linked folders contain the actual screens, Cubits and data helpers. The API companion lists wire contracts; do not infer endpoint availability from screen existence.

| Cycle | In-app entry and implementation chain | Server responsibilities / current boundary |
| --- | --- | --- |
| C01: listing → discovery → visit | Owner listing/draft screens → owner draft/inventory Cubits → [owner/home](../../apps/sokoun_app/lib/features/owner/home/) and [rental_offers](../../apps/sokoun_app/lib/features/shared/rental_offers/); tenant Home/Search → property detail → `BookVisitCubit`; owner visit inbox → request detail/actions; [tenant visits](../../apps/sokoun_app/lib/features/tenant/visits/) / [owner visits](../../apps/sokoun_app/lib/features/owner/visits/) | Listing ownership, moderation, publication, exact offer selection, schedule/slot availability, both inboxes, consent-based contact/chat, actual eligible review. Historical public discovery 401 and localization defects remain release checks. |
| C02: visit rejection/cancellation | Same visit detail/action Cubits; preserved note/date/offer and refreshed resource after conflicts | Authoritative allowed actions, reason requirements, permitted resubmission, contact disclosure history and notification consistency. Rejecting/accepting a visit does not allocate rental inventory. |
| C03: invitation → legacy draft | Owner eligible visit/tenant context → [tenancy invitations](../../apps/sokoun_app/lib/features/shared/tenancy_invitations/) → tenant invitation response → `LeaseTenantPickerScreen` / `LeaseDraftCubit` → [digital leases](../../apps/sokoun_app/lib/features/shared/digital_leases/) | Pending/confirmed visit eligibility; seven-day invitation validity; atomic consent consumption; legacy body and raw response compatibility; owner draft cancellation. Latest historical tests resolved several older invitation/cancel defects. |
| C04: structured rental agreement | Property exact offer → [rental interests](../../apps/sokoun_app/lib/features/shared/rental_interests/) / terms proposal → structured invitation → `RentalAgreementCommandCubit` / `RentalAgreementData` → signing → [rent management](../../apps/sokoun_app/lib/features/shared/rent_management/) → handover | Capabilities, versions, signatures, inventory holds/activation, invoice ledger, PSP capture and reconciliation. Client exists, but historical capabilities were empty; no deployed full-cycle proof. |
| C05: in-tenancy operations | My Rentals / [rental center](../../apps/sokoun_app/lib/features/shared/rental_center/) → invoice, deposit, [maintenance](../../apps/sokoun_app/lib/features/shared/rental_maintenance/), [changes](../../apps/sokoun_app/lib/features/shared/rental_changes/), documents | Scheduled invoices, payment extensions, cost approvals, amendments, renewals, external payment claims, immutable documents and counterpart projections. Requires active-lease fixtures and jobs. |
| C06: move-out → closure | Rental Center → termination/change, [handovers and condition reports](../../apps/sokoun_app/lib/features/shared/rental_handovers/), transition screens, [settlement](../../apps/sokoun_app/lib/features/shared/rental_settlement/), disputes, refunds, payouts | Separate legal end, occupancy return, financial settlement, deposit, refund and owner payout states. Planning notice/replacement services historically missing. Cancelled unoccupied draft blocker text is historically contradictory. |
| C07: owner banner → tenant placement | Owner Home → [banner ads](../../apps/sokoun_app/lib/features/shared/banner_ads/) create/upload/recovery → tenant carousel | Independent advertising API, durable original artwork, same operation replay, **mock** activation, placement eligibility and expiry. Historical original media 404 and mock-payment failure block completion. |
| C08: roommates → group decisions | Tenant tools → [lifestyle/roommates](../../apps/sokoun_app/lib/features/tenant/roommates/) → [housing groups](../../apps/sokoun_app/lib/features/shared/housing_groups/) → invite/shortlist/vote/costs/group visit/application | Private profile consent, member/roster versions, individual approvals, capacity and expiry, real qualifying visits. Planning routes historically 404; group membership does not establish a tenancy. |
| C09: housing request → owner offer | Tenant [housing requests](../../apps/sokoun_app/lib/features/shared/housing_requests/) → [owner housing demand](../../apps/sokoun_app/lib/features/owner/housing_demand/) → exact offer response → compare/shortlist/decline → explicit property/visit flow | Eligible owner feed, request and offer revisions, price/period snapshots, participant privacy, expiry. Planning routes historically missing. Comparison now permits at most three distinct response records. |
| S01: accommodation identity | Shared `RentalSelection`, inventory read/mutation helpers; offer-aware discovery/favorites/visits/leases | Preserve property + offer + offer revision + whole/room/group/bed identity. Lock overlapping inventory atoms. Never substitute the first available offer. |
| S02: decision support | Saved search/alerts, [commute](../../apps/sokoun_app/lib/features/tenant/commute/), [tenant assistant](../../apps/sokoun_app/lib/features/tenant/ai_assistant/) | Alert delivery workers, catalog validation, real routing coverage, grounded assistant replies with explicit user review. Local saved filters are not proof of an alert worker or AI/routing service. |
| S03: recovery and consistency | [premium API helpers](../../apps/sokoun_app/lib/features/shared/premium/data/), [recovery](../../apps/sokoun_app/lib/features/shared/recovery/), `AccountSession`, receipt and operation lookup, payment attempt recovery | Scoped idempotency, durable operation status, authoritative absence, replay, account isolation, stale revision rejection, counterpart readback. Legacy endpoints do not all support the structured recovery protocol. |

## 3. Prioritized work register

Each row must return an owner, backend ticket/PR, deployed commit, test names and sanitized evidence. “Implemented locally” is not a deployment result.

| ID | Priority | Evidence / problem | Required backend work and exit condition |
| --- | --- | --- | --- |
| BE001 | P0 for public journey | Historical guest Home/list/catalog 401 while public detail returned 200 | Reconcile documented public discovery with authentication/permission classes. Guest sees only published public data, private owner/contact fields remain protected; filters/types/governorates/cities and pagination work without login where public contract requires. |
| BE002 | P0 for banner completion | Original pending ad media 404; mock-payment 400 with `errors.banner` | Repair durable media lookup/storage/authorization for the **existing** ad and operation. Replay same activation intention, prove original image retrievable, tenant placement correct, restart persistence and expiry. Do not replace it with a new paid record to hide failure. |
| BE003 | P1 | English visit request returned Arabic labels despite English headers | Translate server-owned tabs/status/display strings under the selected locale; test `ar` and `en`, `Content-Language`, cache variation and stored free text preservation. |
| GAP001 | P1 | Cancelled, never-occupied legacy draft showed occupancy-return / final-settlement blockers | Correct aggregate applicability. A never-occupied draft must not demand move-out. Define financial-closure policy explicitly; do not automatically mark all cancelled records financially settled. Check list, detail and Rental Center together. |
| DEP001 | P0 before planning rollout | `planning-capabilities` and planning collections historically 404 | Implement/version/migrate planning families C08/C09/S02 and condition/transition services; advertise only deployed, verified capability/action pairs. Missing services remain disabled. |
| DEP002 | P0 before structured rental rollout | Empty rental capabilities/actions; no active fixture/provider proof | Complete C04–C06 and owner finance, seed authorized fixtures, verify signature/PSP/worker integrations, then return granular capabilities. Do not enable all flags merely to render screens. |
| OBS001 | P1 investigation | Chat ACK + REST persistence observed; counterpart WebSocket broadcast inconsistent | Trace two authenticated connections, channel subscription, commit/outbox, reconnect and event IDs. This is an observation, not a proven channel-layer root cause. Prove counterpart delivery and REST recovery independently. |
| DEC001 | Release dependency | Unresolved policy choices | Return approved studio/zero-bedroom rules, commission refund/tax treatment, deletion/retention, activation ordering and pending financial closure semantics. Version the chosen policy and add boundary tests. |

Latest historical observations **already resolved**: `lease-configuration.can_create=true`; new invitation-created draft `legacy_read_only=false`; owner cancellation permitted, tenant cancellation denied; `can_sign=false`; repeated same cancellation returned revision 2 with HTTP 200; eligible picker changed pending → accepted → consumed/absent; draft/cancel created no invoices. Keep these as regressions rather than reporting them again as currently failing.

## 4. Flutter enhancements delivered with this guide

1. Structured agreement creation now confirms the returned owner, tenant, invitation, property, exact accommodation snapshot, draft state, editable classification and reviewed terms. A mismatched success payload remains an **unknown** outcome so recovery can retain the same intention.
2. Legacy draft creation now checks returned dates and rejects contradictory owner/tenant IDs when present. Older projections may still omit participant IDs. Existing property/offer/rent checks remain in place. This does not upgrade legacy transport to the structured operation-lookup protocol.
3. Planning pages now support per-record scope validation and reject late responses after a session change. Housing-offer pages must match the requested request ID; condition-report and transition pages must match the requested lease; transition pages must match the known collection kind. Invalid pages fail as a whole rather than quietly hiding a wrong record.
4. Housing comparison counts response records, not unique properties. Two to three offers can be compared even when several belong to the same property; a fourth requires deselecting one. Re-selecting the same record cannot create duplicates. Arabic/English help text reflects this rule.

These checks defend against accidental API mismatch. Django must still enforce authorization and invariants; a malicious client can bypass every UI check. Unknown transition kinds already lose actions in parsing; they are not evidence of a supported new business state.

## 5. Django implementation structure and shared invariants

### 5.1 Before coding

Inventory the installed Python/Django/DRF/database versions, auth classes, timezone settings, storage backend, task runner/scheduler, WebSocket service, signing/PSP/routing providers and release mechanism. Return exact versions and configuration **names**, never secret values. The framework references below use Django 6.0 for explanation; adapt to the supported version actually installed. This guide does not require a framework upgrade.

Keep transport serializers separate from business commands and actor-scoped read projections. Use explicit input fields and validation; do not expose writable model fields such as `owner_id`, `paid`, `accepted_by`, `occupancy_status`, `commission` or capability grants via a broad `ModelSerializer(fields='__all__')`. Resolve the actor from authenticated `request.user`. A `workspace=owner` query is a view selection, not proof of ownership.

Use the same policy/permission function to calculate `allowed_actions` and to recheck a command immediately before mutation. Querysets must scope both list and detail resources; object permissions alone are not a list filter. Child routes must join through the authorized parent. Validate cross-resource links: invoice→lease, evidence→lease, offer→property, invitation→both parties, candidate→consented source. Return no private resource before checking authorization.

### 5.2 Transactions, revisions and operation identity

Apply the following command protocol to new structured mutations; preserve the legacy adapters described in the API guide:

1. Authenticate, validate request schema and classify action/subject. Authorize access to the command subject and any replayed resource before returning saved data. Canonicalize semantic body fields for a payload hash. Do not include transient authentication or locale in this hash.
2. Find or reserve a durable idempotency operation scoped to the actor and action namespace. Same key + same semantics replays the original outcome; same key + changed body conflicts. Check existing operation identity **before** rejecting a replay merely because its submitted revision is old.
3. In a short database transaction, lock the relevant aggregate and source rows in a consistent order; validate roles, revisions, expiry, current offer/capacity and permitted transition. A create usually has `expected_revision=0`; source revision fields still need independent checks.
4. Write the resource, new revision, immutable history, receipt, and durable outbox entry atomically. Use unique/check constraints as a second defense against concurrent workers/requests. Ensure two concurrent first uses of the same key converge on one operation.
5. Commit; return the saved canonical projection and receipt. Enqueue/deliver outbox work after commit, and let a periodic dispatcher retry committed-but-undelivered records.
6. Perform external provider calls outside long database locks, using the persisted operation identity as the provider idempotency key. Persist provider request/result transitions and reconcile uncertainty instead of creating a new operation.

`transaction.atomic()` groups database changes; `transaction.on_commit()` defers callbacks until commit, but a callback is not a durable queue. The outbox requirement above is Sokoun's proposed reliability design. Catch database exceptions at an appropriate transaction/savepoint boundary rather than querying inside a broken transaction. [Django transactions](https://docs.djangoproject.com/en/6.0/topics/db/transactions/)

Use `select_for_update()` where row locking is supported, and explicit constraints for uniqueness/overlap. Locking behavior is database-dependent; SQLite does not establish production row-lock correctness. Exercise races with `TransactionTestCase`/`APITransactionTestCase` and separate connections against the deployment database engine. Ordinary `TestCase` wraps tests in transactions and can conceal incorrect lock usage. [Django row locking](https://docs.djangoproject.com/en/6.0/ref/models/querysets/#select-for-update)

Recommended constraints (map to actual schema):

| Aggregate | Constraint / concurrency protection |
| --- | --- |
| Operations | Unique actor + action namespace + key; immutable canonical payload hash; unique receipt; durable final-absence tombstone if advertised |
| Invitations | No duplicate live invitation for the same authorized parties/exact selection under the approved policy; one consuming lease; expiry tested under lock |
| Allocation | No overlapping active hold/occupancy for the same underlying room/bed atoms and time interval; whole property overlaps all included atoms |
| Signatures | Unique provider event; document ID/hash/revision immutable once signing starts; signature belongs to authorized party |
| Billing | Unique tenancy root + billing period + invoice type; immutable original due date; journal source IDs unique |
| Payments/refunds/payouts | Unique provider event and idempotency key; one applicable capture posting; refund ≤ remaining refundable balance; no duplicate payable/payout posting |
| Groups | Unique active membership; unique actor vote/approval at item + item revision + roster revision; no admin-less active group |
| Reports | Stable item identity; one actor acknowledgment per report revision; final report immutable; lease/evidence/baseline scope enforced |

`absent_final` and `absence_confirmed=true` are strong promises: a delayed original operation can never later commit. Implement a tombstone/operation reservation protocol to enforce that, or return unresolved. A 404, timeout, temporarily empty read replica or empty list alone is not final absence. The current generic Flutter lookup rejects `absent_final`; enabling such a result requires a coordinated contract/client update even after a server tombstone is implemented.

### 5.3 Separate state machines

Do not use a single `status` field to imply all of these facts:

| Domain | Independent facts |
| --- | --- |
| Visit | requested/accepted/rejected/cancelled/completed; granted contact/chat; slot occupancy |
| Invitation | pending/accepted/rejected/expired/revoked/consumed; eligible source; lease link |
| Agreement | draft/review/signature/legal lifecycle; exact revision/document; legacy classification |
| Inventory | available/future availability/held/allocated; hold expiry; atom overlap |
| Occupancy | never handed over / possession transferred / returned; accepted handover evidence |
| Finance | invoice due/partial/paid/credited; payment authorization/capture; PSP settlement; owner payout |
| Closure | accepted settlement; deposit allocation/return; refund execution; dispute resolution; final financial closure |

The above are conceptual states. Emit only wire tokens recognized by the linked Dart enums and return any proposed additions before changing them. Every read projection should derive from the same facts, including the counterparty's view. Avoid treating expiry/revision-dependent permissions as long-lived cached values.

## 6. Implementation and acceptance by cycle

### C01 / C02 — listing, discovery and visits

1. Validate owner listing fields, category and inventory mode; assign stable server IDs while echoing local `client_key` values. Preserve inventory/offer revisions. Persist uploads durably before declaring publication usable.
2. Apply moderation and publication to all discovery feeds and detail eligibility. Apply scope/price-period/availability filters **before** grouping and pagination. Never take the minimum of mixed monthly/yearly prices.
3. Return server-authored available dates/times with a documented timezone. Book against the actual slot and exact offer revision. Atomically enforce capacity, self-booking/ownership rules and duplicate policy.
4. Persist `offer_snapshot` at booking. Rejection, cancellation and resubmission use explicit allowed transitions and reason policy. Preserve the original record/history; do not manufacture completion from the passage of a date.
5. On acceptance, update both actor projections and granted contact/chat consistently. Preserve historical contact disclosure according to the existing accepted-visit policy even if the visit is later cancelled; do not accidentally expose contact for a never-accepted request.
6. Calendar export/reminders must reflect the current appointment, timezone and cancellation. Review eligibility must derive from the real visit policy, with one eligible author and no self-review.

**Proof:** guest discovery and authenticated detail; two tenant requests racing for the last slot; stale offer revision; owner A attempting owner B's action; rejection note persistence; allowed resubmission; cancel after acceptance; both inboxes/counters; Arabic/English labels; deduplicated notifications; review eligibility; no lease/invoice/inventory rental allocation caused by a visit action.

### C03 — consent invitation and legacy lease draft

The agreed existing source is a pending/confirmed visit for the same owner/tenant/property; an exact offer must match when present. Do not expand to completed visits without accepting that policy and updating tests. Both actors must meet server verification requirements. Invitation lifetime is seven days including accepted but unconsumed invitations.

Owner creates → tenant reads/responds → accepted invitation becomes eligible in `lease-tenants` → owner submits a legacy draft → invitation is consumed in the same transaction. A pending/rejected/expired/revoked/consumed invitation must not appear as eligible. Prevent two simultaneous drafts consuming one consent. Cancellation never restores eligibility or reuses consent. The legacy body has no `invitation_id`, so resolve the unique eligible source under lock; reject ambiguity instead of guessing.

Create only a draft: no invoice, no occupancy, no automatic signing/payment/activation. Respect the distinction between old immutable legacy history and a newly created editable/cancellable legacy-shaped draft. Return truthful `can_cancel`, `can_sign`, `legacy_read_only` and actions for each actor.

**Proof:** pre/post picker reads; wrong owner/tenant/offer; pending acceptance; expiry before and after acceptance; duplicate create same key; changed-body same key; two distinct keys racing for the same invitation; owner cancel same key twice; tenant cancel denied; consumed invitation remains unavailable; exact dates/rent retained; no financial or possession side effects. Include historical cancelled drafts in migration/readback tests.

### C04 — structured agreement, signing, first payment and move-in

1. Authorize the tenant's exact current offer interest, desired dates, occupants and duration. Owner proposals pin interest revision, offer revision and full approved terms. Editing terms invalidates prior acceptance/review.
2. Create an interest-sourced invitation only from an eligible source and accepted required proposal. Do not let a property ID alone authorize an unrelated tenant. Preserve both parties and exact offer snapshot through the agreement response.
3. Server validates the commercial/template policy, civil dates, occupancy capacity and handover/billing dates. Generate the versioned document and digest from the exact reviewed terms. Review/signing actions pin revision; hosted signing pins document ID/hash and expiry. A WebView return is not a signature event.
4. Verify signature provider callbacks, replay handling, signer identity and document digest. Keep provider pending/failure visible and reconcile. Define a bounded inventory hold and release policy; never sell the same room/bed through an overlapping whole-property offer.
5. **Return an explicit activation policy.** The specification is not enough to assume universal payment-before-activation or activation-before-payment. State which signatures, deposit/first rent, hold, owner readiness and handover facts are required at each boundary. Implement one auditable activation command; test it under retries and concurrent eligibility changes.
6. Issue server-calculated invoices at the approved boundary. Quote the stored invoice, persist one payment attempt before contacting the PSP, bind checkout to quote/revision/amount, and reconcile by the same key after timeout. Validate signed provider events and ledger posting exactly once. Display capture, receipt, PSP settlement and owner payout independently.
7. Move-in handover requires the correct parties' acknowledgment of the current report/version. Transfer possession only at the defined acceptance boundary. A condition report submission or a visit acceptance cannot transfer possession.

**Proof:** stale proposal/review/signature; mismatched snapshot; expired signing session; repeated/out-of-order webhooks; hold expiry during signing/payment; two competing offers for overlapping atoms; tenant A paying tenant B's invoice denied; owner checkout denied; two checkout retries one attempt/charge; lost response then lookup; captured payment without receipt still captured with receipt pending; no payout until payout eligibility; both Rental Centers agree.

### C05 — recurring stay operations

Billing schedule uses civil dates, `ends_on_exclusive`, approved timezone and original billing anchor. Test January 31 → February → March without permanently shifting the anchor, leap years, DST, final partial periods and amount rounding. A repeated scheduler run issues the same invoice once. Deposit is a separate invoice/balance; do not treat it as rent revenue.

Maintenance: validate category/priority/access preferences and evidence ownership; record appointment and responses as history. A proposed tenant cost is not payable until that tenant approves the exact amount/version. A resolution report is not tenant confirmation. Reopen/cancel must honor current state and role.

Payment extension: preserve `original_due_at`; store `deferred_until` separately after approval. Amendment/renewal: preserve previous terms, invalidate old reviews, require new signatures where the policy requires, and apply effective dates without rewriting historical invoices. Renewal retains the tenancy root and does not repeat the first-period commission. An external payment claim is pending evidence until the authorized process confirms and posts the appropriate accounting adjustment.

**Proof:** repeated job; boundary dates; extension rejected/accepted; unauthorized cost approval; amendment during pending payment; renewal conflicting with future inventory; no double commission; external claim replay/rejection; private documents expire and cannot be downloaded by strangers; both parties read the same timeline and invoices.

### C06 — end, condition, settlement, refunds and replacement

Keep legal termination, notice receipt, effective end, occupancy return, settlement acceptance and actual fund movement distinct. A notice `acknowledge` records receipt; it does not terminate a lease. A finalized condition report records agreed observations; it does not establish liability, accept a handover, charge damages or deduct a deposit.

Condition reports need stable item IDs, permitted spaces, `notInspected`/`unknown` distinctions, evidence bindings, exact revision acknowledgments, objection history and a final immutable baseline. For move-out comparison, use the authorized final move-in baseline of the same leased selection. Re-submission invalidates acknowledgments of the old version. Reject cross-lease media and invented baseline IDs.

Settlement totals come from the ledger and authorized item proposals. Owner/tenant acceptance or dispute references exact version/item IDs; operations resolves disputed responsibility under policy. Refund requests never directly execute PSP refunds. Enforce remaining refundable balance under lock, process callbacks idempotently and keep failure/retry history. Payout retry must reuse provider identity, not duplicate a transfer.

Replacement has three separate tracks: outgoing release, incoming agreement, and future availability. Candidate nomination is not candidate consent; group membership is not a signature; approving future availability does not release current possession. Coordinate the required contracts, consent, inventory and dates through a resumable journal/outbox. Keep the old occupant's obligations unchanged until the approved release becomes effective; retain pending recovery if any step is uncertain.

**Proof:** notice read/acknowledge/withdraw; report object/revise/finalize; stale baseline; one party's approval cannot stand for everyone; settlement dispute one item; partial/refused refund; refund/provider timeout; retained payout hold; replacement declined/withdrawn/stale candidate; double replacement race; no incoming occupancy before eligibility; never-occupied cancellation shows no move-out obligation.

### C07 — banner advertising

Preserve the existing advertising API and `payment_mode=mock` semantics. This is not rental PSP payment and must not be described as a real captured charge. Server plan price/duration/revision are authoritative; a property link is optional and must be owned/eligible when supplied.

Create/upload stores the original artwork and operation journal durably. Verify content/size, authorization and media availability before accepting activation. Repeated same create/activation intention must return the same advertisement. Publication and tenant placement depend on actual status, moderation, start/end and property eligibility; expiry removes placement without deleting evidence required for recovery.

**Proof:** original blocked ad recovery, same operation after app/server restart, pending private artwork access, active public artwork access, wrong owner denied, bad/corrupt upload, plan revision conflict, tenant feed independent readback, expired/unpublished target removed, no accidental rental invoice/provider charge.

### C08 — lifestyle, roommates and housing groups

Lifestyle profile data requires explicit disclosure consent and purpose/retention policy. Match explanations must not expose private answers. Canonical user-pair connections prevent duplicates; blocking applies in both discovery and connection/chat authorization. Return the real `user_id` for a granted chat, not a connection resource ID.

Group creation atomically creates the admin membership. Membership/capacity, transfer/removal/leave, private token invites and revocation must survive simultaneous joins. Hash invite tokens at rest and omit raw tokens from logs/analytics/push. Preview is read-only and must not consume a token. Departed members lose future private reads according to the approved archive policy.

Shortlists pin exact offer versions. Votes and contributions bind to item, proposal, offer and roster versions. Contributions must cover exactly the active participants with nonnegative integer amounts summing to total; a planning proposal does not create payables. Changes invalidate approvals. Group visits/applications collect each participant's own consent and source eligibility; a coordinator cannot approve for everyone.

**Proof:** private profile access, withdrawal/block, duplicate connection, last slot invite race, revoked/expired token, preview no join, last-admin leave, roster change invalidates votes/cost approval, unauthorized history read, contribution total error, per-member visit/application consent and withdrawal, no automatic lease creation.

### C09 — demand requests and owner offers

Tenant request states and owner visibility must be explicit. Feed applies eligibility/block/expiry and prevents self-dealing. Criteria write and read schemas differ (see API guide); free-text neighborhood is not a district ID. Owner responses use owned published exact inventory, current request revision and server-authoritative rent/deposit/price period. Do not derive bed rent from whole-property rent.

Shortlist/decline/withdraw affects planning only. Communication requires a separate grant, and booking starts through the existing property/visit flow. Preserve response snapshots while requiring fresh eligibility at the next action. Editing/pausing/closing/expiring a request must prevent stale new offers. Offer list count and pagination must remain request-scoped.

**Proof:** two owners' offers and tenant view; owner cannot see another owner's private responses unless policy allows; stale request/offer; closed request; offer from unowned property; four offers on one property compare at most three; same response never duplicated; shortlist creates no lease/hold/invoice; selected offer survives navigation into property details.

### S01 / S02 / S03 — cross-cycle requirements

S01: model allocation against underlying inventory atoms so whole/room/group/bed paths cannot double-book. Keep immutable historical snapshots even after archive/edit. Never replace the selected offer on deep-link resolution, favorites, visit, invitation, lease, handover or invoice.

S02: a saved search is local until an alert is created; prove real worker evaluation, deduplication and notification delivery before claiming alerts are operational. Commute must use an actual routing provider, all destinations and hard time limits before pagination, with explicit unknown/coverage states. The assistant must use authorized grounded property IDs/catalog filters and expose unresolved requirements; it proposes drafts/actions that the user reviews in the normal feature, never executes hidden rental commands.

S03: preserve input and operation identity after timeout, malformed success, app kill and account switch. Fresh success may replace cached content; fresh empty is authoritative. A read failure should retain valid scoped data and Retry, but stale cached permissions cannot authorize a mutation. Backend replies, jobs and callbacks must be replay-safe independently of the client.

## 7. Test plan for the Django engineer

### 7.1 Required fixtures

Use isolated authorized test accounts: verified owner A, owner B, verified tenants A/B/C, unverified account, guest and a staff/operations actor with explicit permissions. Do not share a logged-in client across actors. Include whole-property, independent room, room group and bed offers with overlapping inventory; published, draft, rejected, archived, expired and unavailable variants.

Create visit variants; pending/accepted/expired/consumed invitations; editable legacy draft, historical read-only lease, structured draft/review/signature/active/ended/settlement-pending leases; unpaid/partial/paid/credited invoices; pending/captured/failed/unknown attempts; groups with changed rosters; request/offer/report/transition fixtures. Use deterministic clocks, approved templates/policy and synthetic media. Keep credentials outside reports.

### 7.2 Test layers and what each proves

| Layer | Required assertions | Evidence |
| --- | --- | --- |
| Serializer/unit | Exact bodies/types/omissions, nested Money, civil dates, enum rejection, nested identity, approved policy, bilingual messages | Test names and fixture/schema version |
| Database/service | Atomic transitions, constraints, revision changes, consent consumption, ledger invariants, immutable audit | Database engine/version and postcondition queries |
| API permissions | Every actor for collection/detail/action/attachment/operation lookup; real authentication path, validation and conflict codes | Status + sanitized response + unchanged DB for forbidden writes |
| Concurrency | Same key race; distinct keys same source; last slot/member; overlapping allocation; duplicate webhook/refund/billing | Separate connections, controlled barrier, exactly one effect |
| Provider sandbox | Signing, payment capture, reconciliation, refund and payout events; invalid signatures, retries, out-of-order events | Provider environment, event IDs redacted, event→resource correlation |
| Worker/storage | Outbox survives restart, scheduler catch-up, expiry, artifact generation, durable media after deploy | Job execution and queue/object evidence |
| Staging HTTP | Real reverse proxy/auth/routing/database/storage/worker integration across actors | Requests/responses, release SHA, timestamps and actor readback |
| Flutter local / later integration | Parser/body compatibility and recovery first; then real in-app journeys after backend return | Local command results now; device/live evidence in next phase |

DRF's `APIClient` and `APITransactionTestCase` support API tests against the test application. Its `RequestsClient` uses an in-process adapter, so naming a test “live” does not prove a deployed request. Use an actual network client such as `requests.Session` against the returned staging base URL for release evidence. Test authentication without `force_authenticate` in at least the auth/permission layer. [DRF testing](https://www.django-rest-framework.org/api-guide/testing/)

### 7.3 Mandatory test pattern for every mutation

Run: success; forbidden actor; unverified/expired session; missing/invalid fields; stale target revision; stale source revision; expired source; duplicate same key/same body; same key/changed body; response lost after commit; replay after subsequent unrelated updates; simultaneous requests; linked resource from another lease/account; counterpart reads; outbox/ledger exactly once. For a failed command, assert **no partial** allocation, invoice, approval, membership or journal effect.

Add explicit parser mismatch fixtures: wrong owner/tenant/invitation/property, changed room/bed/offer revision/price, wrong dates, missing required receipt, wrong key/subject/revision and unexpected status. A 200 with wrong facts must fail contract validation.

For each C01–C09 and S01–S03, record a test set ID, preconditions, actor, request, expected response, database postconditions, counterpart projection, job/provider evidence and cleanup policy. Preserve failed cases until a rerun identifies the fixing commit.

## 8. Configure, migrate and deploy safely

### 8.1 Preflight commands

Run these from the **actual backend checkout**, with that project's isolated test configuration. They are standard Django commands, not commands for this Flutter repository. Replace settings/module/test labels with the returned real names. Pin and report the versions already supported by the backend.

```bash
python --version
python -m django --version
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate --plan
python manage.py test <actual_cycle_test_package> --keepdb
python manage.py check --deploy --settings=<actual_production_settings_module>
```

If pytest is already installed/configured, use the project's existing pytest command instead of inventing a second test runner. Export machine-readable results through the project's configured reporter. Run race tests on the production database engine with separate connections. Never point destructive test setup at production data.

`check --deploy` checks deployment-sensitive settings; run it with the settings used by the deployed service. It does not test Sokoun cycles or prove providers/workers are healthy. Review HTTPS/proxy trust, hosts, `DEBUG`, secret handling, cookies, static/media separation, backups and logging in the context of the actual deployment. [Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)

### 8.2 Configuration checklist

| Area | Verify and return |
| --- | --- |
| Authentication | Installed auth/permission classes, access/refresh transport, expiry/rotation/revocation, cookie/CSRF behavior for the actual scheme. Do not assume Django means session auth or disable CSRF globally. |
| Locale/time | Default locale, `ar`/`en`, translation fallback, `Content-Language`, timezone/civil-date rules, DST behavior, aware instants |
| Database | Engine/version, transactions/isolation, constraints/indexes, connection limits, migration compatibility and tested restore |
| Jobs | Worker and scheduler commands, queues, retry/backoff/dead-letter policy, outbox dispatch, expiry, billing, provider reconciliation, alerts, document generation |
| Storage | Durable private evidence/documents, banner artwork lifetime, MIME/size/digest checks, signed URL TTL, object authorization, restart/deploy persistence |
| Providers | Sandbox/live identity, webhook endpoint ownership, signature verification, event dedup, timeouts, idempotency, reconciliation, secret manager configuration names |
| Feature gates | Build availability separately from server `enabled_capabilities`, `verified_services` and per-resource actions; verification bypass off for acceptance/release |
| Observability | Correlation/operation/resource IDs, actor-safe logs, status/revision, latency, queue lag, unresolved attempt age, overdue job, failed media and mismatch alerts; no tokens, raw private messages or payment credentials |

### 8.3 Migration and rollout sequence

1. Back up and verify restore on an isolated database. Inventory old rows and contradictions before backfilling. Preserve old financial/legal history.
2. Add backward-compatible fields/tables/indexes first; deploy code that tolerates old rows. Classify legacy records explicitly; do not infer signatures, possession or paid status from old generic flags.
3. Backfill in bounded resumable batches with audit counts. Detect duplicate invitations/allocations/payments and resolve them under approved policy before enabling stricter constraints. Never silently drop conflicting obligations.
4. Review `migrate --plan`, apply approved migrations through the deployment job, then run `migrate --check`. Verify all web/worker versions are schema-compatible. Perform static collection only as required by the project's deployment setup.
5. Deploy API/worker/scheduler/WebSocket components with capabilities still disabled for unverified families. Verify durable storage and job credentials from the deployed runtime.
6. Run real HTTP smoke and the backend cycle suite on isolated staging fixtures. Capture both actors and actual provider sandbox events. Confirm no duplicated effects on restart/retry.
7. Return the API contract, evidence and unresolved issues. Enable only independently passed capability families for a limited rollout; keep reconciliation/read access for existing pending operations available.
8. Monitor invariant violations and queue/provider/media failures. Define an operator and rollback trigger before rollout. Prefer disabling new writes and rolling forward schema-compatible code; do not reverse a migration that would erase operations, signatures or financial history. Reconcile existing pending work after rollback.

### 8.4 Deployment acceptance criteria

A successful deployment needs all of: correct release SHA exposed or otherwise correlated to requests; migrations applied; web and workers on compatible versions; real authenticated/guest endpoints resolve correctly; fresh scoped capabilities; counterpart reads agree; original media survives restart; outbox/jobs run; provider callbacks correlate; no unresolved P0 issues for enabled families; rollback/recovery procedure verified.

Do not mark C04–C06 complete from synthetic `paid=true`, seeded active rows, mocked webhooks alone or a checkout return page. Do not mark C08/C09 complete from route registration alone. An unsupported family is a documented disabled family, not a passed cycle.

## 9. Local mobile verification and next handoff

Use `make ownerTenantCyclesCheck FLUTTER=/path/to/flutter` in `apps/sokoun_app` to run the focused local contract/behavior suite with default-disabled planning gates and with the relevant planning gates enabled **only for fake-transport tests**. See the command definition in [the Makefile](../../apps/sokoun_app/Makefile). It performs no staging mutations and does not enable production services.

The focused suite covers agreement response identity/terms, legacy compatibility, planning parent scope/session changes, comparison selection, existing invitation/lease contracts, recovery and the documented sample payloads. The verification record is in the companion guide. This is not a claim that every backend cycle is deployed.

The next phase starts after the Django engineer returns the completed [contract return form](SOKOUN_OWNER_TENANT_API_CONTRACT_AND_RETURN.md#12-backend-return-form). We will validate its exact schemas, configure a dedicated test environment and actors, then implement/run integration journeys across both owner and tenant. Any schema deviation or missing provider/worker evidence remains explicit until tested.
