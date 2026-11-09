# Sprint 03 — Fix state, accounting and recovery behavior

**Outcome:** edge cases and retries produce correct durable outcomes across alternate routes and historical data.
**Evidence:** A1-04/A1-06/A1-07; A2-03/A2-10; A3-03; A4-01/A4-03/A4-04/A4-11;
A5-09/A5-10/A5-12/A5-15; A6-02/A6-05/A6-08.

## Stories

- Keep commission recognition immutable. Partial refunds post additive adjustments/reversals and update payable balances
  without reusing an existing ledger source with a different amount. Confirmed provider proof must repair accounting
  without another external refund. Move eligibility evaluation out of HTTP modules as part of the fix.
- Unify scalar listing concurrency/idempotency across detail PATCH and the alternate update/PUT route. Validate against
  the locked current instance; preserve rental inventory revisions and media identity.
- Route unsupported non-rental refund IDs through explicit authorized domain selection, not null-lease dereferences.
  Complete handover/maintenance date and nested-command transitions after Sprint 02 validation.
- Use one amenity mapping so `near_metro` matches the actual property field. Replace invented owner acceptance/rating
  values with agreed real aggregates and explicit no-history states.
- Fix current KYC filtering and full historical transaction/audit pagination; older matching records must remain reachable.
  Apply recipient caps to the actual campaign audience, distinguishing scan limits from eligible-recipient limits.
- Select any currently authorized digest source rather than permanently suppressing from the first expired device.
  Persist immutable original send receipts so retries after edit/deletion do not conflict with mutable message text.
- Make presence connection-scoped with renewable leases, and align all enabled social login issuers with bound sessions.
  Make refresh parsing safe for supported JSON/form/cookie combinations.
- Move document/draft creation out of GET into originating transitions or an explicit idempotent backfill. Define absent
  states without fabricating persistence. Resolve poll contract drift without discarding valid tests.

## Acceptance

- Financial matrix: refund before/after commission recognition, before/after payout, rent/deposit split, repeated partial
  refunds, full refund, timeout, duplicate event and confirmed-proof repair; ledger balanced and external submission once.
- Both listing aliases detect stale/conflicting writes and replay the same command safely.
- Unsupported domain IDs, null dates/containers and stale revisions return defined errors without side effects.
- Historical records beyond previous caps are searchable/pageable with correct totals and stable ordering.
- Metro matching/no-history owner statistics, mixed-device digests, edited/deleted-message retries and multi-tab presence
  have focused regression cases. Provider/network behavior is tested through controlled adapters before staging acceptance.
- Read-only document/catalog GETs have zero creation/repair writes. Intentional security/bug contract changes are documented
  separately from the later mechanical CBV changes.
