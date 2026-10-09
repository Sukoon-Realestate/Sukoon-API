# Mobile Developer Handoff — Recovery, Durable Chat, and App Links

## Delivery status

The backend recovery contracts in this document are implemented. Endpoint paths are
unchanged. Mobile can adopt them incrementally by adding the headers/fields below.

Base API path: `/api/v1/`

## Idempotent HTTP writes

Send a stable, opaque `Idempotency-Key` header (maximum 100 characters) for every
logical write that must be safe after a timeout, lost response, or app restart.

```http
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

The same authenticated account, endpoint operation/resource, key, and normalized
request will receive the original HTTP status and response body. A replay also includes:

```http
Idempotency-Replayed: true
```

Reusing a key with different text, metadata, IDs, or file bytes returns `409 Conflict`
with code `idempotency_conflict`. File fingerprints include the bytes, filename,
content type, and size. Keys are account-scoped, and resource mutations are additionally
scoped by their property, visit, ticket, or workspace. Another account cannot inspect
or replay a key.

Confirmed records are retained for at least 30 days by default. The mutation and its
stored response commit in the same database transaction. A concurrent duplicate waits
for the winning transaction and then receives the confirmed replay; these endpoints do
not expose a separate pending/status-read URL.

The header is optional for legacy clients, except where the existing rental inventory
contract already requires it. Do not automatically retry an ambiguous write unless the
original request used a key.

### Supported routes

| Operation | Route | Scope | Success |
|---|---|---|---|
| Create listing | `POST properties/create/` | account + create operation | `201`, original property `id` |
| Upload listing image | `POST properties/{property_id}/images/` | account + property | `201`, original image `id` |
| Request viewing | `POST properties/{property_id}/visits/` | account + property | `201`, original visit `id` |
| Submit viewing review | `POST properties/visits/{visit_id}/review/` | account + visit | `201`, original review `id` |
| Create support ticket | `POST support/tickets/` | account + workspace | `201`, original ticket `id` and `reference` |
| Reply to support ticket | `POST support/tickets/{id}/replies/` | account + ticket | `200`, original updated thread |

Ownership/membership and current business rules are checked before a resource replay.
Listing creation and image upload requests that opt into recoverable writes require the
authenticated account to be currently identity-verified; otherwise they return `403`.
Image uploads still reject missing/invalid media through serializer validation.
Viewing slot conflicts, review eligibility, ticket ownership/workspace, and resolved or
closed ticket restrictions remain authoritative.

Client behavior:

1. Generate one key when the user initiates a logical submission.
2. Persist the key with the local pending operation before transmission.
3. Reuse that exact key and exact payload after transport ambiguity.
4. Mark confirmed only after receiving the server resource ID/reference.
5. On `409 idempotency_conflict`, stop retrying and surface a recoverable local error.
6. Generate a new key only for a genuinely new or edited submission.

## Durable chat delivery

Both transports accept the same UUID `client_message_id`:

```json
{
  "type": "message.send",
  "conversation_id": "<conversation UUID>",
  "client_message_id": "<client-generated UUID>",
  "content": "Is the apartment available?"
}
```

- WebSocket: `/ws/chat/`
- REST fallback: `POST /api/v1/chat/conversations/{conversation_id}/messages/create/`
- History: `GET /api/v1/chat/conversations/{conversation_id}/messages/`

An identical `(conversation, sender, client_message_id)` returns the existing server
message and does not increment unread counts, notify again, or broadcast a second
message. REST, WebSocket ACK, WebSocket `message.new`, and history all include both
`id` and `client_message_id`.

A WebSocket send with a client ID receives:

```json
{
  "type": "message.ack",
  "payload": {
    "id": "<server message UUID>",
    "conversation": "<conversation UUID>",
    "client_message_id": "<same client UUID>",
    "content": "Is the apartment available?"
  }
}
```

Same ID with changed content returns REST `409` with code
`client_message_conflict`; WebSocket returns an error event with
`code: "client_message_conflict"` and the client ID. Invalid WebSocket UUIDs return
`code: "invalid_client_message_id"`.

Keep `SOKOUN_CHAT_DURABLE_REPLAY=false` until staging proves this sequence:

1. Send by WebSocket and suppress/drop the ACK locally.
2. Send the same client ID and content through REST.
3. Reconnect and replay the same ID through WebSocket.
4. Fetch history and verify one server message ID across all responses.
5. Confirm a late ACK only settles the pending item in the matching account and
   conversation.

Account switching must stop socket/REST retry workers before protected local records
are removed.

## Viewing, reviews, support, and profile

Available viewing dates/times continue to use `Africa/Cairo`. Revalidate a locally
restored slot against the current availability response and preserve the user's note if
the slot conflicts. Review eligibility continues to come from server `can_review` and
existing-review fields.

Support success requires the returned ticket `id` and `reference`. Profile update
success requires the current authorized profile response. Do not infer confirmation by
matching text.

## Hosted app associations

The backend now serves these exact, extensionless/non-redirected paths:

- `/.well-known/assetlinks.json`
- `/.well-known/apple-app-site-association`

They must be reachable on both `https://sokoun.app` and
`https://www.sokoun.app`. Until release signing identities are configured, they return
`503` with `Cache-Control: no-store` rather than unsafe placeholder data.

Production configuration required:

- `SOKOUN_ANDROID_PROD_SHA256_FINGERPRINTS`: comma-separated release/Play SHA-256
  fingerprints for `com.app.sokoon.real.estate`.
- `SOKOUN_ANDROID_DEV_SHA256_FINGERPRINTS`: comma-separated verified fingerprints for
  `com.app.sokoon.real.estate.dev`.
- `SOKOUN_APPLE_TEAM_ID`: the real Apple Team ID. Both production and dev bundle IDs
  are emitted with `/properties/*` access.

After configuration, verify HTTP `200`, `Content-Type: application/json`, no redirect,
and the exact identities on both hosts. Then test cold/warm property URLs, guest access,
workspace selection, repeated OS delivery, and missing/inaccessible property behavior
on signed physical-device builds.

Deferred links after store installation remain outside this delivery.
