# Sokoun static-data audit and backend requirements

Audit date: 2026-10-02. Scope: `apps/sokoun_app/lib`.

The initial scan covered 567 Dart files, including 59 files under `screens/`
and 317 files under feature `widgets/` or `shared_widgets/`. Screen classes
outside those folders and the models supplying UI content were included.
Hardcoded literals, sample lists, localization strings containing sample facts,
initial-state fallbacks, and their production call sites were checked against
`collection.json` and existing data sources. This is a source and widget-test
audit; it does not certify live backend responses.

## Frontend fixes completed

| Area | Finding | Result |
| --- | --- | --- |
| Tenant home | The banner ignored `homepage.banner` and always claimed a visit today at 3 PM at a Nasr City apartment. | Displays the actual non-empty API/cached banner text. Null and blank banners are hidden. |
| Booking | The selected property always had sample metadata saying 6500 per month and three rooms. The screen also defaulted to a prototype property. | Booking requires a supplied property and builds metadata from its actual price, rental period, and bedrooms. |
| Property details | Review count was always zero. | Loads `summary.total_reviews` and `summary.average_rating` from the documented reviews endpoint, with a cache per property. Missing or failed summaries do not display invented totals. |
| Property and owner listings | Rental prices could always be labelled monthly. | Displays the supplied `price_period`. Owner listings retain this value through parsing, cache serialization, and edits. |
| Property owner | The owner badge always said verified, including when owner verification was unknown. Property verification was also treated as verified ownership proof. | Uses independent explicit flags. Missing flags do not display either claim. See the required backend fields below. |
| Owner profile | Missing labels became a fixed 4.8 rating from 42 reviews and a January 2025 membership date. The avatar always had a check badge. | Rating fallback uses returned numerical rating/review totals. Missing membership displays a neutral unset value. The avatar check follows verification. |
| Tenant profile and summary | Missing membership labels became January 2026/January 2024. Contract and review subtitles defaulted to one active contract and two reviews. | Uses returned membership labels or a generic tenant label, and returned menu counts for subtitles. |
| Profile editing | Owner city was always Cairo. The loaded avatar URL was ignored. | City displays an unset value until a location contract exists. The avatar uses the loaded URL. |
| Property creation | A fixed list of property types was rendered despite an existing lookup endpoint. | Uses API names for chips and retains the selected API slug separately for submission. Existing edited values remain supported. |
| Owner availability | Dates/hours and all initial slot states were created locally; saved availability was never read. | Reads server dates and slots, initializes available/booked/disabled states, disables booked controls, and preserves booked flags in PUT submissions. An empty successful schedule has an explicit empty state. |
| Analytics | A notification's view count was combined with initial zero values for unavailable statistics. Dates said 30/14 days without response metadata. | Partial analytics shows the notification view count and an unavailable-details message. Unsupported date claims were removed. Zero-valued charts no longer divide by zero. |
| Sample helpers | Sample visits, listings, obsolete Cairo-only filter choices, and favorites existed in production model files. Request-loading skeletons also contained sample names, cities, and appointments. | Removed unused visit/listing/filter samples. Moved favorites fixtures to `apps/sokoun_app/test/helpers/favorites_fixtures.dart`. Request skeletons use neutral shapes. |

Existing API-backed lists remain API-backed. Optional fixture constructor inputs
used by tests are caller-supplied; production routes do not supply sample lists.
Loading-only empty models and shimmer shapes remain local.

## Existing endpoints now used by these fixes

Paths below are relative to the existing API base, including its version prefix.
These methods and response structures are present in `collection.json`.

| Method and path | Consumed data |
| --- | --- |
| `GET homepage/` | `data.banner`: string or null; property results remain paginated. |
| `GET properties/types/` | `data.results[]`: `id`, `name`, `slug`; the owner form submits the slug as `property_type`. |
| `GET properties/{property_id}/reviews/` | `data.summary.total_reviews`, `data.summary.average_rating`. Query: `page=1&page_size=10`. Review-list pagination still has its own owner. |
| `GET properties/owner/properties/{property_id}/availability/` | `data.week_start`, `week_end`, `days[].date`, `day`, `slots[].id`, `time`, `is_enabled`, `state`, `visit`. |
| `PUT properties/owner/properties/{property_id}/availability/` | Existing body: `availability_date`, `slots[]` containing `time` and `is_enabled`. |

## Backend work or confirmation still needed

### 1. Profile city

Affected widget:
`features/shared/profile/presentation/widgets/shared/profile_edit_view.dart`.

`GET profiles/user/my-profile/` has no city in the supplied example. Please
define a canonical location field, its null behavior, and whether users can edit
it. Suggested additive read fields:

```json
{
  "data": {
    "city": {"id": "city-id", "name": "Alexandria", "slug": "alexandria"}
  }
}
```

If editable, confirm the field accepted by `PATCH profiles/edit/` (for example
`city_id`) and whether it uses `properties/cities/` or a separate profile-city
lookup. The client currently shows an unset value; no city write was invented.

### 2. Owner verification and verified ownership proof

Affected model: `features/tenant/home/data/models/property_details_model.dart`.
Affected widgets: `tenant_property_details/owner_card.dart` and
`tenant_property_details/details_content.dart`.

Confirm/add independent fields in `GET properties/{property_id}/`:

```json
{
  "data": {
    "is_verified": true,
    "owner": {"id": "owner-id", "full_name": "Owner name", "is_verified": false},
    "is_ownership_verified": false
  }
}
```

The frontend accepts nested `owner.is_verified` or flat `owner_is_verified`
for the owner badge, and `is_ownership_verified` for the ownership banner.
These are additive fields supported by the frontend, requiring backend
confirmation. A property's `is_verified` and the existence of an uploaded
`ownership_proof` do not establish either independent status. Omitted fields
are treated as unknown and their badges are hidden.

### 3. Availability for new schedules and other weeks

The documented GET response supplies a week and its existing slots, but does
not specify a week-selection query or a catalog of editable disabled slots.
Please confirm:

- The default returned week and schedule timezone.
- How to request another week/date. Document a query such as `week_start`
  before the client uses it; the current client sends the documented GET
  without an invented query.
- Whether GET includes disabled candidate slots and days with no enabled slots.
  Return the valid candidate dates/times if this grid is intended to create a
  property's first schedule. Currently an empty response has no editable
  hours and cannot create a schedule.
- Whether PUT replaces that day's complete schedule, and how omitted/booked
  slots are handled. Revalidate booked slots server-side and reject conflicting
  changes.

The screen uses the server's returned days and selects the requested date when
present, otherwise the first returned day. It does not invent a missing week.
The calendar currently has no production action opening the availability
screen; adding that product entry point is separate from this data audit.

### 4. Detailed owner analytics and revenue

Affected screens: `OwnerPropertyAnalyticsScreen`, `OwnerRevenueScreen`.

No detailed analytics/revenue request is wired in the existing app. Analytics
can be opened from a property-views notification, which supplies a view count
but not the other statistics. Revenue takes constructor data and has no
production call site. Define/document endpoints before enabling these full
features. Required analytics data:

- Property ID and the actual reporting period (`period_start`, `period_end`,
  timezone, aggregation interval).
- `views`, `visit_requests`, `saves`, `acceptance_rate`.
- View history with dates and counts; clarify order and whether missing dates
  mean zero or unavailable.
- `space_interest`, `price_interest`, `location_interest`, `amenities_interest`,
  with units and calculation definitions.

Required revenue data:

- Reporting month/year, currency, total, growth value and comparison period.
- Per-property ID/title, amount, due date, payment status.
- Paginated transactions with ID, title, date, amount, and credit/debit meaning.

Treat unavailable values separately from actual zero values. No guessed
endpoint or fabricated financial/statistical data was added.

### 5. Existing profile labels and counters

The existing owner/profile and account-summary responses already have the
necessary fields. Ensure they contain each user's real data:

- `GET properties/owner/profile/`: `owner.average_rating`, `reviews_count`,
  optional `rating_label`, `member_since_label`, and `is_verified`.
- `GET profiles/my-account/`: `user.role_label`, `member_since_label`,
  `menu_items.contracts.count`, `menu_items.reviews.count`, and optional
  localized subtitles.
- `GET profiles/account-summary/`: `user.role_label`, `member_since_label`.

No new endpoints are needed for these fixed fallbacks. Return labels in the
requested language if the backend owns their formatting.

### 6. Fixed business choices and policy copy

The following local values describe choices/rules, not sample user records:

- Property amenities, deposit choices, rental units, suitable tenant categories,
  smoking choices, gender choices, and supported app languages.
- Property photo limits (10–25), video duration limit (60 seconds), KYC upload
  copy stating a 5 MB limit, password-reset copy stating 15 minutes, owner
  response copy stating 24 hours, and property-review copy stating 24–48 hours.

Confirm that these match backend validation and the actual service policies.
If they are configurable, provide a documented options/config response with
stable submission values, localized labels, enabled flags, and numerical
limits/expiry durations. The existing search-filter options endpoint is not
assumed to be the creation-form policy contract. Fixed UI labels, weekday
names, icons, colors, asset paths, and navigation destinations do not require
backend integration.

## Feature coverage

| Group | Screens/flows checked |
| --- | --- |
| Shell/splash | Splash, workspace navigation, home tabs and counts. |
| Auth | Welcome, registration, login, OTP, recovery, KYC intro/upload/pending/approved. |
| Tenant discovery | Home, search, filters, results, details, gallery and sharing. |
| Tenant visits/favorites | Booking, confirmation, visits, details/reviews, favorites. |
| Owner home/listings | Dashboard, requests, listings, property creation/editing, location picker. |
| Owner visits | Request details, calendar, availability. |
| Owner properties | Properties, edit, rejection/resubmission, analytics, revenue. |
| Shared profile | Both profiles/edit forms, summary, settings, language, owner menu. |
| Chat | Lists, search, current/previous conversations, thread/start/restricted screens. |
| Notifications/content | Lists, detail/actions/settings, public pages, property/my reviews, what's new. |

## Verification

- Dart formatting and `git diff --check` passed.
- `flutter analyze --no-pub`: no errors; six existing warnings and two existing
  deprecation notices remain in unrelated files/pubspec configuration.
- All eight new tests in `test/static_data_integration_test.dart` passed.
  They cover actual booking metadata, independent verification, per-property
  review-summary loading/cache/identity, missing summary values, API property
  types and submitted slugs, availability loading/booked-slot preservation,
  profile-count fallbacks, partial analytics, and empty/error states.
- The final focused run, including owner property creation and owner visit
  requests, passed all 33 tests.
- Final full app suite: **1,255 passed, 10 failed**. Every failing test also
  failed on the original `HEAD` in a separate temporary checkout with the
  same Flutter SDK. The failures are eight refresh-indicator assertions, one
  workspace preference restoration assertion, and one selection-chip semantics
  assertion (`Tristate.isTrue` versus `true`). These are outside this audit's
  changes.
- Existing adaptive layout tests passed, including property details, booking,
  availability, and tenant profile content in Arabic/English at widths 320,
  390, 600, 768, 1024, and 1366 and text scales 1, 1.3, and 2. The new data
  integration tests render phone-size widgets and exercise their interactions.

Commands ran from `apps/sokoun_app` using Flutter 3.44.7. Verification uses
fake repositories populated with explicit test responses and the supplied API
collection. No live backend credentials, physical device session, or visual
screenshot comparison was used for this audit.
