# Sokoun recovery and app-link integration handoff

Client defaults remain conservative. This checkout contains no backend service implementation, and verification for this change uses local fixtures. Existing mobile handoffs describe contracts; they do not establish that a particular deployment implements them.

## Listing creation and image uploads

Existing legacy property create is `POST /properties/create/`. Image upload is `POST /properties/{property_id}/images/`. The client preserves the created property ID and each confirmed image ID. A transmitted operation with no usable acknowledgment remains unknown. It cannot safely be replayed merely because a local UUID exists.

**PROPOSED contract extension:** accept `Idempotency-Key` on legacy create and image upload, scoped to authenticated owner, operation and property. Persist the normalized request fingerprint and original response. A duplicate key with matching input returns the same property/image ID; different input returns 409. Enforce ownership and current verification on every request. Reject missing/invalid media with 400/422, inaccessible property with 403/404 and revoked session with 401. Document the retention period and whether an in-progress duplicate returns 409 or 202 plus an authorized status-read location. A status read must distinguish pending, confirmed and definitely rejected; absence alone must not authorize a second create while the first is processing. No new status endpoint name is assumed by this client.

Acceptance: losing the create response and submitting the same key yields one listing; losing the image response and retrying the same file/key yields one image; another owner cannot inspect or reuse that key; changing captions or file content under the same key returns a conflict. Chunk/resumable upload is outside this task. Existing rental-inventory idempotency is used only behind its existing capability gates.

## Chat delivery

The 8 October mobile handoff specifies `client_message_id` for raw WebSocket `/ws/chat/` and REST send, deduplicated by conversation, sender and client ID. Both acknowledgments and REST/history must return the same server message ID and client ID. Same-ID/different-content requests must conflict, with conversation membership and current sending permission checked on each transport.

The new `SOKOUN_CHAT_DURABLE_REPLAY` compile-time flag defaults to **false**. Enable only after staging proves both-transport deduplication, lost-ACK REST fallback, history reconciliation and replay following process termination. With the flag off, a lost acknowledgment preserves text and an unconfirmed delivery state without an automatic second transmission. Local queued work is not a promise of delivery after app termination.

Acceptance: deliver a WebSocket message, suppress its ACK, then send the same ID by REST and reconnect/replay that ID. All reads show one server message. A late socket ACK resolves the local pending item. An unrelated conversation/sender ID never settles it. Account switch stops transmission/retry work before protected record removal.

## Viewing, reviews, support and profile

Tenant available dates/times are present in the current collection and use Cairo timezone rules. The client revalidates a recovered viewing selection and keeps its note on conflicts. Existing accepted-versus-completed review fallback policy remains unchanged; server `can_review` and existing-review data decide eligibility when present.

Advanced support/profile contracts remain marked PROPOSED in `docs/profile_settings_support_backend.md`. The client must receive a real ticket ID/reference or a current authorized profile before reporting success. Server deployment and support-backed chat reporting require staging verification.

**PROPOSED extension where duplicate-safe retries are required:** persist an account/resource-scoped idempotency key for viewing/review/support-create/support-reply submissions and return the original confirmed result for identical requests. Different input under one key returns 409. Fresh authorization, slot conflicts, review eligibility and resolved-ticket restrictions still apply. An ambiguous write must be reconcilable by key or an authorized operation-status read, rather than text equality. No endpoint name is invented here.

## Hosted app associations

The client uses existing HTTPS hosts `sokoun.app` and `www.sokoun.app`. Android intent filters already cover `/properties`. iOS entitlements now declare both hosts for the six existing dev/prod Runner configurations.

Publish `/.well-known/assetlinks.json` on **both** hosts without redirects. Use the actual package names `com.app.sokoon.real.estate` and `com.app.sokoon.real.estate.dev`, `delegate_permission/common.handle_all_urls`, and verified release/Play signing certificate SHA-256 fingerprints. Fingerprints are not available in this checkout and must not be replaced by invented or debug values.

Publish `/.well-known/apple-app-site-association` on both hosts. Its `applinks.details` must authorize the actual Apple Team ID plus each enabled bundle ID (`com.app.sokoon.real.estate`, `com.app.sokoon.real.estate.dev`) and `/properties/*` paths. Team IDs and signing/provisioning capabilities require the release owner's configuration; no placeholder is presented as deployable data.

Verify cold/warm property and offer URLs, repeated OS deliveries, guest access, authenticated workspace selection and missing/inaccessible resources on physical devices. Association hosting, signed builds and deferred links after store installation remain unverified. See [Android verification guidance](https://developer.android.com/training/app-links/verify-applinks) and [Flutter universal-link setup](https://docs.flutter.dev/cookbook/navigation/set-up-universal-links).

Saved searches are local manual shortcuts. Alerts, per-conversation mute, remote device-session revocation and cross-device draft sync require separately documented services. Existing payment/lease/offers/provider gates remain unchanged.
