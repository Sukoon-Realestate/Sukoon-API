# Visit note field design

- Reproduction: Arabic booking form displayed nested outlines and a filled/glass surface extending behind the character counter, as shown in the user screenshot.
- Impact: visual clutter and cramped counter spacing (P2).
- Cause: an outlined Container enclosed a DefaultTextField whose supplied decoration inherited enabled/focused borders and fill from the app theme.
- Fix: removed the enclosing Container; the input now owns one explicit outline, surface, padding and focus treatment. Disabled glass for this field so the counter sits outside the input surface. Kept optional note entry, controller, 1000-character limit, newline input and submission; allowed growth from three to five lines. Hint and counter use theme-aware muted colors.
- Verification: Dart formatting and diff whitespace check passed. Existing tenant_visits_flow_test.dart passed all 12 tests from apps/sokoun_app, including empty and populated note submission. App analysis reported 12 unrelated existing diagnostics and none in the changed file.
- Limits: no fresh device screenshot or RTL/dark/large-text visual review captured. Broad root-level tests included device integration fixtures unavailable here; reran the focused visit suite from the app directory to resolve test font assets.
