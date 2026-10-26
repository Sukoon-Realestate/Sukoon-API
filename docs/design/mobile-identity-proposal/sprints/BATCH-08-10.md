# Sprints 8–10 — review batch

60 distinct mockups, S161–S220, following the original S01–S20 identity. [Open all 295 completed screens](../index.html). Every section has a title, with shared appearance controls and cross-section navigation.

| Sprint | Screens | Coverage |
| --- | --- | --- |
| [8](sprint-08/index.html) | S161–S180 | Maintenance list, disputes, rental changes/signing, departures/replacements, settlement, documents/refunds and owner payables |
| [9](sprint-09/index.html) | S181–S200 | Owner readiness/payout history/analytics, review permissions/experiences, reputation/grants/moderation/composition, group action and invite creation |
| [10](sprint-10/index.html) | S201–S220 | Group invitation/join/management/application flows, rental summary sharing and student planning/consent/history/search |

## Source audit and counting

The Flutter sibling checkout remains the authority for permissions, recovery, fields and navigation. [Source audit](batch-08-10-source-audit.json) records 60 primary source files and 332 dependency references. Each sprint manifest records hashes, behavior, original visual references and rendered states; AUDIT.md supplies per-screen notes.

`RentalReviewsScreen` and `MyReviewsScreen` directly return `ReviewsHubScreen`. They are reconciled as aliases, with lease and personal contexts represented on the hub. Only unbuilt IDs changed. There are 304 source screen/page files: 20 original destinations, nine reconciled wrappers/components/aliases, and 275 continuation destinations. Ten completed sprints plus the original proposal total 220 screens; 75 destinations remain across Sprints 11–14.

## Important workflow distinctions

- Bank-transfer beneficiary onboarding is disabled in the current data source. Readiness and historical payables/payouts stay readable; the proposal does not enable transfers.
- A replacement nomination/consent does not release the outgoing tenant. Received notice, requested date and effective date remain distinct.
- Settlement agreement, refund obligation and confirmed transfer are separate. Reports of off-platform payment route to support and do not confirm collection.
- Review drafts, immutable final submission, receipt and release conditions are separate. Company writing/viewing permissions are independent; private grants only expose selected summaries.
- Each group member approves their own participation. Group votes/applications do not create a joint lease or consent for other members.
- Rental summary sharing requires an explicit recipient, expiry, selected booking/invoice/receipt scope and consent. It grants no control over contracts or payments.
- Student planning and family sharing remain optional. Independent student search stays accessible when planning is unavailable; check-in reporting is not arrival confirmation.

## Verification and exports

[Recorded batch checks](batch-08-10-review-results.json) cover 898 state/theme combinations, 29 local interaction checks, source hashes, and 360/390/768/1680px layouts. Tests cover draft preservation, Light/Dark/System, confirmation/cancel, uncertain writes, permission/stale variants, line editing, authority toggle freezing, final review warnings, sharing scopes, capacity validation, expired invites and independent student search.

The exports contain 120 individual 720 × 1600 PNGs, six overviews and 30 four-screen sheets. All 60 primary screens were visually inspected in both themes. The [combined gallery checks](../gallery-review-results.json) verify 220 screens in eleven titled sections, shared appearance/S20, preserved drafts, section filtering, previews and cross-batch navigation.

All names, amounts, dates, ratings and statuses are illustrative. Interactions run locally; no external services or real legal/financial/consent operations are performed. Native device, API/provider, accessibility, text scaling and localization tests remain implementation work. No production Flutter files were changed.

## Rebuild and gate

```sh
python3 docs/design/mobile-identity-proposal/sprints/build_batch08_10.py
node docs/design/mobile-identity-proposal/sprints/review_batch08_10.cjs
node docs/design/mobile-identity-proposal/review_gallery.cjs
```

Sprints 8–10 were approved to continue. The final authorized batch is [Sprints 11–14](BATCH-11-14.md), now built and awaiting complete design review. The 220-screen counts above describe this historical delivery; the combined gallery now contains 295 screens.
