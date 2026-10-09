# Mobile handoff — end-to-end rental backend

Date: 2026-10-09  
API base: existing `/api/v1/`; paths below are relative to it.

## Current integration status

Phases 1–6 are implemented and verified locally. The complete rental lifecycle is modeled from interest through closure/reopening. All external integrations are deterministic development/test fakes, so production build gates must remain disabled until the listed operational prerequisites are complete.

| Contract area | Status | Mobile action |
| --- | --- | --- |
| Fresh capabilities | Implemented locally | Integrate and honor absent capabilities/actions |
| Operation recovery | Implemented locally for newly recorded current rental operations | Keep unknown intentions protected; never treat `unknown` as safe to retry |
| Separate lease/occupancy/closure fields | Implemented on current lease reads | Parse unknown values defensively |
| Extended invoice revision/status/balance permissions | Implemented locally | Integrate defensively |
| Legacy tenancy invitations | Preserved | Existing integration remains compatible |
| Owner readiness and policy | Implemented locally with fake hosted provider | Integrate DTOs; do not enable in production |
| Interest → terms → invitation v2 | Implemented locally | New bodies use canonical mutation envelopes |
| Agreement review/sign/activation | Implemented locally with fake document/signature provider | Use only in local/test environments |
| Secure quote/attempt/PSP checkout | Implemented with fake PSP locally/tests | Keep production `SOKOUN_RENT_CHECKOUT` false |
| Evidence, handovers, deposits, payouts | Implemented with fake storage/scanner/payout locally/tests | Keep production gates false |
| Maintenance and tenancy changes | Implemented locally with fake signatures | Keep production gates false |
| Settlement, refunds, disputes, documents, closure | Implemented locally with fake providers | Keep production gates false |

## Implemented endpoints

### Capability discovery

`GET features/v1/rental-capabilities/?subject_id={uuid}&action={optional_action}`

Example response envelope:

```json
{
  "key": "success",
  "msg": "",
  "data": {
    "account_id": "account-uuid",
    "account_verified": true,
    "enabled_capabilities": ["rental_interests", "rental_agreements"],
    "policy_version": "rental-policy-v1",
    "allowed_actions": [],
    "blocking_reasons": ["The requested rental action is not available yet."]
  }
}
```

The subject must be the authenticated account or a rental resource/property in which that account participates. Unrelated and unknown subjects return 404. This read is fresh and returns `Cache-Control: private, no-store`.

In local/test settings, `rental_interests` and `rental_agreements` are returned for applicable subjects because the fake provider is explicitly allowed. Production settings use `RENTAL_PROVIDER_BACKEND=disabled`, so these capabilities remain absent. The `action` query never grants authority.

### Unknown-write recovery

`GET features/v1/rental-operations/{request_key}/?subject_id={original_subject_uuid}`

Confirmed example:

```json
{
  "key": "success",
  "msg": "",
  "data": {
    "request_key": "request-uuid",
    "request_subject_id": "original-subject-uuid",
    "status": "confirmed",
    "operation_receipt": {
      "id": "operation-receipt-uuid",
      "subject_id": "result-resource-uuid",
      "request_key": "request-uuid",
      "revision": 2,
      "status": "confirmed"
    }
  }
}
```

If no durable operation is found, the endpoint currently returns:

```json
{
  "key": "success",
  "msg": "",
  "data": {
    "request_key": "request-uuid",
    "request_subject_id": "original-subject-uuid",
    "status": "unknown",
    "operation_receipt": null
  }
}
```

Important: `unknown` is not permission to submit again. Keep the protected recovery intent and offer status/support UX. The backend does not currently produce `absent_final`; permanent tombstones require worker/queue guarantees that are not implemented yet.

Recovery metadata is now recorded for current tenancy invitation create/respond, legacy lease create/sign/cancel, and checkout only when checkout is explicitly enabled. Old operations created before migration `features.0003` do not have recoverable subject metadata.

## Phase 2 — locally implemented contracts

### Owner readiness

- `GET features/v1/owner-payment-profile/`
- `POST features/v1/owner-payment-profile/onboarding-session/`

The profile returns masked beneficiary data only, required/accepted policy versions, revision, actions, and blocking reasons. The onboarding response pins `session_id`, profile subject/revision, request key, hosted URL, expiry, and operation receipt. Fake completion is accepted only through the signed local/test provider webhook; returning from a hosted page does not complete readiness.

### Interests and terms

- `GET/POST features/v1/rental-interests/`
- `GET features/v1/rental-interests/{id}/`
- `POST features/v1/rental-interests/{id}/respond/`
- `GET/POST features/v1/terms-proposals/`
- `GET/PATCH features/v1/terms-proposals/{id}/`
- `POST features/v1/terms-proposals/{id}/respond/`

Interest creation requires the exact available offer ID/revision, a monthly offer, a non-past desired start, supported capacity, `expected_revision=0`, and a request UUID. Terms enforce `rental-policy-v1`, EGP exponent 2, the offer's own monthly price, Cairo timezone, 10% owner commission on first-period base rent, platform processing-fee payer, and zero renewal commission. Editing terms preserves prior snapshots, invalidates approvals, and revokes unused invitations sourced from the changed proposal.

### Invitation v2

The existing `POST tenancy-invitations/` route now accepts the new interest-sourced body and returns the canonical resource/receipt envelope. Legacy bodies and their raw response remain unchanged.

- `POST features/v1/tenancy-invitations/{id}/revoke/`

An accepted proposal is required. The invitation expires after seven days, can be revoked only by the owner before consumption, and is consumed permanently when a draft is created. Cancelling a draft never restores it.

### Agreements

- structured `POST features/v1/leases/`
- structured `PATCH features/v1/leases/{id}/`
- `POST features/v1/leases/{id}/review/`
- `POST features/v1/leases/{id}/submit-for-signature/`
- structured `POST features/v1/leases/{id}/signing-session/`
- `GET features/v1/leases/{id}/timeline/`
- `GET features/v1/leases/{id}/billing-schedule/`

Structured agreement creation consumes the exact invitation and creates one database-unique daily lock for every `[starts_on, ends_on_exclusive)` stay day. Editing is owner-only, preserves participants/accommodation, replaces the hold atomically, advances revision, and invalidates reviews/document data. Submission requires both current reviews, owner readiness, and a complete unexpired hold. Signing sessions bind signer, request key, lease revision, document UUID, and SHA-256 hash. The lease activates only after signed fake-provider events for both participants; held inventory then becomes occupied.

The billing-schedule endpoint returns persisted `[start, end_exclusive)` periods, issue/due instants, money, state, and issued invoice IDs.

## Phase 3 — locally implemented contracts

- `GET features/v1/leases/{id}/billing-schedule/`
- `GET features/v1/rent-invoices/` and `GET features/v1/rent-invoices/{id}/`
- `POST features/v1/rent-invoices/{id}/quote/`
- `POST features/v1/rent-invoices/{id}/checkout/`
- `GET features/v1/payment-attempts/?invoice_id={id}&request_key={uuid}`
- `GET features/v1/payment-attempts/{id}/`
- `POST features/v1/payment-attempts/{id}/reconcile/`
- `GET features/v1/owner-payables/?workspace=owner`

Activation generates Cairo billing periods anchored to the original contract day. A January 31 anchor therefore produces February 28/29 and returns to March 31. The first period is issued immediately; later periods are issued by the billing worker. Invoice lines and period dates are immutable snapshots.

Quote responses are canonical mutations whose `resource` contains `quote_id`, invoice ID/revision, nested payer and zero-fee Money values, `rental-policy-v1`, SHA-256 fingerprint, and five-minute expiry. Checkout requires that exact unexpired quote, matching invoice revision, invoice ID, and a new request UUID. Its resource contains the persisted attempt/session IDs, amount, fifteen-minute fake hosted URL, exact HTTPS origin allowlist, attempt-bound return state, configured return URL, and approved external schemes. A second live intention is rejected; replaying the same request key returns the original receipt/resource.

Recovery GETs never create a charge. They return at most the authenticated payer's exact invoice/request-key attempt, `absence_confirmed`, and an existing unexpired active session when resumable. Hosted return data and `success=true` do not capture funds.

Only an HMAC-verified provider event can establish capture. Fake events are deduplicated by provider event ID and digest, bind exact amount/currency/account, and tolerate settlement arriving before capture. Capture posts balanced receivable/PSP and owner-liability/commission-reserve transactions, creates an allocation and receipt, and calculates the one-time 10% deduction on first-period base rent. PSP settlement remains a separate state. Owner payables expose gross, commission, processing fee, net, settlement/payout states, and blocking reasons.

Support-ticket creation accepts optional `rental_context` with authorized lease, invoice, payment-attempt, and subject IDs; all supplied resources must be visible to the requester and belong to one lease.

Example recovery resource:

```json
{"invoice_id":"invoice-uuid","request_key":"request-uuid","results":[{"payment_attempt_id":"attempt-uuid","invoice_id":"invoice-uuid","payment_status":"pending","settlement_status":"pending","payout_status":"held","amount":{"amount_minor":1000000,"currency":"EGP","exponent":2}}],"absence_confirmed":false,"active_session":{"session_id":"session-uuid","checkout_url":"https://fake-rental-provider.test/checkout/opaque","expires_at":"2026-10-09T10:15:00Z"}}
```

Stable errors include `stale_revision`, `quote_expired`, `document_changed`, `payment_in_progress`, and `capability_unavailable`. The payment reconcile endpoint is user-rate-limited and is status-only with the fake adapter; it never creates another charge.

## Phase 4 — locally implemented contracts

- `POST features/v1/rental-attachments/` (multipart PNG)
- `GET features/v1/rental-attachments/{id}/`
- `GET features/v1/rental-attachments/{id}/download/`
- `GET/POST features/v1/leases/{id}/handovers/`
- `GET/PATCH features/v1/handovers/{id}/`
- `POST features/v1/handovers/{id}/respond/`
- `GET features/v1/leases/{id}/deposit/`
- `GET features/v1/payouts/?workspace=owner`
- `GET features/v1/payouts/{id}/`

Evidence upload accepts only actual PNG magic bytes, declared `image/png`, at most 5 MiB, and an exact SHA-256. It stores immutable metadata and a private fake-storage key; metadata and five-minute links are participant-authorized. Uploads are recoverable by the same request key/digest, and scanning transitions `pending` to `ready` or `unsafe`. Never persist the returned link.

Handovers contain exact condition, keys, meters, inventory, up to five safe evidence IDs, possession date, revision, and participant approvals. Any edit clears all approvals. Both participants must accept the same revision; move-in acceptance changes occupancy to `occupied` and reevaluates owner payables. Dispute changes occupancy to `handover_disputed`.

Deposit reads lazily persist the agreement and a separate `invoice_type=deposit` invoice from signed agreement terms. Agreed, due, collected, returned, applied, disputed, and remaining balances are independent of rent; deposit captures credit `deposit_liability` and never create owner rent payables.

Owner payout eligibility requires PSP settlement, accepted move-in, ready beneficiary/KYC, accepted policy, and no holds. Owners can read payouts but cannot execute them. Execution/reconciliation endpoints live under `features/v1/operations/payouts/`, require the dedicated payout-operator role, allocate locked eligible payables once, use the fake payout adapter, write audit events, and post a balanced owner-liability/cash ledger transaction.

## Phase 5 — locally implemented contracts

- `GET/POST features/v1/leases/{id}/maintenance-requests/`
- `GET features/v1/maintenance-requests/{id}/`
- `POST features/v1/maintenance-requests/{id}/actions/`
- lease-scoped `payment-extension-requests/`, `amendments/`, `renewals/`, and `termination-requests/`
- each change type's detail and `respond/` routes
- amendment/renewal `submit-for-signature/` and `signing-session/`
- invoice-scoped create and lease-scoped list/detail/respond for `external-payment-claims`

Maintenance supports exactly: `acknowledge`, `reply`, `propose_appointment`, `accept_appointment`, `start_work`, `report_resolved`, `confirm_resolved`, `reopen`, `cancel`, `propose_cost`, `approve_cost`, and `reject_cost`. Events are append-only. The declared owner/tenant payer alone can approve the exact current positive EGP cost version; stale approvals are rejected and approval itself does not invent a charge.

All tenancy changes preserve their prior terms/facts and use lease/change revisions plus request-key receipts. Accepted payment extensions leave contractual `due_at` untouched and set only `deferred_until`. Amendments and renewals freeze deterministic document UUID/hash values and require exact-document signatures from both participants. Future application runs idempotently in the change worker. Continuous renewals preserve `tenancy_root_id` and require `renewal_commission_rate_bps=0`.

Accepted terminations affect only future occupancy from the accepted effective date. External-payment claims remain `review_required`; ordinary participants cannot approve them, authorized finance/PSP staff review them, and even acceptance does not change invoice capture, status, allocations, or ledger facts.

## Phase 6 — locally implemented contracts

- final settlement: `GET`, `propose/`, and `respond/` under `leases/{id}/final-settlement/`
- `GET/POST refund-requests/`, detail, and operations `respond/`
- `GET/POST disputes/`, detail, and append-only/operations `respond/`
- lease documents, private document download, and `POST rental-statements/`
- lease reviews and `GET leases/{id}/rental-center/`

Settlement lines require supported types, stable unique item IDs, integer EGP Money, and safe lease-owned evidence. The server recomputes rent balance, deposit return, refund due, and total due. Both participants accept the exact revision; disputes name persisted line IDs.

Refunds bind a captured payment attempt and cannot exceed its remaining allocation after nonfailed refund reservations. Dedicated refund/financial staff approve them. The worker executes the fake provider exactly once, writes a balanced reversal, reopens the invoice, and reverses first-period commission proportionally using round-half-up arithmetic. Mobile state never establishes refund success.

Dispute subjects and evidence must belong to the lease. Party replies are append-only; only a dispute resolver may resolve/reject. Queued ledger statements and rental documents expose metadata first, then participant-authorized five-minute private links. Never persist a returned link.

One review per author/tenancy is enforced after evidenced move-in. Accepted move-out returns occupied inventory. Closure requires returned occupancy, zero invoice balance, resolved deposit/refunds/disputes/chargebacks/payables/payouts, returned inventory, and an accepted final settlement. A late chargeback reopens financial closure without changing `occupancy_status=returned`.

`reconcile_legacy_rentals --apply` marks unsupported history read-only while preserving IDs, participants, prices, and financial facts. It never fabricates balances, commissions, or payouts. The closure worker records access revocation for inactive accounts without deleting obligations.

### Canonical mutation, error, idempotency, and recovery examples

New resource mutations use this shape (resource fields vary by endpoint):

```json
{"key":"success","msg":"","data":{"resource":{"id":"resource-uuid","revision":2,"status":"proposed"},"operation_receipt":{"id":"receipt-uuid","subject_id":"resource-uuid","request_key":"request-uuid","revision":2,"status":"confirmed"}}}
```

Replaying the same account/operation/request key with the same body returns the same HTTP status, resource, and receipt. Reusing it for a different body returns HTTP 409:

```json
{"message":"This request_key was already used for a different intention.","code":"idempotency_conflict"}
```

Revision and financial conflicts are also explicit, for example:

```json
{"message":"Settlement revision conflict.","code":"stale_revision"}
```

For an uncertain upload, recover through `GET rental-attachments/{known_id}/` when the operation receipt supplied the ID, or through the protected `rental-operations/{request_key}/?subject_id={lease_id}` receipt lookup. A missing generic operation remains `unknown`, never `absent_final`. Payment recovery remains the stricter invoice/request-key lookup documented in Phase 3 and never creates another attempt.

### Phase 2 local provider and workers

Celery and Redis configuration now includes five-minute jobs for invitation/hold expiry and hosted-session expiry/reconciliation. The fake onboarding/document/signature adapter is rejected when `DEBUG=false` and `RENTAL_FAKE_PROVIDER_ALLOWED=false`.

The local webhook is `POST features/v1/provider-webhooks/rental/`. It exists only when the configured backend is `fake`, requires an HMAC signature, and must never be called or integrated by the mobile application.

## Extended current DTOs

Current lease reads now additionally return:

- `tenancy_root_id`
- `lease_status` (same current value as legacy `status`)
- `occupancy_status`
- `financial_closure_status`
- `legacy_read_only`
- `allowed_actions`
- `blocking_reasons`

Existing leases default to `legacy_read_only=true`, `occupancy_status=not_started`, and `financial_closure_status=open`. These defaults are migration classifications, not proof that a historical tenancy never started or owes no money. Mobile must not infer financial facts from them.

Current invoice reads return:

- `revision`
- `invoice_status` (same current value as legacy `status`)
- `balance`
- `allowed_actions`
- `blocking_reasons`

They also return invoice type, billing-period dates, contractual `due_at`, separate `deferred_until`, immutable lines, receipt ID, and any live payment-attempt ID. Balance is calculated from charges minus credits and applied allocations.

## Checkout safety change

`RENTAL_CHECKOUT_ENABLED` remains false in production defaults and is true only in local/test settings. While false:

- invoice `can_pay` is false;
- `allowed_actions` excludes `quote` and `checkout`;
- `POST features/v1/rent-invoices/{id}/checkout/` returns HTTP 403 with `code=capability_unavailable`;
- no placeholder hosted URL is created.

Do not enable this setting in production while the provider backend is fake. A real PSP, secrets, monitoring, operational reconciliation, PostgreSQL concurrency evidence, and staging verification are still required.

## Error and cache behavior

Feature API errors remain flat and may now preserve stable fields such as `code`, `subject_id`, `next_action`, `payment_attempt_id`, and `correlation_id`. All feature-v1 responses are marked `private, no-store` in this foundation release.

## Mobile rollout checklist

- Keep production rental build gates false; Phase 2 capabilities are local/test-only until real providers and staging verification exist.
- Integrate capability discovery as a server authorization hint, then still handle mutation denial.
- Persist only the protected recovery identifiers described in the mobile contract; do not persist hosted URLs or return state.
- Treat `confirmed` as API commit only, not payment/signature/refund/payout completion.
- Treat `unknown` and `pending` as unresolved; never generate a replacement request key automatically.
- Parse lifecycle values defensively and disable actions on unknown statuses.
- Select invitation parsing from the request contract: legacy bodies receive the legacy raw resource, while interest-sourced bodies receive the canonical mutation envelope.

## Backend deployment note

Apply `features.0003` through `features.0009`, `support.0002`, `notifications.0005`–`0008`, and `admin_api.0002` before exercising the local contracts. They are applied to the local SQLite test database. Staging deployment, real provider integration, production database migration, PostgreSQL race verification, and live mobile integration have not been performed.

Production prerequisites remain: real KYC/beneficiary, signature, PSP, private-storage, malware-scanning, payout, and refund adapters; provider secrets and exact PSP/3DS origins; operational roles/runbooks; Redis workers/Beat and monitoring; PostgreSQL concurrency tests; migration rehearsal; staging webhook/reconciliation evidence; and physical-device mobile verification. Keep every production capability/build flag false until these pass.

## Phase changelog

### 2026-10-09 — Phase 2

- Added Celery/Redis worker configuration and local/test-only provider adapters.
- Added owner payment readiness and policy v1 persistence.
- Added interests, terms proposals, invitation v2/revocation, daily inventory locks, agreement review, deterministic documents, bound signing sessions, provider-webhook activation, timelines, typed notifications, and operations roles.
- Verified the complete local owner/tenant flow, access denial, stale revisions, overlap prevention, consumed-invitation expiry behavior, and fake-provider production rejection.

### 2026-10-09 — Phase 3

- Added anchored billing periods, immutable invoice lines, quotes, attempts, hosted checkout sessions, recovery, rate-limited reconciliation, signed/deduplicated provider events, ledger entries, allocations, receipts, PSP settlement, and owner payables.
- Added billing/payment Celery jobs and validated rental context on support tickets.
- Added migrations `features.0006` and `support.0002`; applied them locally.
- Verified month-end/leap-year anchoring, replay and recovery, exact navigation origins, out-of-order and duplicate webhooks, callback non-authority, commission arithmetic, and balanced ledger entries. Full backend result: 515 passed, 3 skipped.

### 2026-10-09 — Phase 4

- Added private PNG evidence metadata/storage/scanning/download links, versioned move-in/out handovers, approval invalidation, separate deposit invoices/liability, payable eligibility, payout batches, payout audit, and role-protected execution/reconciliation.
- Added migrations `features.0007` and `notifications.0006`; applied them locally.
- Verified MIME/magic/digest/size/access handling, handover conflicts and acceptance, rent/deposit separation, ordinary-user payout denial, and repeated-worker transfer prevention. Full backend result: 518 passed, 3 skipped.

### 2026-10-09 — Phase 5

- Added append-only maintenance events and all documented transitions, exact cost-version approval, a shared versioned rental-change aggregate, deferred payment dates, signed amendments/renewals, accepted termination handling, and operations-reviewed external-payment claims.
- Added expiry/application workers, migrations `features.0008` and `notifications.0007`, and local migration application.
- Verified the complete maintenance vocabulary, payer permission/version conflicts, immutable original due dates, exact-document change signatures, applied amendment terms, and non-authoritative external claims. Full backend result: 521 passed, 3 skipped.

### 2026-10-09 — Phase 6

- Added server-recomputed final settlement, bounded refunds and proportional commission reversal, disputes, private documents/statements, reviews, closure/reopening, chargebacks, inventory return, access revocation, and conservative legacy reconciliation.
- Added migrations `features.0009` and `notifications.0008`; applied them locally.
- Verified settlement items, refund bounds/idempotency/balanced reversal, private authorization, dispute resolution, late-chargeback reopening, review uniqueness, and legacy ID/fact preservation. Full backend result: 525 passed, 3 skipped.
