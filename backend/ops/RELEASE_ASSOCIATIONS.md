# App association release preparation

17 November 2026: read-only probes reproduce public 504 responses on both
`api.sukoon.rent` and the DigitalOcean default domain. Runtime access logs show
that the matching requests reach Django and return 503. The active deployment
has no `SOKOUN_ANDROID_*` / `SOKOUN_APPLE_*` identity environment entries at either
app or service scope. Its ingress sends `/` to `sukoon-api:8080`.
This supports missing release identity configuration with gateway status
translation, rather than a missing route or a demonstrated slow handler.

Keep the handlers' explicit 503/no-store behavior when configuration is absent.
Returning successful empty associations would conceal the release blocker.
`release-associations.env.example` names the existing inputs without fabricating
certificates or an Apple team. Nothing in this preparation deploys configuration.

Before an explicitly authorized release:

1. Obtain and verify SHA-256 certificates for each distributed Android flavor.
   Play App Signing's app-signing certificate can differ from the upload key.
   Production package: `com.app.sokoon.real.estate`; development package:
   `com.app.sokoon.real.estate.dev`. Never substitute a debug certificate.
2. Obtain the Apple distribution profile's actual team and application IDs.
   The source uses the same two flavor bundle IDs. No `DEVELOPMENT_TEAM` is set
   in the checked-in Xcode project. A simulator's unsigned entitlements cannot
   prove distribution entitlement validity.
3. Configure the verified values using the existing environment inputs, then
   review the resulting JSON locally with `common/test_app_associations.py`.
   The current backend includes both Apple bundle IDs under the configured team.
4. Verify the **actual link host** too. Mobile entitlements and Android links
   name `sukoon.rent`, `www.sukoon.rent`, `sokoun.app` and `www.sokoun.app`;
   success on `api.sukoon.rent` alone does not associate those domains. Each
   supported host must serve its association JSON directly, without a redirect,
   with HTTPS and the correct release identities. Decide which legacy hosts
   remain supported before changing client configuration.
5. Verify installed/uninstalled Android and iOS link handling and public store
   destinations against the signed release. No App Store numeric ID or confirmed
   public listing destination was found in the checked-in configuration.

Local acceptance remains separate from live acceptance. A subsequent read-only
check found a private release-wrapper configuration pointing to an existing
signing-properties file and keystore. Its dry-run succeeds; the absence of
`android/key.properties` alone is not proof that signing material is missing,
because the wrapper installs that file temporarily. The existing local
`com.app.sokoon.real.estate.dev` release APK verifies with v2 signing and matches
the referenced keystore certificate. Its public SHA-256 is
`F3:B9:D2:67:E8:09:10:85:49:AE:FC:B9:E9:4B:50:FA:85:95:1B:93:C3:B1:0D:01:68:34:0C:2A:30:5A:55:A8`.

The verified dev-only association JSON is retained in the QA evidence directory
`signing-and-timing/verified-dev-assetlinks.json`. It is preparation evidence,
not a production association manifest. Local handlers return that exact JSON
when configured with the dev package/certificate alone; the normal deployment
map still returns 503 while production identity is absent. Do not substitute
the dev certificate for a missing production Play App Signing certificate.
No prod artifact, Apple distribution identity or confirmed store listing was
established. Do not generate replacement signing identities to fill those gaps.

The landing app now has exact server-side rewrites for both well-known paths,
using its existing validated `SOKOUN_API_PROXY_URL`. Local production-build HTTP
probes preserve upstream JSON and 200/503/cache behavior. These rules prepare the
landing host only: the apex's platform-level 308 redirect must separately exempt
association requests, and unresolved legacy DNS cannot be repaired by Next.js.
No gateway setting, domain record or release identity has been changed.

This dependency update also adds upstream social-auth migrations 0017–0020.
Before any later deployment, check existing `social_auth_usersocialauth` rows for
empty UIDs and review provider `id_key` backfills; the new constraint must not be
worked around by dropping associations. The local synthetic migration drill
preserves three existing associations, but does not certify real release data.
