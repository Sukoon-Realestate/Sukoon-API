# Sprint 1 — source and behavior audit

S21–S40. Audited against the sibling `sokoun` code on 2026-10-25. The original S01–S20 and foundation remain unchanged. All names, statuses, notification content and device data are illustrative. No external operations occur.

## Material source findings

- Registration currently proceeds to email OTP then login, not directly to identity approval.
- KYC has inconsistent optional copy versus executed required-document validation. S23 follows the executed validator; native copy/validation alignment requires a separate implementation decision.
- Password change logs out on success. Email change verifies both old and new addresses with the shared OTP challenge.
- Privacy preferences and device permissions are separate. Notification capabilities and menu visibility come from the server/workspace.
- ProfileScreen and RegisterFlowScreen are dispatch/flow hosts; they do not inflate the new-screen count. Tenant and owner profiles remain distinct.

## Theme and layout contract

Reuse the original design tokens, Readex Pro headings, IBM Plex Sans Arabic body, real signature, pine actions and restrained arches. System is default, Light/Dark persist and follow OS in System. Switching theme preserves drafts, scroll and review state. Native ThemeCubit, storage key, 320ms/easeInOutCubic and reduced-motion policy remain implementation constraints. The prototype reuses the original compact type scale and component proportions; native large text and safe areas still require implementation checks.

## Per-screen contract

<a id="s21"></a>

### S21 — Registration

Source: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/register_screen.dart`

Original visual references: S02, S17.

Separate first/last names, Egyptian mobile, email, password and confirmation. RegisterFlowScreen submits registration then shows email OTP; successful verification returns to login. Do not route registration directly to KYC or mark identity verified.

Required states: empty, invalid, submitting, server-error, otp-next.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/register_flow_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/widgets/register/register_intro.dart`, `sokoun/packages/core/lib/core/helpers/credential_validators.dart`.

<a id="s22"></a>

### S22 — Password recovery

Source: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/forgot_password_screen.dart`

Original visual references: S02.

Email reset link, not an OTP password-reset flow. Mask sent-to address, allow changing email and resending; display authoritative server messages and cooldown.

Required states: empty, invalid, sending, sent, server-error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/widgets/forgot_password/forgot_password_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/widgets/forgot_password/forgot_password_sent_view_content.dart`.

<a id="s23"></a>

### S23 — Identity documents

Source: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart`

Original visual references: S04, S17.

Audit mismatch: widgets label some existing-account inputs optional and canSubmit permits blank ID, but _submit always calls MediaValidators.validateKycDocuments, which requires a valid Egyptian national ID and all three images. Proposal follows the executed validator, flags the copy mismatch; no invented optional bypass. Preserve unsaved changes and file limits.

Required states: empty, selected, invalid, uploading, permission-denied, server-error, pending.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/widgets/kyc/kyc_upload_documents_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/auth/data/models/kyc_upload_documents_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_document_picker.dart`, `sokoun/packages/core/lib/core/helpers/media_validators.dart`.

<a id="s24"></a>

### S24 — Identity pending

Source: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_pending_screen.dart`

Original visual references: S03, S19.

Pending is not approved. Name, submittedAt and expectedReviewTime render only when present. OK returns existing accounts to initial route; new registration returns to login.

Required states: pending, metadata-absent, existing-account.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/widgets/kyc/kyc_status_summary_card.dart`.

<a id="s25"></a>

### S25 — Identity approved

Source: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_approved_screen.dart`

Original visual references: S03, S04.

Render approved only from authoritative verification result. Current KycApprovedScreen primary navigation is TenantSearchScreen; preserve entitlement decisions in app/server rather than granting capabilities from prototype.

Required states: approved.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/widgets/kyc/kyc_feature_tile.dart`.

<a id="s26"></a>

### S26 — Tenant profile

Source: `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/screens/tenant_profile_screen.dart`

Original visual references: S05, S18.

ProfileScreen dispatches workspace; this mockup represents TenantProfileScreen, not owner/company variants. Keep API-driven account details, activity and menu visibility, refresh after edits; preserve five individual-workspace tabs (home, saved, messages, housing, profile); company workspace has different activity entry.

Required states: loaded, loading, empty, server-error, unverified.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_screen.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/widgets/tenant_profile_content_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_content_view.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/widgets/tenant_profile_actions.dart`, `sokoun/apps/sokoun_app/lib/features/main_view/presentation/models/home_tab.dart`.

<a id="s27"></a>

### S27 — Edit profile

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_edit_screen.dart`

Original visual references: S17, S19.

Editable full name, avatar and city. Email is read-only with separate email-change flow. Preserve draft on failed save, server-known details on load failure and unsaved-changes guard. Save/refresh only after successful response.

Required states: loaded, dirty, saving, saved, load-error, server-error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_editor_scaffold.dart`, `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_account_fields.dart`.

<a id="s28"></a>

### S28 — Account settings

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_settings_screen.dart`

Original visual references: S20.

Preserve billing visibility (!workspace.isCompany), preference routes, security, public pages, experience guide and business policies. Logout and delete remain separate confirmed operations. Company/owner copy and visibility use workspace.

Required states: loaded, owner, company.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_settings_content_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/settings/profile_logout_sheet.dart`.

<a id="s29"></a>

### S29 — Verification status

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_verification_screen.dart`

Original visual references: S03, S19.

Status comes from ProfileVerificationContent: approved, pending, rejected, incomplete, unknown. Show rejection reason when present. Upload action only for canSubmit; refresh after returning from KycIntroScreen.

Required states: approved, pending, rejected, incomplete, unknown, loading, server-error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/shared/profile_verification_content_view.dart`.

<a id="s30"></a>

### S30 — Privacy

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_privacy_screen.dart`

Original visual references: S20.

Only shareLocation and showProfile from server settings values. Per-toggle pending; preserve/restore baseline on failure. Do not invent phone disclosure switches or treat sharing preference as OS permission.

Required states: loaded, saving, server-error, empty.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/settings/profile_privacy_content_view.dart`.

<a id="s31"></a>

### S31 — Change password

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/change_password_screen.dart`

Original visual references: S02, S17.

Current/new/confirmation fields; same credential policy as app validator. Preserve unsaved-changes guard. Successful save stops notification device registration and logs out; never return with a still-authenticated success.

Required states: empty, invalid, saving, server-error, reauthenticate.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/settings/change_password_form.dart`, `sokoun/packages/core/lib/core/helpers/credential_validators.dart`.

<a id="s32"></a>

### S32 — Change email

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/email_change_screen.dart`

Original visual references: S02, S03.

Start → verify_old (shared 6-digit OTP challenge) → enter_new → verify_new → complete. Authoritative resendAt, status recovery, expired/restart; only update local user after server complete, retain server email if local cache write fails.

Required states: start, verify-old, enter-new, verify-new, expired, server-error, complete.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/email_change/email_change_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/email_change/email_change_recovery_actions.dart`.

<a id="s33"></a>

### S33 — Security sessions

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/security_sessions_screen.dart`

Original visual references: S18, S20.

Distinct confirmed revoke-one, others, all, compromise. Other session revocation reloads; current/all/compromised stops device notifications and logs out only after successful write. Keep no-session/read failure states.

Required states: loaded, confirming, saving, empty, server-error, reauthenticate.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/settings/security_sessions_body.dart`.

<a id="s34"></a>

### S34 — Language

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/language_selection_screen.dart`

Original visual references: S20.

Arabic and English selection; explicit confirm persists via Languages. This Arabic visual proposal demonstrates selection/confirmation only, not a fabricated complete English translation.

Required states: arabic, english-selected, saving, server-error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/language_selection/language_selection_options.dart`.

<a id="s35"></a>

### S35 — Delete account

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_delete_account_screen.dart`

Original visual references: S20, S19.

Acknowledgement checkbox gates delete. Preserve server refusal and message, lock back during submission. Only successful delete triggers device-notification stop and logout. Prototype never deletes or collects real credentials.

Required states: unchecked, acknowledged, saving, server-error, deleted.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/settings/profile_deletion_content.dart`.

<a id="s36"></a>

### S36 — Profile contracts

Source: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_contracts_screen.dart`

Original visual references: S18, S19.

Paginated server contracts; statuses active/expired/cancelled/unknown; document link is validated and can be unavailable. Preserve workspace-specific journey entries. Owner rentals/leases/finance and tenancy invitations belong to later destinations.

Required states: loaded, loading, empty, server-error, document-unavailable.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/contracts/profile_contracts_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/contracts/profile_contract_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/widgets/contracts/contracts_journey_actions.dart`.

<a id="s37"></a>

### S37 — Notifications

Source: `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notifications_screen.dart`

Original visual references: S05, S18.

Role-resolved paginated inbox, unread count, mark-one/read-all with rollback and account-session guard. Detail fetches authoritative data; related destination is validated, not an arbitrary push URL. Invoice shortcut preserved when available.

Required states: loaded, loading, empty, marking, server-error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/widgets/notifications_screen_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/notifications/data/notification_destination.dart`.

<a id="s38"></a>

### S38 — Notification detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notification_detail_screen.dart`

Original visual references: S19.

Load detail, preserve primary destination from validated notification data and role. Dismiss returns; do not convert pending request into confirmed visit. Related content may be unavailable/unauthorized/deleted.

Required states: loaded, loading, server-error, destination-unavailable.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/widgets/notification_details_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/notification_navigation.dart`.

<a id="s39"></a>

### S39 — Notification settings

Source: `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notification_settings_screen.dart`

Original visual references: S20.

Server-driven items, canChange and footerNote; five known fallback keys. Demonstrated locked security alert is illustrative, not a hardcoded rule. Per-key optimistic preference with baseline recovery; device permission separate.

Required states: loaded, saving, server-error, permission-denied, empty.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/widgets/notification_settings_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/widgets/device_notification_permission_tile.dart`.

<a id="s40"></a>

### S40 — Help center

Source: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_screen.dart`

Original visual references: S05, S18.

Workspace/language-scoped remote help, FAQ search and empty results; support new/tickets/feedback are separate next-sprint destinations. Email contact only if backend supplies a valid address. FAQ content here is illustrative.

Required states: loaded, loading, server-error, empty, no-search-results, contact-unavailable.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/help/support_help_header.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/help/support_help_content_view.dart`.

## Review boundary

Mockup state selectors expose loading, read failure, empty and specific workflow variants. These are local design demonstrations; pending writes must keep real loaded content and drafts in Flutter. Unrepresented destinations explain the next app step. Production navigation, APIs, entitlement checks and confirmations remain authoritative. Sprint 2 is not started.
