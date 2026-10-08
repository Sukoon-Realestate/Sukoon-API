# Visit acceptance and phone disclosure — backend handoff

## Business rule

Owner and tenant phone numbers stay private until the owner accepts a visit.
Acceptance shares **both** numbers with that visit's two participants. A displayed
number replaces the hidden-phone notice; it must never appear beside a notice
saying it is hidden. Verification, starting a chat, sending a message, or merely
submitting a visit request does not grant phone access.

The mobile integration now follows
[the backend return handoff](VISIT_PHONE_DISCLOSURE_BACKEND_RETURN_HANDOFF.md).
The backend reports that its implementation and migration are complete locally;
deployment to staging/production remains outstanding. The server implementation
is not in this repository, and client fixture tests do not establish deployed
server authorization or push delivery.

## Where the messages appeared in the app journey

Paths below are relative to `apps/sokoun_app/lib/features/`.

| Journey / screen | Source | Result after this change |
| --- | --- | --- |
| Tenant browses a property → owner card | `tenant/home/presentation/widgets/tenant_property_details/owner_card.dart` | Show the granted owner number; show unavailable when granted without a stored number; show the acceptance policy when not granted. |
| Tenant books a visit | `tenant/visits/presentation/widgets/book_visit/visit_privacy_banner.dart` | Explain that acceptance shares the tenant's number with the owner and the owner's number with the tenant. |
| Owner opens Visit Requests | `owner/home/presentation/screens/owner_visit_requests_screen.dart` and its `owner_visit_request_card.dart` | Granted cards show the tenant number or the unavailable-number state, independently of the current visit status. Accepting from the list opens request details. |
| Owner opens request details | `owner/visits/presentation/widgets/owner_request_details/owner_request_details_content.dart` | Replace the privacy banner with a selectable number and call action. Ignore stale `phone_notice` when showing the number. |
| Owner confirms acceptance | `owner/visits/presentation/widgets/owner_request_details/owner_accept_request_sheet.dart` | Confirmation copy explains that both numbers will be shared. Details reload after a successful acceptance. |
| Tenant opens visit details | `tenant/visits/presentation/widgets/details/visit_details_content.dart` and `visit_details_extra.dart` | Show the granted owner number and call action; omit the old masked-number row. |
| Owner or tenant opens Chats | `shared/chat/presentation/widgets/chat_list/chat_list_content.dart` | Remove the unconditional inbox banner claiming numbers are always hidden. |
| Owner or tenant opens a chat | `shared/chat/presentation/widgets/chat_thread/chat_messages_view.dart` | Show the granted counterpart number, otherwise explain the acceptance rule. An authorized but missing number shows an unavailable message. |
| Read-only chat history | Same `chat_messages_view.dart`, used by `previous_chat_screen.dart` | Refresh contact metadata on entry, acceptance notification and resume; show the current grant without creating a socket connection or composer. |
| Owner views their own profile | `shared/profile/presentation/widgets/owner/owner_profile_content_view.dart` | Keep the general policy explaining when their number is shared; this is about their own account, not a particular counterpart. |
| Privacy settings | `shared/profile/presentation/widgets/settings/profile_privacy_content_view.dart` | Explain that numbers are not public and acceptance shares them between the two participants. |

The example screen files delegate their contact copy to the widgets above.
Photo/video instructions forbidding contact details in public media and the
confidential-report banner are separate policies and remain appropriate.

## Backend implementation

### 1. Commit the visit acceptance and contact grant together

Use the existing owner action:

```http
POST /api/v1/properties/owner/visits/requests/{visit_id}/accept/
```

1. Authenticate the owner and authorize ownership of the actual visit property.
2. Validate that this request can be accepted. Preserve the existing verification
   and visit-state rules.
3. In one transaction, accept the visit and grant reciprocal phone access to its
   owner and tenant. Retain an acceptance timestamp or equivalent persisted
   evidence; do not infer historical acceptance from a currently canceled state.
4. Subsequent reads must calculate authorization and current phone values from
   fresh state. The returned backend has no relevant response-cache layer;
   mobile refreshes its own visit/property/conversation snapshots.
5. After commit, deliver the tenant's `visit_accepted` notification. Include
   `visit_id`, `property_id`, and `conversation_id` when a conversation exists.
   Do not put either phone number in push notifications.
6. Repeated acceptance must not create duplicate grants or notifications. A failed
   or rejected acceptance must not disclose either number.

Acceptance confirms a viewing appointment. It does not create a tenancy, sign a
lease, or change rental inventory.

### 2. Use one authorization policy for all serializers

Compute disclosure for the **authenticated viewer**, counterpart and actual
accepted relationship. Never accept a client-supplied `is_phone_revealed` value
as authorization. An unrelated tenant, another owner, and guests must not receive
the raw phone in any response, even if the UI would hide it.

Implemented scope: retain the qualifying `(owner_id, tenant_id, property_id,
visit_id)` relationship. Property details use a qualifying visit for that
property. Direct chat is currently between users, not a single property: a
qualifying accepted visit between those two users grants reciprocal contact in
their conversation. Do not expose either number to other conversations or users.

| Relationship state | Server disclosure |
| --- | --- |
| No accepted relationship; pending/new/rejected visit | `is_phone_revealed: false`; raw phone is an empty string. |
| Accepted / confirmed visit | `is_phone_revealed: true`; full counterpart number returned. |
| Completed visit | Keep the acceptance grant; return the counterpart number. |
| Canceled before acceptance | No grant; do not return the raw phone. |
| Canceled after acceptance | Retain the prior grant through persisted `accepted_at`, because the numbers were already shared. Return an explicit flag; mobile cannot infer prior acceptance from `canceled`. |
| Another pending request while the same pair already has a qualifying acceptance | Derive the explicit flag from that qualifying relationship, rather than from this pending request alone. |
| Access revoked by an existing block/account policy | Explicitly return false and omit the raw phone. Mobile replaces a prior grant on a successful refresh. |

The returned backend retains cancellation grants and backfills historical
acceptances only when evidence exists. There is currently no account-block model;
a future revocation policy must use the same authorization policy on all reads.

### 3. Return the contact fields consistently

Use these existing field names on the counterpart object:

Before a qualifying acceptance:

```json
{
  "id": "counterpart-id",
  "phone_number": "",
  "masked_phone_number": "010****432",
  "is_phone_revealed": false,
  "phone_notice": "Phone numbers appear after the owner accepts the visit."
}
```

After acceptance:

```json
{
  "id": "counterpart-id",
  "phone_number": "+201001234567",
  "masked_phone_number": "",
  "is_phone_revealed": true,
  "phone_notice": ""
}
```

Return the real stored number, preferably with country code. Do not return a
masked value in `phone_number`. Clear obsolete hidden-phone copy from
`phone_notice` and any contact-specific summaries. Localize backend-owned
notices and messages using the existing `Accept-Language` contract.

When authorized but no phone is stored, return `phone_number: null`, keep
`is_phone_revealed: true`, and leave the notice empty. Mobile preserves the grant,
shows its unavailable-number message, and keeps server-authorized chat available.
A canonical nested null clears an older flattened number instead of reusing it.

| Mobile read | Counterpart object / required result |
| --- | --- |
| `GET properties/owner/visits/requests/` | Each result's `tenant` must include the tenant phone and disclosure flag after acceptance. Legacy flattened `phone` plus `is_phone_revealed` is also parsed. |
| `GET properties/owner/visits/requests/{visit_id}/` | `tenant.phone_number`, `tenant.is_phone_revealed`, and cleared `tenant.phone_notice`. |
| `GET properties/visits/received/` and `GET properties/visits/{visit_id}/` | Apply the same owner-view tenant serialization to legacy received-visit routes. |
| `GET properties/visits/requests/` and `GET properties/visits/requests/{visit_id}/` | Each tenant-view `owner` includes the owner's full phone and flag after acceptance. Legacy flattened `owner_phone` plus `is_phone_revealed` is also parsed. |
| `GET properties/{property_id}/` | Viewer-specific `owner.phone_number` and `owner.is_phone_revealed`. Mobile also parses flattened `owner_phone` / `is_owner_phone_revealed`. |
| `GET chat/conversations/` | Every `other_participant` includes the viewer-authorized phone and explicit disclosure flag. |
| `POST chat/conversations/create/` | Return the same contact fields whether creating or returning an existing conversation. Creating a conversation grants no access by itself. |
| **Contact refresh:** `GET chat/conversations/{conversation_id}/` | The returned backend implements this participant-only route. Mobile calls it on opening/resuming active or read-only chat and after acceptance notifications. |

All paths in the table are relative to `/api/v1/`. Keep the existing response
envelope, pagination, participant names, unread counts and permissions. A
conversation-details response looks like:

```json
{
  "id": "conversation-id",
  "other_participant": {
    "id": "counterpart-id",
    "full_name": "Counterpart name",
    "phone_number": "+201001234567",
    "is_phone_revealed": true,
    "can_send": true
  },
  "unread_count": 0,
  "last_message_preview": "",
  "updated_at": "2026-10-08T10:00:00Z"
}
```

Only conversation members may call the details route. Do not add unrestricted
phone fields to chat-message sender objects, socket broadcasts, property feeds,
search results or public user profiles.

## Mobile behavior and compatibility

- A full, granted number renders as selectable text with a call action. Masked
  values never become callable numbers.
- All visit, property and chat contact reads require `is_phone_revealed: true`.
  Missing, null or false flags do not authorize disclosure, even for a confirmed
  visit or a full raw number. The previous visit-status fallback was removed.
- A true flag is honored for pending, rejected, completed or canceled visits
  with an existing accepted relationship; mobile does not reconstruct history.
- Every granted contact with no usable phone shows “The phone number is currently
  unavailable. You can use the app chat.” Stale hidden notices and masked values
  are ignored for granted contacts, including null phones.
- Successful owner decisions invalidate the local pre-decision details cache.
  Details then reload. Accepting from the list opens that details screen.
- Visit/property details refresh for relevant acceptance notifications and app
  resume. Owner/tenant visit lists and the conversation list refresh on acceptance
  notifications and resume. Visit lists refresh on return from details; tenant
  cancellation also refreshes the authoritative list. Property details refresh
  when returning from a child flow.
- Active chat refreshes only contact metadata; message history, draft and socket
  ownership are preserved. A failed contact refresh does not grant access or
  interrupt messaging. A successful false flag replaces a previous grant.
- `other_participant.can_send` is mapped into conversation permissions; the older
  root `can_send` format remains supported. A fresh permission updates both the
  composer and sending guard without resetting drafts or message history. Queued
  messages pause if sending is denied. Read-only history refreshes contact but
  never connects, sends, or takes ownership of an active socket.
- The new chat details read requests fresh data without a separate persistent
  contact cache. Existing list/visit/property snapshots serialize contact flags
  and use the app's account-scoped cache. Offline snapshots represent the last
  known permission, so server revocation cannot erase a number already viewed or
  make offline devices immediately aware of a policy change.
- Refresh subscriptions and responses are bound to the account-session
  generation. The existing account navigation/cache lifecycle recreates account
  screens on account replacement and clears account caches on logout; responses
  from the old session cannot grant access in the new one.
- Own-account profile/settings copy explains the general policy and remains
  appropriate after individual visits are accepted.

## Backend acceptance checks

Run these with two real test accounts and an unrelated third account:

1. Before acceptance, check owner and tenant lists/details, property details,
   conversation list/create/details. Neither counterpart raw number may appear in
   response bodies. Both apps must explain the acceptance rule.
2. Accept through the owner list and through request details. Check that the next
   reads return both full numbers and true flags, and all hidden notices are
   empty. Check that the owner details screen displays the tenant number.
3. Keep the tenant's visit details or chat open while the owner accepts on another
   device. Deliver the acceptance push after commit. The tenant must receive the
   owner's number after the metadata refresh, without reopening message history.
4. Repeat acceptance, simulate a failed transaction, and race acceptance against
   cancellation/rejection. Verify grants and notification deduplication.
5. Check completed visits, cancellation before/after acceptance, multiple visits
   between the same pair, and the chosen block/revocation policy across all reads.
6. Attempt the new chat-details route and visit/property reads as the third
   account and as a guest. Never disclose either counterpart number.
7. Test Arabic and English notices, cached-to-fresh transitions, app resume,
   account switch/logout, and a phone number updated after acceptance.

Client verification is recorded in the accompanying code tests. Live API,
cross-device push delivery and server authorization still need staging evidence.

## Client integration verification — 2026-10-08

- Focused coverage: **210 passing tests, 1 existing skipped** across phone disclosure,
  chat API/flow/Cubit, owner visit requests, tenant visit data/flow, and property
  details tests, plus notification/resume contact-refresh tests.
- Disclosure coverage includes explicit grants for every visit status, missing
  and denied flags on confirmed visits, canonical null phones overriding stale
  flattened numbers, stale hidden notices/masks, and symmetric cache mapping.
- Flow coverage includes conversation permission refresh with retained drafts,
  queued-delivery denial, read-only contact refresh without socket ownership,
  collection refresh on acceptance/resume, acceptance during an older contact
  read, failed refreshes, and responses arriving after account switches.
- The shared contact card renders in Arabic and English at widths 320, 390,
  600, 768, 1024 and 1366, with text scales 1, 1.3 and 2. Phone text keeps LTR
  direction inside RTL screens.
- Rendered fixtures include owner pending/accepted and tenant accepted details,
  plus authorized missing-number states for owner/tenant visit details and the
  property owner card in Arabic/English at width 320 and text scale 2. The latter
  omit hidden copy and masks; tenant chat remains available. These are widget-test
  renders, not real-device or live API validation. Native dialer launch still
  requires device verification.
- Dart analysis and whitespace checks were run. The existing
  `TickerMode.of` deprecation in the chat list is unrelated to disclosure.

## Remaining rollout work

Apply `properties.0020_propertyvisit_accepted_at` to the target PostgreSQL
database before enabling the client against that deployment. Then run the
three-account acceptance checks above on staging, including current phone
updates, historical cancellation grants, Arabic/English notices, actual
cross-device push refresh and native dialer launch. The returned backend has
only applied this migration to its local development database; those deployment
and device checks were not performed in this mobile integration.
