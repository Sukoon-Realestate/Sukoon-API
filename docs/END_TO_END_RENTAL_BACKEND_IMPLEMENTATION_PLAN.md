# End-to-end rental backend implementation plan

Date: 2026-10-09  
Source: `SOKOUN_END_TO_END_RENTAL_BACKEND_HANDOFF.md` supplied by the mobile team.

## Requirements summary

The mobile contract describes a complete rental platform, not only a lease screen. The backend must remain authoritative for permissions, offer and inventory consistency, revisions, Cairo civil dates, money, PSP outcomes, ledger postings, payouts, refunds, and financial closure. Client callbacks and UI actions are intentions only; they cannot establish a financial or legal outcome.

The cross-cutting contract requires:

- participant authorization on every private resource, attachment, document, and recovery lookup;
- fresh capability discovery with capabilities disabled until all operational dependencies are ready;
- optimistic revisions and account/operation/request-key scoped idempotency;
- durable operation receipts and recovery that never treats temporary absence as permanent absence;
- integer minor-unit EGP money, end-exclusive civil date ranges, and `Africa/Cairo` calendar authority;
- separate lease, occupancy, financial-closure, invoice, payment, refund, payout, and deposit state machines;
- immutable snapshots and auditable, balanced ledger facts;
- signed PSP webhooks and reconciliation, with capture, PSP settlement, owner liability, and payout represented separately;
- backward-compatible reads and identifiers, with unsupported legacy data explicitly read-only.

## Delivery plan

### Phase 1 — safety and protocol foundation (started)

- Add participant-scoped `rental-capabilities` and exact operation recovery endpoints.
- Extend durable idempotency records with original subject, result subject/revision, receipt identity, and recovery status.
- Add explicit lease occupancy and financial-closure states and complete the declared lease/invoice status vocabularies.
- Add root-level permissions/blocking reasons to current lease and invoice reads.
- Apply `private, no-store` to feature API responses and preserve stable error metadata.
- Default secure checkout off until quotes, attempts, PSP configuration, and webhook reconciliation exist.
- Add migration and contract tests.

Exit criteria: recovery cannot leak cross-account resources, missing records return `unknown` rather than `absent_final`, current private reads are non-cacheable, and no placeholder checkout is advertised as payable.

### Phase 2 — onboarding, interests, proposals, invitation v2, and agreements (implemented locally)

- Add owner beneficiary/KYC profile and policy acceptance through a real hosted provider.
- Add exact-offer rental interests and versioned terms proposals.
- Extend invitations with interest/proposal source revisions and owner revocation while preserving the legacy raw response.
- Require `invitation_id`, invitation revision, offer revision, full terms, and target revision for new agreement creation.
- Add mutual review, inventory holds, immutable document hashes, hosted signing, and activation.
- Mark only fully evidenced new agreements as `legacy_read_only=false`.

Exit criteria: a real owner and tenant can complete interest through activation with concurrent invitation and inventory races covered by database tests.

### Phase 3 — billing and payments (implemented locally)

- Persist Cairo-anchored billing periods and immutable invoice lines.
- Add payment quotes, payment attempts, provider sessions, exact navigation allowlists, and recovery lookup.
- Integrate a selected PSP with signed webhook verification, provider event deduplication, out-of-order handling, and reconciliation.
- Add a balanced financial ledger, capture allocation, receipts, settlement matching, and owner payable records.

Exit criteria: timeout, retry, delayed/duplicate webhook, 3DS return, app restart, and account switch tests cannot create a duplicate charge or invented success.

### Phase 4 — possession, deposits, and owner payouts (implemented locally)

- Add evidence-safe move-in handovers and mutual acceptance.
- Add deposit invoice/balances separately from rent.
- Implement settlement-aware owner payable eligibility, payout holds, operations-only payout execution, and reconciliation.

### Phase 5 — in-tenancy operations and contract changes (implemented locally)

- Add maintenance and exact cost approval.
- Add payment extensions without rewriting contractual due dates.
- Add signed amendments, renewals without repeat acquisition commission, termination requests, and external-payment claims.

### Phase 6 — move-out and financial closure (implemented locally)

- Add move-out handover, line-based final settlement, disputes, refunds, statements, tenancy reviews, and closure/reopening rules.
- Add privacy/retention operations and full historical migration/reconciliation tools.

## Release controls

Capabilities remain the rollout authority. Build flags alone cannot enable writes. Each capability must stay absent until its API, jobs, provider dependencies, operations procedures, migrations, monitoring, and integration fixtures have passed its phase exit criteria. Recovery and historical reads remain available if creation is later disabled.

## Phase 1 implementation status

Implemented locally in this change:

- `GET features/v1/rental-capabilities/`
- `GET features/v1/rental-operations/{request_key}/`
- durable rental-operation metadata on existing idempotency records
- lease occupancy/financial-closure/tenancy-root fields and expanded state vocabulary
- invoice revision and expanded state vocabulary
- lease/invoice permission and blocking-reason fields
- private no-store feature responses and stable error metadata
- secure checkout default-off gate
- migration `features.0003` and focused tests

Phases 2–6 are implemented locally. Phase 6 adds final settlement, refunds/reversals, disputes, private documents/statements, reviews, complete closure/reopening, retention revocation, chargebacks, inventory return, and conservative legacy classification. Permanent tombstone production, real providers, staging/PostgreSQL concurrency verification, monitoring, and operational rollout remain incomplete. `absent_final` is deliberately never inferred from a missing row.
