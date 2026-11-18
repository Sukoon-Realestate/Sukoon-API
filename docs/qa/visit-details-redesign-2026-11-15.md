# Visit details redesign

## Finding and change

The supplied Arabic pending-visit screen placed several unrelated button treatments ahead of the status, repeated the status in the summary, and spent substantial height on a centered icon, pill and heading (P2). The redesign places a compact status banner first, followed by a property heading with readable owner/appointment metadata. One tools panel groups arrival, appointment negotiation, eligible delay, calendar and checklist in consistent leading-aligned icon rows. Help sits beside the tools heading. Page gutters are 20 logical pixels. Long property and metadata values wrap rather than truncate.

Existing freshness, workspace, date, identity, capability and command gates remain. Rental snapshots, stay preferences, decision/reassignment, notes, reviews, privacy, chat, cancellation and rating remain in their original data and navigation flows. Updated capability placement in the app repository's REFERENCE-ADAPTATION.md.

## Verification

- 45 tests passed: 32 layout combinations (Arabic/English, 320/390 widths, light/dark, 1x/2x text, normal/reduced motion), appointment navigation/return refresh, and 12 existing visit flow tests.
- Layout checks confirm status precedes property and tools, 20-pixel text gutters, no duplicate summary status, and minimum 48-pixel action height. Calendar-enabled capability fixture included.
- Rendered Arabic preview inspected: output/visit-details-redesign/visit-details-ar.png.
- Dart formatted; git diff whitespace check passed.
- App analysis: 12 unrelated existing diagnostics; no diagnostics in changed widgets or new tests.
- No physical-device runtime/motion or performance review performed. Widget tests exercise existing navigation with animation enabled; they do not establish device frame rate. No new animation or command behavior was introduced.
