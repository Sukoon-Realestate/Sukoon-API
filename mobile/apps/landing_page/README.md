# Sokoon landing page

Arabic-first Flutter web landing page for the tenant and owner experiences in
`apps/sokoun_app`. The header switches between Arabic/RTL and English/LTR.

## Run and verify

From this directory:

```sh
flutter pub get
flutter run -d chrome
flutter analyze
flutter test
flutter build web --release
```

Deploy the output of `build/web`. For a subdirectory deployment, supply
`--base-href /your-path/` at build time.

## Product alignment

The content is based on these app implementations, rather than a separate
marketing feature specification:

| Landing content | App source under `apps/sokoun_app/lib/features` |
| --- | --- |
| Search by area, budget, type, rental period and amenities | `tenant/home/data/models/property_search_model.dart` |
| Property details and saved photos | `tenant/home/presentation/screens/property_details_screen.dart`, `tenant/home/presentation/cubits/property_photo_save_cubit.dart` |
| Favorites | `tenant/favorites/presentation/screens/favorites_screen.dart` |
| Property conversations | `shared/chat/presentation/cubits/socket_cubit.dart` |
| Booking, cancellation and post-visit reviews | `tenant/visits/presentation/cubits/` |
| Listings and media | `owner/home/presentation/screens/owner_add_property_flow_screen.dart` |
| Availability and visit requests | `owner/visits/presentation/cubits/` |
| Owner dashboard and analytics | `owner/home/data/models/owner_dashboard_model.dart`, `owner/properties/presentation/screens/owner_property_analytics_screen.dart` |
| Notifications and identity verification | `shared/notifications/`, `shared/auth/presentation/screens/kyc_intro_screen.dart` |

This is a product introduction, not a live inventory or authentication client.
Property cards and phone previews are illustrative. Sample favorites only affect
the current page. Store availability is explicitly marked as coming soon.
There is no promised verification turnaround, media-message guarantee, or blanket
phone-number privacy claim inferred from UI alone.

## Design and motion

- Shared app logo through `AppLogoWidget`; the same source artwork supplies web branding.
- Local vector interiors avoid remote image requests and missing-photo placeholders.
- Tenant/owner selection is shared by the feature and journey sections.
- `ScrollReveal` animates once on viewport entry, removes its scroll listener,
  and disposes its animation. Feature cards have staggered entrances.
- Cards and buttons have hover feedback; the app preview has a keyed slide/fade transition.
- Reduced-motion settings disable entrances, smooth scrolling and implicit transitions.
  Accessible navigation also bypasses entrance animations.
- Every user-facing translation belongs in `packages/core/assets/translations/lang.json`.
  Run `dart run generate/strings/main.dart` from the repository root after edits.
  The current generator rejects commas and hyphens in English source values.

## Before public launch

1. Supply real App Store and Google Play URLs, then make the coming-soon badges
   actionable. Do not route download or login labels to an unrelated page.
2. Publish approved privacy/terms documents and a real support destination before
   adding legal/support links. Placeholder social links were removed.
3. Replace sample previews with approved release screenshots when available.
   Keep examples distinct from real availability and property verification.
4. Add the production canonical URL and an absolute social-sharing image URL once
   the public domain is known. Basic page metadata and a no-JavaScript description
   are included; Flutter canvas content alone is not a complete search-indexing strategy.
5. Confirm privacy statements and review timelines against backend behavior and
   the published service policy before making stronger marketing claims.
