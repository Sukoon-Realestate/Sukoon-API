# Google login and notification verification — 2026-11-16

## Results

- Backend isolated tests: **113 passed, 1 skipped** (social authentication and notifications); see local `/private/tmp/sukoon-google-notifications-backend.log`.
- Flutter app tests: **37 passed** (Google login, notification API, UI flow, read cache and MVP delivery); see local `/private/tmp/sukoon-google-notifications-flutter.log`.
- Shared Flutter tests: **26 passed** (notification routing and denied/revoked permission behavior); see local `/private/tmp/sukoon-notification-core-tests.log`.
- Live Google endpoint rejected an invalid `token` with HTTP 400; notification list and device registration rejected unauthenticated requests with HTTP 401.
- Simulator Google button opened the native consent sheet and Google's actual sign-in page. Account entry, OAuth callback, successful backend session and post-login navigation remain **unverified**, pending the user's test-account sign-in. No Google credentials were entered by the agent.
- Live Google client allowlist includes both iOS dev and production client IDs. The inspected iOS client and backend Firebase project are `sokoun-99c7b`. The separately migrated Android development app uses `sukoon-dev-testing`; its integration with this backend was not established by these checks.
- Live Firebase service-account token refresh succeeded. An FCM HTTP v1 **validate_only** request using an active Android registration token returned HTTP 200. No notification was delivered by this check. This validates an existing token in the backend project, not the newly migrated Android development build.
- Registered-device aggregate: 21 active Android records, 21 inactive Android records, **zero iOS records**. Counts are records, not unique people or physical devices.

## iOS push finding

`apps/sokoun_app/ios/Runner/Runner.entitlements` contains associated domains but no `aps-environment` key. The inspected installed simulator app has an empty signing-entitlements dictionary. The source project also has no push-capability entry. This is a configuration gap for remote APNs notifications; local notifications and in-app notification lists are separate paths. Physical iPhone signing/provisioning, Firebase APNs credentials and actual foreground/background/tap delivery still need verification. Simulator build evidence alone does not establish physical-device signing state.

## Limits

No successful Google account login or actual push delivery has been claimed. No notification was sent, no account was created, no production data was modified and no app/deployment configuration was changed. Flutter widget tests emitted missing-translation fixture warnings; all selected tests passed. Backend run had one skip and 37 warnings; see the logs for details.
