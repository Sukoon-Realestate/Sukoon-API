# Sprint 9 — S181–S200

This sprint belongs to the authorized three-sprint batch (8–10). Stop after Sprint 10 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-08-10-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s181"></a>
### S181 — Owner payment readiness

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/owner_payment_readiness_screen.dart`

Feature currently disables onboarding. Summary retains identity, beneficiary, policy versions and unknown/failed/pending states. Fresh permission and nonempty policy summary/versions would be needed if enabled; read history/refresh remain possible.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, unavailable, unknown-outcome.

Rendered review variants: loading, error, stale, restricted, unavailable, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/cubits/owner_payment_profile_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/data/models/owner_payment_profile.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/owner_payment_readiness.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/owner_payment_summary.dart`.

<a id="s182"></a>
### S182 — Rental payout detail

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/rental_payout_detail_screen.dart`

Read amount, masked beneficiary, reason, payout status, permissions and guide. Refresh only; no release-payout action. Unknown/failure/pending cannot be displayed as money received.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, processing, paid.

Rendered review variants: loading, error, stale, restricted, processing, paid.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/cubits/rental_payout_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/data/models/rental_payout.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/rental_payout_details.dart`.

<a id="s183"></a>
### S183 — Rental payouts list

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/rental_payout_list_screen.dart`

Paginated workspace/lease scoped historical payouts and legitimate empty state. Display provider status as recorded; history visibility does not enable deferred banking execution.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/rental_payout_list.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/data/models/rental_payout.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/rental_payout_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/rental_payout_card.dart`.

<a id="s184"></a>
### S184 — Advanced property analytics

Source: `sokoun/apps/sokoun_app/lib/features/owner/advanced_analytics/presentation/screens/advanced_analytics_screen.dart`

Owner workspace and subscription feature gate. Only selected property loads metrics; periods 7/30/90 and language respected. MeasuredAt, methodology and per-metric definitions retained; export only if server exportAvailable. Missing metrics valid empty, not zero.

Original visual references: S15, S19.

Required implementation states: loading, error, stale, restricted, subscription-required, no-selection.

Rendered review variants: no-selection, subscription-required, loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/owner/advanced_analytics/presentation/widgets/advanced_analytics_content_view.dart`, `sokoun/apps/sokoun_app/lib/features/owner/advanced_analytics/data/models/advanced_analytics_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/advanced_analytics/presentation/widgets/advanced_analytics_summary.dart`.

<a id="s185"></a>
### S185 — Company review authorities

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/company_review_authorities_screen.dart`

Binding/company scoped paginated eligible members. canSubmit/canView independently editable, active if either true. Save membership revision; pending command freezes toggles and reconciles receipt/same intent. No broad company permission inferred.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_experience.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/review_experiences_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experiences_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/company_review_authority_row.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/experience_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/experience_command_button.dart`.

<a id="s186"></a>
### S186 — Review experience record choice

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/experience_choice_screen.dart`

Private-memory paginated choices(kind,companyId,leaseId), returns typed selected item to caller. No record creation or eligibility grant from picker; empty opportunities valid.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_experience.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/review_experiences_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_opportunities_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/experience_command.dart`.

<a id="s187"></a>
### S187 — Portfolio reputation

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/portfolio_reputation_screen.dart`

Kind/id scoped historical rollup and reputation sections. Preserve distinct experience/unit counts, optional average, limited sample, archived portfolio and management-change association. No double counting sections as separate experiences.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, archived, limited-sample.

Rendered review variants: loading, error, stale, restricted, empty, limited-sample, archived.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_summary_panel.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_sections_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_section.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/property_reviews_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_section_card.dart`.

<a id="s188"></a>
### S188 — Property reviews

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/property_reviews_screen.dart`

Property portfolio association and two independent property_stay/property_visit collections, each own summary/sections. No combining viewing scores into stay average. Legacy/waiting/management changed labels retained.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, limited-sample, waiting.

Rendered review variants: loading, error, stale, restricted, empty, waiting, limited-sample.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/property_portfolio_reviews.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_summary_panel.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_sections_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/property_portfolio_links.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_section.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/property_reviews_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_section_card.dart`.

<a id="s189"></a>
### S189 — Reputation section detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_detail_screen.dart`

Section server actions control reply/report/withdraw and canWithdrawReply. Reports reason codes differ from appeal/eligibility requests; pending receipt freezes body and reconciles. Legacy/gate/content status, privacy and management-change labels preserved. Withdraw does not rewrite original review.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, legacy-read-only, waiting, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, waiting, stale, legacy-read-only, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/cubits/reputation_detail_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_section.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_detail_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_action_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_action_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_section_card.dart`.

<a id="s190"></a>
### S190 — Shared reputation summary

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_grant_summary_screen.dart`

GrantId-scoped summary read, independent authorization/expiry. Aggregates, criteria answered counts, unit counts and archive flags; no recipient access to raw private sections from grant summary.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, expired, limited-sample.

Rendered review variants: loading, error, stale, restricted, limited-sample, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/cubits/reputation_grant_summary_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_summary_panel.dart`.

<a id="s191"></a>
### S191 — Reputation summary grants

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_grants_screen.dart`

Recipient picker supplies real typed ID; explicit purpose/role and consent. Create/revoke bound to grant/request identity, freeze unknown body, reconcile before resend. Revoked grant cannot expose summary; no general public reputation link.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, revoked.

Rendered review variants: loading, error, saving, unknown-outcome, revoked, stale, expired, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_grants_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_grant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_sharing_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_grant_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_action_body.dart`.

<a id="s192"></a>
### S192 — Reputation recipient choice

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_recipient_screen.dart`

Private-memory paginated eligible reputation recipients; return selected typed recipient. Empty recipient set distinct from no existing grants. No freeform arbitrary email recipient or account enumeration.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_grant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/reputation_grants_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_sharing_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_action_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_summary.dart`.

<a id="s193"></a>
### S193 — Review moderation case

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_case_screen.dart`

Read-only case reference, pending vs resolved and optional resolution. Do not add arbitrary replies/financial decisions or imply report accepted. Account session/read state governs access.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, resolved.

Rendered review variants: resolved, loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/cubits/review_case_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/cubits/review_case_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_action_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_case_record.dart`.

<a id="s194"></a>
### S194 — Review moderation cases

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_cases_screen.dart`

Private paginated cases, type/reference/date and status. Pending/closed from server, detail only; no reclassification of rental disputes as moderation cases.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_cases_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_case_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_cases_empty_state.dart`.

<a id="s195"></a>
### S195 — Review experience detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_experience_screen.dart`

Kinds companyBinding/employeeAssignment/ownership differ. Permission-gated confirm/manage authorities/assign/view assignments/actual arrival/departure. Evidence IDs, actual dates/periods and revision required by respective form; request recovery scoped to account/session.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: employee-assignment, loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_experience.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/cubits/review_experience_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experience_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experience_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/experience_command_button.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/experience_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experiences_list.dart`.

<a id="s196"></a>
### S196 — Review experience records

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_experiences_screen.dart`

Three tabs unless company context then binding-only. Embedded forms are state variants: company lease binding, employee assignment and ownership transfer require eligible picks, evidence and dates. Preserve private drafts, active account and original command receipt.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: ownership-form, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experience_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_experience.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experiences_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/experience_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/experience_command_button.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experiences_empty_state.dart`.

<a id="s197"></a>
### S197 — Review opportunity composer

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_opportunity_screen.dart`

Opportunity revision/policy/schema/targets authoritative. Section criteria 1–5 and N/A, audience per section, optional comment and skipped sections. Final review warns immutable; release after mutual/deadline/moderation differs. Company save-for-company separate from submit, conflicts freeze, pending receipt recovery never creates duplicate review.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, revision-changed, waiting.

Rendered review variants: waiting, loading, error, saving, unknown-outcome, stale, expired, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/cubits/review_opportunity_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_opportunity.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_composer.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_reminder_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_submission_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_reminder_control.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_section_editor.dart`.

<a id="s198"></a>
### S198 — Reviews hub

Source: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reviews_hub_screen.dart`

Unified hub covers MyReviewsScreen and RentalReviewsScreen direct wrappers. Context lease/visit controls eligibility; company hides personal grant/own-reputation routes. Tabs opportunities/mine/received have separate private queries. No automatic eligibility from canReview legacy flag.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: lease-context, company-context, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_eligibility_button.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_cases_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_grants_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_experiences_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_opportunities_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_sections_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/enums/review_collection.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/own_reputation_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_action_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_action_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_cases_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_grants_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experience_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_experience.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_experiences_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/review_opportunity.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/review_opportunities_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/data/models/reputation_section.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/property_reviews_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_section_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/widgets/reputation_summary_panel.dart`.

<a id="s199"></a>
### S199 — Housing group action

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_action_screen.dart`

One parameterized action screen: vote/comment/shortlist/visit/apply/costs/transfer/leave and academic context. Active eligible participants, group/item/academic revisions, correct shortlist selection, proposal minor-unit totals, self consent and admin transfer guards. Each person approves own participation; no joint lease promise.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: cost-proposal, visit-request, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/housing_group_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_action_review.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/widgets/group_action_fields.dart`.

<a id="s200"></a>
### S200 — Group invite creation

Source: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invite_create_screen.dart`

No native freeform invite fields. Create scoped to current group revision/capability, recover original request then navigate only with confirmed resource ID to GroupInviteScreen. No membership change merely by creating link.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/cubits/group_invite_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invite_screen.dart`.

