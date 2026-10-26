# Sprint 12 — S241–S260

This sprint belongs to the authorized final batch (11–14). Complete remaining source coverage and stop for design review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Primary screens and their relevant presentation/data dependencies were audited; the complete dependency index below was hash-checked from the sibling `sokoun` checkout. `../batch-11-14-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s241"></a>
### S241 — Save offer to company list

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_save_offer_screen.dart`

Reload company, preserve portfolioOfferId or property/offer identity, then choose authorized company list. Saved-list write permission separate from coordinating a request. Canonical offer availability rechecked at later request/booking step.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_saved_lists_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_saved_list.dart`.

<a id="s242"></a>
### S242 — Company saved-list action

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_saved_action_screen.dart`

Create/rename title required <=120; archive/remove/add do not require title. Draft entity scopes company/list/action/item/offer; expected list revision/requestKey and current permission govern every mutation. Archiving returns and refreshes list.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: archive-list, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_saved_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/company_saved_data.dart`.

<a id="s243"></a>
### S243 — Company saved-list detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_saved_detail_screen.dart`

Read fresh list independently of item pagination. Rename/archive/remove only when canWrite and successful list read. Unavailable items do not expose viewing actions; current company scope/offer identity retained. Refresh read and pages after action.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, empty, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_saved_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_saved_list_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_saved_action_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/company_saved_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_viewing_entry.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`.

<a id="s244"></a>
### S244 — Company staff batch results

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_staff_batch_screen.dart`

Batch ID/company read, per-row created/conflict outcome. Partial success must remain visible and retries only failed rows with original identity. Prepared staff records are not active company membership or confirmed rental allocations.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, partial-error.

Rendered review variants: retry-form, loading, error, stale, restricted, partial-error.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_batch_results.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_batch_form.dart`.

<a id="s245"></a>
### S245 — Company staff CSV import

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_staff_import_screen.dart`

CSV parser/preview feed CompanyStaffBatchForm; headers, row identities, validation and duplicate/conflict handling precede command. Confirmation does not imply account invitations; partial results preserve successful rows. No real staff import in prototype.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, partial-error.

Rendered review variants: loading, error, saving, unknown-outcome, stale, partial-error, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_import.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_import.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_batch_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`.

<a id="s246"></a>
### S246 — Company staff list and detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_staff_screen.dart`

CompanyStaffScreen list + CompanyStaffDetailScreen native route. Employee code/contact/membership link and eligibility; placements and record updates/offboarding require scoped company permission, revisions and refresh. Staff records do not grant coordinator/admin access.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: staff-detail, staff-form, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_batch_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_command_body.dart`.

<a id="s247"></a>
### S247 — Company tenancy lifecycle

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_tenancy_screen.dart`

Fresh company tenancy, revision and quote/package identity. Signature release, occupancy, payments, adjustments, deposits, exit/handover and financial closure remain separate permission-gated actions. Continuations reconcile original request; no editable server fact from aggregate status.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, unknown-outcome.

Rendered review variants: tenancy-action, loading, error, stale, restricted, revision-changed, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_tenancy_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_tenancy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_booking_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contract_preparation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_tenancy_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_continuation_controls.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_package_summary.dart`.

<a id="s248"></a>
### S248 — Company viewing request

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_viewing_request_screen.dart`

Read company and require canCoordinate. CompanyViewingSource with current property/offer/package context enters shared location/people/review wizard; monthly interval, coordinates/source, headcount/cost-center/requirements loaded before confirmation. Source unavailable or changed blocks submission.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed, source-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, source-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_viewing_source.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_request_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_request_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_request_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_request_steps.dart`.

<a id="s249"></a>
### S249 — Company workspace

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_workspace_screen.dart`

Workspace shell restores selected company and tabs, refreshes on resume; authorization/scope key resets child subscriptions. Missing selection shows company list; inactive membership blocks work. Switching company clears scoped context without granting permission. Current work/recovery entry preserved.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, inactive-membership.

Rendered review variants: inactive-membership, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_workspace_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_workspace_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_workspace_tab_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_saved_lists_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_rental_summary_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_saved_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_housing_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_dashboard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_settings.dart`.

<a id="s250"></a>
### S250 — Owner property creation choices

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/owner_creation_screen.dart`

OwnerCreationScreen choices preserve seed and excluded mode. ResidentialAssetCreateScreen handles building/complex forms under owner portfolio capability; geometry, hierarchy and public-property flow differ. No fake publication when creating inventory.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: asset-create, loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/owner_creation_seed.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/enums/property_creation_mode.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/property_creation_choices.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/residential_asset_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_offers_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/residential_asset_facts_editor.dart`.

<a id="s251"></a>
### S251 — Portfolio change proposal

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/portfolio_change_screen.dart`

Three native destinations: create proposal, change review and destination picker. Explicit unit IDs/revisions, destination exclusion, move/split/merge/bulk semantics and inheritance/reset-overrides. Preview before commit; optimistic expected revisions/conflicts never silently replace inventory.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: change-review, destination-picker, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_change_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_change_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_destination_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_unit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_field.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_fields_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_replacement_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_command_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`.

<a id="s252"></a>
### S252 — Portfolio media evidence

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/portfolio_media_screen.dart`

List/create/item/byte-preview preserve asset scope and file identity; upload/scan/ready states differ. Authenticated bytes only, no unsafe public links; evict image bytes on account cleanup/dispose. Retry/resume/remove only with permissions and acknowledged upload identity.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, processing, unsafe.

Rendered review variants: media-item, media-preview, media-create, loading, error, stale, restricted, empty, processing, unsafe.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_media_create_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_media_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_media_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_unit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_command_body.dart`.

<a id="s253"></a>
### S253 — Residential portfolio assets

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/residential_assets_screen.dart`

List kind building/complex, distinct ResidentialAssetScreen detail. Route-aware refresh after child/batch returns only same account generation; fresh asset actions. Subtree facts/capacity and inherited defaults differ from public offers; attach/media/change/listing workflows scoped.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: asset-detail, complex-list, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/residential_assets_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/residential_asset_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_unit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_changes_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/residential_asset_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_attach_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_offer_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/portfolio_fields_editor.dart`.

<a id="s254"></a>
### S254 — Create multiple units batch

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/unit_batch_screen.dart`

UnitBatchScreen + UnitBatchResultScreen. Required template, nonempty units, unique per-unit codes and metadata, count/prefix generation. Partial successes retained; retry only failed units with previous acknowledgement. No duplicate creation/publication on unknown outcome.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, partial-error.

Rendered review variants: unit-batch-result, unit-batch-retry, loading, error, saving, unknown-outcome, stale, partial-error, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/owner_creation_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/enums/property_creation_mode.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/unit_batch_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/unit_batch_results.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_unit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_unit_draft.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/owner_creation_seed.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/property_creation_choices.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/residential_asset_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/unit_draft_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`.

<a id="s255"></a>
### S255 — Housing tender detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/housing_tender_screen.dart`

Fresh tender snapshot/group/source/dates and own requirement, phase-specific actions. Sealed bids only released to authorized viewers/phase, no competitor disclosure. Amendments invalidate dependent snapshots/consent; planning separate from execution.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, closed.

Rendered review variants: loading, error, stale, restricted, revision-changed, closed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/cubits/housing_tender_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/housing_tender_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`.

<a id="s256"></a>
### S256 — Housing tenders collection

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/housing_tenders_screen.dart`

GroupId vs owner collection filters and planning capability are resource-scoped. Owner bid opportunity and organizer create routes differ; pagination/empty/read-only context valid. No arbitrary tender visibility outside current account.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/housing_tenders_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`.

<a id="s257"></a>
### S257 — Tender participant action

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_action_screen.dart`

Action requirements/publish/amend/withdraw. Required dates/rent/deposit and scope/minimum 1..participantCount, multi-property choice, disclosure and independent ack reset on draft restore. Publish/amend bind tender revision; amend makes prior dependent consent obsolete.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: tender-lifecycle, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/cubits/housing_tender_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_requirement_options.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`.

<a id="s258"></a>
### S258 — Tender sealed bid editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_bid_edit_screen.dart`

Selections nonempty, canonical terms and owner inventory; future expiry, min quantity within selection count, pricing ack. Tier rule canonical/all_units/marginal with threshold 2..count and rate <= base, optional combines. Supersedes identity for revision, sealed visibility and same-intent recovery retained.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed, expired.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, expired, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_pricing_input.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_bid_selections.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_pricing_fields.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`.

<a id="s259"></a>
### S259 — Withdraw tender bid

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_bid_withdraw_screen.dart`

Withdraw uses bid expectedRevision/requestKey, allowed phase and recovery identity. It is not package cancellation or reversal of confirmed execution. No arbitrary bid editing after submission through withdrawal.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`.

<a id="s260"></a>
### S260 — Tender bids list and picking

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_bids_screen.dart`

Tender-scoped list; picking mode returns selected eligible bid to allocator, not submit/award. Sealed content and owner own-bid visibility respect phase/permissions. Expired/superseded bids cannot be allocated as fresh.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, sealed.

Rendered review variants: sealed, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_bids_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`.

