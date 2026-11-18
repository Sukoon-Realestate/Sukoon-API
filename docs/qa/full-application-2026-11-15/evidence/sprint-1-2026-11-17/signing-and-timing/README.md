# Signing and Back timing checks — 17 November 2026

- `android-signing.json`: existing private configuration references a valid local keystore and a private-key entry. Certificate validity and public SHA-256 are retained; no credentials or private file locations are included.
- `key-proof.json`: the configured private-key password successfully signs a temporary local certificate request. No request was transmitted; the request file was removed and the keystore SHA-256 stayed identical.
- `android-artifact-verification.json`: existing dev-release APK verifies with APK v2 and matches the configured keystore. Package/version/artifact SHA-256 are retained. This is not a fresh/current-source or production artifact acceptance.
- `release-dry-run.json`: the existing release wrapper validates local configuration without a build, authentication request, upload, invitation or signing-file write.
- `verified-dev-assetlinks.json`: prepared dev-only association JSON using the verified certificate; not deployed and not a production signing identity.
- `dev-association-local.log`: existing handler returns exact expected dev-only JSON/cache policy, while normal configuration with missing production identity still fails closed with 503/no-store.
- `back-timing.log`: four focused tests pass, covering 16 combinations of normal/reduced motion, toolbar/system Back and 0/16/100/350 ms after empty validation. Toolbar callbacks are invoked directly to isolate route lifecycle from toast hit testing. No Flutter exception or create request. Negative reproduction only.
- `mobile-regressions.log`: 130 cases pass across property creation, validation, owner requests and tenant visits. The initially slow upload/retry case completed without changing an assertion. `upload-baseline.log` shows that exact case also passes alone against the pre-matrix test file.

Private keystore paths/passwords, service-account material, full keytool output and
raw credential-bearing dry-run details remain outside the repository. No build,
install, upload, deployment, invitation or production mutation was performed by
these signing checks. Existing dev artifact signing does not establish Play App
Signing, Apple distribution, a public store listing, or device link acceptance.
