# Sprints 3–7 — five-sprint review batch

100 distinct mockups, S61–S160, continuing the original S01–S20 identity. [Open all 160 screens](../index.html). Each section has its own title and can also be opened separately.

| Sprint | Screens | Coverage |
| --- | --- | --- |
| [3](sprint-03/index.html) | S61–S80 | Property pricing/review, analytics, availability, capture, tours, commute and decision tools |
| [4](sprint-04/index.html) | S81–S100 | Banner advertising, services, billing, subscriptions, decisions and conversations |
| [5](sprint-05/index.html) | S101–S120 | Housing requests/offers, interests, proposed terms, invitations, private application sharing and group booking |
| [6](sprint-06/index.html) | S121–S140 | Group consent, rental cases/holds, agreements, signing, personal housing and rental management |
| [7](sprint-07/index.html) | S141–S160 | Payment/invoice history, deposits, condition reports, evidence, handovers, assets and maintenance |

## Source and identity

The sibling `sokoun/apps/sokoun_app/lib` is the behavioral authority. Each mockup records its exact primary source hash, relevant dependency hashes, required states, rendered review variants and behavioral notes in its sprint manifest and AUDIT.md. This is a browser design proposal; Flutter production code is unchanged.

The audit reconciles `PromotionsScreen` as a direct wrapper for `CreateBannerAdScreen`, avoiding a duplicate screen. At that delivery, the inventory covered 304 source screen/page files: 20 original destinations, seven reconciled hosts/components/aliases, and 277 continuation destinations across 14 sprints. At that delivery, seven sprints were built; the newer [Sprints 8–10 audit](BATCH-08-10.md) updates the remaining count and aliases.

The layouts reuse the original embedded Readex/Plex typography, actual calligraphic mark, forest green actions, warm paper surfaces, restrained cards, dividers, forms and status layouts. The immersive viewers retain their own dark palette in either theme.

## Review evidence

[Batch results](batch-03-07-review-results.json) record 100 source hash checks, 1,182 rendered state/theme combinations and 32 local interaction checks. All five atlases passed at widths 360, 390, 768 and 1680 without horizontal overflow. Checks cover Light/Dark/System, draft preservation, confirmation/cancellation, uncertain outcome recovery, preview restoration and immutable booked availability. No JavaScript errors or external requests occurred.

The exports contain 200 individual 720 × 1600 PNGs, ten overviews and 50 four-screen sheets. All 100 screens were visually reviewed in both themes. Long lists/forms scroll in the interactive mockups; PNGs show the starting viewport.

[Gallery checks](../gallery-review-results.json) verify all 160 screens in eight titled sections, shared theme/S20 controls, input preservation, section filtering, enlarged previews and cross-section navigation.

Only local prototype interactions are implemented. Payment/provider results, signatures, publication, device capture, uploads, messages and AI replies are illustrative. The mockups preserve the distinction between an invitation, hold, agreement and signed contract, and between an uncertain payment attempt and a confirmed receipt. Browser checks do not replace native device, accessibility, text scaling, localization, API or provider testing.

## Rebuild

From `Sukoon-API`:

```sh
python3 docs/design/mobile-identity-proposal/sprints/build_sprints.py
python3 docs/design/mobile-identity-proposal/sprints/build_sprint02.py
python3 docs/design/mobile-identity-proposal/sprints/build_batch03_07.py
node docs/design/mobile-identity-proposal/sprints/review_batch03_07.cjs
node docs/design/mobile-identity-proposal/review_gallery.cjs
```

Review scripts accept `PLAYWRIGHT_MODULE` and `CHROME_EXECUTABLE` for local installations. `SKIP_EXPORT=1` runs the batch behavior/layout checks without regenerating images.

## Review gate

Sprints 3–7 were approved to continue. Sprints 8–10 were also approved to continue. The final authorized batch is [Sprints 11–14](BATCH-11-14.md), now built and awaiting complete design review. `review-policy.json` and `sprint-status.json` record the current gate.
