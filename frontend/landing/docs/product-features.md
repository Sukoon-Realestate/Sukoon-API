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

## Localized phone previews

All eight feature phones render `FeaturePhoneScreen` inside the shared
`IPhoneFrame`. Their text is selected using the route locale passed through
`ProductFeatures`; Arabic uses RTL and English uses LTR. The carousel remounts
when the locale changes so its scroll direction and active slide reset together.
The hero phone continues to use the locale dictionary.

The previews use sample data and local property photos. They are illustrative
HTML interfaces, not screenshots of a running Flutter build. Theme-aware colors
follow the site's `data-theme` attribute. The previous Arabic-only raster captures
in `public/images/app/` are no longer rendered.

## Validation

- ESLint and TypeScript checks pass.
- Both `/ar` and `/en` render the expected localized screen copy.
- Neither route renders the previous static screenshot paths.
