# Personal lease termination notice

Version: `contract_notice_bilateral_v1` (2026-10-29).

The personal/student termination workflow preserves the notice clause in the current canonical lease terms. Ending sooner requires explicit independent agreement by both parties to the same date and frozen proposal. This agreement does not settle money, return possession, execute a refund, or supply a provider signature. Company termination retains its separate billing-boundary policy.

The product decision uses the distinction between bilateral contract modification and natural fixed-term expiry in Egyptian Civil Code articles 147, 148, 150 and 598. Article 563 does not establish a universal thirty-day rule for these fixed-term contracts. [Official Civil Code source](https://www.eta.gov.eg/sites/default/files/2024-10/law-131-1948.pdf). This API does not implement old-rent or contested judicial eviction procedures.

Lease and rental-center responses expose `termination_notice_policy`: current signed notice days, Cairo civil policy date, minimum date, earliest date satisfying notice, natural end, lease revision, basis digest and localized blockers. An applied amendment matching current terms contributes its document provenance. Missing or malformed notice never becomes zero days.

`POST leases/{id}/termination-requests/` keeps its operation key and revision fields and requires:

- `termination_mode`: `contract_notice`, `mutual_short_notice`, or `natural_expiry`.
- `notice_basis_digest`: exact digest from a fresh lease/center read.
- `short_notice_acknowledged: true`: strict JSON boolean for a shorter-notice proposal.

`natural_expiry` uses the unchanged end date and does not waive separate departure-notice duties. Automatic expiry remains independent of this proposal workflow.

The change's `termination_notice` response contains the immutable date, mode, clause, material basis and digest, with separately derived acknowledgment status. Acceptance through `termination-requests/{id}/respond/` requires `termination_notice_digest` and an independent explicit acknowledgment when shortening notice. Rejection requires no acknowledgment. There is no termination edit or request-changes shortcut; reject and propose afresh.

Creation and acceptance validate under the existing lease/change locks. Exact-key replay returns the original receipt. Changed payload, stale terms, an elapsed date, a competing renewal or missing independent consent cannot apply a new end. Notification delivery/read state is not contractual consent or proof of legally served notice.

Migration `0093` adds an empty JSON snapshot field only. Historical accepted/applied outcomes and receipts are retained; pending snapshotless proposals require rejection/reproposal. No consent is backfilled.

Verification: 60 distinct PostgreSQL cases passed across focused notice tests and existing journey regressions. Dual-create and dual-accept concurrency were tested. The full race matrix against billing, amendment, renewal and expiry workers remains outside this bounded verification. Deployment, device behavior and provider evidence are separate.
