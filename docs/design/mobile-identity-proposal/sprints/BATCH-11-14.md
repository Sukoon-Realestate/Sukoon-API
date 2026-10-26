# Sprints 11–14 — final design review batch

The final authorized batch completes **75 primary mockups, S221–S295**, using the original S01–S20 identity. [Open all 295 completed screens](../index.html), organized into fifteen titled sections. Every section is visible by default; appearance, filtering, enlarged previews and cross-section navigation are shared.

| Sprint | Primary screens | Coverage |
| --- | --- | --- |
| [11](sprint-11/index.html) | S221–S240 · 20 | Student policies, academic plans, requirements and publication; company access, proof, contracts, costs, accounts, members, invitations, summary and requests |
| [12](sprint-12/index.html) | S241–S260 · 20 | Company saved lists, staff CSV/results, tenancy and viewing; company workspace, property inventory, media and unit batches; tenders, participation and sealed bids |
| [13](sprint-13/index.html) | S261–S280 · 20 | Tender clarifications, own allocation consent, package construction and execution preparation; shared living plans, private inputs, disclosure and company housing simulation |
| [14](sprint-14/index.html) | S281–S295 · 15 | Scenario decisions, transition plans, matching candidates and history, interest decisions, execution preparation, uncertain outcomes, independent legs and execution inbox |

## Source coverage

The [source audit](batch-11-14-source-audit.json) records 75 primary Flutter files and 809 dependency references. The primary files contain 89 native Screen classes: 75 primary destinations, 13 additional rendered subpages, and one entry host sharing the request-detail surface. Each native class maps to a primary or rendered variant in the sprint manifest. No duplicate aliases were added to fill a sprint.

The complete inventory reconciles **304 screen/page source files** into 20 original destinations, 275 continuation destinations and nine documented wrappers/components/aliases. All **295 primary destinations** are built; **zero remain unbuilt**. The final sprint contains the actual remainder of 15. [Source and export verification](batch-11-14-source-verification.json) checks hashes, class coverage, IDs, states and export dimensions.

## Behavior represented

- Student planning remains optional. Publishing uses explicit consent for the displayed revision. Private requirements and shared publication remain separate; ending a study plan does not end a lease.
- Company access, membership, coordination, approval and financial authority remain separate. Invitations and employment proof do not automatically accept membership. Company tenancy preparation does not sign, collect or confirm occupancy.
- CSV preview is a simplified local example. Duplicate rows and unit codes are blocked; partial batch results retry only incomplete rows. Media is illustrative; no device file is read or uploaded.
- Sealed bids expose the viewer's permitted context. Base and quantity-tier pricing are separate. Package construction is a review process; each participant consents to their own allocation and current revision.
- Living plans preserve private and omitted inputs. Missing values are unknown, rather than zero. Disclosure and counterfactual comparisons have separate review states. Bounded feasible results do not imply global optimality.
- Transition sharing, candidate interest and execution preparation do not release the current lease or confirm a new one. Unknown write outcomes reconcile the original attempt; confirmed legs are retained without replaying them. Approval, signature, payment and occupancy remain independent.

## Verification and exports

[Browser results](batch-11-14-review-results.json) pass **1,184 state/theme checks and 43 local interaction checks** across the final 75 primary screens. Checks include Light/Dark/System, draft preservation, confirmations/cancel, permissions, stale revisions, unknown outcomes, private inputs, sealed bids, conditional tiers, CSV preview, duplicate codes and partial recovery. Layout checks cover 360, 390, 768 and 1680px presentation widths. The Sprint 2 regression also passes after connecting company workspace navigation.

Exports contain **222 PNGs**: 150 primary-screen images and 26 native-subpage images at 720 × 1600, eight overviews and 38 four-screen sheets. Long forms and lists scroll inside the atlas; PNGs show the starting viewport. Primary and additional native subpages were visually reviewed in both themes. Original typography, paper/forest colors, calligraphic mark and component proportions remain the reference.

The [combined gallery checks](../gallery-review-results.json) verify 295 unique primary IDs in fifteen titled sections, final-sprint filtering, shared appearance/S20, preserved drafts, previews and cross-batch navigation through company, tender, transition and execution flows.

All data and outcomes are illustrative. Interactions run locally, without service calls, messages, uploads, signatures, payments or AI calls. Production Flutter files remain unchanged. Browser prototype verification does not replace native accessibility, device, text-scaling, localization or API/provider tests during implementation.

## Rebuild and review gate

```sh
python3 docs/design/mobile-identity-proposal/sprints/build_sprints.py
python3 docs/design/mobile-identity-proposal/sprints/audit_batch11_14.py
python3 docs/design/mobile-identity-proposal/sprints/build_batch11_14.py
node docs/design/mobile-identity-proposal/sprints/review_batch11_14.cjs
python3 docs/design/mobile-identity-proposal/sprints/verify_batch11_14.py
node docs/design/mobile-identity-proposal/review_gallery.cjs
```

Review scripts accept `PLAYWRIGHT_MODULE` and `CHROME_EXECUTABLE`; `SKIP_EXPORT=1` skips image export. Sprints 1–10 were approved to continue. **Sprints 11–14 are built and awaiting complete design review.** There is no unbuilt next sprint. Production Flutter implementation requires a separate request.
