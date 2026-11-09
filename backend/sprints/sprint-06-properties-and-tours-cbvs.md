# Sprint 06 — Property, visit and tour CBVs

**Scope:** `core_apps/properties/`, `core_apps/virtual_tours/`, shared portfolio storage interfaces.
**Prerequisites:** publication, retention, media/input and read-budget stories; **evidence:** A2 findings, A3-01.

## Batches

- Listings/catalog/owner/saved/public reviews: named selectors and one canonical publication/read policy.
- Listing edits/media/inventory/moderation receipts: typed commands, one locked capacity/revision/retry service.
- Visits, owner availability/closures, time proposals/arrival/post-visit decisions: appointment services and batched
  current-authority/read context; explicit command classes.
- Tour authoring/uploads/reviews, capture selection/jobs and viewer credential/session/manifest/byte endpoints:
  explicit public/owner/reviewer/viewer policy classes delegating to lifecycle/processing/read services.

Move ORM state transitions from image ordering, availability preview/commit and capture selection views into cohesive
domain commands. Retain bounded helpers for geometry/content verification. Use an appropriate Django View for the HTML
viewer if converting it; preserve CSP/template behavior. Preserve streaming PUT body/parsers and signed-byte behavior.

## Acceptance

- The 17 direct property and 42 custom-decorated tour function endpoint definitions are migrated or explicitly reconciled
  with the maintained runtime inventory; all routed project HTTP handlers meet the authored-CBV target.
- No thin class merely delegates to the unchanged mixed HTTP function. Commands have explicit lock/version/current
  eligibility/receipt rules; selectors prepare page data without hidden query loops.
- Public closure/retirement/moderation checks apply to new and already-issued public tour credentials; private historical/
  owner/reviewer previews stay separately authorized.
- Media upload/selection retry, fencing, pixel/container validation, cleanup/retention, stale updates, booking capacity,
  Cairo DST slot boundaries and request ordering pass focused cases and necessary PostgreSQL races.
- Page/query/payload budgets, headers, no-store/nosniff/referrer controls, status/error envelopes and supported aliases
  remain stable. Do not remove the explicit legacy client-update responses without client approval.
