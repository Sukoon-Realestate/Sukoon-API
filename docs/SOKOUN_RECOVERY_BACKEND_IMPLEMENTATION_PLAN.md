# Sokoun Recovery Backend Implementation Plan

## Scope

Implement the server-side recovery contracts described in
`sokoun_professional_features_handoff.md` without changing existing endpoint paths.

## Plan

1. Add a shared idempotency utility backed by the existing `IdempotencyRecord` model.
   It will normalize request bodies, hash uploaded file bytes, scope keys to the
   authenticated user and operation/resource, replay the original response for an
   identical request, and return `409 Conflict` for key reuse with different input.
2. Apply optional `Idempotency-Key` handling to legacy property creation and property
   image upload. Preserve existing clients that do not yet send a key. Keep property
   ownership checks ahead of any replay lookup.
3. Apply the same optional contract to viewing requests, viewing reviews, support
   ticket creation, and support replies. Scope resource mutations by property, visit,
   workspace, or ticket so a key cannot settle a different operation.
4. Harden chat `client_message_id` deduplication for concurrent WebSocket and REST
   sends. Preserve one message row and return the same server/client IDs on replay;
   expose same-ID/different-content as a conflict.
5. Add focused API/service/WebSocket tests for lost-response replay, changed payloads,
   file-content fingerprints, resource/user isolation, and chat cross-transport replay.
6. Document the exact mobile contract, response semantics, retention window, rollout
   gate, and the hosted association prerequisites that cannot be generated without
   release signing identities.

## Deployment notes

- Idempotency records are retained for at least 30 days by default. The value is
  configurable with `IDEMPOTENCY_RETENTION_DAYS`.
- The protected write and its stored response commit in one database transaction.
  Concurrent identical requests wait for the winning transaction and then replay its
  result; the API does not expose an intermediate `pending` receipt for these routes.
- Android certificate fingerprints and Apple Team IDs are not present in the
  repository. Association files must not be published until release owners supply
  those values.

