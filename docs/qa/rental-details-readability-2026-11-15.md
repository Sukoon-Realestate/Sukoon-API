# Rental details readability

Updated the sibling mobile repository's `RentalSelectionPanel`. The selected
offer's existing data is preserved. The price now uses the shared amount/unit
typography; availability and accommodation are secondary text. Rental terms use
aligned labels and values, stacking on narrow screens or at large text sizes.
Description and house rules have separate headings, larger section gaps and
comfortable line spacing. Rules render as individual bullet rows. Historical
offer snapshots retain their existing source and historical notice.

Validation: 16 layout checks passed across Arabic/English, light/dark, 320/390
widths and 1×/2× text. Checks include long-description preservation and actual
section separation. The existing historical bed summary check passed as well.
Targeted Dart analysis reports no issues. The rendered Arabic preview was
visually reviewed and saved to `output/rental-details-readability/arabic.png`.
No live simulator rebuild was performed for this revision.
