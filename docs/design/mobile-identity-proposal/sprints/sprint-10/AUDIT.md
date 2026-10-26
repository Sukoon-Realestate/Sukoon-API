# Sprint 10 — S201–S220

This sprint belongs to the authorized three-sprint batch (8–10). Stop after Sprint 10 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-08-10-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s201"></a>
### S201 — Group invitation preview

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invite_screen.dart`

ID read vs token preview distinct. Token + canJoin permits join; owner ID mode only copies validated link, never joins as invitee. Expired/full/revoked disables joining; native clipboard not used in prototype.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, expired.

Rendered review variants: owner-link, loading, error, stale, restricted, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/group_invite_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_screen.dart`.

<a id="s202"></a>
### S202 — Group invitation links

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invites_screen.dart`

Group-scoped invite list; revision/capability permissions gate create/revoke and refresh. Never expose real invite tokens in a screenshot; expiry/full capacity and revoked states prevent joining.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, expired.

Rendered review variants: loading, error, stale, restricted, empty, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_invites_list.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_invite_card.dart`.

<a id="s203"></a>
### S203 — Group join request detail

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_detail_screen.dart`

Load by request ID, display current card/permissions; approve/decline/withdraw routes separate review action. Refresh after result; cannot approve using stale request revision.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/group_join_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_join_card.dart`.

<a id="s204"></a>
### S204 — Group join review decision

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_review_screen.dart`

Request_join uses group context/revision; review uses requestId/expectedRevision. Optional note, capability/recovery action suffix and confirmation. Refresh on return; not direct membership change before confirmed response.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/group_join_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`.

<a id="s205"></a>
### S205 — Group join by invitation

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_screen.dart`

Validate canJoin before token-bound join using group revision/requestKey. Native fields empty, only review. After confirmed resource ID replace with group screen; expiry/capacity/revocation invalidates join and uncertain attempts recover same identity.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, expired, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/housing_group_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_group_screen.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_board.dart`.

<a id="s206"></a>
### S206 — Housing group create or edit

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_group_create_screen.dart`

HousingGroupEditor create/edit with required name up to 80 characters, integer capacity at least two, open/invite-only plus city/rental-scope/budget-period/people/date criteria. Existing group revision and active member count constrain edit. Draft recovery/leave guard; no silent creation of academic plan or rental contract.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_editor.dart`.

<a id="s207"></a>
### S207 — Housing group workspace

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_group_screen.dart`

Group board includes overview/members/shortlist/viewings/applications/decisions and chat unread, not all mutated from one approval. Archived state readonly; item/group/academic revisions and permissions gate management, cost proposals, votes and participant consent. Separate group booking preserves individual allocations.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, archived.

Rendered review variants: archived, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/housing_group_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_board.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_chat_button.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_overview_tab.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_members_tab.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_shortlist_tab.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_proposals_tab.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_viewings_tab.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_group_applications_tab.dart`.

<a id="s208"></a>
### S208 — My housing groups

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_groups_screen.dart`

Private paginated groups with pending join/chat unread counts. Optional rental selection permits add-shortlist only in chosen group context; refresh after changed return. Capability gates creation; valid empty state preserved.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_groups_list.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/housing_groups_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_chat_button.dart`.

<a id="s209"></a>
### S209 — Open housing groups

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/open_groups_screen.dart`

Paginated discoverable groups; request join requires separate group-specific review. Existing requests retain approve/decline/withdraw permissions in cards; invitation-only group is labelled, not made joinable by browsing.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_review_screen.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_join_card.dart`.

<a id="s210"></a>
### S210 — Group rental application detail

Source: `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/screens/group_application_detail_screen.dart`

Owner reads group process selection/proposal/consent count and owner note. Action permissions gate accept/decline/request_changes. Confirmed eligible application may start group booking allocation; no automatic joint lease and no approval on behalf of tenants.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/cubits/group_application_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/widgets/owner_group_applications.dart`.

<a id="s211"></a>
### S211 — Owner group application review

Source: `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/screens/group_application_review_screen.dart`

Parameterized accept/decline/request_changes. Required note only for request_changes, optional otherwise. Historical selection, no joint lease disclaimer, application revision/capability/requestKey and uncertain-command recovery retained.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/cubits/group_application_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`.

<a id="s212"></a>
### S212 — Rental summary shares

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/rental_summaries_screen.dart`

Lease/group scoped summary options and grants. Only explicitly selected booking/invoice/receipt projections; recipientName/accommodation and record statuses shown if supplied. Revoke permission and expiry apply; not a broad family account or payment authority.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, expired, revoked.

Rendered review variants: loading, error, stale, restricted, empty, revoked, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/rental_summary_grant_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/rental_summary_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/rental_summary_grant_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`.

<a id="s213"></a>
### S213 — Rental summary sharing consent

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/rental_summary_grant_screen.dart`

Read sharing options first; recipient email/expiry/explicit own consent plus allowed selected booking/invoice/receipt. Selected IDs must belong to loaded options, at least allowed projection. No arbitrary full rental/financial access. Revision and command recovery retained.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed, expired.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, expired, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/rental_summary_grant_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`.

<a id="s214"></a>
### S214 — Student arrangement editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_arrangement_edit_screen.dart`

Shared-living/exam kinds have distinct capabilities/rules, dates and plan revision. Edit captures full arrangement draft; approve/discuss reads current rules/digest and requires own checkbox, not editable rule inputs. Revised arrangements invalidate earlier consent.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: decision, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_arrangement_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`.

<a id="s215"></a>
### S215 — Student living arrangements

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_arrangements_screen.dart`

Plan-scoped paginated shared_living/exam versions with dates/rules/status. Actions approve/discuss/revise only when supplied, refresh on return. accepted/review_required/waiting separate; no claim that personal acceptance binds others.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, empty, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_arrangement_edit_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_arrangement_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`.

<a id="s216"></a>
### S216 — Student check-in issue report

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_check_in_screen.dart`

This check-in screen reports an issue, not an arrival/occupancy confirmation. Required note and StudentLabels issue kind tied to plan+lease with studentTransitions capability, expected plan revision/requestKey and recoverable kind.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_choice_field.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`.

<a id="s217"></a>
### S217 — Student plan consent

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_consent_screen.dart`

review vs publish explicit modes; own requirements/disclosures and shared participants differ. Review uses plan digest; publish uses previewDigest/publication projection and studentDemand capability. Mandatory checkbox and revision. No implicit disclosure of all student data or consent for another member.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: publication, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_publication_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_requirement_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`.

<a id="s218"></a>
### S218 — Student plan history

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_history_screen.dart`

PlanId private paginated historical revisions, label/dates/budget basis/min-max/occupants and own requirements. Historical read-only snapshots never current writable plan; unknown values remain unknown.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_requirement_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`.

<a id="s219"></a>
### S219 — Student housing home

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_home_screen.dart`

Independent student search works without academic plan/group. Student context, campus, city, rental scope, monthly budget and optional dates preserved; group variant adds people and per-person/whole-group basis. Existing continuation/session draft and visit banner retained; valid availability searches still recheck server.

Original visual references: S05, S07.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted.

Rendered review variants: group-search, loading, error, saving, unknown-outcome, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_search_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_home_actions.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_choice_field.dart`.

<a id="s220"></a>
### S220 — Student planning hub

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_hub_screen.dart`

StudentRentalEntry remains usable independently of planning gate. Optional personal/family planning, group-context plans and shared-with-me separated. Plans have blockers/revisions; planning unavailable must not hide independent rental/search. No compulsory family sharing.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, unavailable.

Rendered review variants: unavailable, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_rental_entry.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_hub_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`.

