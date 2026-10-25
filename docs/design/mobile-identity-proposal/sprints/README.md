# Mobile identity proposal — continuation sprints

Start with [all 160 completed screens](../index.html), grouped under titled sections. [Sprint 2 alone](sprint-02/index.html) is also available. [Sprint 1](sprint-01/index.html) remains available as the approved-to-continue batch. Both atlases are self-contained and work offline, with Light/Dark/System, enlarged previews, screen groups and review-state menus.

[Full sprint plan](SPRINT-PLAN.md) · [Source inventory](screen-inventory.json) · [Visual direction](DESIGN-DIRECTION.md) · [Sprint 2 behavior audit](sprint-02/AUDIT.md) · [Browser results](sprint-02/review-results.json)

The original S01–S20 remain intact. The current app source is the sibling `sokoun/apps/sokoun_app/lib`, replacing the handoff's `mobile/` location. The source inventory reconciles 304 screen/page files: 20 originally covered, seven hosts/components/aliases, and 277 remaining destinations. Those are scheduled in 14 sprints: 13 of 20, then 17.

Sprint 1 delivers S21–S40. Sprint 2 delivers S41–S60. Sprints 3–7 add S61–S160 as one authorized five-sprint batch. **137 destinations remain planned across 7 later sprints. Stop for user review before Sprint 8.** Later sprints need their own source/dependency audit before design work.

## Sprint 2 audit correction

`OwnerListingsScreen` directly returns the already-covered `OwnerPropertiesScreen` (original S16). It is now an alias rather than a second mockup. S41–S57 retain their IDs; unbuilt later IDs shift by one. Sprint 2 includes OwnerRequestsScreen, location picking, and the distinct property photos step instead. The later five-sprint audit also reconciled `PromotionsScreen`, which only returns `CreateBannerAdScreen`. There are now 277 remaining destinations after the original proposal; no alias is padded into the 100-screen batch.

## Deliverables

Each completed sprint has:

- `index.html`: 20 distinct primary mockups with important additional review variants.
- `screen-manifest.json` and `AUDIT.md`: exact current source hashes, dependencies, required implementation states, rendered variants and original visual references.
- `exports/`: 40 individual 720 × 1600 PNGs, two overviews and ten four-screen sheets. Long forms/lists scroll in the atlas; PNGs show their initial viewport.
- `review-results.json`: browser, overflow and local interaction evidence (the original palette contrast audit is linked in the root proposal).

Sprint 2's native splash intentionally stays light and the immersive photo viewer stays dark in both themes, as their current source requires. Maps are offline schematic illustrations. Public-page/legal text and release notes are explicitly illustrative. Support submissions, messages, uploads, media saves, device location and booking operations never call external services.

Shared prototype navigation connects represented screens across all 160 represented screens. Unrepresented destinations identify the next native app step. Production Flutter code, shared native tokens, account permissions and API behavior are unchanged.

## Rebuild and review

From `Sukoon-API`, with the sibling `sokoun` checkout available:

```sh
python3 docs/design/mobile-identity-proposal/sprints/build_sprints.py
python3 docs/design/mobile-identity-proposal/sprints/build_sprint02.py
PLAYWRIGHT_MODULE=/absolute/path/to/playwright CHROME_EXECUTABLE=/absolute/path/to/chrome node docs/design/mobile-identity-proposal/sprints/review_sprint.cjs
PLAYWRIGHT_MODULE=/absolute/path/to/playwright CHROME_EXECUTABLE=/absolute/path/to/chrome node docs/design/mobile-identity-proposal/sprints/review_sprint02.cjs
```

`build_sprints.py` reconciles the inventory/plan and rebuilds Sprint 1. `build_sprint02.py` builds only Sprint 2 from the audited inventory. `sprint-status.json` preserves the review gate across rebuilds. Both use the original embedded foundation, fonts, signature and icon registry.

The review scripts require Playwright and a local Chromium executable. Browser tests check rendered states, 360/390/768/1680px widths, original component parity, theme/draft preservation and local interactions. They do not replace native Flutter/device, accessibility/text scaling, API integration or map/media runtime testing.

The portable Sprint 2 ZIP includes original offline review pages and both sprint folders so review navigation works after extraction. Flutter source links and rebuilding still require the original sibling checkout.

## Five-sprint batch 3–7

[Batch audit](BATCH-03-07.md) · [Recorded checks](batch-03-07-review-results.json). `build_batch03_07.py` rebuilds all 100 screens, manifests and audit documents, then refreshes the main gallery. `review_batch03_07.cjs` verifies and exports them. The current review gate is recorded in `review-policy.json`; Sprint 8 remains unstarted.
