# Sokoun UI and UX review

Implemented on 2026-09-29. Scope: Sokoun and the core controls it consumes.
Tajawal and the Arabic-first navy/teal/gold identity are retained.

[Open the interactive before/after gallery](comparison.html).
The gallery contains 24 real Flutter renders: three subjects, two languages,
two viewports, before and after. Welcome is a full screen; property cards and
dashboard metrics are isolated component fixtures. These are widget-test
renders, not screenshots of a live backend session.

## Implemented changes

- Added a shared Material theme, width constraints, adaptive grids, action
  footer, and reduced-motion policy. Standard screens share `AppScaffold`;
  authentication composes it through `AuthScaffold`.
- Disabled viewport inflation of ScreenUtil dimensions while preserving
  accessibility text scaling. Forms cap at 520 logical pixels, reading/task
  pages at 720, and collections/details at 1200.
- Added tablet side navigation at 600 pixels with stable tab state, natural
  one-to-three-column property collections, four-column dashboard metrics,
  and gallery/details columns at 960 available pixels. Tablet displays may
  rotate; phones retain portrait orientation.
- Refined typography, card hierarchy, property imagery, loading controls,
  touch targets, focus ownership, and selection/progress animations.
  Large text wraps or expands its container instead of being shrunk to fit.
- Fixed large-text overflows in date selectors, notifications, chat metadata,
  and profile badges. Date strips keep natural height and remain scrollable.
- Split the owner photo/video flow into dedicated grid, metadata, tips,
  upload, preview, and requirements widgets.
- Migrated tenant-home pagination to the shared `AppPagify` and a data helper.
  Preserved server page links, per-page cache contracts and cached banner
  metadata; added adaptive rows, refresh completion, and stale-result guards.
- Restored existing account-summary shortcuts and refreshed account badges
  when returning to that tab. Removed invented gallery photo counts.
- Added all nine requested rules to the architecture skill and updated
  `Design.md`. A single stale landing-page localization reference was corrected
  to enable its existing smoke tests; its layout was not redesigned.

## Verification

- Sokoun: **741 tests passed**, including the existing feature/navigation suite,
  **540 responsive cases**, 12 render fixtures, and five shared-control checks.
- Responsive cases: 15 representative subjects × widths 320, 390, 600, 768,
  1024, and 1366 × text scales 1, 1.3, and 2 × Arabic/English.
- Covered subjects: actual tenant home, welcome, login, KYC upload, search
  result cards, property details, owner metrics, photo/video steps, booking,
  owner availability, profile header, notification list elements, chat cards,
  and bottom navigation.
- Behavior checks cover phone/tablet navigation state, workspace state,
  pagination and resizing, delayed responses after disposal, refresh completion,
  disabled/duplicate submissions, keyboard insets, footer geometry, and
  reduced motion.
- Shared core: **42 tests passed**. Landing page: **3 tests passed**.
- Final keyboard/footer follow-up: **549 focused checks passed**, including
  the responsive matrix, KYC layouts, and assertions that fixed actions remain
  above the keyboard.
- Analyzer: **zero errors**. Eight pre-existing diagnostics remain: unused
  Google-login method; mutable/unused connectivity-helper members; deprecated
  bottom-sheet/radio APIs; a nullable type-parameter assertion; and a
  super-parameter suggestion.
- Dart formatting and `git diff --check` completed. Skill YAML metadata checked
  with Ruby's standard YAML parser; the optional Python skill validator was
  unavailable because this environment does not have PyYAML.

Native Android/iOS execution, camera/video plugins, live network responses,
and physical-device performance were not verified in this pass. No iOS
simulator was booted. Layout tests cover tablet landscape dimensions and
split-view widths, but are not a substitute for a physical iPad check.

## Reproduce

Use Flutter **3.35.1 / Dart 3.9.0**, matching the resolved workspace SDK.

```sh
cd apps/sokoun_app
flutter test --no-pub
flutter test --no-pub test/ui_visual_review_test.dart --dart-define=UI_REVIEW_DIR=/tmp/sokoun-ui-review
```

Run `flutter test --no-pub` from `packages/core` and `apps/landing_page` for
the shared-control and landing smoke suites. Before images were rendered from
an isolated archive of the original Git HEAD, with equivalent fixture data
and the original layout/theme settings.

## Source-review inventory

The source review covered 54 files under `presentation/screens`, including
aliases/delegating entry points, plus the splash screen. Rendered coverage is
listed above; this inventory does not claim an end-to-end device run of every
screen. Ordinary screens use a shared scaffold directly or through their
flow/body composition. The root shell, splash, and full-screen photo viewer
keep specialized layouts.

| Family | Screen files reviewed |
| --- | --- |
| main_view | [view.dart](../../apps/sokoun_app/lib/features/main_view/presentation/screens/view.dart) |
| owner/home | [owner_add_property_flow_screen.dart](../../apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_add_property_flow_screen.dart), [owner_home_screen.dart](../../apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_home_screen.dart), [owner_listings_screen.dart](../../apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_listings_screen.dart), [owner_requests_screen.dart](../../apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_requests_screen.dart), [owner_visit_requests_screen.dart](../../apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_visit_requests_screen.dart) |
| owner/properties | [owner_edit_property_screen.dart](../../apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_edit_property_screen.dart), [owner_properties_screen.dart](../../apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_properties_screen.dart), [owner_property_analytics_screen.dart](../../apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_analytics_screen.dart), [owner_property_rejection_screen.dart](../../apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_rejection_screen.dart), [owner_revenue_screen.dart](../../apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_revenue_screen.dart) |
| owner/visits | [owner_availability_screen.dart](../../apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_availability_screen.dart), [owner_request_details_screen.dart](../../apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_request_details_screen.dart), [owner_requests_calendar_screen.dart](../../apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_requests_calendar_screen.dart) |
| shared/auth | [forgot_password_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/forgot_password_screen.dart), [kyc_approved_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_approved_screen.dart), [kyc_intro_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_intro_screen.dart), [kyc_pending_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_pending_screen.dart), [kyc_upload_documents_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart), [login_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/login_screen.dart), [otp_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/otp_screen.dart), [register_flow_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/register_flow_screen.dart), [register_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/register_screen.dart), [welcome_screen.dart](../../apps/sokoun_app/lib/features/shared/auth/presentation/screens/welcome_screen.dart) |
| shared/chat | [chat_list_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_list_screen.dart), [chat_restricted_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_restricted_screen.dart), [chat_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_screen.dart), [chat_search_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_search_screen.dart), [chat_thread_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_thread_screen.dart), [chats_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/chats_screen.dart), [previous_chat_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/previous_chat_screen.dart), [start_conversation_screen.dart](../../apps/sokoun_app/lib/features/shared/chat/presentation/screens/start_conversation_screen.dart) |
| shared/notifications | [notification_detail_screen.dart](../../apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notification_detail_screen.dart), [notification_settings_screen.dart](../../apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notification_settings_screen.dart), [notifications_empty_screen.dart](../../apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notifications_empty_screen.dart), [notifications_screen.dart](../../apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notifications_screen.dart) |
| shared/profile | [language_selection_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/language_selection_screen.dart), [owner_edit_profile_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/owner_edit_profile_screen.dart), [owner_more_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/owner_more_screen.dart), [owner_profile_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/owner_profile_screen.dart), [tenant_account_summary_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/tenant_account_summary_screen.dart), [tenant_edit_profile_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/tenant_edit_profile_screen.dart), [tenant_profile_screen.dart](../../apps/sokoun_app/lib/features/shared/profile/presentation/screens/tenant_profile_screen.dart) |
| tenant/favorites | [favorites_screen.dart](../../apps/sokoun_app/lib/features/tenant/favorites/presentation/screens/favorites_screen.dart) |
| tenant/home | [property_details_screen.dart](../../apps/sokoun_app/lib/features/tenant/home/presentation/screens/property_details_screen.dart), [tenant_filter_screen.dart](../../apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_filter_screen.dart), [tenant_home_screen.dart](../../apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_home_screen.dart), [tenant_property_photos_screen.dart](../../apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart), [tenant_search_results_screen.dart](../../apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_search_results_screen.dart), [tenant_search_screen.dart](../../apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_search_screen.dart) |
| tenant/visits | [book_visit_screen.dart](../../apps/sokoun_app/lib/features/tenant/visits/presentation/screens/book_visit_screen.dart), [tenant_visits_screen.dart](../../apps/sokoun_app/lib/features/tenant/visits/presentation/screens/tenant_visits_screen.dart), [visit_confirmed_screen.dart](../../apps/sokoun_app/lib/features/tenant/visits/presentation/screens/visit_confirmed_screen.dart), [visit_details_screen.dart](../../apps/sokoun_app/lib/features/tenant/visits/presentation/screens/visit_details_screen.dart) |
| splash | [splash_screen.dart](../../apps/sokoun_app/lib/features/splash_screen.dart) |
