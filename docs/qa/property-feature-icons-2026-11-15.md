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

## Follow-up: hosted data and seen badge spacing

Read the public hosted homepage at
`https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/homepage/?page=1&rental_offers_version=1`.
Its nine rows match the user's property titles and omit `amenities`, tags and
boolean feature flags. This confirms why the new feature row is empty against
the hosted service. The previous local API changes have not reached that service.
DigitalOcean CLI is installed but has no authenticated access token, so this
session cannot deploy it.

The seen badge on home/search now gets 12 logical pixels of top spacing and the
same side gutters as its card copy. Spacing is applied only for visible memory
content; unseen cards retain zero blank margin. Existing saved/offer placements
retain their defaults. Three rendered geometry tests passed for RTL/LTR and an
unseen card, and targeted analysis reports no issues. Combined with the previous
amenity/home regression suite, 14 mobile tests passed. Flutter attach could not
connect to the running simulator, so this change was not hot-reloaded or observed
in the live app.

## Hosted verification after deployment authorization

The prepared API commit `07f2d0b894f163c759b6e675da78507bf07b7383` is now
on GitHub `main`. A subsequent read of the hosted homepage confirmed that all
nine property rows now expose `amenities`, including Wi-Fi, air conditioning,
elevator and other available features. The hosted response changed since the
earlier inspection; no manual DigitalOcean deployment was needed or performed.
Refresh the mobile property list to replace its earlier cached response.
