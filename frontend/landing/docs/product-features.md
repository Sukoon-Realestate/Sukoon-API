# Landing-page product features

The “Inside Sukoon” section uses English and Arabic copy in `src/i18n/features.ts`.
It describes implemented tenant and owner workflows, without promising payment,
electronic-signature or other provider-dependent services.

## Source evidence

Paths below are relative to the repository root.

| Benefit | Implementation evidence |
| --- | --- |
| Find suitable homes | `backend/core_apps/properties/filters.py`; `mobile/apps/sokoun_app/lib/features/tenant/home/data/models/property_search_model.dart` |
| Save and compare options | Saved-property routes in `backend/core_apps/properties/urls.py`; `mobile/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/comparison_table.dart` |
| Understand costs and keep private notes | `mobile/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/property_cost_card.dart`; `mobile/apps/sokoun_app/lib/features/tenant/decision_tools/data/decision_tools_data.dart` (account-scoped storage on the device, not a cloud-sync claim) |
| Arrange and track viewings | Available dates, tenant visits and cancellation routes in `backend/core_apps/properties/urls.py`; `mobile/apps/sokoun_app/lib/features/tenant/visits/` |
| Manage properties and requests | Owner dashboard, property editing, visibility, availability and request-response routes in `backend/core_apps/properties/urls.py`; `mobile/apps/sokoun_app/lib/features/owner/` |
| Direct conversations | `backend/core_apps/chat/urls.py`; `mobile/apps/sokoun_app/lib/features/shared/chat/`; reporting uses support tickets in `presentation/widgets/report/chat_report_sheet.dart` |
| Follow updates and manage notifications | `backend/core_apps/notifications/urls.py`; `mobile/apps/sokoun_app/lib/features/shared/notifications/` |
| Review a viewing | `backend/core_apps/properties/views/visit_parts/property_visit_review_create_apiview.py`; property review list in the same directory; the review API accepts cleanliness, listing accuracy, owner interaction and an optional comment |
| Get help and track support tickets | `backend/core_apps/support/urls.py`, `views/ticket.py`, `serializers/ticket.py`; `mobile/apps/sokoun_app/lib/features/shared/support/` |

## Image provenance

The sixteen PNGs in `public/images/app/` are browser captures of the repository's
**mobile design prototype**, not screenshots of a running Flutter build.
Flutter was not available in the capture environment. Each image has a visible
prototype/sample-data caption on both language versions of the landing page.
The English page deliberately identifies the previews as Arabic. Every screen
has a `-light.png` image and a `-dark.png` variant. The site’s existing `data-theme`
CSS variant selects the matching image immediately when its theme changes.

The capture entry adapts the prototype palette for the dark variants and adds
sample interior photos to saved-property cards, the viewing thumbnail and the
backdrop behind search/review sheets. These are marketing design previews.
The original prototype screen components are unchanged.

All eight previews use the shared `IPhoneFrame` with a metal band, black bezel
and physical side buttons. Captures reserve 59 pixels for a consistent iPhone
status bar/Dynamic Island and 34 pixels for the home indicator. Existing
prototype status bars are removed in the capture entry to avoid duplicates.

Sample photos are stored locally in the prototype’s `public/landing-photos/`;
their source image URLs are:

- `https://images.unsplash.com/photo-1600210492486-724fe5c67fb0`
- `https://images.unsplash.com/photo-1600607687939-ce8a6c25118c`
- `https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea`

Source: `mobile/Sokoon Figma Prototype Design/`:

| Image | Original component |
| --- | --- |
| `discovery-{light,dark}.png` | `FilterSheetScreen` in `src/app/screens-tenant.tsx` |
| `shortlist-{light,dark}.png` | `SavedListingsScreen` in `src/app/screens-tenant.tsx` |
| `viewings-{light,dark}.png` | `BookVisitScreen` in `src/app/screens-tenant.tsx` |
| `owners-{light,dark}.png` | `OwnerDashboardScreen` in `src/app/screens-owner.tsx` |
| `conversations-{light,dark}.png` | `TenantChatThreadScreen` in `src/app/screens-tenant.tsx` |
| `notifications-{light,dark}.png` | `TenantNotificationsScreen` in `src/app/screens-tenant.tsx` |
| `reviews-{light,dark}.png` | `RatePropertyScreen` in `src/app/screens-tenant.tsx` |
| `support-{light,dark}.png` | `TenantSubmitTicketScreen` in `src/app/screens-tenant.tsx` |

To reproduce, install the prototype dependencies and run `npm run dev -- --host
127.0.0.1`. Open `/landing-capture.html?screen=discovery` (or `shortlist`,
`viewings`, `owners`, `conversations`, `notifications`, `reviews`, `support`)
at a 390 × 844 CSS-pixel viewport and device scale factor 2.
Add `&theme=dark` to capture the dark variant. Wait for `document.fonts.ready`
and for the local photos to decode, then capture the viewport. Sample names,
prices and counts come from the prototype; the sample photos are illustrative.
They are not live inventory or business performance claims.

For future Flutter captures, the app already has opt-in PNG exporters in
`test/ui_visual_review_test.dart` and `test/free_features_ui_review_test.dart`.
Replace the assets and update the captions/provenance together once those
captures are available.

## Validation

- Production build and TypeScript check passed.
- ESLint passed for the changed landing files.
- Browser checks passed for `/ar` and `/en` at 390, 768 and 1440 pixels:
  eight feature rows, decoded images, no horizontal overflow or page exceptions.
- Desktop, mobile RTL and dark-theme previews were inspected.
- The actual theme toggle was checked in both languages at mobile and desktop
  widths: exactly one matching image is visible in every row in each theme.
