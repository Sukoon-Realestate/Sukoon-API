# Sprint 11 — S221–S240

This sprint belongs to the authorized final batch (11–14). Complete remaining source coverage and stop for design review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Primary screens and their relevant presentation/data dependencies were audited; the complete dependency index below was hash-checked from the sibling `sokoun` checkout. `../batch-11-14-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s221"></a>
### S221 — Student offer policies

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_offer_policies_screen.dart`

Selection property/offer IDs and revisions must match policy; show only selected offer. Owner can add/edit, student read-only; historical policy labelled changed. Expiry/eligibility/periods and request flags independent. Owner editor is a rendered variant, not student authority.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, expired, revision-changed.

Rendered review variants: owner-editor, loading, error, stale, restricted, empty, expired, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_policy_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_choice_field.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`.

<a id="s222"></a>
### S222 — Student academic plan editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_plan_edit_screen.dart`

Create/edit personal or group plan; reload missing group context. Label <=160, valid civil interval, monthly budget basis, allowed active participants and own requirements; preserving draft does not preserve prior consent. Group creation never auto-consents for members.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_plan_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_choice_field.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/study_requirements_editor.dart`.

<a id="s223"></a>
### S223 — Student plan lifecycle

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_plan_lifecycle_screen.dart`

complete and withdraw differ; completion body uses revision, withdrawal adds digest and own consent. Fresh capability/requestKey/recovery identity remain mandatory; completing planning is not rental termination or financial closure.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted.

Rendered review variants: withdraw, loading, error, saving, unknown-outcome, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/student_housing_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_history.dart`.

<a id="s224"></a>
### S224 — Student academic plan detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_plan_screen.dart`

Fresh plan read on resume. Role/actions gate edit/requirements/review/publish/arrangements/linked rental/next-year/completion; roster reviews and budget/campus conflicts remain explicit. Planning completion separate from rental duties.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, conflict.

Rendered review variants: loading, error, stale, restricted, revision-changed, conflict.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_plan_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_plan_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`.

<a id="s225"></a>
### S225 — Student study profile

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_profile_screen.dart`

Account-scoped profile revision, campus/institution/stage/enrollment and study dates. Save profile before evidence; changes can affect verification. Private drafts reset on account or profile identity change; backend verification is not inferred from user-entered study status.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_profile_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_choice_field.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`.

<a id="s226"></a>
### S226 — Student publication preview

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_publication_screen.dart`

Dedicated fresh preview=true read then embedded StudentConsentScreen publish mode. previewDigest and plan revision bind explicit checkbox to displayed publication, not arbitrary private participant data. Expired/stale preview cannot publish.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/cubits/student_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_consent_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_profile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_arrangement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_offer_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_publication_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_requirement_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`.

<a id="s227"></a>
### S227 — Student participant requirements

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_requirements_screen.dart`

Own participant requirements and selectable campus IDs, per-person monthly budget, optional study/internet/commute/internship/summer/accessibility; selected campus/affordability/study disclosures independent. Submission uses participant/plan revisions; no consent on behalf of others.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_participant_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_next_step.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/study_requirements.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_publication.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/academic_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/study_requirements_editor.dart`.

<a id="s228"></a>
### S228 — Student context search

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_search_screen.dart`

Distinct search route supports groupId/name and supplied initial filters using shared StudentSearchForm. Independent mode omits group-only people/basis. Campus and monthly/date filters, draft flush/session generation and route recovery must survive; results recheck availability.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted.

Rendered review variants: independent-search, loading, error, saving, unknown-outcome, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_search_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_search_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/data/models/student_campus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/widgets/student_choice_field.dart`.

<a id="s229"></a>
### S229 — Student study evidence

Source: `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_verification_screen.dart`

Student evidence selection scoped to AccountSession.userId, studentVerification availability and student evidence picker; privacy/pending notices remain. Not a completed enrollment badge or generic lease evidence context.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, processing, unsafe.

Rendered review variants: loading, error, stale, restricted, processing, unsafe.

Dependencies: .

<a id="s230"></a>
### S230 — Account contexts

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/account_contexts_screen.dart`

Read allowed user/student/company contexts only, with current membership state. Selection follows workspace navigation, no role grant from UI label. Inactive/revoked/expired contexts and fresh authorization revision handled.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/account_contexts_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`.

<a id="s231"></a>
### S231 — Company access activation

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_activation_screen.dart`

Activation input and CompanyActivationReviewScreen are distinct native routes, represented by input + review variant. Preview token before accepted/declined choice. Wrong account may require work-contact proof; no broad membership creation from pasted token. Secrets route-memory only, never persisted in real implementation.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, wrong-account.

Rendered review variants: activation-review, wrong-account, loading, error, saving, unknown-outcome, stale, expired, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_activation_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contact_proof_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`.

<a id="s232"></a>
### S232 — Company work-contact proof

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_contact_proof_screen.dart`

Proof resource tied to activation/company and intended account; delivery status separate from proof verification. Code cleared after confirmed verification. Request another code uses reviewed consent, refresh/check prior delivery, expiry and wrong-account protection. Verified proof returns to activation review.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, delivery-unknown, verified.

Rendered review variants: verified, loading, error, saving, unknown-outcome, stale, expired, delivery-unknown, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contact_proof_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof_body.dart`.

<a id="s233"></a>
### S233 — Company contract preparation

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_contract_screen.dart`

CompanyContractScreen detail + CompanyContractFormScreen context-loaded booking preparation. Preserve package quote/booking revision, signer authorization and document identity. Actions reject/request_changes/release/cancel gated; contract preparation and live tenancy lifecycle differ.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: contract-form, loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_contract_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contract_preparation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contract_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_booking_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_package_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_command_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contract_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_mandate.dart`.

<a id="s234"></a>
### S234 — Company housing cost report

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_costs_screen.dart`

Applied company report filters stay separate from editor draft. Refresh before CSV/JSON export, verify freshness/filter/account generation then share; stale/cached report cannot export authoritatively. Money unknown vs zero, invoice and tenancy IDs retained.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, partial-error.

Rendered review variants: filters, loading, error, stale, restricted, revision-changed, partial-error.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_rental_value_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_report_filter.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/company_report_export.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_cost_filters.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_cost_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_tenancy_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_import.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_offer_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_tenancy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_details.dart`.

<a id="s235"></a>
### S235 — Create company account

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_create_screen.dart`

CompanyCreateScreen and CompanyJoinScreen covered separately as primary/join variant. Name/contact email validation; registration optional. Joining uses invitation token >=32 chars and current account, preserves recovery intent; membership assigned by server, never inferred from company creation.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted.

Rendered review variants: join-company, loading, error, saving, unknown-outcome, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_create_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_create_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_accept_body.dart`.

<a id="s236"></a>
### S236 — Company accounts hub

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_hub_screen.dart`

CompanyHubScreen list and CompanyScreen account overview plus openWork/openMandates modes. Fresh company read, membership roles and permission-scoped work/mandates. Returned child updates refresh company; personal/company budgets and identities stay separate.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: company-overview, company-work, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_mandate_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_work_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_mandate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_mandate_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contract_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_work_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_approval_reassignment_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_settings.dart`.

<a id="s237"></a>
### S237 — Company invitation detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_invitation_screen.dart`

Read invitation ID scoped to company. Form/details represent role, invite token, send/revoke and delivery status separately; no real token exposure, delivery retry or membership upgrade. Version/expiry/expected identity checks retained.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, expired, delivery-unknown.

Rendered review variants: loading, error, stale, restricted, expired, delivery-unknown.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_invitation_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`.

<a id="s238"></a>
### S238 — Company members and authority

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_members_screen.dart`

Membership list vs staff/occupants distinct. Company roles, scoped permissions, invite/offboard/role changes use fresh membership authority; actions unavailable on inactive membership and may need reassignment. Do not confuse employee occupancy with company administrator.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, empty, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_members_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_staff_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member_body.dart`.

<a id="s239"></a>
### S239 — Company rental summary dashboard

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_rental_summary_screen.dart`

Same summary projection supports dashboard and housing=true occupancy list; authenticated company scope, blockers, unknown financial values and current tenancy/review links. No aggregate status grants contract/payment authority.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: housing-overview, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_rental_value_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_rental_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_housing_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_dashboard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_report_filter.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_import.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_work_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_assistance.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_tenancy_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_contract_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_work_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_offer_facts.dart`.

<a id="s240"></a>
### S240 — Company housing requests and detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_requests_screen.dart`

CompanyRequestEntryScreen reloads company before deep-link detail; CompanyRequestsScreen list and CompanyRequestScreen detail are rendered variants. Wizard location/people/review validates monthly interval, capacity, budgets, cost center, purpose and loaded requirements. Approval route/canCoordinate fresh; repeat/edit/withdraw/source quote changes separate.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: request-list, request-form, loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/cubits/company_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_account.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_requests_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_housing_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_request_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_staff_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_activation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_contact_proof.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/account_contexts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/residential_asset.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_batch.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/portfolio_media.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_member.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_budget.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_viewing_entry.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_request_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_viewing_source.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_booking_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_assistance.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_request_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/data/models/company_request_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_offer_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_sourcing_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_offer_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/widgets/company_package_summary.dart`.

