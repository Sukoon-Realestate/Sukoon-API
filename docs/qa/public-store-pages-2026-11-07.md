# Public store pages — 7 November 2026

Implemented in the existing `frontend/landing` application. The mobile UI and
native account-deletion flow are unchanged. These are public web pages suitable
for store URL fields and for viewing in a browser or WebView; no app installation
or login is required.

## URLs after deployment

| Page | English | Arabic | Store use |
| --- | --- | --- | --- |
| Privacy policy | `/en/privacy` | `/ar/privacy` | Google Play privacy policy; App Store Connect privacy policy URL |
| Account deletion | `/en/delete-account` | `/ar/delete-account` | Google Play account-deletion URL in Data safety |
| Support/contact | `/en/support` | `/ar/support` | App Store Connect Support URL; public support contact |
| Terms of use | `/en/terms` | `/ar/terms` | Public terms; review separately if using a custom EULA or paid services |

The configured public origin is `https://sukoon.rent`. Locale-less `/privacy`,
`/terms`, `/delete-account` and `/support` redirect to Arabic or English using
the visitor's language. Explicit locale URLs are preferable in localized store
metadata. All pages appear in the site navigation, footer and sitemap.

## Content and request behavior

- Privacy and terms are read from the existing public API at
  `https://api.sukoon.rent/api/v1/pages/`, with the requested language, a one-hour
  revalidation interval and the published revision/update date. The existing
  policy text remains the source shared with the app. Unavailable published
  content produces an error/retry view, never substitute policy promises.
- The privacy page prominently links to account deletion and support.
- The external deletion pathway prepares an email addressed to the existing
  `BUSINESS.email`, currently `info@sukoon.rent`, with a localized request subject
  and body. The visitor must review and send it. The address and manual email
  instructions remain visible for people without a configured mail app.
- The owner confirmed `info@sukoon.rent` for support, privacy and account-deletion
  requests. Processing time and retention rules use explicitly marked draft
  placeholders in both languages on the privacy and deletion pages, as requested.
- The page also explains the existing native route: Profile → Settings → Delete
  account, verification, request status/history and required follow-up.
- Deletion copy describes inspected backend behavior in
  `core_apps/users/services/account_closure.py`: session revocation, profile
  erasure/anonymization, removal of social links/private notes, and separately
  retained verification/shared/rental/financial/security/closure evidence. It
  does not promise instant deletion or an invented retention deadline.
- No email was sent, no account was deleted, and no production data was changed
  during verification.

## Verification

- `npm run build`: passed, including TypeScript and static generation of all
  eight public pages in the existing merged public/admin application.
- Production preview HTTP checks: all eight URLs returned 200 with the correct
  HTML language/direction, one main heading, canonical URL and related links.
- All four privacy/terms documents matched the published API text, allowing
  only whitespace normalization for rendered headings/paragraphs.
- Both deletion drafts decoded to the intended recipient, localized subject and
  account/data-deletion request. No delivery was attempted.
- All four locale-less paths redirected correctly; all eight localized URLs
  appeared in the sitemap; an unknown legal path returned 404.
- Browser review: desktop Arabic/English deletion pages, plus narrow-screen
  Arabic/English navigation and email request presentation. The native mail
  client handoff and in-app WebView behavior were not exercised.
- `git diff --check`: passed.
- Final placeholder update: production build passed; both placeholder fields
  were present in the generated Arabic/English privacy and deletion pages, and
  the confirmed mailbox appeared in both support and deletion page languages.

## Deployment correction

The first Vercel build of `b16a2de6` failed with 26 unresolved `lucide-react`
imports from shared code in `frontend/src`. The Vercel project builds from
`frontend/landing` and had installed only that package's dependencies.

`frontend/landing/vercel.json` now installs both packages with
`npm ci --prefix .. && npm ci`, using their existing lockfiles. Verification used
an isolated checkout containing only tracked frontend/design sources and no
pre-existing dependencies: both installs, all three `vercel-build.test.mjs`
checks and `VERCEL_ENV=production node scripts/vercel-build.mjs` passed. All eight
localized public pages were generated successfully.

## Before publication and store submission

1. Replace the visible draft placeholders with the approved processing time and
   retention schedule, including the
   reasons and durations for retained identity, chat, transaction and audit data.
   The implementation has no approved schedule to quote. The existing policy
   also needs the owner's review of SDK/provider disclosures, secure handling
   and the full current data inventory. Update the managed policy source so the
   app and website remain consistent.
2. Deploy the existing Next.js application to its current host and verify the
   public URLs. At the time of the check, `sukoon.rent/en/privacy` redirected to
   `www.sukoon.rent/en/privacy`, which returned 404. Local success does not prove
   the current public deployment serves these routes.
3. Keep the native in-app deletion option: Apple's requirement is not satisfied
   by an external support page alone. Ensure the operational process completes
   deletion of all non-retained associated data, rather than only disabling the
   account. This page work does not certify that full operational process.
4. Complete the Google Play Data safety and Apple App Privacy declarations to
   match actual app/SDK behavior. These are store forms, not extra web pages.

Initial verification was local. Deployment status is checked separately when
the source is pushed. No store submission or change to the managed policy source
was performed. The error/retry UI compiled, but a live policy-source outage was
not forced during browser review.

## Official requirements checked

- [Google Play User Data policy](https://support.google.com/googleplay/android-developer/answer/10144311?hl=en): public privacy policy, accurate data/SDK disclosures, retention/deletion practices and in-app/external account-deletion routes.
- [Google Play account-deletion guidance](https://support.google.com/googleplay/android-developer/answer/13327111?hl=en): the public route must work without reinstalling the app; a customer-service email is an accepted external request pathway.
- [Apple account-deletion guidance](https://developer.apple.com/help/app-review/guideline-reference/5-1-1-account-deletion): initiate deletion in the app; simple deactivation is insufficient; ordinary apps must not require a support conversation to complete the native deletion flow.
- [Apple App Review Guidelines, 5.1.1](https://developer.apple.com/app-store/review/guidelines/): privacy policy in metadata and in the app, describing collection/use/sharing and retention/deletion.
- [App Store Connect platform-version fields](https://developer.apple.com/help/app-store-connect/reference/app-information/platform-version-information/): required Support URL with actual contact information.
