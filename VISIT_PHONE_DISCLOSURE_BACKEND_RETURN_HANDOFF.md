# Visit Phone Disclosure — Backend Return Handoff

Date: 2026-10-08

## Status

The backend implementation is complete locally. Migration `properties.0020_propertyvisit_accepted_at` has been applied to `backend/dev.sqlite3`. It has not been deployed to a remote or staging database as part of this task.

Backend verification completed with **502 passing tests and 3 skipped**, plus Django system checks, migration-drift checks, and changed-file lint.

## Implemented policy

- Owner and tenant phone numbers remain hidden until the owner accepts a visit.
- Acceptance grants reciprocal access: the owner sees the tenant's current stored phone and the tenant sees the owner's current stored phone.
- Verification, a pending/rejected visit, creating a conversation, and sending messages do not grant phone access.
- The grant is recorded by `PropertyVisit.accepted_at`; it survives later cancellation because the number was already disclosed.
- Cancellation before acceptance does not grant access.
- Another visit between the same owner and tenant can use their existing accepted relationship. Property detail remains scoped to an accepted visit for that exact property; direct-chat disclosure is scoped to the participant pair.
- Guests, unrelated users, inactive users, message sender objects, sockets, feeds, public profiles, and notifications never receive a raw counterpart phone.
- The project currently has no account-block model. Any future block/revocation rule should be added to the shared disclosure policy.

## API contract

Counterpart objects now consistently include:

```json
{
  "phone_number": "",
  "masked_phone_number": "010****432",
  "is_phone_revealed": false,
  "phone_notice": "Phone numbers appear after the owner accepts the visit."
}
```

After acceptance:

```json
{
  "phone_number": "+201001234567",
  "masked_phone_number": "",
  "is_phone_revealed": true,
  "phone_notice": ""
}
```

For backward compatibility, the hidden `phone_number` value is an empty string rather than `null`. When disclosure is authorized but the account has no stored phone, `phone_number` is `null`, the flag remains `true`, and the hidden notice remains empty. Backend-owned hidden notices follow `Accept-Language` for English and Arabic.

The policy is applied to:

- `GET /api/v1/properties/owner/visits/requests/`
- `GET /api/v1/properties/owner/visits/requests/{visit_id}/`
- `GET /api/v1/properties/visits/received/`
- `GET /api/v1/properties/visits/{visit_id}/`
- `GET /api/v1/properties/visits/requests/`
- `GET /api/v1/properties/visits/requests/{visit_id}/`
- `GET /api/v1/properties/{property_id}/`
- `GET /api/v1/chat/conversations/`
- `POST /api/v1/chat/conversations/create/`
- `GET /api/v1/chat/conversations/{conversation_id}/` — newly added, participant-only

Conversation-level `other_participant` objects contain the contact fields and `can_send`. Chat-message sender objects remain unchanged and contain no phone fields.

## Acceptance behavior

`POST /api/v1/properties/owner/visits/requests/{visit_id}/accept/` now locks and updates the visit transactionally. It saves `accepted_at` together with the confirmed status. Repeating an already completed acceptance returns successfully without creating another grant or notification.

The tenant's `visit_accepted` notification is created once and push delivery is scheduled only after transaction commit. Its data includes `visit_id`, `property_id`, and `conversation_id` when a direct conversation already exists. It never contains either phone number.

Existing currently confirmed visits are backfilled from their update timestamp. Previously cancelled accepted visits are backfilled when an existing `visit_accepted` notification provides historical evidence. Older cancelled rows with no such evidence cannot safely be inferred and remain undisclosed.

There is no relevant server response-cache layer in these endpoints; authorization and current phone values are calculated from fresh database state. Mobile should still refresh its local visit/property/conversation snapshots after acceptance, notification, resume, and account changes as described in the original handoff.

## Mobile integration notes

- Trust `is_phone_revealed`; never infer authorization from a non-empty masked number.
- When the flag is `true`, display `phone_number` and ignore stale hidden copy.
- When the flag is `true` but `phone_number` is null, display the app's unavailable-number state and keep chat available.
- Use the new conversation-detail route when opening/resuming a thread and after an acceptance notification.
- A successful refresh with `is_phone_revealed: false` must replace an older locally cached grant.
- No lease, tenancy, signing, or rental inventory state is created by accepting a visit.

## Remaining rollout checks

Before enabling this against production, apply migration `0020` to the target PostgreSQL database and run the original handoff's three-account staging checks. Real-device notification refresh and native dialer behavior still require mobile/staging validation.
