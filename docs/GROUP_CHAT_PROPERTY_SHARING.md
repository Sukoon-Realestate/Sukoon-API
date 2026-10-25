# Property cards in student housing-group chats

Existing housing-group conversations accept `kind: "property"` through the current REST and WebSocket message-send paths. The payload contains an optional caption in `content` and a typed `property` reference with `property_id` (UUID) and optional `offer_id`. Attachments and locations cannot be mixed with the property reference. Direct and company conversations reject this message kind.

Only housing-group summaries advertise `property` in `limits.message_kinds`. Clients should discover this capability before presenting the action. Group membership, its current period, account verification, planning access and send permissions remain authoritative on every request.

The conversation list accepts `conversation_type=housing_group`, combined with `workspace=student`, before pagination. Existing `q` search rules still apply. The default inbox remains scoped to the individual workspace; `include_groups` does not override this scope, and `workspace=all` is not a supported inbox. Aggregate workspace badges retain their existing behavior.

## Storage and projection

Migration `chat.0021_message_property_reference` adds a nullable JSON reference to `Message`. Existing messages and older writers remain compatible. The database stores only identities, not a user-supplied title, price or image.

ACKs, realtime events and history return a current public property card. The projection excludes owner/contact data, proofs and favorite membership. History/context pages batch property lookups. Withdrawn properties and unavailable, archived or mismatched offers return the original identities with `availability: "unavailable"`, without stale display fields. Deleting a chat message removes the card from its projection.

New sends of unavailable references return HTTP 422 / `chat_property_unavailable`. An exact retry of an already accepted client operation still resolves to its original message after property withdrawal. Changing the reference or caption with the same client operation identity conflicts. Membership and history-visibility boundaries still apply.

## Release

Deploy on top of the current `main`. The existing `scripts/run_api.py` runs `migrate_release` with the PostgreSQL migration lock before starting API/background processes. Confirm the intended release SHA, applied `chat.0021`, no pending migrations and a healthy `/health/` after deployment. Preserve current private/local media before replacing a runtime with ephemeral storage.

Updated Flutter lives in the separate `darak-app` repository. Backend deployment does not distribute a mobile build. Older mobile clients render the message as an unsupported kind.

## Verification

Run from `backend` against isolated PostgreSQL:

```sh
python -m pytest --ds=config.settings.postgres_test \
  core_apps/chat/tests/test_property_sharing.py \
  core_apps/chat/tests/test_group_socket.py \
  core_apps/chat/tests/test_group_messages.py \
  core_apps/chat/tests/test_group_api.py \
  core_apps/chat/tests/test_rich_attachments.py \
  core_apps/chat/tests/test_workspace_group_scope.py -q
```

Tests cover canonical/current projections, property and offer identity, authorization, deleted/replied messages, pagination scope, exact retry, group visibility, batch loading, and two WebSocket clients followed by REST retry. Legacy inbox test expectations were updated to match the existing workspace isolation contract without relaxing production permissions.
