# Sokoun mobile backend integration

Date: 2026-10-03. Contract: [MOBILE_DEV_HANDOFF.md](MOBILE_DEV_HANDOFF.md).
Scope: `apps/sokoun_app/lib` and supporting core helpers.

## Implemented

| Backend area | Mobile behavior |
| --- | --- |
| Profile city | Owner and tenant profile editing loads the nested city and email. A paginated city picker reads `properties/cities/`. Saving a changed city sends its ID; clearing sends `city_id: ""`; unrelated edits omit `city_id`. |
| Property verification | Existing models keep listing verification, owner KYC, and ownership verification independent. Tests verify the handoff response and nested owner flag precedence. |
| Availability | GET requests send `week_start`, with separate caches for each property and week. All seven returned-week dates are selectable, including days with no saved slots. Users add their own times; no preset availability is invented. |
| Availability saves | PUT replaces the selected date's slots. Booked slots cannot be toggled. Edits survive date/week changes; saving submits every edited date. Failures retain drafts, and partial success retries only failed dates. Server conflict messages are shown. |
| Property analytics | Loads `properties/{id}/statistics/` with 7-, 30-, or 90-day filters. Displays actual views, visit requests, saves, acceptance rate, dated chart history, and returned search criteria. A later filter selection cannot be overwritten by a slower request. |
| Revenue | Loads `properties/owner/revenues/`. Uses decimal amounts, supplied currency/formatting, comparison text, paid/upcoming labels, nullable due dates, and explicit credit/debit direction. Empty and failed responses have recovery states. |
| Property creation options | Rental periods, amenities, and tenant categories use the existing filter-options lookup. Review displays returned labels while requests send API values. Editing retains weekly periods, student categories, and electricity/water meters. |
| Business policies | Reset-link guidance now says 24 hours; OTP guidance says 10 minutes, retaining six digits and the 60-second resend timer. Existing avatar/KYC validation already supports the confirmed 10 MB limit and formats. Property media retains the recommended 10–25 photos and 60-second video limit. |
| Profile counters | Existing API-backed ratings, review counts, membership labels, account/menu counters, completion percentage, and identity status remain connected to their documented responses. |

Availability opened from a property starts in the current **Africa/Cairo** week,
using daylight-saving rules rather than a fixed UTC offset. Explicit calendar
dates remain selectable.

## Where to find the features

- **Edit profile → City:** choose or clear a city for either account workspace.
- **Owner → My properties → Property analytics:** statistics and period filters.
- **Owner → My properties → Availability times:** week navigation and visit times.
- **Owner → Visit calendar → Manage availability:** availability for that property.
- **Owner → More → Revenue:** monthly revenue, property amounts, and transactions.
- **Owner → Add/edit property → Pricing:** supported backend option labels.

## Verification

The contract and widget tests use responses copied from the supplied handoff,
without making changes to live backend data. They cover city preservation,
selection/clearing and PATCH requests; independent verification; analytics
queries, caching and stale responses; revenue parsing, empty/error states and
retry; availability week queries, adding times, booked-slot protection,
multi-day saves and conflicts; creation options; and real navigation entry points.

Analytics, revenue, and availability were rendered and scrolled in Arabic and
English at widths **320, 390, 600, 768, 1024, and 1366**, with text scales
**1, 1.3, and 2**. Phone and desktop previews were also captured and inspected.

Final checks used Flutter **3.35.1**, matching the current workspace package
configuration:

- **169 relevant tests passed**, including 55 new handoff tests.
- Full app suite: **1,332 passed; 9 existing failures**. Eight are refresh
  indicator expectations in `test/sokoun_refresh_indicator_test.dart`; one is
  the workspace reset expectation in `test/workspace_account_test.dart`.
  These tests and their implementation files are unchanged from HEAD.
- App analysis: **no errors or new warnings**; six existing warnings remain
  for unused imports and a path dependency.
- Time-zone helper analysis: no issues. Formatting and `git diff --check` passed.

To repeat the checks from `apps/sokoun_app` with the workspace's configured Flutter:

```sh
flutter test --no-pub test/mobile_dev_handoff_integration_test.dart
flutter test --no-pub
flutter analyze --no-pub
```

Optional preview capture:

```sh
HANDOFF_CAPTURE_DIR=/tmp/sokoun-handoff-previews \
  flutter test --no-pub test/mobile_dev_handoff_integration_test.dart
```

Live authenticated backend/device smoke testing has not been performed.
The older backend task list and static-data audit describe the state before this
handoff; this document records the integration that followed it.
