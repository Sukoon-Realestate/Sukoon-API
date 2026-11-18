# Search filters UI redesign — 2026-11-15

The supplied Arabic screen showed large outlined choice grids, duplicate section/field labels, nested text-field frames and a large priorities block. The redesign keeps the existing filter model, server option labels, controllers and apply/reset ownership.

## Capability placement

| Existing capability | New entry / outcome |
| --- | --- |
| Sort order | Labelled current-value picker at the top; shared cancellable single-choice sheet. |
| Personalized ordering and housing priorities | One compact switch row next to sort, with a labelled/accessible priorities-settings icon; existing discovery/workspace gate retained. |
| Physical property type | Current-value picker with All and active reset; backend selectionValue and labels retained. |
| Accommodation scope | Visible current-value picker beside the other primary criteria; same supported scopes and callback. |
| City and district | Always-visible location card; existing city label/identifier handling retained. |
| Price range, price period and correction | Always-visible budget card, with period directly beside the bounds; validation, required-period checks and swap correction retained. |
| Stay dates and people | Labelled expandable stay card; active preferences start open. Existing student-context exclusion retained. |
| Rooms, bathrooms, suitability, furnishing and smoking | Expandable property-details card with compact choice sheets and active count; existing values start open. |
| Amenities | Expandable multi-select card with soft chips and active count; selections survive collapse. |
| Verified property | Visible current-value selector below the detailed groups. |
| Reset/back and Show results | Fixed toolbar and footer; reset becomes an accessible icon at larger text sizes to protect the title. Query/context reset semantics and apply callback retained. |

Expandable sections keep their child state mounted and exclude collapsed children from keyboard focus. Native expansion uses the shared reduced-motion duration policy. Content and footer use fixed 20-point horizontal gutters. Inputs now have one field border, theme-aware hint colors and normal internal padding.

## Verification

All 56 focused checks passed, including 21 new filter-page checks and related city-identity/search/currency regressions. Coverage includes Arabic/English, 320/390 widths, light/dark themes, 100%/200% text, normal/reduced motion, the actual pushed page, selector changes, personalization, active groups, value retention, invalid-range correction, reset/apply, focus isolation, and an intermediate expansion frame.

Changed-target analysis and whitespace checks passed. Inspected the rendered Arabic overview and lower-section previews at `output/filter-screen-redesign/filters-ar.png` and `details-ar.png`. Catalog labels such as Studio/Newest are test fixtures; production labels remain supplied by the backend.

Live simulator/device review and physical-device performance remain unverified. The previously stalled, widely failing whole-app suite was not repeated for this scoped change; these results do not establish a clean repository-wide release gate.

Logs: `/tmp/filter-redesign-complete-tests.log`, `/tmp/filter-redesign-complete-analysis.log`.
