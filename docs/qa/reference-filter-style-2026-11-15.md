# Reference filter styling

Applied the supplied reference to shared filter controls in the Flutter app: pale green selected pills, muted unboxed inactive text, fully rounded corners, and no default checkmark. Updated shared selection buttons, filter picker, and native ChipTheme; removed local overrides in property filters, priorities, and support topics. Existing filter behavior and layouts remain intact.

Verified Arabic/English, light/dark, widths 320/390, text scales 1/2, contrast, selection, minimum tap targets, and focus behavior. Native chips use the page canvas color for their inactive fill because RawChip paints a canvas Material beneath its Ink.

Validation: 16 reference style cases and 144 affected filter/screen regression tests passed. Diff whitespace checks passed. App analyzer reported 13 existing issues outside these filter style changes (one warning, 12 informational findings), no errors.

Preview: ../../output/reference-filter-style/filters-ar.png
