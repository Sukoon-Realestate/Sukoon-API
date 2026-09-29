# Motion and interaction review

This pass improves tenant discovery and owner listing management equally. It
builds on the shared layouts, typography, and responsive controls documented in
`Design.md`.

## Where to see the animations

| Place | Trigger | Result |
| --- | --- | --- |
| Tenant search | Open search; choose a property type | Loaded property types and suggested areas fade in with a short upward slide, over 320 ms. Suggested areas use a 60 ms delay. |
| Search category chips | Select a property type | The selected background and border transition over 200 ms. Selection is also announced to assistive technology. |
| Recent searches | Remove an entry, clear history, or Undo | The history section resizes over 260 ms, including disappearing when empty. |
| Search results | Clear the last active filter | The filter bar collapses over 240 ms. |
| Price filters | Enter a minimum greater than the maximum; choose Swap prices | The inline explanation appears and disappears over 240 ms. |
| Property details | Open a property | The content fades and slides in over 320 ms. |
| Property description | Tap Show more or Show less on a long description | The text expands or collapses over 260 ms and the chevron rotates. Short descriptions have no expansion control. |
| Owner dashboard | Open the dashboard | Statistics and visit requests enter over 320 ms, with a 60 ms stagger. |
| Add/edit property | Complete a step or change its readiness | The information banner changes color and resizes over 240 ms. |
| Add/edit property review | Tap Review listing on the final step | Five review sections enter with delays from 0 to 160 ms. Edit shortcuts return to the corresponding form step. |

`SokounReveal` owns the reusable entrance. Ordinary rebuilds preserve its child
state and do not replay the entrance. `SokounMotion` bypasses app-owned motion
when reduced motion or accessible navigation is enabled. Property-step
navigation jumps directly in that mode.

## Useful behavior added

- **Search history:** remove individual queries, clear all, and Undo. The five
  most recent entries persist locally. Whitespace and case duplicates collapse.
  Writes are serialized; failed writes restore the last saved history and show
  recovery feedback. Undo retains newer searches.
- **Search input:** clear the query without leaving the screen; dismiss the
  keyboard on scrolling/submission; ignore repeat submission while results are
  opening or already on top.
- **Price range:** prevent applying a reversed range and offer Swap prices.
  Either bound can remain empty. Numeric fields accept Arabic, Persian, and
  Western digits in search filters and owner property forms.
- **Property details:** long descriptions can be read in full. The ownership
  verification banner appears only when the property is verified.
- **Owner listing review:** inspect title, type, address, room counts, area,
  floor, building year, photo count, optional video duration, price, deposit,
  rental period, amenities, description, house rules, and proof filename before
  submission. Each section links back to its form step and retains the draft.
  Opening or dismissing the review does not submit a request.

Persistence remains in the history Cubit/data layer. Submission still uses the
existing create/update Cubits and backend contract. Local expansion and motion
state stay in the narrowest widget that owns them.

## Rendered previews

The [preview gallery](motion/index.html) contains real Flutter renders of the
new search controls and listing review in Arabic and English at phone and tablet
widths. These are component fixtures with sample property data, not screenshots
of a live backend session.

Reproduce with Flutter 3.35.1 from `apps/sokoun_app`:

```sh
flutter test --no-pub test/motion_ux_test.dart --concurrency=1 \
  --dart-define=MOTION_REVIEW_DIR=/absolute/path/to/previews
```

The interaction suite covers 320, 390, 600, 768, 1024, and 1366 logical pixels,
text scales 1, 1.3, and 2, and both Arabic and English. Other checks cover entrance
progress and retained field state, reduced motion, description expansion,
history persistence/failure/races, price correction, and owner review navigation
with draft preservation. The existing adaptive-layout and feature-flow suites
remain part of regression verification.

The complete Sokoun regression suite passed **826 tests** with Flutter 3.35.1
(`flutter test --no-pub --concurrency=1`). Analysis reports the existing unused
`_submitGoogle` declaration in `login_screen.dart`; this pass adds no diagnostics.

Native device profiling, physical iPad behavior, and live backend submission are
outside the widget-test evidence recorded here.
