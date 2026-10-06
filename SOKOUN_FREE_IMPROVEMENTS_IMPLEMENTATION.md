# Sokoun — free improvements implemented

> Historical record of the original free batch. For the current all-free feature policy, complete backend contracts and backend response format, use [SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md](SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md). Send that consolidated file to the backend.

This document describes the client changes in this batch. The features have no subscription or paywall. Backend-dependent additions are listed separately so implemented screens are not confused with services that still need server work.

## Features and where to find them

| Improvement | In-app entry | Behavior |
| --- | --- | --- |
| Property comparison | Property details → Compare; search results or Favorites → My decision tools | Save up to three properties and compare their current details. Missing listings remain identifiable and removable. Cached listings are labelled. Listing, owner identity, and ownership verification appear separately. |
| Clear rental costs | Property details and comparison | Show listed rent, a stated deposit, and their known subtotal. Missing terms remain unknown. Month-based deposits are calculated only against monthly rent. Utilities, services, and brokerage charges are not assumed to be zero. |
| Private decision lists | My decision tools | Group properties into named lists and keep private notes on this device, scoped to the account. Removing a comparison selection preserves its notes. |
| Viewing checklist | Property details → Private notes; visit details → Private viewing notes | Check water, daylight, noise, maintenance, internet, costs, and safety. Notes are associated with the actual property ID. |
| Saved searches | Search results → Save search; My decision tools → Saved searches | Save a name and all selected search criteria. Reopening runs the existing search with those criteria. Duplicate criteria update the existing saved search. Automatic alerts are not enabled. |
| Search map and list | Search results → Map and list | Display actual coordinates from loaded search results. Filter those results to the visible map area, clear the area filter, and load additional pages. Missing coordinates are explained rather than replaced by invented pins. |
| Explained matches | Open a property from filtered results or the map | Describe matches supported by actual price, billing period, property type, amenities, bedrooms, or listing verification. No inferred commute, neighbourhood score, or AI recommendation is shown. |
| Availability transparency | Property details | Show `availability_confirmed_at` when provided. Otherwise explicitly say that owner confirmation has not been provided. Updating a listing is not treated as confirming its availability. |
| Real viewing slots | Property details → Book visit | Load server-provided dates and available times, exclude past or invalid Egypt times, clear the time when the date changes, and recheck availability before reviewing the request. Cached slots cannot authorize a booking. |
| Booking review and clear confirmation | Book visit → Confirm request | Review the property, day, time, note, and pending status before submitting. Failed submissions preserve the form and refresh times. Success means the request was sent; it does not promise owner acceptance or a response within 24 hours. |
| Calendar export | An accepted visit with exact `visit_date` and `visit_time` → Export to calendar | Share an `.ics` appointment using Egypt time converted to UTC, with a stable visit ID and a reminder one hour before it. The OS/calendar application handles importing it. This is not automatic calendar synchronization. |
| Review eligibility and notification navigation | Visit details and review notifications | Prefer explicit server action permissions. Without them, accepted visits need a known past appointment, or a completed status, before review. Review notifications open real visit details; missing visit IDs open the visits list. Existing reviews are not submitted again. |
| Owner draft recovery | Add/edit property → Save draft; reopening the same editor | Autosave form fields, step, media, metadata, and acknowledged property/image IDs. Copy picked photos, video, and proof into the account's private application directory. Offer resume, discard the local draft, or save before leaving. Missing files are reported. Storage failures remain visible and can be retried. |
| Photo order and cover | Owner property photo tiles → menu | Move a photo earlier or later and select the cover while preserving file references, remote IDs, and captions. Local drafts preserve the order. Server ordering of retained images needs contract confirmation. |
| Listing quality suggestions | Owner publication review | Show practical checks for photos, map location, description, deposit, captions, and video. Suggestions do not change publication validators or imply verification. |
| Rejection explanation | Owner rejected-property screen | Display an actual backend rejection reason when supplied, with a clear fallback when it is absent. |
| Honest owner statistics | Owner profile → Statistics | Distinguish an unavailable acceptance rate from an explicitly supplied 0%. Preserve that distinction when caching profile data. |
| Durable chat drafts | Chat composer and recovered-message panel | Encrypt local drafts and uncertain outgoing messages by account and conversation. Save before sending. Restore uncertain messages for explicit review and sending after restart; never automatically replay them. Preserve typed text when saving fails. |
| Messaging permissions and lifecycle | Chat entries and composer | The other participant's verification badge does not decide the current account's permission. Open history, and hide sending when `can_send` is explicitly false. Draft persistence cannot delay socket ownership during pause/resume or closing. |
| Real reports with receipts | Chat → menu → Report a problem | Submit a support ticket with conversation, participant, property, reason, and details. Success requires an ID, reference, and saved message. Failure or an incomplete receipt preserves the details for retry. Successful reporting keeps the chat accessible. |

## Architecture

The implementation follows [.agents/skills/sokoun-feature-architecture/SKILL.md](.agents/skills/sokoun-feature-architecture/SKILL.md) and [apps/sokoun_app/AGENTS.md](apps/sokoun_app/AGENTS.md).

- `features/tenant/decision_tools/data/` owns notebook, comparison, cost, and matching models plus local storage and rules. `presentation/cubits/` owns state and remote comparison loading. Screens compose extracted widgets.
- The map uses the existing `PropertySearchData` and `AppPagify` contract. Its leaf widget owns pagination and temporary viewport/camera state; screen code does not perform network calls.
- Visits retain their existing part/import barrel. Availability uses typed `AsyncCubit` states, stored initial futures, cache serialization, property/date/account cache keys, and suppression of stale date responses. The request review is an extracted widget.
- Owner drafts use a data store and a local Cubit. Local encoding is separate from the multipart publication body. Autosaves are serialized, file writes are atomic, and account-session changes suppress stale writes and state updates.
- Chat persistence lives in `data/`, and transport/state remain in `ChatThreadCubit`. UI controllers remain in the leaf widgets. Chat cache keys encode the account/conversation pair without ambiguous separators.
- Navigation uses `Go`. Pagination and remote state views retain the project's existing components. Labels originate in `packages/core/assets/translations/lang.json`; Arabic, English, and `LocaleKeys` files are generated from it.

Existing owner requirements remain **10–25 photos and a valid 1–60 second video**. Rental billing period and minimum stay remain separate. Guest discovery, shared account identity, and separate owner/tenant workspaces continue through the existing navigation.

## Backend contracts and remaining free work

| Area | Client behavior now | Backend work or confirmation still required |
| --- | --- | --- |
| Availability | Uses `GET properties/{id}/available_dates/` and the same route with `?date=YYYY-MM-DD`. Days require `visit_date`; times require `visit_time` and `is_available`. | Atomically validate the slot during booking and return conflicts. Cached availability must never override server authorization. |
| Calendar and reviews | Read exact `visit_date`/`visit_time` and explicit `actions`. | Return exact appointment fields and accurate permissions in visit responses. Rescheduling, completion recording, synchronized calendar changes, and cancellation updates need lifecycle contracts. |
| Saved searches | Account-scoped storage and manual rerunning. | Server-saved searches, matching jobs, delivery preferences, and push/email alerts. |
| Map search | Area filtering is explicitly limited to loaded results. | Whole-catalogue bounding-box/radius search, location-privacy rules, and nearby service/route data. |
| Listing freshness | Reads `availability_confirmed_at`, never `updated_at` as a substitute. | Provide owner confirmation metadata and an authorized confirmation action. |
| Property lifecycle | Shows existing statuses and supplied rejection reasons. | Pause, rented/unavailable, renewal, reactivation, and stale-listing transitions. No invented transition endpoint has been added. |
| Owner media | Saves acknowledged IDs and copies pending files durably. | Confirm ordering of `retained_image_ids` and all media-ID responses. Uploads acknowledged after local storage fails cannot be guaranteed to survive a process kill. Server idempotency is needed for an ambiguous create/upload response. |
| Chat eligibility | Opens history; honors explicit `can_send: false`. | Return current-account eligibility and enforce KYC/authorization on the server. A peer's badge is not sufficient evidence. |
| Chat delivery | Existing live retries remain; restart recovery requires explicit review. | Socket/REST acknowledgements need a shared `client_message_id` and idempotency contract to guarantee that a timeout/fallback cannot duplicate a message. That guarantee is not claimed by this batch. |
| Reports | Uses existing support-ticket submission with `report_owner` or `report_tenant` and contextual details. | Return a durable receipt; enforce ticket privacy and moderation access. Server-side blocking is a separate action and has not been simulated locally. |
| Owner statistics | Existing API-backed dashboard remains available; an absent or invalid acceptance rate displays “Not set yet”. | Additional funnel counts and metric definitions need real server measurements. No income or activity has been invented. |

Basic browsing, search, favourites, chat history, viewing requests, support, and verification access remain free. This batch does not introduce promoted listings, priority alerts, paid analytics, AI services, contracts/signing, or payment collection.

## Verification and visual review

Use Flutter **3.44.7 / Dart 3.12.2**, the SDK used for this session, or a compatible project SDK.

```sh
cd apps/sokoun_app
make freeFeaturesCheck
make freeFeaturesUiReview FREE_REVIEW_DIR=/tmp/sokoun-free-after
```

The new data tests exercise account isolation, concurrent notebook updates, comparison capacity, full filter restoration, unknown costs, Egypt daylight-saving rules, calendar escaping/folding, truthful matching, viewport bounds, durable file recovery, missing media, and failed storage. Chat tests cover explicit recovery, restricted sending, delayed delivery, socket ownership, and draft retention. Visit/report flows cover stale availability and failed or incomplete receipts.

Visual review covers Arabic and English, both themes, widths **320, 390, 600, 768, 1024, and 1366**, and text scales **1, 1.3, and 2**. Representative PNGs are exported for 390 and 1024 widths. The existing visual fixtures provide the before renders in `/tmp/sokoun-free-before`; the new fixtures export to `/tmp/sokoun-free-after`.

The review checks: reachable entry points, primary actions, content hierarchy, spacing and wrapping, currency/term clarity, RTL direction, contrast/theme consistency, text scaling and scrolling, and empty/error/cached/retry states. Generated empty-state animations respect reduced-motion settings. Comparison is horizontally scrollable on small screens and uses a wider layout on tablets.

Native map tiles, calendar import through the OS share sheet, picker permissions, and recovery after an actual device process kill still require device verification. Widget tests replace native surfaces where necessary; they do not prove native SDK rendering, backend deployment, or receipt durability on a live server.

## Verification results

Verified on **2026-10-06** with Flutter **3.44.7 / Dart 3.12.2**.

| Check | Result |
| --- | --- |
| Complete Sokoun app test suite, including architecture checks | **2,730 passed, 0 failed**. The final run includes the unavailable-listing title adjustment. |
| New free-feature visual fixtures | **72 configurations**, rendering seven panels each (**504 layouts**), without Flutter layout exceptions. |
| Screenshot export | **56 PNGs** in `/tmp/sokoun-free-after`. Arabic/English, light/dark, phone/tablet examples inspected for direction, wrapping, contrast, actions, and missing/cached states. |
| App analyzer | **0 errors**, with two existing unused-import warnings and three existing `TickerMode.of` deprecation notices. None is in a new file. |
| Dart formatting | All **97 changed/new Dart files** pass the formatting check. |
| Whitespace and translation JSON | `git diff --check` passes; source and generated translation JSON parse successfully. |

The analyzer notices remain in `lib/generated/assets.dart`, `lib/shared_widgets/sokoun_refresh_indicator.dart`, `lib/shared_widgets/sokoun_content_transition.dart`, and `lib/features/shared/chat/presentation/widgets/chat_list/chat_list_content.dart`.

An isolated checkout of the original `68747dc` commit reproduced **77 failures in five existing test files**. The updated tests correct the Flutter semantics type, wait for persisted Undo actions and their overlay animation, select API chips by value, and assert the current profile and owner-request flows. The missing acceptance-rate display was corrected in production code. Booking and report fixtures now exercise real availability and receipt contracts. Tests have not been disabled to obtain the passing result.

Final commands, from `apps/sokoun_app`:

```sh
flutter analyze --no-pub --no-fatal-infos --no-fatal-warnings
flutter test --no-pub --dart-define=FREE_UI_REVIEW_DIR=/tmp/sokoun-free-after
```

This verification does not include a native release build or a live-backend run. Native maps, calendar import, media permissions, and recovery after device process termination remain the device checks described above; server-dependent work remains in the backend table.
