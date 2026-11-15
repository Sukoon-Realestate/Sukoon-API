# Viewing day plan UI cleanup

Reduced guidance and dropdown typography, localized the date display while preserving the explicit Africa/Cairo time zone, used a compact calendar row, and standardized dense field padding. The optional starting-point action is leading-aligned with a 48px minimum target; refresh and the fresh-plan empty state have separate spacing. Existing origin/departure picker and removal, loading/error/message feedback, query changes, recalculation, conflicts, visit arrival/scheduling links and lifecycle reload remain.

25 checks passed: 16 responsive interaction cases across Arabic/English, 320/390 widths, dark/light and 1x/2x text, plus 9 existing arrival/day-plan checks. Selecting 45 minutes still updates the query and clears stale plans. Arabic preview inspected. Diff whitespace check passed. Device maps, keyboard and physical-device runtime were not reviewed; no real visit or plan was changed.
