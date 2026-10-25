# Sprint 2 — S41–S60

Current code audit: 2026-10-25. Original S01–S20 is the visual authority. Sprint 1 approved to continue; stop after Sprint 2 for user review. All data, maps, documents, prices and notes are illustrative. No Flutter production code changed.

## Inventory correction

OwnerListingsScreen directly returns OwnerPropertiesScreen, already covered by S16. It is now a reconciled alias, not a new screen. The remaining inventory is 278 destinations in 14 sprints (13 × 20, final 18). S41–S57 retain their IDs; the later unbuilt IDs shift by one. Sprint 2 ends with the real AddPropertyPhotosPage.

## Material behavior constraints

- Fixed-light native splash is intentional in the source, even in dark mode. Gallery is an immersive dark media surface in both themes.
- Workspace selection is presentation intent, not an authentication or company-authorization grant.
- Unknown support writes and continuation/payment checks must recover the original operation; never offer blind resubmission.
- Current and accepted historical policies are distinct. Missing accepted history must not fall back to current. Mock legal/terms text is explicitly illustrative.
- Map area filtering acts on loaded results. The offline map art is schematic and makes no geographic accuracy claim.
- Visit mutations require fresh authoritative data and permission; pending requests are not confirmed visits.
- Property media currently requires 10–25 nonduplicate photos and a prepared 1–60-second video, separately from virtual-tour capture.

## Visual contract

Inherited original CSS, Readex/Plex fonts, exact signature/icon registry, compact fields/actions, forest hub headers and restrained cards. Main-screen visual lineage is recorded per screen. Native text scaling, device permissions, safe areas, API behaviors and map/media runtimes still require native verification during implementation.

## Screen audit

<a id="s41"></a>
## S41 — Owner profile

Source: `sokoun/apps/sokoun_app/lib/features/owner/profile/presentation/screens/owner_profile_screen.dart`

OwnerProfileScreen uses the shared profile scaffold, verification, owner actions (reviews hub and revenue), account details and recent reviews. Listen for logged-in user updates, refresh after edit. Owner workspace uses the same pine action system, not a separate gold identity.

Original visual references: S05, S18, S19.

Required implementation states: loaded, loading, empty, error, unverified.

Rendered review variants: loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/owner/profile/presentation/widgets/owner_profile_content_view.dart`, `sokoun/apps/sokoun_app/lib/features/owner/profile/presentation/widgets/owner_profile_actions.dart`, `sokoun/apps/sokoun_app/lib/features/main_view/presentation/models/home_tab.dart`.

<a id="s42"></a>
## S42 — Tenant account summary

Source: `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/screens/tenant_account_summary_screen.dart`

Server-owned user, identity status, saved/completed-visit/chat counters and shortcuts. Labels/counts may come from API; absence is not an invented zero success. Shortcuts retain FavoritesScreen, TenantVisitsScreen and ProfileVerificationScreen.

Original visual references: S05, S19, S20.

Required implementation states: loaded, loading, empty, error, unverified.

Rendered review variants: loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/widgets/tenant_account_summary_content_view.dart`.

<a id="s43"></a>
## S43 — Private support attachment

Source: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_attachment_screen.dart`

Authenticated, workspace-scoped bytes; no public attachment URL or new sharing grant. Account cleanup clears preview and closes Cubit. PrivateFilePreview supports image pan/zoom, PDF and video with temporary-file cleanup; retain decode/load failure. This mockup bundles only an illustrative photo.

Original visual references: S08, S19.

Required implementation states: image, pdf, video, loading, error, session-ended.

Rendered review variants: pdf, video, session-ended, loading, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/private_attachments/presentation/widgets/private_file_preview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/cubits/support_attachment_cubit.dart`.

<a id="s44"></a>
## S44 — Create support ticket

Source: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_new_ticket_screen.dart`

Workspace-specific SupportTopic list; feedback defaults other, rental/payment context defaults payment. Subject 3–160 and description 10–4000. Payment issue can be general/off-platform-request/off-platform-payment. Preserve draft and context, retain had-attachments marker across recovery, reselect missing files. Unknown transmitted outcome blocks resubmit and recovers the original request key; do not create duplicate tickets. Navigate to details only after a confirmed ticket.

Original visual references: S02, S17, S20.

Required implementation states: empty, invalid, saving, error, unknown-outcome, payment, feedback, attachments-missing.

Rendered review variants: payment, feedback, unknown-outcome, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/new_ticket/support_ticket_form_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/new_ticket/support_ticket_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/data/enums/support_topic.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/data/enums/support_payment_issue.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/new_ticket/support_ticket_attachments.dart`.

<a id="s45"></a>
## S45 — Support ticket thread

Source: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_ticket_detail_screen.dart`

Authoritative ticket and reply Cubits; thread reference/status/messages, optional linked rental case. Reply enabled only for a fresh open ticket, with text or attachment validation, draft/unsaved guard and request-key recovery. Resolved tickets show new-ticket action with reply disabled; do not pretend a local chat message is a backend send.

Original visual references: S14, S19.

Required implementation states: loaded, loading, error, empty, resolved, unknown-outcome, attachments-missing.

Rendered review variants: resolved, unknown-outcome, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/detail/support_ticket_thread.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/detail/support_ticket_reply.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/detail/support_ticket_detail_content_view.dart`.

<a id="s46"></a>
## S46 — Support ticket list

Source: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_tickets_screen.dart`

Paginated workspace-scoped tickets, open/waiting/resolved/unknown statuses with authoritative subjects/reference/timestamps. Valid empty response shows a new-ticket action. Next pages and retry preserve loaded rows; no invented unread count.

Original visual references: S12, S18.

Required implementation states: loaded, loading, empty, error, loading-more.

Rendered review variants: loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/tickets/support_tickets_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/tickets/support_ticket_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/widgets/shared/support_ticket_status.dart`.

<a id="s47"></a>
## S47 — Public information page

Source: `sokoun/apps/sokoun_app/lib/features/shared/public_pages/presentation/screens/public_page_screen.dart`

One reusable PublicPageScreen for terms, privacy and aboutUs, not three counted screens. Load by page/language, reload on locale/parameter change, render backend content and links safely. About adds app identity. Empty published content is a valid empty state; mock text is explicitly illustrative, never approved legal content.

Original visual references: S02, S20.

Required implementation states: terms, privacy, about, loading, empty, error.

Rendered review variants: privacy, about, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/public_pages/data/enums/public_page.dart`, `sokoun/apps/sokoun_app/lib/features/shared/public_pages/presentation/widgets/public_page_body.dart`.

<a id="s48"></a>
## S48 — Current and accepted business policies

Source: `sokoun/apps/sokoun_app/lib/features/shared/business_policies/presentation/screens/business_policies_screen.dart`

accepted=null loads current rules; accepted=[] means historical version unknown and must not fall back to current. Show version, effectiveAt, description, rule labels/values. After a failed refresh, retained current data must be marked unconfirmed. No accept-agreement action exists on this read-only page.

Original visual references: S19, S20.

Required implementation states: current, loading, empty, error, accepted, unconfirmed.

Rendered review variants: accepted, unconfirmed, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/business_policies/presentation/widgets/business_policies_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/business_policies/presentation/widgets/business_policy_card.dart`.

<a id="s49"></a>
## S49 — Guide preferences and replay

Source: `sokoun/apps/sokoun_app/lib/features/shared/contextual_onboarding/presentation/screens/guide_settings_screen.dart`

Local preference loads asynchronously: disable until known, show failure and preserve baseline if persistence fails. Owner tours: home/navigation/requests; other workspaces: tenant home/navigation/decision tools. Replay checks safe root, update/prompt state and pending destination, opens workspace/tab before requesting tour. Demonstration is a small local tour, not a production navigation replacement.

Original visual references: S20.

Required implementation states: loaded, loading, error, owner, preference-failure, replay-blocked.

Rendered review variants: owner, loading, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/contextual_onboarding/presentation/cubits/guide_settings_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/contextual_onboarding/presentation/guide_replay.dart`.

<a id="s50"></a>
## S50 — Release notes

Source: `sokoun/apps/sokoun_app/lib/features/shared/whats_new/presentation/screens/release_notes_screen.dart`

Role-scoped release notes begin with installed version. Version chips combine installed/current/service history, deduplicated. Retry current selected version or reload installed when unknown. Notes empty is legitimate; sample release text is not a claim that new features shipped.

Original visual references: S04, S20.

Required implementation states: loaded, loading, empty, error, older-version.

Rendered review variants: older-version, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/whats_new/presentation/cubits/release_notes_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/whats_new/presentation/whats_new_service.dart`.

<a id="s51"></a>
## S51 — Continue drafts and operations

Source: `sokoun/apps/sokoun_app/lib/features/shared/recovery/presentation/screens/continuation_screen.dart`

Local continuation list and private-memory paginated server records remain separate. recoveryOnly filters applicable local work. Draft resumes are not blind write replays; unknown submissions/payment checks resolve original operation identity. Preserve upload counts and unsupported destination state; return refreshes server list.

Original visual references: S18, S20.

Required implementation states: loaded, loading, empty, error, recovery-only, unsupported, upload-incomplete.

Rendered review variants: recovery-only, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/shared/recovery/presentation/widgets/server_continuation_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/presentation/widgets/continuation_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/presentation/widgets/continuation_list.dart`.

<a id="s52"></a>
## S52 — Branded splash

Source: `sokoun/apps/sokoun_app/lib/features/splash_screen.dart`

Native startup waits for initialization, session restore and logo completion, checks route/mounted state, navigates authenticated users to HomeScreen and others to WorkspaceEntryScreen, then enables pending property-link delivery. Reduced-motion applies. Source explicitly keeps splash light in both themes, including retry theme; preserve this documented exception. No artificial login success or timed browser redirect.

Original visual references: S01, S02.

Required implementation states: starting, startup-error, guest, authenticated.

Rendered review variants: startup-error, guest.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/splash/presentation/cubits/splash_startup_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/splash/presentation/widgets/animated_splash_logo.dart`.

<a id="s53"></a>
## S53 — Workspace entry

Source: `sokoun/apps/sokoun_app/lib/features/main_view/presentation/screens/workspace_entry_screen.dart`

Four workspaces: individual, owner, student, company. selectEntry persists intent and replaces route with HomeScreen. A workspace is presentation context, not account identity, ownership, verification or company authorization. Do not invent an access gate or require login solely to choose; deeper features retain original gates.

Original visual references: S01, S02, S20.

Required implementation states: loaded, selection, storage-failure.

Rendered review variants: .

Read dependencies: `sokoun/apps/sokoun_app/lib/features/main_view/data/enums/app_workspace.dart`, `sokoun/apps/sokoun_app/lib/features/main_view/presentation/cubits/workspace_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/main_view/presentation/models/workspace_labels.dart`.

<a id="s54"></a>
## S54 — Map search results

Source: `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/property_map_screen.dart`

Map/list use paginated loaded public properties; only valid coordinates receive markers. Viewport filtering only filters loaded results, not a server search of all inventory. Show loaded/located counts and load-more footer, no-location rows stay accessible. Category uses rentalScope, resets page/cache/map owner and preserves viewing/group context. Schematic artwork and marker selection are local.

Original visual references: S06, S08.

Required implementation states: loaded, loading, empty, error, map-unavailable, no-coordinates, loading-more.

Rendered review variants: map-unavailable, no-coordinates, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/widgets/property_map/property_map_results.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/widgets/property_map/property_map_results_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/widgets/property_map/property_map_header.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_offers/data/enums/rental_listing_category.dart`.

<a id="s55"></a>
## S55 — Property photo viewer

Source: `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart`

Fixed slate/dark immersive viewer in both themes. Preserve initialIndex and image-transition identity, previous/next boundaries, thumbnail selection, photo labels/descriptions and empty gallery. Save uses PropertyPhotoSaveCubit and permission/error handling; prototype does not download actual files.

Original visual references: S08.

Required implementation states: loaded, empty, image-error, saving, permission-denied.

Rendered review variants: permission-denied, empty.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/widgets/tenant_property_photos/photo_viewer.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/widgets/tenant_property_photos/tenant_property_photo_viewer_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/cubits/property_photo_save_cubit.dart`.

<a id="s56"></a>
## S56 — Search entry

Source: `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_search_screen.dart`

Search query, property type, rental scope, areas, recent searches, filter count and saved-search restoration. Recent item/current-area/filter return preserve current filters and navigate results with correct context. Location resolves an area, not a silently accepted address. Restore validates saved filters; server options failure is not fabricated success.

Original visual references: S02, S05, S07.

Required implementation states: loaded, loading, empty, error, permission-denied, restored-search.

Rendered review variants: permission-denied, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/widgets/tenant_search_screen_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_search_entry_commands.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/cubits/search_restoration_cubit.dart`.

<a id="s57"></a>
## S57 — Tenant viewing detail

Source: `sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/screens/visit_details_screen.dart`

Fresh authoritative details gate cancel/review/reschedule/reassign. Pending remains awaiting owner, not confirmed. Cancellation requires confirmation and successful server result, then returns updated visit. CanChat starts context-aware conversation; canReview opens ReviewsHub, and contact permission refreshes on return/resume. Calendar export only when VisitCalendarData can build an event. Cached data cannot trigger mutating actions. Owner phone is never invented or exposed.

Original visual references: S11, S12, S19.

Required implementation states: pending, confirmed, completed, cancelled, loading, error, stale, restricted-contact.

Rendered review variants: confirmed, completed, cancelled, stale, loading, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/details/visit_details_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/details/visit_details_actions.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/details/visit_details_extra.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/widgets/details/visit_calendar_button.dart`.

<a id="s58"></a>
## S58 — Owner requests workspace

Source: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_requests_screen.dart`

Distinct multi-tab OwnerRequestsScreen, unlike the already-covered embedded OwnerVisitRequestsScreen. Visits always; housingOffers enables demand and my-offers; groupApplications enables group tab, with tab-set reset key when capability set changes. Verified-account and planning gates stay authoritative; no blanket entitlement from tab preview.

Original visual references: S18.

Required implementation states: visits, loading, empty, error, restricted, groups, offers, capability-change.

Rendered review variants: restricted, groups, offers, loading, empty, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_requests_screen.dart`, `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/widgets/owner_group_applications.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/planning_feature_gate.dart`.

<a id="s59"></a>
## S59 — Property location picker

Source: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/screens/property_location_picker_screen.dart`

Map tap/search/native locate selects valid coordinates; confirm Go.back(selected) only when valid and not busy. Satellite is a separate local view option. Async generation rejects stale geocoder results; reverse-geocode failure retains coordinates. Distinct denied/denied-forever/service-off/no-results/unavailable failures with settings entry. Tablet uses map/sidebar; no real device location is requested by this offline mockup.

Original visual references: S07, S17.

Required implementation states: selected, no-location, loading, error, permission-denied, map-unavailable, no-results, geocoder-offline.

Rendered review variants: no-location, permission-denied, map-unavailable, loading, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/property_location/property_location_confirmation.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/cubits/property_location_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/property_location/property_location_controls.dart`.

<a id="s60"></a>
## S60 — Property creation: media step

Source: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_photos_page.dart`

Photos step is distinct from original S17 basics. Current validator requires 10–25 nonduplicate photos AND ready video (1–60s); video preparation blocks next. Keep main selection, reorder/replace/delete, names/descriptions, virtual-tour-later checkbox and partial-offering accommodation media. This is step 2 of 3, not publish. Demo thumbnails reuse bundled artwork for visual layout only; no real media validation/upload occurs. Next opens later planned pricing step explanation.

Original visual references: S17, S08.

Required implementation states: ready, empty, duplicate, preparing, video-missing, permission-denied, partial-offering, error.

Rendered review variants: preparing, duplicate, partial-offering, error.

Read dependencies: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_photos_page.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/property_form_validation.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/property_photo_grid.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/property_video_picker.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/rental_accommodation_media_section.dart`, `sokoun/packages/core/lib/core/helpers/validators.dart`.

## Delivery gate

Sprint 3 remains unstarted. User review/confirmation is required before creating further mockups.
