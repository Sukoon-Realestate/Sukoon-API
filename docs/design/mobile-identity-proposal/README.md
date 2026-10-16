# Sukoon mobile identity — 20 screens

Open **[index.html](index.html)** for the interactive atlas and **[design-map.html](design-map.html)** for the visual UI design map. Both files embed their fonts, photos, CSS and JavaScript and work offline.

There are **20 distinct screens in Light and Dark**, plus System mode. The global switch and S20 stay synchronized. The preference persists, follows OS changes in System mode, and carries into the design-map page. Switching theme preserves the current fields, scroll and preview state.

## Deliverables

- [Light overview](exports/light-overview.png) / [Dark overview](exports/dark-overview.png): all 20 screens.
- [Light design map](exports/design-map-light.png) / [Dark design map](exports/design-map-dark.png): four foundation panels matching the supplied reference structure.
- `exports/light-sheet-1.png` through `light-sheet-5.png`, with matching dark sheets: four screens per presentation page.
- `exports/S01-light.png` through `S20-light.png`, with matching dark files: **40 individual 720 × 1600 PNGs**.
- [DESIGN-MAP.md](DESIGN-MAP.md): implementation rules, navigation relationships and rollout.
- [design-tokens.json](design-tokens.json): semantic palette, typography, spacing and theme behavior.
- [screen-manifest.json](screen-manifest.json): current Flutter source, reusable components and required states for every screen.
- [review-results.json](review-results.json): contrast, overflow and interaction checks.

## Scope

This is a design reference and local browser prototype, not a native Flutter implementation. Names, prices, verification badges, counts, messages and schedules are illustrative. No API calls, messages, document uploads, authentication, published properties or visit requests are sent.

Interactions demonstrate theme switching, screen focus/previous/next, role filters, saves, local filters, basic form checks, local chat messages, booking review and request decisions. Unrepresented destinations explain the app step. Navigation shortcuts connect the 20 represented screens; preserve the full existing navigation graph during implementation.

The original three proposals continue as S05, S08 and S18. Shared app code, production tokens, API integrations and existing product/design documents were not changed.

## Rebuild

```powershell
python docs/design/mobile-identity-proposal/build_atlas.py
```

`build_atlas.py` reads repository assets and bundled Readex subsets, then writes both self-contained HTML files and JSON references. `atlas.css` and `atlas.js` define the presentation and prototype behavior. `build_proposal.py` retains original asset helpers; running it directly writes only `initial-three-screens.html`.

Regenerate exports with an installed Playwright package and Edge:

```powershell
$env:PLAYWRIGHT_MODULE = 'absolute/path/to/node_modules/playwright'
node docs/design/mobile-identity-proposal/review_atlas.cjs
```

Checks cover desktop and 360/390/768px presentation widths, both themes, System changes, persistence, filters, saves, request confirmation, booking navigation and local chat. All screens were visually reviewed in both themes. Native device, accessibility, localization and tablet checks remain part of Flutter implementation.
