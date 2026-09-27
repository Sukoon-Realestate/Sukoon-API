# One account, tenant and owner workspaces

## Flutter behavior

Every signed-in account can open both workspaces. New accounts start in tenant;
the last selection is saved per account on this device. Switching preserves the
session, visited tabs, and the shared message/notification inboxes. It never
updates a server role. Existing cached selections migrate to their original
account once. Previously separate accounts are not merged.

Registration sends the existing identity/password/document fields without
`type`. Login and Google login establish identity using a fresh
`GET auth/users/me/`; this request deliberately has no offline cache fallback.
Legacy response `type` is retained as metadata only. The existing OTP and KYC
flows remain in place.

## Required API behavior (server implementation is outside this repository)

- `POST auth/users/` must accept registration without an exclusive role.
- One cookie session must authorize the same account to use both tenant and
  owner APIs. Do not require a switch-role request or a second account.
- `properties/owned/`, `properties/owner/dashboard/`, owner profile/calendar,
  and received visit requests must work for accounts without existing listings,
  returning ordinary empty results with the existing response schemas.
- Property/visit mutations must authorize the authenticated account against
  resource ownership or participation, plus existing verification/moderation
  requirements. Opening a workspace must not grant those permissions.
- `profiles/edit/` edits shared identity. `profiles/my-account/` and
  `properties/owner/profile/` must reflect the same name/contact/avatar fields.
- `notifications/`, unread counts, device registration, chat conversations and
  `/ws/chat/` must cover the whole account, independently of the visible workspace.
- Preserve `notification_type`, resource IDs and action fields. A `visit_request`
  belongs in owner requests; accepted/rejected tenant visits belong in tenant.
  An ambiguous `view_visit` action without an event type cannot identify a role.
- Reject booking one's own property and creating a conversation with oneself.
  Flutter guards known ownership too; server enforcement is still required.
- Return meaningful 403 responses for verification/ownership restrictions and
  401 only for invalid authentication. Flutter displays the server's restriction
  message; changing workspace must not be treated as an authentication failure.

## Release gate

Do not release this client against a server that still restricts accounts by a
single `type`. On staging, verify one newly registered account and one account
of each legacy type: browse/save/request visits, create/manage a listing, receive
and resolve requests, edit the shared profile, and use both inboxes with the same
cookie session. Check unverified/restricted accounts separately.

Verify cold-start and signed-out push taps, expired sessions, offline data,
logout followed by a different account, and Arabic/English navigation on a
mobile device. App/widget tests do not establish that the deployed server meets
this contract. No backend or production changes are included here.

## Relevant checks

From `apps/sokoun_app`: `flutter test --no-pub` and `dart analyze .`.
The workspace tests cover migration, independent account parsing, session/cache
isolation, deferred notification routing, retained tabs, and unsaved edits.
