# Sokoun — Profile, Settings and Support backend handoff

Date: 2026-10-03. Reference: repository export `Sokoon Figma Prototype Design`, storyboard groups 13–18 in `src/app/App.tsx`.

The Flutter screens are implemented for both workspaces. The endpoints marked **proposed** below are client contracts awaiting backend implementation and confirmation; their presence in `ApiConstants` does not mean they are deployed. The app shows actual API errors when a service is unavailable and never invents tickets, contact numbers, contracts or successful saves.

Import [the proposed Postman collection](profile_settings_support.postman_collection.json), implement the contracts, then add the confirmed requests and real response examples to the authoritative root `collection.json`. That collection has not been changed to imply the proposed endpoints are live.

## Screen coverage and ownership

| Prototype group | App screens and access | Responsibility |
| --- | --- | --- |
| Profile — Tenant | Final Profile tab → edit profile, verification status, contracts, reviews and detailed account summary | Shared identity layout and tenant activity; visits stay in the Visits tab |
| Profile — Owner | Final Profile tab → edit profile, verification status, revenue and recent reviews | Shared identity layout and owner statistics; properties and requests stay in their own tabs |
| Settings — Tenant | Profile settings icon → settings → language, existing notifications, privacy, password, legal/about, delete and logout confirmation | Preferences and account controls |
| Settings — Owner | Profile settings icon → settings, with the owner notification destination | Same account controls, owner context |
| Support — Tenant | Profile support icon → help center → new ticket / my tickets → ticket details and replies | Help, complaints about owners and issue tracking |
| Support — Owner | Profile support icon → owner support → same ticket flow with complaints about tenants | Help, listings and tenant complaints |

Both workspaces use `ProfileScreen` as their final tab, labelled **الملف الشخصي** in Arabic and **Profile** in English. It selects the existing role-specific profile Cubit, while both roles share the scaffold, identity header, edit action, verification tile and account-detail layout. The owner More menu is consolidated into Profile. Settings and Support appear once each in the Profile app bar and remain available when a profile API fails.

Profile editing and identity verification do not also appear in Settings. Language, legal pages, logout and deletion only appear in Settings. Notification switches are owned by the existing notification-settings feature; privacy only owns location and profile visibility. The tenant Profile no longer repeats the Visits tab entry. The detailed tenant account summary remains a secondary destination for completion and activity totals. Owner identity uses gold; shared primary actions remain teal. Account-verification notifications open verification status, and security alerts open Settings after selecting the Profile tab.

This navigation unification requires no new endpoint. Keep the tenant and owner read contracts below, sourcing common identity fields from the same account record so an edit in either workspace is reflected in both. The legacy tenant `menu_items.visit_requests` field may remain for compatibility; it is no longer rendered as a Profile menu option.

All 28 storyboard frames in groups 13–18 map to these implemented or reused routes:

| Prototype frames | Flutter destination |
| --- | --- |
| `T-PROFILE-01`, `T-SUMMARY-01` | `TenantProfileScreen`, `TenantAccountSummaryScreen` |
| `O-PROFILE-01`, `O-MORE-01` | Consolidated `ProfileScreen(workspace: owner)` → `OwnerProfileScreen` |
| `T-EDIT-01`, `O-EDIT-P-01` | Existing `ProfileEditScreen`, with the correct workspace |
| `T-KYC-04c`, `O-KYC-01b` | `ProfileVerificationScreen`, displaying the actual server status |
| `T-SETTINGS-01`, `O-SETTINGS-01` | `ProfileSettingsScreen`, with role-specific notification routing |
| `T-PRIV-01`, `O-PRIV-01` | `ProfilePrivacyScreen` |
| `T-PWD-01`, `O-PWD-01` | `ChangePasswordScreen` |
| `T-TERMS-01`, `O-TERMS-01` | Existing `PublicPageScreen` for terms |
| `T-ABOUT-01`, `O-ABOUT-01` | Existing `PublicPageScreen` for about, with the app logo and installed version |
| `T-DELETE-01`, `O-DELETE-01` | `ProfileDeleteAccountScreen`, with acknowledgement |
| `T-LOGOUT-01`, `O-LOGOUT-01` | `ProfileLogoutSheet` |
| `T-SUPPORT-01`, `O-SUPPORT-01` | `SupportScreen`, with workspace/language-specific help |
| `T-SUPPORT-02`, `O-SUPPORT-02` | `SupportNewTicketScreen`, with role-specific complaint categories |
| `T-TICKET-01`, `O-TICKET-01` | `SupportTicketDetailScreen`, with real thread/status/replies |

`SupportTicketsScreen` adds access to previous tickets; `ProfileContractsScreen` makes the existing tenant contracts entry usable. Shared account screens are reused across workspaces rather than duplicated.

The exported prototype contains unrelated appearance and two-factor toggles without corresponding storyboard screens or a complete authentication contract. They are not represented as fake working switches. Dark mode and login challenge/2FA need separate product and authentication work. Live support chat and the prototype's `16xxx` numbers are replaced by tickets and backend-configured phone/email contacts.

## Shared API conventions

- Base path: `{{base_url}}/api/v1/`. Keep trailing slashes.
- Reuse the current authenticated session/cookie mechanism. Determine account identity from the session, never a submitted user ID. A single account can use tenant and owner workspaces.
- `workspace=tenant|owner` identifies UI context, not authorization. Confirm listing, contract, ticket and attachment ownership on every operation. Ticket IDs must not grant cross-account access.
- Arabic is the initial and fallback app language. Help and public pages accept `lang=ar|en`, defaulting to `ar`. Return concise Arabic errors for Arabic requests. Saved user language remains respected.
- Successful reads use the current envelope: `{ "key": "success", "message": "", "data": ... }`. Empty collections are valid `200` responses. Dates/timestamps use ISO 8601; booleans must be JSON booleans.
- Paginated `data` is `{ "count": 0, "per_page": 20, "total_pages": 1, "next": null, "results": [] }`. Return stable IDs and deterministic ordering. `total_pages` includes all results, not only the current page.
- Writes return success only after persistence. Validation/authentication errors use appropriate 400/401/403/404/409/429 status codes and the existing error envelope. Do not return an HTML error page or a 200 with an embedded failure.
- Cacheable GETs use the existing account-scoped core cache. FAQ cache also includes workspace/language; ticket detail cache includes workspace/ID. Writes are never cached as reads. Successful create/reply invalidates ticket lists; a confirmed complete reply response also replaces the cached detail representation.

## Reuse existing endpoints

| Method | Path | Backend checks |
| --- | --- | --- |
| GET | `profiles/my-account/` | Tenant identity, real counts, masked account fields and contracts count |
| GET | `profiles/account-summary/` | Accurate account completion and activity summary |
| GET | `properties/owner/profile/` | Owner identity, accurate statistics and reviews |
| GET | `properties/owner/revenues/` | Existing owner revenue destination; scope real totals and rows to the signed-in owner |
| GET | `profiles/user/my-profile/` | Editable account fields |
| PATCH | `profiles/edit/` | Existing multipart edit contract and avatar |
| GET/PATCH | `profiles/settings/` | Persist `share_location_for_search` and `show_profile_in_search`; absent options are not fabricated |
| GET/PATCH | `notifications/settings/` | Authoritative notification controls; do not create another source of notification preferences |
| GET | `pages/terms/`, `pages/privacy-policy/`, `pages/about-us/` | Real approved content for `lang=ar|en`, correct format and `updated_at` |
| POST | `auth/logout/` | Revoke this session before success |
| DELETE | `auth/delete-account/` | Remove/deactivate the account, revoke sessions and device tokens, handle listing/chat/visit relationships and document retention according to the approved deletion policy |

The existing profile-settings response may still include `visit_notifications` and `promotions_and_updates` for compatibility. The new privacy UI does not render those duplicate notification controls. Keep notification behavior consistent during migration.

Confirm deletion behavior against the copy on the dedicated deletion screen before release. It requires an explicit acknowledgement and logs the user out only after server success. Rejected deletions must keep the account signed in. Any retention/blocked-deletion rules must be returned clearly instead of silently succeeding.

## Edit profile loading and partial updates

Both roles open the same editor with the actual account identity already loaded by Profile. The page, form and back button stay visible while `GET profiles/user/my-profile/` runs or fails. A failed read shows the server error and a retry action inside the editor. Name and phone drafts survive a delayed response or retry. Optional city, gender and birth-date controls appear after a successful read, including an actual cached response. Save waits for an in-flight read to finish; after a failed read, the known name and phone fields can still be submitted to the existing PATCH endpoint.

Confirm that `GET profiles/user/my-profile/` is deployed and authorized for the current account in both workspaces. Return the standard JSON envelope with `data.id`, `full_name` (or `first_name` and `last_name`), `phone_number`, `email`, `gender`, `birth_date`, `avatar` and `city: {"id": "...", "name": "...", "slug": "..."}` or `null`. Use null/empty values only for genuinely unset optional fields. Add real success, validation and authentication response examples to the existing collection request. Missing identity fields must not become an empty account.

`PATCH profiles/edit/` remains multipart and sends `full_name`, `phone_number`, an optional new `avatar`, and only changed `gender`/`city_id`. Omitted fields must preserve their stored values. In particular, a failed GET must never erase city or gender when a user saves their name. An explicit city clear sends `city_id: ""`; an unchanged city omits the field. Email and birth date remain read-only in this editor. Keep the same omitted-field behavior on the legacy `PATCH profiles/user/update/` contract. A rejected PATCH keeps the user signed in with their draft intact; the client returns to Profile and updates account identity only after server success.

## Proposed endpoints to implement and add to the collection

### 1. Change password

`POST auth/users/set_password/` (proposed; verify the route and body with backend before deployment).

```json
{
  "current_password": "current password entered by the user",
  "new_password": "new password entered by the user",
  "re_new_password": "same new password"
}
```

Validate the existing password, confirmation and the backend password policy. The client enforces the repository's minimum of 8 characters and never trims passwords. Return `200 {"key":"success","message":"تم تغيير كلمة المرور","data":{}}` or `204` after success; the core handles an empty successful response. Return a validation error for an incorrect current password or mismatched/weak new password. Document whether the current session stays valid; the implemented flow expects it to stay valid and returns to Settings. Revoke other sessions as required by the agreed policy. For social-only accounts, return a clear account-specific response instead of a generic server error. Never log credential bodies.

### 2. Shared identity-verification status

`GET profiles/verification-status/` (proposed; shared by both workspaces).

```json
{
  "key": "success",
  "message": "",
  "data": {
    "status": "pending",
    "full_name": "اسم الحساب",
    "submitted_at": "2026-10-03T10:15:00Z",
    "rejection_reason": ""
  }
}
```

Allowed statuses: `incomplete`, `pending`, `approved`, `rejected`. `rejection_reason` is required when rejected. Do not return identity-document URLs in this summary. The existing upload flow is reused for incomplete/rejected accounts; pending and approved accounts do not show a resubmit action. Keep status consistent with tenant/owner profile verification flags and the admin review result. The UI can refresh after an upload or admin decision; it does not fake approval from a boolean toggle.

### 3. Tenant contracts

`GET profiles/contracts/?page=1&page_size=20` (proposed).

```json
{
  "key": "success", "message": "",
  "data": {
    "count": 1, "per_page": 20, "total_pages": 1, "next": null,
    "results": [{
      "id": "contract-example",
      "property_title": "شقة في المعادي",
      "status": "active",
      "start_date": "2026-10-01",
      "end_date": "2027-09-30",
      "document_url": "https://files.example.invalid/contracts/signed-document.pdf"
    }]
  }
}
```

Statuses: `active`, `expired`, `cancelled`. Return `results: []` for accounts without contracts and keep the profile contracts count accurate. Documents must be authorized, expiring HTTPS links suitable for the system document viewer. A nullable/empty `document_url` omits the document action. No contract is synthesized from the profile's count. This flow lists existing contracts; contract signing/creation is outside these six groups.

### 4. Role-specific help center

`GET support/help-center/?workspace=tenant&lang=ar` (proposed; also supports owner/en).

```json
{
  "key": "success", "message": "",
  "data": {
    "phone": "", "email": "", "hours": "",
    "faqs": [{
      "id": "visit-booking",
      "question": "كيف أحجز زيارة؟",
      "answer": "افتح صفحة العقار، ثم اختر موعدًا متاحًا وأرسل طلب الزيارة."
    }]
  }
}
```

Maintain separate relevant FAQ content for tenants and owners. All IDs must be stable and unique. Send only actual phone/email contacts and actual hours; empty values omit the corresponding action. FAQ answers are plain text and searchable within the returned role/language list. An empty FAQ list keeps the new-ticket and my-tickets actions available. Do not advertise live chat or placeholder phone numbers without an implemented service.

### 5. List the signed-in user's tickets

`GET support/tickets/?workspace=tenant&page=1&page_size=20` (proposed).

Return the standard paginated envelope with ticket summaries matching the model below. Filter by authenticated user and workspace; order by latest update descending with an ID tie-breaker. Both open and resolved tickets remain discoverable. `messages` can be omitted from summaries. Empty results are a successful empty state, not an error.

### 6. Create a support ticket

`POST support/tickets/` (proposed), JSON without attachments, multipart with attachments.

```json
{
  "workspace": "owner",
  "category": "report_tenant",
  "subject": "موضوع المشكلة",
  "description": "وصف المشكلة بالتفصيل"
}
```

- Shared categories: `visit`, `payment`, `verification`, `property`, `other`.
- Tenant-only category: `report_owner`. Owner-only category: `report_tenant`.
- Subject: 3–160 characters. Description: 10–4000 characters, after trimming. Validate nonblank content on the server.
- Optional multipart `attachments`: repeated files under that field name (no JSON file paths). Maximum 3 images, 5 MB each; JPG/JPEG, PNG and WebP. Verify the actual file type and return localized errors. Backend limits must match these client limits.
- Return `201` with the complete created ticket, including a nonempty stable `id`, a readable reference, and the initial user message containing the description/attachments. Missing IDs cannot be treated as a successful navigable ticket.
- Route tickets into the existing admin support console. Preserve workspace/category in the admin record. A complaint is a support ticket until a separate moderation action is taken; creating it must not automatically ban a tenant or owner.

### 7. Ticket detail and replies

`GET support/tickets/{id}/?workspace=owner` and `POST support/tickets/{id}/replies/` (proposed).

Detail returns:

```json
{
  "key": "success", "message": "",
  "data": {
    "id": "ticket-example", "reference": "SUP-00142",
    "subject": "مشكلة في حجز الزيارة", "status": "open",
    "created_at": "2026-10-03T10:15:00Z",
    "messages": [{
      "id": "message-example", "sender": "user",
      "body": "لا أستطيع إكمال طلب الزيارة.",
      "created_at": "2026-10-03T10:15:00Z",
      "attachments": [{
        "id": "attachment-example", "name": "screenshot.png",
        "url": "https://files.example.invalid/support/signed-image.png"
      }]
    }]
  }
}
```

- Ticket statuses: `open`, `in_progress`, `resolved`, `closed`. `sender` is `user` or `support`, relative to the signed-in account, never inferred from display names.
- Return the initial description as a message. Return messages in chronological order, with stable unique IDs. The current detail contract is a bounded full thread; agree limits before large production threads require a separate paginated message endpoint.
- Replies use JSON `{ "body": "نص الرد" }`, 1–4000 characters after trimming. The response is the **complete updated ticket** in the same envelope, not just the new message.
- Reject replies to resolved/closed tickets with a clear 409. The client hides the reply composer for these statuses and offers a new-ticket action.
- Detail must validate the account and requested workspace. Return 404 for a ticket the account cannot access. Attachment links must enforce ownership and expire; never expose public permanent complaint media.
- Save a reply before returning success. Failed writes preserve the draft and do not append a fake message. Notify the support team and user through the established notification pipeline; a refresh action updates the detail screen.
- Refreshing detail preserves an unfinished reply. Sending is disabled while the detail is refreshing, and refresh is disabled during a reply write. Unknown ticket statuses do not enable replies.

## Collection checklist for backend

1. Import the proposed collection alongside the current collection. Set `base_url`, an authenticated session, `workspace`, `ticket_id`, `lang` and local image paths.
2. Implement and confirm routes 1–7. Keep endpoint paths/body fields synchronized with `packages/core/lib/core/network/api_endpoints.dart` and the typed models before renaming anything.
3. Add Arabic/English help content, real contacts, empty collections, verification statuses, owner/tenant complaints, ticket replies and attachment examples.
4. Add failure examples: wrong current password, invalid fields/files, expired session, another account's ticket/contract, workspace mismatch, resolved-ticket reply and throttling.
5. Connect admin support replies/status changes to these records. Verify create → list → detail → reply → resolve with both workspaces and separate accounts.
6. Replace example.invalid links and sample text with real test response captures in the authoritative collection once deployed. Supply backend deployment/version information to mobile before release.

## Verification and remaining integration work

Client tests cover the final Profile tab in both workspaces, shared editing/verification, role-specific activity, Settings/Support access after profile failures, language changes on return to Profile, account/security notification routing, nonduplicate ownership, form validation, duplicate submission guards, failed-write draft retention, resolved ticket behavior, successful empty states and response/cache serialization. Edit-profile regressions also cover delayed/offline/failed reads, retry draft preservation, Back during a pending read, omitted unknown metadata, changed gender, duplicate writes, keyboard focus during saving and returning updated identity to both Profile tabs. The six main screens and both editors in success/error states are checked at 320/390/600/768/1024/1366 logical pixels with Arabic/English and text scales 1/1.3/2. Rendered comparisons use the repository's exported prototype; connected Figma reads were denied for both configured accounts.

The feature follows `data/enums`, `data/models`, data helpers and `presentation/cubits`, `screens`, `widgets`. Screens own remote lifecycle; form widgets own controllers/drafts; cacheable reads use the core cache contract; ticket/contract lists use `AppPagify`. The unchanged app bootstrap already starts in Arabic and falls back to Arabic.

From `apps/sokoun_app`, run `make accountCheck` for focused checks, or `make accountUiReview REVIEW_DIR=/tmp/sokoun-account-ui` to repeat responsive checks and export the Arabic screen captures. Tests inject fixtures only through test repositories.

Verification on Flutter 3.44.7:

- After the Edit profile fix, `make accountCheck` passes 502 focused tests: 501 profile/settings/support/workspace/architecture checks and the existing owner-revenue integration check updated for its Profile entry. Focused analysis reports no issues. Seven filtered checks also pass for the profile request/response contracts and city selection, clearing and serialization.
- The full app suite before this navigation refactor reported 1,931 passing tests and two existing failures: `motion_ux_test.dart` compares the current SDK's `Tristate.isTrue` semantics value to a boolean, and `mobile_dev_handoff_integration_test.dart` expects the property-card availability action that is already commented out in the existing source. The property-card source and those failing assertions were not changed. The full suite has not been repeated for the navigation or editor fixes.
- The earlier full app analysis reported 11 existing warnings/deprecation notices outside this change. Formatting, JSON validation and `git diff --check` pass.
- Arabic renders were reviewed against the bundled prototype export, then updated captures of the unified Profile layouts were reviewed on phones, narrow screens with large text and tablets. Responsive checks also cover short landscape height, form keyboard insets and text scales up to 2. Profile headers, statistics and account values reflow; masked phone numbers and email addresses preserve LTR reading order inside the Arabic layout. Unified captures are in `/tmp/sokoun-unified-profile-ui`; editor success/loading/error and actual pushed-route captures are in `/tmp/sokoun-edit-profile-ui` on the development machine.

Backend implementation, real-account integration, physical-device media picking/contact/document opening and admin notification delivery still require verification after the services are supplied. See the accompanying tests and visual captures for client evidence; fixtures are test-only and are not fallback content in the app.
