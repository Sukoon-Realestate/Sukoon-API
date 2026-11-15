# Mobile bottom navigation redesign

The shared mobile navigation now uses a rounded, inset, opaque dock with a tonal
selected-icon highlight. Labels remain visible, and selected labels use stronger
text contrast. Unread counts are contained in each icon slot, visually cap at
99+, and retain the full count in accessibility semantics.

The previous item widget discarded taps on the active tab before they reached
the shell's existing reselection handler. It now forwards those taps; switching
tabs still produces selection feedback. Role-specific destinations, permissions,
ordering, restoration and desktop rail routing remain in their existing owners.
Large-text navigation retains its scroll/reveal behavior. No floating overlay
was added above page content.

Changed source is in the sibling `sokoun` repository under
`apps/sokoun_app/lib/features/main_view/presentation/widgets/`:
`home_bottom_navigation.dart`, `home_navigation_item.dart`, and
`home_navigation_icon.dart`.

Validation:

- 16 new dock checks passed across RTL/LTR, 320/390 widths, light/dark themes,
  normal motion and reduced motion with large text. Checks cover badge bounds,
  selection, repeat taps, intermediate-frame layout and 99+ counts.
- 10 existing checks passed for phone/rail semantics, popup semantics, RTL tab
  selection, retained content scroll, safe-area clearance and keyboard hiding.
- Targeted analysis: no issues.
- Broader workspace clearance suite: 44 passed, 11 failed. Failures include
  missing ListTile/TextButton finders for company lists and retry actions. An
  isolated company-list failure was reproduced using temporary copies of the
  original navigation from Git HEAD; temporary files were removed afterward.
  This redesign does not claim to fix those broader workflow tests.
- iOS dev build succeeded and launched on iPhone 18 Pro simulator. Computer-use
  access to Simulator was unavailable, so live tab interactions and physical
  device frame timing were not observed. Widget-test previews establish layout,
  not live motion performance.

Previews: `output/navbar-redesign/light.png` and `dark.png`.

## Stronger visual revision

The user found the first inset light dock too similar to the original. The
revision uses the explicit pine hero/onHero palette pairing for the entire dock,
a full-height light selection tile containing both icon and label, and pale
inactive labels/icons. The previous nested icon-only highlight is removed from
mobile items; desktop rail defaults are retained. Badges remain contained.

The updated revision passed 16 dock tests and 9 existing navigation checks.
Targeted Dart analysis reports no issues. Preview files above show this revision.

## Neutral color revision

The user rejected the pine dock. Mobile navigation now uses the theme surface
for its background, raised neutral surface for the full active tile, primary
text for active content and muted text for inactive content. The revised layout
and behavior are retained. All 16 dock checks pass and targeted analysis is clean.
Previews are `output/navbar-redesign/warm-neutral-light.png` and
`warm-neutral-dark.png`. This color-only revision has not been rebuilt in the
simulator.
