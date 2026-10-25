# Sprint 5 — S101–S120

This sprint belongs to the authorized five-sprint batch (3–7). Stop after Sprint 7 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-03-07-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s101"></a>
### S101 — Housing request detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/screens/housing_request_screen.dart`

Owner vs renter actions differ: offer/edit/pause/resume/fulfill/withdraw only permissions. Academic dates and request criteria preserved; owner offer requires capability and fresh eligible inventory. No conversion from fulfillment status to signed contract.

Original visual references: S08, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/cubits/housing_request_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/models/housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/widgets/housing_request_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/models/housing_criteria.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/widgets/housing_criteria_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/widgets/housing_offers_list.dart`.

<a id="s102"></a>
### S102 — Housing demand and personal requests

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/screens/housing_requests_screen.dart`

Owner demand vs tenant own requests, paginated collections/build capability, live visibility/lifecycle refresh and student city/demand filters. Legitimate empty list stays successful; do not leak personal requests into public demand.

Original visual references: S06, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/widgets/housing_requests_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/models/housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/widgets/housing_requests_empty_state.dart`.

<a id="s103"></a>
### S103 — Housing request lifecycle action

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_requests/presentation/screens/housing_request_action_screen.dart`

Configured tenant request lifecycle action, capability and subject identity. Preserve action-specific validation, draft, revision and uncertain command recovery. Pause/withdraw/fulfill are not interchangeable and require authoritative success.

Original visual references: S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`.

<a id="s104"></a>
### S104 — Housing request editor

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_requests/presentation/screens/housing_request_edit_screen.dart`

City/criteria/budget min-max, occupants, period/dates and note; use typed money, positive counts, valid date order and rental scope/options. Preserve privacy and draft. Publishing requires valid current configuration and successful submission.

Original visual references: S07, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_requests/presentation/widgets/housing_request_editor.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_requests/presentation/widgets/housing_criteria_editor.dart`.

<a id="s105"></a>
### S105 — Owner housing offer composer

Source: `sokoun/apps/sokoun_app/lib/features/owner/housing_demand/presentation/screens/housing_offer_compose_screen.dart`

Choose own eligible property then fresh supported inventory/offer snapshot. Compare current selection and confirm changed terms before submit. No lease creation; preserve matching criteria/academic context and capability gating.

Original visual references: S16, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, inventory-changed.

Rendered review variants: loading, error, saving, unknown-outcome, inventory-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/housing_demand/presentation/widgets/housing_offer_editor.dart`, `sokoun/apps/sokoun_app/lib/features/owner/housing_demand/presentation/widgets/housing_offer_inventory_picker.dart`.

<a id="s106"></a>
### S106 — Rental interest detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/screens/rental_interest_detail_screen.dart`

Permissions gate review/provide/request information/reject/withdraw, owner create terms and invitation. Link frozen shared application only by returned ID. Academic desired end and nonacademic months differ; preserve exact offer snapshot.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/cubits/rental_interest_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/data/models/rental_interest.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/widgets/rental_interest_details.dart`.

<a id="s107"></a>
### S107 — Rental interests inbox

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/screens/rental_interest_list_screen.dart`

Paginated interests role-scoped. Show desired start, waiting-for actor and response deadline when supplied; exact rental selection carried into detail. Empty is successful, later-page errors retain loaded rows.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/widgets/rental_interest_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/data/models/rental_interest.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/widgets/rental_interest_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/widgets/rental_interest_card.dart`.

<a id="s108"></a>
### S108 — Terms proposal review

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/screens/terms_proposal_detail_screen.dart`

Versioned terms, included/excluded services and proposal answer. Owner edit vs tenant approve/reject/request changes according to permissions; response uses revision and fresh resource. Agreement is a later distinct flow.

Original visual references: S19, S20.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/cubits/terms_proposal_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/data/models/terms_proposal.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/widgets/terms_proposal_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/data/models/terms_answer_body.dart`.

<a id="s109"></a>
### S109 — Tenant rental interest form

Source: `sokoun/apps/sokoun_app/lib/features/tenant/rental_interests/presentation/screens/rental_interest_form_screen.dart`

Property/offer and search stay preferences determine fields; academic offering uses requested dates. Attach/revoke shared frozen application intentionally. Validate before create; preserve note and submission key, no confirmed booking implied.

Original visual references: S10, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/rental_interests/presentation/widgets/rental_interest_form.dart`.

<a id="s110"></a>
### S110 — Edit existing terms proposal

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/screens/terms_proposal_edit_screen.dart`

Edit route reloads current interest by proposal.interestId and supplies previous proposal to configuration form. Preserve template/answers, freshness, previous revision and conflict recovery; this is not a new independent proposal.

Original visual references: S17, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, conflict.

Rendered review variants: loading, error, saving, unknown-outcome, conflict.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/widgets/terms_proposal_configuration_form.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/widgets/terms_proposal_form.dart`.

<a id="s111"></a>
### S111 — New terms proposal

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/screens/terms_proposal_form_screen.dart`

Configuration form driven by supplied RentalInterest and optional previous terms. Choose supported template and valid answers; create/edit semantics and current revision retained. Example fields are drawn from shared rental inputs, not a legal template recommendation.

Original visual references: S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/widgets/terms_proposal_configuration_form.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/widgets/terms_proposal_form.dart`.

<a id="s112"></a>
### S112 — Tenancy invitation detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/screens/tenancy_invitation_detail_screen.dart`

Fresh invitation/status/expiry and role canRespond gate accept/reject confirmations; owner revoke/create agreement only when eligible. Stale view refreshes before action. Accepted invitation is not signed lease; disabled feature and unknown status fail closed.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted, expired, accepted.

Rendered review variants: loading, error, stale, restricted, expired, accepted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/cubits/tenancy_invitation_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/cubits/tenancy_invitation_response_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/data/tenancy_invitation_capabilities.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/cubits/tenancy_invitation_command_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitations_unavailable.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/data/models/tenancy_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/data/models/tenancy_invitation_encoding.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/data/models/tenancy_invitation_copy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_response_actions.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_lease_entry.dart`.

<a id="s113"></a>
### S113 — Tenancy invitations list

Source: `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/screens/tenancy_invitations_screen.dart`

Workspace-scoped invitation collection with feature availability and valid empty state. Refresh on detail return, preserve offer/property filtering; do not expose another role/company invitation.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitations_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/data/models/tenancy_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitations_unavailable.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitations_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/widgets/tenancy_invitation_card.dart`.

<a id="s114"></a>
### S114 — Invite from rental interest

Source: `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/screens/rental_interest_invitation_screen.dart`

Invite from identified RentalInterest, preserve exact rentalSelection and tenant/interest identity. Create request does not bypass invitation eligibility or create a lease; returned authoritative invitation is required.

Original visual references: S19, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/widgets/rental_interest_invitation_form.dart`.

<a id="s115"></a>
### S115 — Owner tenancy invite

Source: `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/screens/tenancy_invite_screen.dart`

Invitation capability, current inventory/accommodation and selected tenant identity; block self-invites and unsupported/changed accommodation. Session/revision/subject consistency and uncertain operation recovery retained.

Original visual references: S19, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, inventory-changed.

Rendered review variants: loading, error, saving, unknown-outcome, inventory-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/cubits/tenancy_invitation_create_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/widgets/tenancy_invite_form.dart`, `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/widgets/tenancy_invite_form_content.dart`.

<a id="s116"></a>
### S116 — Private application profile

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_profile_screen.dart`

Read/refresh profile revision, edit via configured form and freeze version before sharing. Property-scoped review share only with identity/revision. Frozen snapshot explanation and private default retained; no automatic disclosure.

Original visual references: S19, S20.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/application_profile_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/application_profile_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`.

<a id="s117"></a>
### S117 — Application share detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_share_detail_screen.dart`

Active frozen snapshot only with returned permissions; expiry/recipient/purpose visible. Revocation gated by permission and fresh response, does not retroactively erase prior disclosure. Inactive/unavailable share hides protected content.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/application_share_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_share.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/application_share_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`.

<a id="s118"></a>
### S118 — Application disclosure review

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_share_screen.dart`

Read frozen version then explicit recipient/purpose/expiry review and share request. No implicit sharing from editing profile; command key and disclosure permissions preserved. No promise that revocation deletes already viewed data.

Original visual references: S19, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/application_share_preview_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_share.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/application_share_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_version.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`.

<a id="s119"></a>
### S119 — Application sharing history

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_shares_screen.dart`

Paginated shares, explicit empty state, refresh after details; retain share identity/status and do not render private snapshot content in every list row.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/application_shares_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/application_share.dart`.

<a id="s120"></a>
### S120 — Group booking allocation setup

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/group_booking_create_screen.dart`

Require supported template/allocation and deadline; preserve each participant allocation and independent-consent semantics. Group booking creation does not create one joint contract or consent for absent members.

Original visual references: S17, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/group_booking_configuration.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/group_booking_form.dart`.

