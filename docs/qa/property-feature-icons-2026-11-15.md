# Property feature icons

The existing mobile home/search card layout is retained. The shared amenity row
now appends available property features with icons and existing localized labels
after rooms, bathrooms and area. It wraps at narrow widths and removes duplicate
amenity IDs. Search no longer repeats the same amenities as plain text chips.

Supported features: Wi-Fi, air conditioning, elevator, parking, security, balcony,
metro proximity, natural gas, electricity meter and water meter. Unknown future
features retain their server label and use a generic check icon.

The home model preserves amenities through JSON, cache, copy and details preview.
Both list serializers in this API repository expose stable amenity IDs derived
from the existing property flags. No database migration is needed.

Mobile changes are in the sibling `sokoun` repository under `apps/sokoun_app`.
Home/search taps, prices, property facts, memory badges and navigation remain at
their existing entry points. No interaction or motion behavior was changed.

Validation:

- 11 mobile tests passed, including actual Arabic/English translations, 320-pixel
  layouts, 1.5 text scale, icon presence/absence, deduplication and home cache flow.
- Targeted Dart analysis: no issues.
- Full app analysis: 12 pre-existing findings in files outside this change.
- 2 API endpoint tests passed, covering homepage and property-list routes.
- Live device review and deployment were not performed.

The mobile and API changes must run together for home-feed amenities to appear;
an older API response with no amenities keeps the existing facts-only row.
