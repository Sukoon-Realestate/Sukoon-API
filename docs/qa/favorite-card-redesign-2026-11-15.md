# Saved property card redesign

The supplied card gave unconfirmed price guidance headline typography, repeated long parent-property labels, and scattered remove, memory and organize controls down a tall offer block (P2).

The revised card leads with title/location, compact property fact chips and type/rating. Parent-property wording remains available through fact tooltips and accessibility labels. Price guidance uses quiet body text. Offers have a separated heading and inset content; missing snapshot/unknown availability remain explicit, without a synthetic dash/currency. One confirmed offer displays its price once at parent level; multiple offers retain individual prices. Organization/removal now share an aligned footer with memory.

Preserved property/image navigation, category context, offer destination, freshness and capability gates, save/remove request ownership, progress/error feedback, folder/pin persistence and memory comparisons. Placement map updated in the app repository.

Verification:
- 62 tests passed: 48 card layouts (missing snapshot, valid offer, legacy favorite; Arabic/English; 320/390 widths; light/dark; 1x/2x text), organize-sheet/legacy-remove interactions, existing favorites UI and saved endpoint tests.
- Removal targets >=48px; organize and removal centers align; no Flutter layout exceptions.
- Arabic fixture previews inspected. Photos use the intentional empty-image placeholder in these tests; production image pipeline is unchanged.
- Dart formatting and diff whitespace check passed. App analysis reported 12 unrelated existing diagnostics, none in changed card widgets.
- No physical-device runtime/motion review or frame-rate claim. Existing organize sheet exercised with normal motion in widget tests; no new animation added.
