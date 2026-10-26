# Mobile identity proposal — continuation sprints

Open [all 295 completed screens](../index.html), grouped into fifteen titled sections: the original proposal and Sprints 1–14. Each sprint can also be opened separately. The atlases work offline with Light/Dark/System, enlarged previews, source-linked notes and review-state menus.

[Full sprint plan](SPRINT-PLAN.md) · [Source inventory](screen-inventory.json) · [Visual direction](DESIGN-DIRECTION.md) · [Final batch: Sprints 11–14](BATCH-11-14.md) · [Browser results](batch-11-14-review-results.json)

The original S01–S20 remain intact. The behavioral source is the sibling `sokoun/apps/sokoun_app/lib`. The inventory reconciles 304 source screen/page files: 20 original destinations, nine wrappers/components/aliases and 275 continuation destinations across 14 sprints (13 × 20, then 15).

Sprints 1–10 were approved to continue. The final authorized batch, Sprints 11–14, adds **75 primary screens, S221–S295**. **All 295 primary destinations are built; zero remain unbuilt.** Sprints 11–14 await complete design review. The final sprint contains 15 primary screens; native subpages are included as variants, without padding the sprint count.

## Audited aliases

`OwnerListingsScreen` directly returns original `OwnerPropertiesScreen`; `PromotionsScreen` directly returns `CreateBannerAdScreen`. The current audit also reconciles `RentalReviewsScreen` and `MyReviewsScreen` as direct `ReviewsHubScreen` wrappers. The shared hub covers lease/personal/company contexts as variants. No duplicate wrapper is padded into a sprint. IDs S01–S160 remain unchanged; only previously unbuilt IDs were rescheduled.

## Deliverables and scope

Each completed sprint contains:

- `index.html`: 20 distinct primary mockups (15 in Sprint 14) with relevant review variants.
- `screen-manifest.json` and `AUDIT.md`: exact source/dependency hashes, behavior, required states, rendered variants and original visual references.
- `exports/`: two 720 × 1600 PNGs per primary screen, two overviews and four-screen sheets in both themes. The final batch also exports its 13 additional native subpages in both themes. Long lists/forms scroll in the atlas; PNGs show the starting viewport.
- `review-results.json`: browser, overflow, appearance and local interaction evidence. The original token contrast audit remains in the root proposal.

Original Readex/Plex typography, paper/forest palette, calligraphic mark and component proportions remain the visual authority. Native splash and immersive viewers retain source-specific fixed appearances. Maps and all sample data are illustrative. No API requests, uploads, payments, signatures, device capture, messages, invitations or AI calls occur. Production Flutter code is unchanged.

Current source intentionally defers beneficiary/bank-transfer onboarding; the new mockups keep it disabled while preserving readable history. Agreement, consent, payment and refund states remain separate. Group decisions never imply consent on behalf of other members.

## Rebuild and review

From `Sukoon-API`, with the sibling app checkout available:

```sh
python3 docs/design/mobile-identity-proposal/sprints/build_sprints.py
python3 docs/design/mobile-identity-proposal/sprints/build_sprint02.py
python3 docs/design/mobile-identity-proposal/sprints/build_batch03_07.py
python3 docs/design/mobile-identity-proposal/sprints/build_batch08_10.py
python3 docs/design/mobile-identity-proposal/sprints/build_batch11_14.py
node docs/design/mobile-identity-proposal/sprints/review_batch11_14.cjs
node docs/design/mobile-identity-proposal/review_gallery.cjs
```

`build_sprints.py` reconciles the inventory/plan and rebuilds Sprint 1. Later builders rebuild only their respective batches, then refresh the main gallery. `audit_batch11_14.py` refreshes the source audit used by the current builder. `sprint-status.json` and `review-policy.json` preserve the review gate.

Review scripts accept `PLAYWRIGHT_MODULE` and `CHROME_EXECUTABLE`. `SKIP_EXPORT=1` checks batch behavior/layout without regenerating images. Browser verification does not replace native device, accessibility, text scaling, localization, API integration or provider testing.

Previous delivery notes: [Sprints 8–10](BATCH-08-10.md), [Sprints 3–7](BATCH-03-07.md), [Sprint 2](sprint-02/AUDIT.md), [Sprint 1](sprint-01/AUDIT.md). Historical ZIPs remain snapshots of those deliveries.
