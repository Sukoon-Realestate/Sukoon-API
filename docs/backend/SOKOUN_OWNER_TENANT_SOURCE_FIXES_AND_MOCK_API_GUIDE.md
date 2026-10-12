# Sokoun owner–tenant cycles: source changes, mock API contract and verification

Date: 2026-10-12. Backend: `Sukoon-API/backend`. Mobile contract checked against the separate `darak-app/apps/sokoun_app` checkout.

**These are local source changes with automated verification. They have not been deployed to the shared server. Provider interactions are intentionally mocked, as requested. No external onboarding, signing or payment provider is required for this API test mode.**

This document supersedes earlier claims that seeded C04/C05/C06 rows or enabled capability flags prove completed cycles. It does not reopen previously resolved visit, banner-media, locale or refresh-route issues. Their regression tests remain included.

## 1. Implemented behavior

| Area | Behavior now enforced |
|---|---|
| Onboarding | Verified owner creates a session, then explicitly completes it through an authenticated mock API. Expired/replaced sessions cannot mark the profile ready. |
| Signing | Each participant completes their own session for the exact document and revision. Both signatures produce `signed`, a 48-hour payment hold, and the initial invoice. |
| Initial invoice | One invoice combines first-period rent and the agreed deposit. Deposit GET is a read; it cannot manufacture a second charge. |
| Activation | A matching full capture activates the lease and occupies the reserved inventory. Signing alone does not activate it. |
| Late capture | A capture after hold expiry remains recorded with its receipt/ledger and `activation_review_required`; it cannot reclaim released inventory or falsely activate a lease. |
| Inventory | Room/bed/whole-property overlaps are checked while holding a shared property lock. PostgreSQL concurrency tests cover competing room and bed reservations. |
| Payment recovery | An identical checkout key replays the original session. Lookup returns a complete, receipt-bound active session; completed attempts cannot return a payable session. |
| Rent versus deposit | The owner payable and 10% first-period commission use rent only. The deposit remains a separate liability within the combined payment. |
| Move-in/payout eligibility | Approval is persisted before eligibility is evaluated. Provider settlement and accepted move-in are independently required. Submitted/paid payables are not made eligible again. |
| Flutter contract | Public UUIDs, exact action tokens, session receipt identities, onboarding revision binding and canonical response envelopes match the actual Flutter request helpers. |
| Cancellation | Cancellation updates financial closure in the mutation transaction. Detail/aggregate GET ordering does not change stored lease state. Historical repair is an explicit command. |
| QA setup | The preparation command is additive, preserves passwords and existing financial/visit states, repairs missing offer terms with revision changes, and separates legacy from structured fixtures. |
| Planning | C08/C09, roommates, housing demand, commute and assistant routes now have persisted records, scoped permissions, command receipts and explicit deployment switches. |
| Funded exit | A current two-party settlement executes credits, deposit applications, adjustment invoices and refund instructions exactly once. Closure waits for actual mock refunds, owner payouts and recovery. |
| Partial refunds | Captured rent/deposit components are explicit. Flutter submits the allocation; Django prevents over-refunds and records commission reversal and owner recovery separately. |
| Legal end | An accepted termination updates the operative end date; workers end the lease when due while preserving possession and financial obligations. |

Apply `features.0010_alter_idempotencyrecord_operation`, `0011_settlement_execution_and_refund_allocations` and `0012_planning_cycles`. Migration 0011 permits several owner payables for one invoice while keeping one payable per captured attempt; deposit-funded settlement payables have unique source references. Migration 0012 creates the private planning models and constraints. Historical financial records are retained; these migrations do not manufacture payments or approvals.

## 2. Select mock mode explicitly

Use one of these settings modules:

- Developer environment: existing `config.settings.local` / `local_sqlite`.
- Automated SQLite tests: `config.settings.test`.
- Automated PostgreSQL tests: `config.settings.postgres_test`.
- Shared **isolated staging with API mocks**: new `config.settings.staging_mock`.

`config.settings.staging` keeps the provider unavailable. `staging_mock` opts into the fake provider and checkout, with `DEBUG=False`. Supply a private `RENTAL_PROVIDER_WEBHOOK_SECRET` through the deployment environment. A missing secret prevents staging mock startup. Production rejects the mock completion endpoints even if the fake-provider flag is mistakenly set.

`staging_mock` also explicitly enables all twelve planning services and mock commute estimates. Other settings keep planning disabled unless `PLANNING_ENABLED_SERVICES` names the desired services. The assistant is a deterministic catalog helper; it is not connected to an external AI provider.

Set `DJANGO_SETTINGS_MODULE=config.settings.staging_mock` consistently for the API, Celery workers, beat and management commands. Configure the intended staging database, allowed hosts and existing deployment secrets through the normal deployment environment. Do not point test settings at the production database.

The `https://fake-rental-provider.test/...` URLs are compatibility placeholders, not hosted websites. Complete mock steps using the API descriptors below. The Flutter contract tests validate response handling; they are not a device/WebView journey or a real provider certification.

## 3. Authentication, envelopes and retry rules

Normal requests use:

```http
Authorization: Bearer <current access token for the acting account>
Content-Type: application/json
Accept-Language: en
```

All paths below are relative to `/api/v1/features/v1/` unless the response already supplies an absolute API path. All IDs are public UUIDs. Read the current resource revision immediately before a new mutation.

Successful responses use:

```json
{
  "key": "success",
  "msg": "",
  "data": {
    "resource": {},
    "operation_receipt": {
      "id": "<receipt UUID>",
      "subject_id": "<returned resource UUID>",
      "request_key": "<same submitted UUID>",
      "revision": 1,
      "status": "confirmed"
    }
  }
}
```

GET projections are directly under `data`. Session-creation responses also retain their historical flat fields for existing clients. New clients should consume `data.resource` and `data.operation_receipt`.

For onboarding/signing/checkout **creation**, the receipt subject is the new session UUID. For a mock completion, it is the updated profile/lease/payment-attempt UUID. Onboarding session `revision` binds to the profile revision used to request it; `profile_revision` and the mock descriptor expose the updated pending-profile revision.

Persist the UUID `request_key` and exact body before sending. An uncertain response requires operation/session lookup or an identical replay. Do not replace a key to hide a timeout. Reusing a key with different content returns HTTP 409. A replay is the original result; use a fresh GET to see subsequent changes. An unrelated authenticated account receives 404 for a mock session it does not own. Anonymous mock completion receives 401. Invalid revisions/state return 409; unavailable account/provider operations return 403 or a hidden mock route returns 404.

## 4. API-only onboarding

As the owner:

1. `GET owner-payment-profile/`.
2. Check `GET rental-capabilities/?subject_id=<profile UUID>&action=onboard_beneficiary`.
3. `POST owner-payment-profile/onboarding-session/`:

```json
{
  "expected_revision": 1,
  "request_key": "<new UUID>",
  "accepted_policy_versions": ["rental-policy-v1"]
}
```

HTTP 201 includes a session and this descriptor:

```json
{
  "provider_mode": "mock",
  "mock_completion": {
    "method": "POST",
    "path": "/api/v1/features/v1/mock-provider/onboarding-sessions/<session UUID>/complete/",
    "expected_revision": 2
  }
}
```

POST to that exact path as the same owner:

```json
{"expected_revision": 2, "request_key": "<new completion UUID>"}
```

Use the descriptor's revision, not a hardcoded `2`. HTTP 200 returns the profile with `status:"ready"`, a masked beneficiary, and `provider_mode:"mock"`. Read the profile again. Mock readiness is simulated readiness, not real bank/KYC verification.

## 5. Agreement, signing, invoice and payment

The executable full request sequence is in `backend/core_apps/features/tests/test_rental_phase2.py::test_phase2_complete_interest_to_activation_flow`. Its `agreement_terms()` function supplies the complete accepted terms body, including dates, policy, deposit, billing anchor and fee allocation. Copy that structure and replace IDs, dates, rent and offer revisions with current server values.

Sequence:

1. Tenant creates `rental-interests/` for the selected property/offer/revision.
2. Owner creates `terms-proposals/`; tenant accepts the current proposal.
3. Owner creates `tenancy-invitations/` bound to that proposal; tenant accepts.
4. Owner creates `leases/` bound to the accepted invitation and exact offer terms.
5. Both parties POST `leases/<lease UUID>/review/` with `decision:"accept_review"`, a fresh revision and a distinct request key.
6. Owner POSTs `leases/<lease UUID>/submit-for-signature/` with `decision:"submit_for_signature"`.
7. Each party POSTs `leases/<lease UUID>/signing-session/`:

```json
{
  "document_id": "<current document UUID>",
  "document_hash": "<current SHA-256>",
  "expected_revision": 4,
  "request_key": "<new UUID>"
}
```

8. Each party completes **their own** session using its `mock_completion.path`, with the descriptor's `expected_revision` and a new completion key. Route: `mock-provider/signing-sessions/<session UUID>/complete/`.
9. Read the lease and invoice. After the second signature expect `lease_status:"signed"`, `occupancy_status:"not_started"`, a 48-hour hold and one initial invoice. It must not be active yet.

Example agreed amounts: monthly rent `1000000` minor EGP plus deposit `1000000` produce an initial charge of `2000000` minor EGP. With exponent 2 these mean 10,000 + 10,000 = 20,000 EGP. Invoice lines are `base_rent` and `security_deposit`. The deposit projection references that same invoice.

As tenant, `POST rent-invoices/<invoice UUID>/quote/`:

```json
{"decision": "quote", "expected_revision": 1, "request_key": "<new quote UUID>"}
```

Use the returned `quote_id`; `POST rent-invoices/<invoice UUID>/checkout/`:

```json
{
  "invoice_id": "<invoice UUID>",
  "quote_id": "<returned quote UUID>",
  "expected_revision": 1,
  "request_key": "<new checkout UUID>"
}
```

HTTP 201 contains `session_id`, `payment_attempt_id`, invoice/quote identity, server amount, expiry, navigation rules, mock descriptor and canonical receipt. Keep this operation identity.

To simulate capture, POST as the payer to `mock-provider/payment-attempts/<attempt UUID>/events/`:

```json
{"event": "captured", "expected_revision": 1, "request_key": "<new event UUID>"}
```

The server supplies amount/currency from the attempt. The caller must not calculate a payment amount or send a provider secret. Read the returned attempt revision and use it for the next event:

```json
{"event": "settled", "expected_revision": 2, "request_key": "<new settlement event UUID>"}
```

Supported event names are `captured`, `settled` and `failed`. Values `1` and `2` above are examples, not assumptions about an existing attempt. A settlement event received before capture remains pending and is reconciled when capture arrives.

After capture, verify the lease, invoice, receipt, deposit and owner-payables projections. With the amounts above: owner gross = 1,000,000; commission = 100,000; owner net = 900,000; deposit liability = 1,000,000. Move-in approval is a separate step. Provider settlement alone is not occupancy or permission to pay the owner.

Recovery:

```text
GET payment-attempts/?invoice_id=<invoice UUID>&request_key=<original checkout UUID>
GET payment-attempts/<attempt UUID>/
GET rental-operations/<original request UUID>/?subject_id=<original request subject UUID>
```

Do not recreate checkout when an attempt already exists. A recoverable active session includes all original bindings and its operation receipt ID. Once the attempt is captured, it no longer returns a payable active session.

Change-agreement signing also supports `mock-provider/change-signing-sessions/<session UUID>/complete/`, with the same actor/revision/idempotency requirements.

## 6. Handover, maintenance and cancellation checks

Create a move-in only after activation. The full integration test submits:

```json
{
  "kind": "move_in",
  "possession_on": "<agreed YYYY-MM-DD>",
  "condition": {"summary": "good"},
  "keys": {"count": 2},
  "meters": {},
  "inventory": [],
  "evidence_ids": [],
  "expected_revision": 0,
  "request_key": "<new UUID>"
}
```

POST to `leases/<lease UUID>/handovers/`. Both participants POST `handovers/<handover UUID>/respond/` with `decision:"accept"` and the newly returned revision. An accepted handover cannot be edited back into a pending state. Read lease occupancy and owner-payable eligibility after both approvals.

Maintenance is verified in the same API-created tenancy: create → acknowledge → start work → report resolved → tenant confirms resolved. Capability discovery and detail responses use the same action names. Additional tests cover appointments, exact cost versions, amendments, extensions, external claims and operations-role restrictions.

For a cancellable draft, Flutter may send:

```json
{"decision": "cancel_draft", "expected_revision": 1, "request_key": "<new UUID>", "note": "QA cancellation"}
```

POST to `leases/<lease UUID>/cancel/`. The historical `revision` body remains supported. Verify cancellation response, exact replay, detail and rental-center reads in different orders. A clean never-occupied cancellation closes only when no financial blockers remain. A pending payment must prevent closure even if its invoice was cancelled.

## 7. Prepare staging accounts and fixtures safely

Continue using the established owner and tenant identities. Do not change their emails/passwords or replace them with new seed identities to match example data. The command verifies/enables the ordinary QA actors and listing ownership under explicit nonproduction settings. It refuses staff/superuser identities as ordinary QA actors and does not grant financial operations roles to the owner or tenant.

After migration, run against the intended staging database:

```bash
python manage.py prepare_owner_tenant_cycle_qa \
  --settings=config.settings.staging_mock \
  --output=/private/new-cycle-manifest.json
```

Use a fresh output path. Existing output files are refused. Preserve the old operation journal and exact request bodies. Existing cancelled/rejected visits and financial rows are retained; consumed or ineligible sources are not silently reset. The manifest supplies a separate legacy invitation property/source and the actual structured offer/revision/price when available. Do not submit an offer-less legacy body for a structured property.

For a fresh database, seed actors have unusable passwords until credentials are provisioned privately. The manifest's `has_password` is not proof of successful authentication. Prove identity through the normal current-user endpoint before shared-server tests. No credentials are stored in this document.

Operations tests use separate test staff identities with `PAYOUT_OPERATOR`, `REFUND_OPERATOR`/`FINANCIAL_APPROVER`, and `DISPUTE_RESOLVER` as appropriate. Provision those only if testing the corresponding operations endpoints; ordinary parties must continue receiving 403 there.

Historical clean cancellation repair is explicit:

```bash
python manage.py reconcile_cancelled_rental_closure --settings=config.settings.staging_mock
python manage.py reconcile_cancelled_rental_closure --settings=config.settings.staging_mock --lease-id=<UUID> --apply
```

Review the first command's dry-run output, then apply to the intended lease(s). The command preserves invoice amounts, receipts and unrelated states. It does not force funded or blocked rentals closed.

## 8. Planning routes and current request contracts

Every private route requires a verified, active user, its enabled planning service, and access to the particular resource. Check `GET planning-capabilities/?capability=<service>&action=<action>&subject_id=<UUID>` for the acting account. The server returns only supported, currently authorized actions. A capability response is short-lived; it is not permission to bypass checks on the mutation itself.

The configured service names are:

```text
lifestyle,roommates,housing_groups,group_visits,group_applications,housing_requests,housing_offers,condition_reports,move_out_notices,replacements,commute,tenant_assistant
```

All creates carry `expected_revision:0` and a new UUID `request_key`. Updates carry the current resource revision. Where present, `roster_revision`, `request_revision`, `candidate_revision`, `offer_revision` and baseline revisions are independently checked. Dates are civil `YYYY-MM-DD` dates. Send explicit monetary currency/exponent; all financial amounts and group contributions use integer minor EGP, not decimal pounds.

| Method and route | Actor and important fields | Result / invariant |
|---|---|---|
| GET/POST `lifestyle-profile/` | Self; `discoverable`, `habits`, `preferences`, `disclosed` | Only opted-in, explicitly disclosed information appears to other tenants. |
| GET `roommate-candidates/`, `roommate-connections/` | Verified user | Private candidate/connection pages, no hidden habits or email fallback. |
| POST `roommate-candidates/<id>/request/` | Requester; `candidate_revision`, `decision:"request"`, optional `note` | Creates a pending connection. |
| POST `roommate-connections/<id>/<action>/` | Authorized participant; `decision` matches action | `accept`, `decline`, `withdraw`, `block`; accepted mutual consent controls chat sending through REST and WebSocket. |
| GET/POST `housing-groups/`; GET `housing-groups/<id>/` | Member; creation has `name`, `visibility:"invite_only"`, `capacity`, `criteria`, `roster_revision:0`, `action:"create"`, `consent:false` | Private membership and roster revisions. Unrelated users receive 404. |
| POST `housing-groups/<id>/invitations/` | Admin; `group_id`, `group_revision` | Signed, expiring invitation token. Share its returned link; do not log the token. |
| POST `group-invitations/preview/` | Invitee; `token` | Redacted preview; does not join the group. |
| POST `group-invitations/join/` | Invitee; token, `group_id`, `group_revision`, current `expected_revision` | Capacity enforced under locking; duplicate key replays the original join. |
| POST `housing-groups/<id>/<action>/` | Follow `allowed_actions`; current group/roster revisions | Group lifecycle, shortlist, cost proposals, member consent, visits and applications. |
| GET/POST `housing-requests/`; GET `housing-requests/<id>/` | Request author | Persists criteria and state. |
| GET `housing-demand/` | Owner with verified ownership of a published property in the requested city | Scoped eligible demand; not a public tenant directory. |
| POST `housing-requests/<id>/<action>/` | Author | `edit`, `pause`, `publish`, `close`, `fulfill`; criteria changes invalidate older offers. |
| GET/POST `housing-requests/<id>/offers/` | Request author reads; eligible owner creates | Submitted selection is checked against the owner's current offer, request criteria and current prices. |
| POST `housing-offers/<id>/<action>/` | Request author/offer owner as allowed | `shortlist`, `decline`, `withdraw`. Shortlisting does not sign a lease. |
| GET `leases/<id>/condition-report-context/` | Lease participant | Canonical accommodation, report items and move-in baseline. |
| GET/POST `leases/<id>/condition-reports/` | Lease participant | Report for `move_in` or `move_out`, separate from legal possession handover. |
| GET `condition-reports/<id>/`; POST `condition-reports/<id>/<action>/` | Participant | `submit` (including revision after objection), `acknowledge`, `object`, `finalize`; current content and baseline must match. Final reports are immutable. |
| GET/POST `leases/<id>/move-out-notices/` | Participant; author submits | Receipt/acknowledgement does not end the agreement or return possession. |
| GET/POST `leases/<id>/replacement-requests/` | Outgoing lease participant | Replacement planning is separate from the incoming agreement. |
| GET `leases/<id>/replacement-candidates/` | Owner; outgoing tenant receives consented candidates only | Uses existing authorized rental interests, not an unrestricted user search. |
| GET `replacement-invitations/` | Incoming candidate | Minimal private nomination, without the outgoing tenant's reason or financial information. |
| POST `replacement-requests/<id>/candidate-consent/` | Incoming candidate only | Explicit `accept`/`decline`, current revision and exact replay. |
| POST `replacement-requests/<id>/<action>/` | Owner/outgoing tenant as allowed | `nominate`, `approve_candidate`, `approve_availability`, `withdraw`, `decline`, `cancel`; owner approval cannot replace incoming consent. |
| POST `commute-searches/`; GET `commute-searches/<id>/results/` | Search author only | One or two destinations, explicit mode/time/timezone, every hard limit evaluated before pagination. |
| POST `tenant-assistant/turns/` | Turn author | Grounded public catalog matches and non-mutating suggestions. No automatic booking, application or payment. |

### Housing criteria and authoritative offers

Example `POST housing-requests/` body (replace placeholders and dates with actual current values):

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 0,
  "action": "publish",
  "title": "Shared apartment",
  "criteria": {
    "city_id": "<catalog city UUID>",
    "district_ids": [],
    "property_type": "<catalog property type slug>",
    "rental_scope": "entire_property",
    "budget_min": {"amount_minor": 100000, "currency": "EGP", "exponent": 2},
    "budget_max": {"amount_minor": 2000000, "currency": "EGP", "exponent": 2},
    "price_period": "monthly",
    "start_on": "<future YYYY-MM-DD>",
    "end_on": null,
    "people": 2,
    "amenities": [],
    "furnished": null
  }
}
```

The owner posts `request_id`, `request_revision`, `selection`, optional `note`, `expected_revision:0` and a request key to its `/offers/` route. `selection` is the server's current rental selection: `property_id`, `offer_id`, `offer_revision`, `rental_scope`, room/bed identifiers and names, capacity, bathroom access, and `terms`. Copy that snapshot; do not fabricate its rent/deposit or normalize a monthly price into another period. Flutter's serialized examples in `flutter-request-bodies.json` are replayed against Django during verification.

HTTP 201 returns the command envelope. An offer resource contains the accepted selection, server-priced money, request binding, revision, status and actions. A forged price or incompatible city/scope/capacity/budget fails without creating an offer.

### C08: group consent must remain current

After joining, add the current selection with `add_shortlist`. Submit `propose_costs` with a `proposal` object:

```json
{
  "id": "",
  "revision": 0,
  "roster_revision": 2,
  "offer_id": "<offer UUID>",
  "offer_revision": 2,
  "start_on": "<future YYYY-MM-DD>",
  "end_on": "",
  "period": "monthly",
  "total": {"amount_minor": 1000000, "currency": "EGP", "exponent": 2},
  "contributions": {"<member A UUID>": 600000, "<member B UUID>": 400000}
}
```

Wrap it in the normal command body with `action:"propose_costs"`, current group/roster revisions and `consent:false`. The total must match the server price and contributions must cover the current roster exactly. Each member separately sends `approve_costs` for the current `item_id`/`item_revision` with `consent:true`.

`request_visit` includes the selection, selected `participant_ids` and `appointment_at`; each participant sends `consent_visit`. Only complete current consent creates the real owner-visible visit. `apply` and `consent_application` likewise create a real rental interest only after every participant has consented to the current roster, selection and costs. Group consent is not a substitute for each later agreement/signature requirement.

A roster, shortlist or cost change invalidates old consent and withdraws the corresponding unfinished process. A member cannot approve on another member's behalf. A departed member may recover their own leave receipt, but cannot fetch the remaining group's private data. Repeated/concurrent join requests cannot exceed capacity.

### C09: condition reports, notice and replacement

Create a report from `condition-report-context/`, preserving the returned selection and stable item IDs. Required report fields are `lease_id`, `kind`, `inspected_on`, `selection`, `items`, `baseline_id`, `baseline_revision`, `evidence_ids`, `action:"submit"`, request key and revision zero. Every item uses `id`, `space`, `label`, `kind`, `condition`, `note`, `reading`, `unit`, `quantity`, `evidence_ids`. Empty strings and null quantity are accepted exactly as Flutter serializes them. Evidence must belong to that lease and have a safe scan status.

The other party acknowledges the identical current content with a new key/current revision. An objection clears approval; the changed version requires new acknowledgement. Finalizing a report cannot charge money or return possession. Complete the actual `/handovers/` cycle separately.

A notice request is:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 0,
  "lease_id": "<outgoing lease UUID>",
  "kind": "moveOutNotice",
  "action": "submit",
  "requested_on": "<YYYY-MM-DD>",
  "reason": "Leaving after this agreement"
}
```

The owner acknowledges using the current transition revision. Early legal termination still requires the two-party `termination-requests/` cycle. The notice becomes effective only when its date has arrived, the legal lease has ended and possession has been returned.

For replacement use `kind:"replacement"`. The owner nominates a current rental-interest candidate with `candidate_id` and `candidate_revision`. The incoming tenant opens **Tenant Home → Replacement invitations** and submits:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 2,
  "decision": "accept",
  "note": "I agree to be considered for this accommodation"
}
```

`POST replacement-requests/<id>/candidate-consent/` returns HTTP 200 and a receipt-bound resource with `status:"candidate_consented"`. `decline` returns `status:"declined"`. The nomination revision above is only an example. Capability action names are `accept_candidate_nomination` and `decline_candidate_nomination`; the resource's button permissions are `accept` and `decline`.

Then the owner separately approves the candidate and future availability. The incoming tenant must still complete a separate invitation, agreement, signatures and capture. The replacement cannot become `effective` until that incoming lease is `active`, the outgoing lease has ended, possession is returned and the effective date has arrived. Candidate consent alone creates no tenancy, charge or transfer of liability. The incoming lease is bound through its invitation to the nominated interest. Normal proposal/invitation revision increases do not invalidate already approved nomination consent; a withdrawn/rejected interest or an unrelated lease cannot complete the replacement.

### Commute and assistant boundaries

Example `POST commute-searches/`:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 0,
  "destinations": [{
    "label": "Work",
    "location": {"latitude": 30.04, "longitude": 31.23},
    "mode": "walking",
    "limit_minutes": 60
  }],
  "local_time": "<future YYYY-MM-DDTHH:MM>",
  "time_kind": "arrive_by",
  "timezone": "Africa/Cairo",
  "balance": false,
  "hard_limits": true,
  "filters": {"city": "<city UUID>", "price_max": "15000", "price_period": "monthly"}
}
```

Price filters use catalog query units (decimal pounds) plus an explicit `price_period`; this differs from financial mutation money. The result says `provider:"mock_haversine"` in mock mode and `coverage:"full_catalog"` because filtering evaluates the eligible catalog before pagination. It is a labeled distance-based simulation, not traffic data. Missing coordinates/provider estimates are unknown, never zero-minute results. With hard limits they are excluded and counted. Private coordinates/results expire and are purged by the closure worker.

Example `POST tenant-assistant/turns/`:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 0,
  "session_id": "<account-scoped session identity>",
  "previous_turn_id": "",
  "language": "en",
  "text": "An apartment in Cairo below 15000 EGP monthly",
  "retain_history": false
}
```

Suggestions reference actual visible catalog IDs. Unsupported requirements remain unresolved. A budget without an explicit daily/weekly/monthly/yearly period is not silently interpreted as monthly. Raw prompts are not retained; the private reply expires after 24 hours. An expired receipt keeps its operation identity but cannot restore purged private data (HTTP 410).

## 9. Funded C06 and partial combined refunds

### Partial refund request and execution

`GET payment-attempts/<id>/` now includes:

```json
{
  "refundable_allocations": {"rent": 1000000, "deposit": 1000000},
  "allowed_actions": ["request_refund"]
}
```

These are example fields from the full resource, not the entire response. Only the payer receives the request action. Existing reservations, prior refunds and applied/returned deposits reduce the available components. The Flutter payment details form shows separate rent/deposit fields for a combined capture.

`POST refund-requests/` as that payer:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 0,
  "lease_id": "<lease UUID>",
  "payment_attempt_id": "<captured attempt UUID>",
  "payment_revision": 3,
  "amount": {"amount_minor": 500000, "currency": "EGP", "exponent": 2},
  "allocations": {"rent": 200000, "deposit": 300000},
  "reason": "Agreed partial refund"
}
```

HTTP 201 returns `status:"requested"`, that same allocation, the refund's UUID/revision and a canonical operation receipt. Recover creation using `GET rental-operations/<request_key>/?subject_id=<payment-attempt UUID>`. The command subject is the original payment attempt; the receipt result identifies the new refund.

Allocation entries must be nonnegative integers whose sum equals `amount.amount_minor`. At least one component must be positive; neither may exceed its unreserved captured balance. Missing allocation for a partial mixed capture gives 409 `refund_allocation_required`; invalid types/totals give 400; excessive or concurrently reserved components give 409 `refund_exceeds_balance`. An identical key/body does not reserve funds twice.

A dedicated refund operator approves via `POST refund-requests/<id>/respond/` with `action:"approve"`, its current revision and a new key. Execute the approved refund through the closure worker or `POST refund-requests/<id>/execute/` with `action:"execute"`, current revision and a new key. The result reaches `status:"succeeded"` after the mock provider confirms; the invoice, deposit and ledger are updated once.

A payment reversal restores the corresponding invoice debt; it is not a waiver. The invoice exposes repayment only when the server permits it. A repayment creates a distinct payment allocation/payable rather than duplicating the original owner income. Deposit-only repayment cannot become rent income.

For refunded rent already paid to an owner, the paid payout remains immutable. The refund records `owner_recovery_minor`; closure stays open until recovery. In explicit mock mode, the authorized operator can use the same `/execute/` route with:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 4,
  "action": "confirm_owner_recovery",
  "amount": {"amount_minor": 180000, "currency": "EGP", "exponent": 2}
}
```

Use the exact current unrecovered amount; `180000` illustrates refunding 200000 rent with 20000 commission reversal. This is a mock accounting confirmation, not evidence of an external bank recovery. A rent refund during an in-flight owner payout waits for payout reconciliation.

### Versioned settlement execution

Prerequisites: legal lease `ended`/`cancelled`, possession `returned`/`not_started`, no open dispute and no unreconciled payment/refund. GET `leases/<id>/final-settlement/` before proposing.

`POST leases/<id>/final-settlement/propose/`:

```json
{
  "request_key": "<new UUID>",
  "expected_revision": 1,
  "lines": [{
    "type": "deposit_deduction",
    "description": "Agreed damaged key",
    "amount": {"amount_minor": 200000, "currency": "EGP", "exponent": 2},
    "evidence_ids": []
  }]
}
```

Supported charge types are `rent`, `utility`, `claim`, `deposit_deduction`, `damage`, `cleaning`, `utilities`, `rent_adjustment`; explicit `credit`, `write_off`, `deposit_return` and `refund` are also supported. Credits apply to invoice debt; refund instructions require actual unrefunded captures. Use a specific `invoice_id` when targeting a particular debt. A supplied deposit-return total must agree with the executable plan; excess is rejected.

The proposer accepts their submitted revision. The other party sends `POST .../final-settlement/respond/` with `action:"accept"`, the proposal revision and a new key. A changed invoice/payment/refund/deposit/payable/dispute invalidates the old financial snapshot; refresh and propose the updated figures for both parties to review. A disputed settlement can be revised; an accepted executed settlement cannot be silently rewritten.

The acceptance resource exposes `status:"accepted"`, `execution_status:"executed"`, `execution_plan`, `executed_at`, balances and history. Here **executed means the agreed ledger plan and payment instructions were committed**, not that every provider operation and payout has finished. The worker executes the reserved settlement refunds. Outstanding adjustment debt can be quoted/paid through the existing rent invoice routes. Closure remains open for pending refunds, owner payables/recoveries, unresolved deposit, invoices, possession or disputes.

Verified example (all integer minor EGP):

| Event | Expected amount/state |
|---|---|
| Original captured rent + deposit | 1000000 + 1000000 |
| Agreed exit deduction | 200000 from held deposit |
| Deposit refund | 800000 to the original payer/capture |
| Owner payable from rent | 900000 after first-period commission |
| Separate payable funded by deposit deduction | 200000; no second acquisition commission |
| Total owner payout | 1100000 |
| Final state after refund and payout reconciliation | `ended`, `returned`, `financial_closure_status:"closed"` |

Uncollected deposit debt is released at exit, not credited as owner income. Paid invoices, ledger history and prior payout records are preserved. Debits must equal credits per ledger transaction; identical settlement acceptance and concurrent workers cannot duplicate an adjustment, refund or payable.

## 10. Local verification and repeatable commands

Final results and filenames are listed below. Evidence is in `Sukoon-API/docs/qa/owner-tenant-remaining-verification/`. Older evidence directories are historical runs.

| Check | Result | Evidence |
|---|---|---|
| Full backend, SQLite | **652 passed, 14 skipped, 0 failed** | `backend-sqlite.log`, `.xml` |
| Full backend, PostgreSQL | **663 passed, 3 skipped, 0 failed** | `backend-postgres.log`, `.xml` |
| Remaining-cycle PostgreSQL cases including HTTP and races | **30 passed** (included in full suite) | `remaining-cycles.log`, `.xml`, `full-http-cycle.json` |
| Actual Flutter JSON request bodies accepted by Django | **8 passed** (included in full suite) | `flutter-request-roundtrip.log`, `.xml`, `flutter-request-bodies.json` |
| New finance tests and Django responses through actual Flutter helpers | **13 passed** | `flutter-remaining-contract.log` |
| New replacement UI/access checks plus architecture | **14 passed, 1 opposite-mode skip** | `flutter-replacement-widgets.log` |
| Full Flutter app | **3988 passed, 42 opt-in/mode skips, 0 failed** | `flutter-full.log` |
| Enabled planning contracts, UI and architecture | **75 passed, 5 opposite-mode skips, 0 failed** | `flutter-planning-enabled.log` |
| Original Django onboarding/signing/payment contract through Flutter | **4 passed** | `flutter-initial-contract.log` |
| Scoped Flutter analysis | **No issues** | `flutter-analysis.log` |
| Fresh PostgreSQL migrate through 0012, consistency and system checks | **Passed, no model changes missing migrations** | `migration-checks.log` |
| Critical Python lint and whitespace | **Passed** | `source-checks.log` |

Eleven SQLite skips require PostgreSQL row locks or the real HTTP PostgreSQL journey; those cases passed on PostgreSQL. Three pre-existing visit-policy tests remain explicitly skipped in both databases: duplicate slot booking, unconfigured-slot rejection, and duplicate visit service rejection. This release does not silently change that separate visit policy. Normal dependency/test warnings include Django deprecations, the test static-files directory and an existing naive-datetime fixture. Do not report skipped tests as passed.

The default Flutter run intentionally skips opt-in live tests, fresh-artifact contract tests and enabled-feature branches. Dedicated targets above exercise the relevant contract/enabled branches. Shared-server/device tests are still a deployment acceptance step.

The full HTTP test uses actual JWT login and HTTP requests over a loopback Django server backed by PostgreSQL. Onboarding → interest → proposal → invitation → lease review → both mock signatures → combined capture/settlement → move-in → maintenance → agreed termination → move-out → funded settlement → deposit refund → owner payout → financial closure all execute. Time is advanced inside the test to reach the agreed termination date. The C09 replacement test also creates the incoming proposal, invitation and lease, reviews it, completes both signatures and captures its invoice through actual API handlers before checking effective replacement; it does not seed an active incoming lease as proof of completion. Workers are invoked synchronously in tests; this does not prove the deployed Celery scheduler is running.

Run from a disposable test environment with PostgreSQL permission to create/drop its test database. Tests do not use the shared staging actors or production database. Dependencies used locally: Python 3.11.17, Django 4.2.11, PostgreSQL 16, Flutter 3.44.7 / Dart 3.12.2.

```bash
cd /path/to/Sukoon-API/backend
export TEST_POSTGRES_DB=sokoun_cycle_qa
export TEST_POSTGRES_USER=<test database role>
export TEST_POSTGRES_HOST=127.0.0.1
export TEST_POSTGRES_PORT=<test PostgreSQL port>
export CYCLE_EVIDENCE=../docs/qa/owner-tenant-remaining-verification
make check-owner-tenant
make test-remaining-cycles
```

Immediately validate the freshly generated responses in the actual Flutter checkout (capability grants/quotes expire):

```bash
cd /path/to/darak-app/apps/sokoun_app
make test-django-remaining-contract \
  FLUTTER=/path/to/flutter/bin/flutter \
  DJANGO_REMAINING=/path/to/Sukoon-API/docs/qa/owner-tenant-remaining-verification
make test-django-contract \
  FLUTTER=/path/to/flutter/bin/flutter \
  DJANGO_CONTRACT=/path/to/Sukoon-API/docs/qa/owner-tenant-remaining-verification/django-cycle-contract.json
```

This checks real Django-produced envelopes through actual Flutter helpers. The first target also writes `flutter-request-bodies.json` using actual Flutter DTO serialization. Then replay those bodies against freshly authorized Django fixtures:

```bash
cd /path/to/Sukoon-API/backend
make test-flutter-request-bodies
export SOKOUN_FLUTTER_REQUEST_BODIES=/path/to/Sukoon-API/docs/qa/owner-tenant-remaining-verification/flutter-request-bodies.json
.venv/bin/python -m pytest --ds=config.settings.postgres_test
.venv/bin/python -m pytest --ds=config.settings.test
```

Only fixture UUIDs/current revisions are rebound in the reverse-contract tests; terms, enums, money, nullable/default fields and body structure remain Flutter's actual output. No credentials or JWTs are written to the evidence artifacts. Artifact grants are test data, not reusable staging authorization.

The Flutter suite also covers default-disabled behavior. For enabled planning UI/contract tests use `make test-planning-cycles` in the app, with `FLUTTER` set to the SDK path. For release builds set only the reviewed `SOKOUN_*` switches corresponding to enabled services. The Make target's `PLANNING_TEST_FLAGS` lists the twelve names. Retain the app's existing signing, checkout, billing and settlement switches and verified-account gates; these switches do not override backend authorization.

## 11. Backend deployment and test enablement — remaining team actions

**The requested source work is implemented locally. The backend team will deploy it after review. No shared-server deployment was performed in this task.** Do the following on the intended isolated mock staging environment:

1. Include the changed source and all new modules, migrations and settings in the reviewed release commit from `Sukoon-API` (local untracked files must not be omitted). Back up the target database and record the exact release/commit being deployed. Preserve existing financial records and operation journals.
2. Install the locked dependencies. Configure `DJANGO_SETTINGS_MODULE=config.settings.staging_mock`, database/environment secrets, explicit allowed hosts, Redis/Celery connectivity and a private `RENTAL_PROVIDER_WEBHOOK_SECRET`. API, worker, beat and management commands must use the same release/settings. This module explicitly enables API mocks and all twelve planning services.
3. Run `python manage.py check`, `makemigrations --check --dry-run`, `migrate --plan`, `migrate --noinput`, `migrate --check`, and `showmigrations features` with those settings. Confirm migrations 0010, 0011 and 0012 are applied before serving new code. Run the deployment's `check --deploy` and resolve environment-specific findings, then `collectstatic --noinput`. Do not reverse migration 0011 after several payables exist for an invoice or shrink migration 0010 while long operation names exist.
4. Restart API and Celery workers and run one beat scheduler using the existing process manager. Verify the scheduled tasks below are registered and actually executing. A successful API response alone cannot validate workers.
5. Run `prepare_owner_tenant_cycle_qa` as shown in section 7, preserving the established ordinary owner/tenant accounts and passwords. Privately provision login credentials for newly created QA actors; test normal login/current-user for every account that will act. The fixture manifest explicitly does not certify full cycle success.
6. Ensure ordinary actors are active and verified, the owner really owns the selected published/verified property, `is_ownership_verified` is true, and its current structured offer/terms/capacity/dates support the requested scope. Complete the owner's mock beneficiary onboarding through the API. Create a fresh eligible visit/interest where needed rather than resetting a consumed financial or legal record.
7. **Provision separate operations users directly** for the test: an active `StaffProfile` with `PAYOUT_OPERATOR`, and another with `REFUND_OPERATOR` (or `FINANCIAL_APPROVER`). Add `DISPUTE_RESOLVER` only for dispute-resolution checks. Do not promote the ordinary owner/tenant. Set credentials privately and verify each role through its normal authenticated endpoint; a role label in a manifest is insufficient.
8. Run the authenticated API sequences in sections 4–9 through the staging public URL, with the real intended owner, tenant, incoming replacement tenant and separate operator identities. For negative tests use the second ordinary owner/tenant. Capture current revisions and reuse the exact same key/body on uncertain responses.
9. Check fresh reads from both parties after each transition. Prove one capture allocation per attempt, balanced ledgers, deposit conservation, exact refund splits, commission reversal, immutable completed payout and one command receipt per repeated request. Verify the final three independent states (`ended`, `returned`, `closed`). Run permissions, stale revision, changed-body replay, expired invitation/report/search and competing-request checks.
10. Enable the matching reviewed Flutter build switches and run the device/app journey against that deployed API. Mock provider URLs are placeholders: complete provider steps by their authenticated API descriptors. Record release ID, migration state, settings mode, worker status, UTC run time and sanitized results; return the result to the mobile team.

For direct operations-role provisioning, the backend team can use the Django shell under staging settings with existing dedicated operations user UUIDs:

```python
from django.conf import settings
from django.db import transaction
from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import User

assert settings.RENTAL_RUNTIME_ENVIRONMENT == "staging"
roles = {
    "<dedicated payout operator UUID>": StaffProfile.RoleName.PAYOUT_OPERATOR,
    "<dedicated refund operator UUID>": StaffProfile.RoleName.REFUND_OPERATOR,
}
with transaction.atomic():
    for public_id, role in roles.items():
        user = User.objects.select_for_update().get(id=public_id)
        # These must be dedicated operations identities, not rental participants.
        user.is_active = True
        user.is_verified = True
        user.save(update_fields=["is_active", "is_verified"])
        StaffProfile.objects.update_or_create(
            user=user, defaults={"role_name": role, "is_active": True}
        )
```

Required beat jobs (all every 300 seconds except evidence scanning at 60 seconds):

- `expire_rental_sources_and_holds`
- `reconcile_rental_provider_sessions`
- `run_rental_billing_cycle`
- `reconcile_ambiguous_rental_payments`
- `scan_rental_evidence`
- `reconcile_approved_payouts`
- `process_rental_changes`
- `process_rental_closure` (includes due legal endings, approved refunds, settlement documents, closure, transition projections and private discovery-data expiry)

These task names live in `core_apps.features.tasks` and are configured in `config/settings/base.py`. Use the deployment's real worker logs/task results to verify delivery. The tests exercise their task functions locally and cannot verify deployed Redis, processes, TLS, routing or device behavior.

There are no remaining unimplemented items from the requested planning/funded-settlement/partial-refund scope identified by these local checks. Passing tests are evidence for the covered scenarios, not a guarantee that every possible defect or deployment issue is absent. Real external providers remain outside the explicitly requested API-mock scope.
