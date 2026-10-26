# Sprint 8 — S161–S180

This sprint belongs to the authorized three-sprint batch (8–10). Stop after Sprint 10 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-08-10-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s161"></a>
### S161 — Rental maintenance list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/screens/maintenance_request_list_screen.dart`

Lease/workspace-scoped paginated maintenance list. Refresh after changed detail/create returns. Appointment, proposed cost and completed work are separate states; empty success is valid.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/widgets/maintenance_request_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/widgets/maintenance_request_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/widgets/maintenance_request_card.dart`.

<a id="s162"></a>
### S162 — Rental dispute detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/screens/rental_dispute_detail_screen.dart`

Reason/resolution, response history and lease-bound evidence. Only reply permission plus fresh detail allows a response; expected revision and original request identity preserved. No automatic adjudication.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, resolved, evidence-missing.

Rendered review variants: loading, error, saving, unknown-outcome, resolved, stale, evidence-missing, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/cubits/rental_dispute_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/data/models/rental_dispute.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/widgets/rental_dispute_details.dart`.

<a id="s163"></a>
### S163 — Rental dispute creation

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/screens/rental_dispute_form_screen.dart`

Subject defaults to lease only when subjectId empty; preserve subjectKind/id and capability. Required reason, evidence IDs and recoverable evidence draft. Submission creates a dispute, not a liability ruling.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, evidence-missing.

Rendered review variants: loading, error, saving, unknown-outcome, stale, evidence-missing, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/widgets/rental_dispute_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/data/models/dispute_body.dart`.

<a id="s164"></a>
### S164 — Rental disputes list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/screens/rental_dispute_list_screen.dart`

Paginated lease/workspace disputes with valid empty data. Detail returns refresh; status/resolution from server. No implied financial hold or settlement from list state.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/widgets/rental_dispute_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/data/models/rental_dispute.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/widgets/rental_dispute_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/widgets/rental_dispute_card.dart`.

<a id="s165"></a>
### S165 — Rental change detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_change_detail_screen.dart`

Kind-specific requested/original/deferred/effective dates and known amount. Amendment/renewal show before/after terms. Sign requires document ID/hash, permission and freshness; accept/reject/request_changes/submit_for_signature/propose_end are separate commands.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: amendment, loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/enums/rental_change_kind.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/cubits/rental_change_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/rental_change_details.dart`.

<a id="s166"></a>
### S166 — Rental change request

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_change_form_screen.dart`

Read current rental center except externalPayment which routes directly to SupportNewTicketScreen with offPlatformPayment lease/invoice context. Extension requires invoice; termination/amendment effective date; renewal uses exclusive current end as next start; terms validate periods/rent/deposit and included/excluded services. Evidence/revision/recovery retained.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: renewal, termination, external-payment, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/enums/rental_change_kind.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/rental_change_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change_body.dart`.

<a id="s167"></a>
### S167 — Rental change signing

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_change_signing_screen.dart`

Read acknowledgment is mandatory; preserve kind, revision, document hash and signature session. Resume original provider session before creating another, sensitive authorization and expiry apply. Returning from hosted signing requires authoritative refresh.

Original visual references: S18, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed, expired, signed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, expired, signed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/enums/rental_change_kind.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/rental_change_signing_form.dart`.

<a id="s168"></a>
### S168 — Rental changes collection

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_changes_screen.dart`

One reusable collection for supplied RentalChangeKind, not separate screen counts. List and creation preserve lease/workspace/kind and refresh on return; do not blend renewal, termination or invoice-extension contexts.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/enums/rental_change_kind.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/rental_changes_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/rental_changes_empty_state.dart`.

<a id="s169"></a>
### S169 — Tenancy transition planning

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/tenancy_planning_screen.dart`

Two tabs for move-out notices/replacements, separate renewal route, history and execution entries; move network tenant-only. Capability gates creation; preserve tenancy selection and future-only transition semantics.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_changes_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/enums/rental_change_kind.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/tenancy_transitions_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/tenancy_transition.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/rental_changes_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/tenancy_transitions_empty_state.dart`.

<a id="s170"></a>
### S170 — Tenancy transition editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/tenancy_transition_edit_screen.dart`

Move-out/replacement and supplied action/previous revision control fields and draft. Replacement requires eligible candidate selection and explicit consent. Preserve requested/effective dates; nomination and candidate consent do not activate replacement or release prior tenant.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: replacement, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/tenancy_transition.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/tenancy_transition_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/replacement_candidate_picker.dart`.

<a id="s171"></a>
### S171 — Tenancy transition detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/tenancy_transition_screen.dart`

Current details distinguish requested, received, effective, outgoing/incoming and nominated candidate. permissions gates acknowledge/withdraw/approve_availability/nominate/approve_candidate/decline/cancel. Each action uses editor and refreshed state; future-only and no-release notices retained.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/data/models/tenancy_transition.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/cubits/tenancy_transition_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/widgets/tenancy_transition_details.dart`.

<a id="s172"></a>
### S172 — Replacement candidate consent

Source: `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/presentation/screens/replacement_consent_screen.dart`

Accept/decline are invitation-revision-bound commands with replacement planning capability, expectedRevision/requestKey and optional note. Identity/expiry/current permission determine availability. Consent is not effective replacement.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, expired, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/data/models/replacement_invitation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/data/replacement_invitations_data.dart`.

<a id="s173"></a>
### S173 — Replacement invitations inbox

Source: `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/presentation/screens/replacement_invitations_screen.dart`

Unread-count scope and paginated invitation list, capability disposal and action permissions. Refresh after response; accept/decline keep invitation revision and recovery flow. Expired invitations cannot be accepted.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, expired.

Rendered review variants: loading, error, stale, restricted, empty, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/presentation/widgets/replacement_invitations_list.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/data/models/replacement_invitation.dart`.

<a id="s174"></a>
### S174 — Final rental settlement

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/final_settlement_screen.dart`

Revision-bound item lines, signed money direction, rent/deposit/refund/total and linked invoices. Per-line disputes preserve item IDs. Fresh permissions gate propose/accept/dispute; notes/history shown. Agreement does not confirm refund or payout.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, disputed.

Rendered review variants: loading, error, stale, restricted, disputed, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/cubits/final_settlement_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/final_settlement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/final_settlement_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_line.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_note.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/settlement_notes.dart`.

<a id="s175"></a>
### S175 — Rental documents

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/rental_documents_screen.dart`

Lease/currentRevision callback plus fresh revision required for statement generation and document access. Link requests require sensitive authorization; preparing/unavailable and invalid date states distinct. No unsafe or arbitrary external URL opened.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, processing, unavailable, revision-changed.

Rendered review variants: loading, error, stale, restricted, empty, processing, unavailable, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/rental_documents_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_document.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/rental_documents_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_statement_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/private_document_link.dart`.

<a id="s176"></a>
### S176 — Rental refund detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/rental_refund_detail_screen.dart`

Read-only refund amount/reason/method/refundable balance/status/permissions; refresh verifies status. Keep receipt allocations, lease/workspace and unknown status. No retry-transfer or direct refund command on this screen.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, processing, paid.

Rendered review variants: loading, error, stale, restricted, processing, paid.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/cubits/rental_refund_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_refund.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/rental_refund_details.dart`.

<a id="s177"></a>
### S177 — Rental refunds list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/rental_refund_list_screen.dart`

Paginated lease/workspace refunds, confirmed statuses and per-record allocations remain authoritative. Unknown amounts stay unknown; history does not imply new payout capability.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/rental_refund_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_refund.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/rental_refund_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/rental_refund_card.dart`.

<a id="s178"></a>
### S178 — Settlement proposal editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/settlement_proposal_screen.dart`

Editable typed settlement lines and recoverable line draft. Line editor validates signed financial meaning by type, amount, description and lease context; remove by line identity. Submit expected settlement revision/requestKey and note, not a refund execution.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/final_settlement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/settlement_proposal_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_line.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_note.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/widgets/settlement_line_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_body.dart`.

<a id="s179"></a>
### S179 — Owner beneficiary setup

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/owner_onboarding_screen.dart`

OwnerPaymentData.onboardingEnabled=false in current source: prototype must not activate onboarding. Retained design explains masked beneficiary and identity/policy summary. If enabled later: versioned policy consent, profile revision, sensitive proof, resume session first, provider expiry and uncertain recovery mandatory.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, unavailable.

Rendered review variants: loading, error, stale, restricted, unavailable.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/data/models/owner_payment_profile.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/owner_onboarding_form.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/owner_payment_summary.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/data/models/owner_onboarding_body.dart`.

<a id="s180"></a>
### S180 — Owner payables

Source: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/owner_payables_screen.dart`

Protected private paginated payables; period/gross/commission/net, settlement and payout states plus blocking reasons. Open payout detail only when payoutId exists. No manual transfer initiation; current bank transfer scope deferred.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/owner_payables_list.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/data/models/owner_payable.dart`, `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/widgets/owner_payables_empty_state.dart`.

