# Sokoun — backend tasks

Date: 2026-10-02

Please implement the missing data or confirm the existing API contracts below
so the app can display real information. If an item already exists, provide its
documented request/response and an example instead of creating another endpoint.

Paths are relative to the existing versioned API base. Proposed fields and
query parameters are labelled; they still require backend confirmation.

## 1. Profile city

**Existing endpoints:**

- `GET profiles/user/my-profile/`
- `PATCH profiles/edit/`

The supplied profile response has no city. Please define:

- The city field returned with the profile, including its ID and display name.
- What is returned when the user has no city.
- Whether users can edit their city. If so, document the accepted PATCH field
  and whether the choices come from `properties/cities/` or another lookup.

Suggested GET response addition, requiring confirmation:

```json
{
  "data": {
    "city": {
      "id": "city-id",
      "name": "Alexandria",
      "slug": "alexandria"
    }
  }
}
```

If editing is supported, `city_id` is a suggested PATCH field, not a confirmed
one. The app currently displays "Not set yet" until this contract is agreed
and integrated.

## 2. Owner verification and ownership verification

**Existing endpoint:** `GET properties/{property_id}/`

Please return separate statuses for:

- Property verification: existing `is_verified`.
- Owner identity verification: `owner.is_verified` or `owner_is_verified`.
- Verified ownership proof: `is_ownership_verified`.

The frontend already supports the latter two field names, but the backend
needs to confirm or add them. Example response with the requested additions:

```json
{
  "data": {
    "is_verified": true,
    "owner": {
      "id": "owner-id",
      "full_name": "Owner name",
      "is_verified": false
    },
    "is_ownership_verified": false
  }
}
```

Each flag must represent its own verified status. An uploaded ownership
document alone does not mean it was approved. The app hides the owner and
ownership badges when their explicit flags are missing or false.

## 3. Visit availability: new schedules and other weeks

**Existing endpoints:**

- `GET properties/owner/properties/{property_id}/availability/`
- `PUT properties/owner/properties/{property_id}/availability/`

The app already reads returned dates and slots and saves changes. Please
complete or confirm these details:

- Which week GET returns by default, and the timezone used for dates/times.
- How to request another week or date. A query such as `week_start` is a
  proposal and must be documented before the app uses it.
- Whether GET includes all valid editable candidate slots, including disabled
  slots and days with no enabled slots. These are needed to create a property's
  first schedule without inventing hours locally.
- Whether PUT replaces the complete schedule for the selected day, and what
  happens to omitted slots.
- How booked slots are protected. Validate conflicts on the server and
  document the error response for rejected changes.

The documented GET fields are `week_start`, `week_end`, and `days[]` containing
`date`, `day`, and `slots[]`. Each slot includes `id`, `time`, `is_enabled`,
`state`, and `visit`.

The existing PUT body contains `availability_date` and `slots[]` with `time`
and `is_enabled`.

Currently an empty GET response shows an empty schedule and provides no hours
to edit. The app preserves booked slot flags when saving. Opening this screen
from the calendar still requires separate frontend navigation work.

## 4. Detailed owner analytics and revenue

**Endpoint paths are not defined in the current integration.** Please document
the endpoints, supported reporting-period filters, and response fields.

### Property analytics

Required data:

- Property ID, reporting start/end dates, timezone, and aggregation interval.
- `views`, `visit_requests`, `saves`, and `acceptance_rate`.
- View history with an explicit date and count for each point.
- `space_interest`, `price_interest`, `location_interest`, and
  `amenities_interest`, including their units and calculation definitions.

Document how missing dates and unavailable metrics are represented. Actual
zero values must be distinguishable from unavailable data.

The current notification supplies only a view count. The app displays that
count and explains that detailed statistics are unavailable.

### Revenue

Required data:

- Reporting month/year, currency, total revenue, growth value, and comparison
  period. Specify whether growth is an amount or a percentage.
- Per-property ID/title, amount, due date, and payment status.
- Paginated transactions with ID, title, date, amount, and credit/debit meaning.

The revenue screen currently has no API integration or production entry point.
Frontend integration can follow once the contract is supplied.

## 5. Confirm real profile labels and counters

These existing endpoints already expose the required fields in the supplied
contract. Please confirm they return each user's actual values:

| Endpoint | Fields under `data` |
| --- | --- |
| `GET properties/owner/profile/` | `owner.average_rating`, `owner.reviews_count`, `owner.is_verified`, optional `owner.rating_label` and `owner.member_since_label`. |
| `GET profiles/my-account/` | `user.role_label`, `user.member_since_label`, `menu_items.contracts.count`, `menu_items.reviews.count`, and optional menu subtitles. |
| `GET profiles/account-summary/` | `user.role_label` and `user.member_since_label`. |

No new endpoint is requested for these fields. If the backend supplies formatted
labels, return them in the requested language. The app already uses returned
counts and neutral fallbacks when labels are absent.

## 6. Confirm business options and limits

Please confirm that backend validation and service policies match these values
currently used by the app:

| Rule or policy | Current frontend value/copy |
| --- | --- |
| Property photos | Minimum 10, maximum 25. |
| Property video duration | Maximum 60 seconds. |
| KYC upload size | Copy states a 5 MB limit. |
| Password-reset expiry | Copy states 15 minutes. |
| Owner response time | Copy states 24 hours. |
| Property submission review time | Copy states 24–48 hours. |

Also confirm supported amenities, deposit choices, rental units, suitable
tenant categories, smoking choices, gender choices, and app languages.

If these options or limits are configurable, document a configuration response
with stable submission values, localized labels, enabled flags, numerical
limits, and expiry durations. The search-filter options endpoint is not yet
confirmed as the contract for property-creation options.

## Information to return for the handoff

For each item, state whether it is implemented, already supported, or awaiting
a product decision. Update the API collection/documentation with confirmed
paths, query parameters, request bodies, response examples, null behavior, and
relevant validation errors. This lets the frontend integration use the agreed
contract.
