# Finding-to-sprint index

Every entry links to its trigger, source evidence and proposed acceptance cases. Architecture goals and policy choices are
distinguished from security defects in the area reports. Findings are open backlog; this audit implemented no application fix.

The suggested severities/priorities guide triage. A source-verified defect is not automatically a reproduced production incident.
Unverified candidates are kept in the area notes and are not promoted to confirmed bugs here.

## Area 1

| Finding | Evidence summary | Sprint packages |
|---|---|---|
| [A1-01](findings/area-1.md#a1-01) | High — Unowned avatar references can become provider-deletion commands | [01](sprint-01-security-and-data-preservation.md), [02](sprint-02-inputs-and-uploads.md), [05](sprint-05-identity-cbvs.md) |
| [A1-02](findings/area-1.md#a1-02) | High — Inherited Djoser deletion bypasses reviewed closure | [01](sprint-01-security-and-data-preservation.md), [05](sprint-05-identity-cbvs.md) |
| [A1-03](findings/area-1.md#a1-03) | High — Social email auto-link preserves attacker-created local credentials | [01](sprint-01-security-and-data-preservation.md), [05](sprint-05-identity-cbvs.md) |
| [A1-04](findings/area-1.md#a1-04) | Medium — OTP attempts/consumption use non-atomic cache operations | [01](sprint-01-security-and-data-preservation.md), [03](sprint-03-correctness-and-recovery.md) |
| [A1-05](findings/area-1.md#a1-05) | Medium — Identity submission loses the authenticated epoch before acquiring its lock | [01](sprint-01-security-and-data-preservation.md), [02](sprint-02-inputs-and-uploads.md), [05](sprint-05-identity-cbvs.md) |
| [A1-06](findings/area-1.md#a1-06) | Medium — Legacy social token issuance does not use the bound-session issuer | [03](sprint-03-correctness-and-recovery.md), [05](sprint-05-identity-cbvs.md) |
| [A1-07](findings/area-1.md#a1-07) | Medium — Refresh mutates potentially immutable request data | [02](sprint-02-inputs-and-uploads.md), [03](sprint-03-correctness-and-recovery.md), [05](sprint-05-identity-cbvs.md) |
| [A1-08](findings/area-1.md#a1-08) | Medium hardening — Cookie JWT writes lack explicit CSRF verification | [01](sprint-01-security-and-data-preservation.md), [05](sprint-05-identity-cbvs.md) |
| [A1-09](findings/area-1.md#a1-09) | Medium performance — Registration performs email I/O inside account transaction | [04](sprint-04-api-performance.md), [05](sprint-05-identity-cbvs.md) |
| [A1-10](findings/area-1.md#a1-10) | Architecture/cleanup — Consolidate identity entry points without removing protections | [05](sprint-05-identity-cbvs.md), [11](sprint-11-cleanup-and-standards.md) |

## Area 2

| Finding | Evidence summary | Sprint packages |
|---|---|---|
| [A2-01](findings/area-2.md#a2-01) | High — Publication checks are absent from visit creation and some public reads | [01](sprint-01-security-and-data-preservation.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-02](findings/area-2.md#a2-02) | High — Published virtual-tour bytes remain public after the owner's closure request | [01](sprint-01-security-and-data-preservation.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-03](findings/area-2.md#a2-03) | Medium — An active alternate listing-update route bypasses the canonical concurrency and retry contract | [03](sprint-03-correctness-and-recovery.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-04](findings/area-2.md#a2-04) | Medium — Cover replacement bypasses the 25-photo limit | [02](sprint-02-inputs-and-uploads.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-05](findings/area-2.md#a2-05) | Medium — Nested inventory/metadata values bypass typed validation and raise raw exceptions | [02](sprint-02-inputs-and-uploads.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-06](findings/area-2.md#a2-06) | Medium — Listing-media inputs have incompatible reference/file and video validation contracts | [02](sprint-02-inputs-and-uploads.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-07](findings/area-2.md#a2-07) | Medium — Visit list serialization performs repeated per-visit authorization/continuation queries | [04](sprint-04-api-performance.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-08](findings/area-2.md#a2-08) | Medium — Availability checks issue a closure query for each candidate slot | [04](sprint-04-api-performance.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-09](findings/area-2.md#a2-09) | Medium — Saved-search reads materialize the complete result set and store unbounded JSON while holding the user lock | [04](sprint-04-api-performance.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-10](findings/area-2.md#a2-10) | Medium — Owner screens return fabricated acceptance and rating statistics | [03](sprint-03-correctness-and-recovery.md), [11](sprint-11-cleanup-and-standards.md) |
| [A2-11](findings/area-2.md#a2-11) | Medium architectural backlog — 59 DRF function endpoints remain, with mixed HTTP and domain logic | [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-12](findings/area-2.md#a2-12) | Medium — Capture-session payloads have multiplicative query and response growth | [04](sprint-04-api-performance.md), [06](sprint-06-properties-and-tours-cbvs.md) |
| [A2-13](findings/area-2.md#a2-13) | Medium — Public reviews and owner dashboard paginate after unbounded work, or not at all | [04](sprint-04-api-performance.md), [06](sprint-06-properties-and-tours-cbvs.md) |

## Area 3

| Finding | Evidence summary | Sprint packages |
|---|---|---|
| [A3-01](findings/area-3.md#a3-01) | P1 — active portfolio images are deleted by the tour-storage cleanup | [01](sprint-01-security-and-data-preservation.md), [06](sprint-06-properties-and-tours-cbvs.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-02](findings/area-3.md#a3-02) | P2 — personal maintenance mutations do not validate their complete command body | [02](sprint-02-inputs-and-uploads.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-03](findings/area-3.md#a3-03) | P2 — transition matching rejects all near-metro requirements | [03](sprint-03-correctness-and-recovery.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-04](findings/area-3.md#a3-04) | P2 — company offer discovery does full-market work before pagination and resolves each scope twice | [04](sprint-04-api-performance.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-05](findings/area-3.md#a3-05) | P2 — company visibility scans every candidate before company/lease filters and pagination | [04](sprint-04-api-performance.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-06](findings/area-3.md#a3-06) | P2 — anonymous public reputation requests issue at least four extra queries per invoice | [04](sprint-04-api-performance.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-07](findings/area-3.md#a3-07) | P2 — maintenance collection is unbounded and still performs a query per maintenance row | [04](sprint-04-api-performance.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-08](findings/area-3.md#a3-08) | P2 — discovery expiry maintenance repeatedly scans and updates all expired history | [04](sprint-04-api-performance.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-09](findings/area-3.md#a3-09) | P2 — tender calculation holds property/domain locks during combinatorial work | [04](sprint-04-api-performance.md), [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-10](findings/area-3.md#a3-10) | P1 delivery prerequisite — CBV migration must replace function-name-dependent company route policies explicitly | [07](sprint-07-rentals-and-housing-cbvs.md) |
| [A3-11](findings/area-3.md#a3-11) | P2 architecture — large mixed projections/handlers still hide domain responsibilities after file splitting | [07](sprint-07-rentals-and-housing-cbvs.md) |

## Area 4

| Finding | Evidence summary | Sprint packages |
|---|---|---|
| [A4-01](findings/area-4.md#a4-01) | High / money correctness — partial refunds conflict with already-earned commission identity | [03](sprint-03-correctness-and-recovery.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-02](findings/area-4.md#a4-02) | Medium / authorization — personal payment readers and commands omit private-access revocation | [01](sprint-01-security-and-data-preservation.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-03](findings/area-4.md#a4-03) | Medium / input validation and correctness — handover commands persist untyped input and return 500 for malformed revisions | [02](sprint-02-inputs-and-uploads.md), [03](sprint-03-correctness-and-recovery.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-04](findings/area-4.md#a4-04) | Medium / domain validation — rental refund endpoint crashes on a valid non-rental payment identity | [02](sprint-02-inputs-and-uploads.md), [03](sprint-03-correctness-and-recovery.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-05](findings/area-4.md#a4-05) | Medium / query growth — billing invoice pagination still issues per-row relation and status queries | [04](sprint-04-api-performance.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-06](findings/area-4.md#a4-06) | Medium / scalability — personal finance lists are unbounded, with nested history N+1 work | [04](sprint-04-api-performance.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-07](findings/area-4.md#a4-07) | Medium / transaction bottleneck — payable evaluation repeats lease-wide work while financial locks are held | [04](sprint-04-api-performance.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-08](findings/area-4.md#a4-08) | Medium / public endpoint bottleneck — advertising feed limits output, not candidate/remote-storage work | [04](sprint-04-api-performance.md), [08](sprint-08-commerce-cbvs.md) |
| [A4-09](findings/area-4.md#a4-09) | Medium / production cleanup and read semantics — public advertising GET contains one-off fixture restoration and fabricated-artwork code | [08](sprint-08-commerce-cbvs.md), [11](sprint-11-cleanup-and-standards.md) |
| [A4-10](findings/area-4.md#a4-10) | Medium / architecture and requested migration — APIs remain FBVs and views own domain mutations | [08](sprint-08-commerce-cbvs.md) |
| [A4-11](findings/area-4.md#a4-11) | Medium / GET side effects and query growth — document catalog performs per-record creation on every read | [03](sprint-03-correctness-and-recovery.md), [04](sprint-04-api-performance.md), [08](sprint-08-commerce-cbvs.md) |

## Area 5

| Finding | Evidence summary | Sprint packages |
|---|---|---|
| [A5-01](findings/area-5.md#a5-01) | High — message edits bypass moderation enqueue | [01](sprint-01-security-and-data-preservation.md), [09](sprint-09-communication-cbvs.md) |
| [A5-02](findings/area-5.md#a5-02) | High — legacy direct socket bypasses text validation and explicit send limits | [01](sprint-01-security-and-data-preservation.md), [09](sprint-09-communication-cbvs.md) |
| [A5-03](findings/area-5.md#a5-03) | High — starting a chat discloses the counterpart's email | [01](sprint-01-security-and-data-preservation.md), [09](sprint-09-communication-cbvs.md) |
| [A5-04](findings/area-5.md#a5-04) | Medium — conversation list prefetch is defeated by repeated per-row authorization/projection queries | [04](sprint-04-api-performance.md), [09](sprint-09-communication-cbvs.md) |
| [A5-05](findings/area-5.md#a5-05) | Medium — rich message pages and event replay have per-message query growth | [04](sprint-04-api-performance.md), [09](sprint-09-communication-cbvs.md) |
| [A5-06](findings/area-5.md#a5-06) | Medium — forward destinations paginate after scanning every conversation | [04](sprint-04-api-performance.md), [09](sprint-09-communication-cbvs.md) |
| [A5-07](findings/area-5.md#a5-07) | Medium — marking a long unread history read creates all receipts in memory under chat locks | [04](sprint-04-api-performance.md), [09](sprint-09-communication-cbvs.md) |
| [A5-08](findings/area-5.md#a5-08) | Medium — support detail/reply/recovery return unbounded threads with nested evidence N+1 queries | [04](sprint-04-api-performance.md), [09](sprint-09-communication-cbvs.md) |
| [A5-09](findings/area-5.md#a5-09) | Medium — one expired device session can suppress a digest despite another authorized device | [03](sprint-03-correctness-and-recovery.md), [09](sprint-09-communication-cbvs.md) |
| [A5-10](findings/area-5.md#a5-10) | Medium — a legacy direct send retry conflicts after that message is edited | [03](sprint-03-correctness-and-recovery.md), [09](sprint-09-communication-cbvs.md) |
| [A5-11](findings/area-5.md#a5-11) | Medium / policy gap — opaque chat files accept every byte format without content inspection | [02](sprint-02-inputs-and-uploads.md), [09](sprint-09-communication-cbvs.md) |
| [A5-12](findings/area-5.md#a5-12) | High for validation readiness — poll-voter tests import a nonexistent helper | [00](sprint-00-baseline-and-contracts.md), [03](sprint-03-correctness-and-recovery.md) |
| [A5-13](findings/area-5.md#a5-13) | Medium / architecture — 14 routed function views remain against the requested CBV rule | [09](sprint-09-communication-cbvs.md) |
| [A5-14](findings/area-5.md#a5-14) | Low / cleanup — unused pre-outbox send helpers and an unrouted preferences view remain | [09](sprint-09-communication-cbvs.md), [11](sprint-11-cleanup-and-standards.md) |
| [A5-15](findings/area-5.md#a5-15) | Low — online presence expires during active sessions and one tab disconnect marks all tabs offline | [03](sprint-03-correctness-and-recovery.md), [09](sprint-09-communication-cbvs.md) |

## Area 6

| Finding | Evidence summary | Sprint packages |
|---|---|---|
| [A6-01](findings/area-6.md#a6-01) | High — Legacy moderation route bypasses canonical decision invariants | [01](sprint-01-security-and-data-preservation.md), [10](sprint-10-admin-and-shared.md) |
| [A6-02](findings/area-6.md#a6-02) | Medium — Admin KYC filters reference the wrong model relation | [03](sprint-03-correctness-and-recovery.md), [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-03](findings/area-6.md#a6-03) | Medium — Admin property list has measured per-row query growth | [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-04](findings/area-6.md#a6-04) | Medium — KYC and report projections still query per list item | [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-05](findings/area-6.md#a6-05) | Medium — Transaction/audit histories are truncated before filtering and pagination | [03](sprint-03-correctness-and-recovery.md), [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-06](findings/area-6.md#a6-06) | Medium — Dashboard/analytics performs repeated daily and role queries | [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-07](findings/area-6.md#a6-07) | Medium — Campaign history expands into per-campaign aggregate queries | [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-08](findings/area-6.md#a6-08) | Medium — Campaign cap is applied before audience eligibility | [03](sprint-03-correctness-and-recovery.md), [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-09](findings/area-6.md#a6-09) | Medium — Content catalog projections lack their relation fetch plan | [04](sprint-04-api-performance.md), [10](sprint-10-admin-and-shared.md) |
| [A6-10](findings/area-6.md#a6-10) | High maintenance priority — Unsupported framework pin and unmeasured dependency security | [01](sprint-01-security-and-data-preservation.md), [12](sprint-12-acceptance-and-rollout.md) |
| [A6-11](findings/area-6.md#a6-11) | Quality backlog — Broad unused-import suppression hides substantial cleanup candidates | [11](sprint-11-cleanup-and-standards.md) |
| [A6-12](findings/area-6.md#a6-12) | Documentation/architecture — Repository instructions conflict with the agreed target | [00](sprint-00-baseline-and-contracts.md), [10](sprint-10-admin-and-shared.md) |

## Cross-domain rules

- One owner per root cause. Portfolio retention is A3-01, independently checked by Area 2, not counted twice.
- Input schemas, projection budgets and transport conversion may reference the same defect but are separate implementation stories.
- Mark a finding resolved only when its regression/acceptance evidence demonstrates the actual behavior changed.
- Preserve the original evidence/ID when code moves. Record a new location and commit instead of deleting historical findings.
