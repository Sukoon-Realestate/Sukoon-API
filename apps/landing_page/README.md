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

## App demo video

The app preview section includes a local 40 second Arabic demo with captions,
a poster, play/pause and seeking controls, and an Arabic/English written
walkthrough. Playback starts on request and pauses when the page is removed or
the app goes into the background. The video is silent.
Flutter controls RTL/LTR inside the app; the HTML shell leaves direction unset
so native video views and accessible controls keep their correct positions.

- Video: `assets/videos/sokoun_demo.mp4` (1280 × 720, H.264, 30 fps).
- Poster: `assets/images/sokoun_demo_poster.jpg`.
- Content: housing discovery, property details and favorites, visit date/time
  selection, and the owner dashboard with requests, statistics and operations.
- App screens are rendered from `apps/sokoun_app` widgets with sample data.
  Listing media uses the landing page's existing local interior illustration.
  This is a composed walkthrough of app UI states, not a live backend recording.

To regenerate after app UI changes, install Node.js and Flutter, then run from
this directory:

```sh
flutter pub get
make demoSetup
make demo
```

The capture harness lives at `../sokoun_app/tool/capture_landing_demo_test.dart`;
the deterministic movie renderer lives at `tool/demo_video/render_demo.cjs`.
Only the final MP4 and poster are bundled with the site. Captures, browser tools
and the generated contact sheet are ignored by Git. Set `CHROME_PATH` to use an
existing Chrome executable or `FLUTTER` to select a specific Flutter binary.

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
