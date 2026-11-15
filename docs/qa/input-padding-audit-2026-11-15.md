# Embedded input action padding audit — 2026-11-15

The reported defect was reproduced in `TenantSearchField`: the filled Search action occupied an input prefix-icon slot with only a start inset, so its colored background touched the top and bottom border. InputDecoration's text contentPadding does not inset icon slots.

The action now uses a standard TextButton with directional outer insets of start/top/bottom 6 points and end 8 points, a minimum 48×48 touch target, and an inner radius suited to the outer field. Submit, clear, keyboard action and query ownership remain unchanged.

## App-wide source audit

Searched all application Dart sources for prefixIcon, suffixIcon, prefixWidget, custom search controls and embedded search actions, and inspected shared core field decoration/input ownership. The 16 app files declaring icon slots include search/results, owner location search, chat search/forwarding/property sharing, public-owner listings, support, rental-center search, authentication, phone/date fields, and property forms. Inspected HomeSearchBox and chat composers as separate composite controls.

| Surface | Finding / action |
| --- | --- |
| Dedicated housing search | Sole occurrence of a filled custom action with only one-sided external padding; fixed. |
| Home search entry | Existing button already provides internal gutters around its content; preserved. |
| Results and chat search | Standard unfilled icon slots and centered clear actions; painted glyphs remained inside field bounds. |
| Owner location / comparison / forwarding / shared search forms | Standard Icon/IconButton controls; no matching colored-prefix defect found in source. |
| Phone and property suffix content | Explicit horizontal insets already present; preserved. |
| Shared date field | Plain IconButtons, no colored-prefix defect; glyph containment checked alongside search and phone inputs. |
| Core DefaultTextField | Correctly forwards icon slots. No blanket padding change was applied to unrelated input types. |

## Verification

All 39 final focused tests passed: 16 corrected-search geometry/interaction cases, four representative shared-input bounds cases, 17 search-screen cases and two results UX cases. Covered RTL/LTR, light/dark search fields, widths 320/390, 100%/200% text, painted-button border insets, text separation, minimum touch size, submit and clear. The other-input tests measure painted icon glyphs rather than full-width decoration slots.

Changed-file analysis and whitespace checks passed. Rendered Arabic initial and selected previews were inspected and exported under `output/input-padding-audit/` with fixture catalog/area data. Live device interaction/performance remains unverified.

The initial broader targeted run also exercised the unchanged `sokoun_date_field_test.dart`; two existing disabled-date-picker assertions failed at line 213. They concern enabled callbacks rather than padding and were not modified. The final padding/search suite is green; this is not an assertion that the whole repository test suite passes.

Logs: `/tmp/input-padding-verified-tests.log`, `/tmp/input-padding-analysis.log`; initial wider run: `/tmp/input-padding-tests.log`.
