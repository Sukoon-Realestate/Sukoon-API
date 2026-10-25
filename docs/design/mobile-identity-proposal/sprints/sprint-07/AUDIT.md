# Sprint 7 — S141–S160

This sprint belongs to the authorized five-sprint batch (3–7). Stop after Sprint 7 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-03-07-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s141"></a>
### S141 — Rental event timeline

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/rental_timeline_screen.dart`

Read-only chronological rental events, pagination and successful empty response. Event labels/times are server data; a historical event does not override current permissions or financial status.

Original visual references: S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_timeline_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_timeline_event.dart`.

<a id="s142"></a>
### S142 — Payment record and reconciliation

Source: `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/payment_record_screen.dart`

Capture confirmation, receipt/doc pending, refund allocations, payout and chargeback states explicit. Refund request only permissions and refundable allocations. Unknown/unconfirmed capture never shown as paid; reconcile original attempt before retry.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted, paid, chargeback, unknown-outcome.

Rendered review variants: loading, error, stale, restricted, paid, chargeback.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/cubits/payment_record_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_attempt.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/payment_record_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/data/models/rental_chargeback.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rental_chargeback_summary.dart`.

<a id="s143"></a>
### S143 — Rent invoice detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/rent_invoice_screen.dart`

Invoice period/type/lease and permissions; tenant payment and extension actions separate, owner view differs. Use invoice-specific attempt/checkout context and current server amount. No mark-paid based on browser return alone.

Original visual references: S19, S10.

Required implementation states: loading, error, stale, restricted, paid, extension-pending.

Rendered review variants: loading, error, stale, restricted, paid, extension-pending.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rent_invoice_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_invoice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rent_invoices_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rent_invoice_details_view.dart`.

<a id="s144"></a>
### S144 — Rent invoices collection

Source: `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/rent_management_screen.dart`

Workspace feature guard, rental-selection/due-date invoice rows and return refresh. Distinguish property-specific title from global list; empty/read error not unpaid amount assumptions.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rent_invoices_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_invoice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rent_invoices_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rent_invoice_card.dart`.

<a id="s145"></a>
### S145 — Rental payment attempts history

Source: `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/rental_payment_history_screen.dart`

Paginated payment-attempt history with references and valid empty state; attempts are not all confirmed captures. Retry/refundable allocations are typed permission-controlled data, not generic list actions.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rental_payment_history_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_attempt.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/widgets/rental_payment_history_empty.dart`.

<a id="s146"></a>
### S146 — Rental checkout session

Source: `sokoun/apps/sokoun_app/lib/features/tenant/rent_management/presentation/screens/rental_checkout_screen.dart`

Source selects RentalMockProviderForm only for mock session, otherwise trusted hosted RentalCheckoutBrowser. Preserve provider/session/attempt and expiry, host/return verification, lifecycle reconciliation. Prototype has no card fields, hosted navigation or money movement.

Original visual references: S19, S03.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, expired.

Rendered review variants: loading, error, saving, unknown-outcome, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/rent_management/presentation/widgets/rental_checkout_browser.dart`.

<a id="s147"></a>
### S147 — Rental security deposit ledger

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_deposits/presentation/screens/rental_deposit_screen.dart`

Agreed/due/collected/applied/returned/disputed/remaining and holder(owner/platform) distinct, unknown money not zero. Linked invoice is only when identified. Return depends on actual settlement/payment records.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_deposits/presentation/cubits/rental_deposit_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_deposits/data/models/rental_deposit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_deposits/presentation/widgets/rental_deposit_details.dart`.

<a id="s148"></a>
### S148 — Condition report acknowledgement/action

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_report_action_screen.dart`

Configured action/objection item and exact content revision, student context and superseding report preserved. Acknowledgement is no financial-liability admission. Never apply objection/ack to a stale or different revision.

Original visual references: S19, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/cubits/condition_report_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/condition_reports_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_condition_report_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_report_version.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_report_acknowledgement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart`.

<a id="s149"></a>
### S149 — Condition report editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_report_edit_screen.dart`

Load current report context; editable spaces/items/inventory/keys/meters/date, evidence reselection. Preserve current revision and report type, not a unilateral signed baseline. Submit/recovery and missing attachments remain explicit.

Original visual references: S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, evidence-missing.

Rendered review variants: loading, error, saving, unknown-outcome, evidence-missing.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/cubits/condition_report_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/condition_report_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_report_version.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_report_acknowledgement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/condition_report_editor_content.dart`.

<a id="s150"></a>
### S150 — Condition report detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_report_screen.dart`

Baseline/move-out without baseline, content revision, acknowledgements and prior versions distinct. Permissions gate edit/submit/addendum/object/docs. Authenticated evidence and malware states preserved; no automatic liability inference.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted, no-baseline, revision-changed.

Rendered review variants: loading, error, stale, restricted, no-baseline, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/cubits/condition_report_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/condition_report_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_report_version.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report_report_acknowledgement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_evidence_list.dart`.

<a id="s151"></a>
### S151 — Condition report collection

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_reports_screen.dart`

Planning capability-gated move-in/out collection, creation only available build. Valid empty and return refresh, baseline/previous report context retained; reports are separate from handover or settlement approvals.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/condition_reports_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/condition_reports_empty_state.dart`.

<a id="s152"></a>
### S152 — Authenticated rental evidence viewer

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_evidence_image_screen.dart`

Authenticated evidence bytes with account cleanup clearing preview; student-specific scoped endpoint when applicable. Use PrivateFilePreview MIME support and unavailable/unsafe/decode errors, no public URL sharing or retained cross-session data.

Original visual references: S08.

Required implementation states: loading, error, stale, restricted, session-ended, unsafe.

Rendered review variants: loading, error, stale, restricted, session-ended, unsafe.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence_link.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/cubits/rental_evidence_image_cubit.dart`.

<a id="s153"></a>
### S153 — Rental handover detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_handover_detail_screen.dart`

Fresh handover version, possession date/keys/condition/evidence and approvals. Permissions separately gate edit/accept/dispute; authenticated evidence and student context preserved. No acceptance inferred from merely opening the document.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted, revision-changed.

Rendered review variants: loading, error, stale, restricted, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/cubits/rental_handover_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_handover.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_handover_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_evidence_list.dart`.

<a id="s154"></a>
### S154 — Handover creation/edit form

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_handover_form_screen.dart`

Create/edit restored typed intent, kind/date/condition/keys and authenticated evidence. Missing reselected files, upload/scanning/unsafe and request-key uncertain operation recovery block inappropriate retries. Preserve student limits/context and unsaved changes.

Original visual references: S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, scanning, unsafe, evidence-missing.

Rendered review variants: loading, error, saving, unknown-outcome, scanning, unsafe, evidence-missing.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_handover.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_handover_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_evidence_picker.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_body.dart`.

<a id="s155"></a>
### S155 — Rental handovers list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_handover_list_screen.dart`

Paginated move-in/out handover list, refresh after changed detail/form returns. No automatic possession/financial closure from a list label; role and lease/student identity maintained.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_handover_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_handover.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_handover_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/widgets/rental_handover_card.dart`.

<a id="s156"></a>
### S156 — Asset item passport

Source: `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/screens/asset_item_screen.dart`

Asset identity/current room/location/make/serial/predecessor-successor/source revision and observation timeline. Allowed actions decide observe/move/replace/update/retire; observations are not liability, warranty or automatic financial adjustments.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/cubits/asset_item_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/data/models/asset_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_action_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_timeline.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_observations.dart`.

<a id="s157"></a>
### S157 — Property asset passport

Source: `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/screens/asset_passport_screen.dart`

Room/property-space asset list with explicit canRegister, source selection and empty observations/source states. Privacy/source revision and manual observation disclaimers preserved; registration is not proof of ownership or warranty.

Original visual references: S16, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/data/models/asset_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_passport_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_action_form.dart`.

<a id="s158"></a>
### S158 — Asset evidence review workspace

Source: `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/screens/asset_review_workspace_screen.dart`

Jobs/findings/patterns/warranty projections and sourceChanged checks, human comparability attestation and allowed actions. Cancel/rerun/close/claim gated; hypotheses are not authoritative liability or warranty decisions.

Original visual references: S19, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, source-changed, processing.

Rendered review variants: loading, error, saving, unknown-outcome, source-changed, processing.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/cubits/asset_review_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/data/models/asset_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_review_workspace.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/data/models/asset_item.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_review_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/widgets/asset_observations.dart`.

<a id="s159"></a>
### S159 — Maintenance request detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/screens/maintenance_request_detail_screen.dart`

Permission-gated acknowledge/appointment start-end/access/cost payer/cost approval/work/resolved/reopen/missed appointment. Fresh revision and expected proposed cost for approval/rejection; emergency/access disclaimers and Cairo times kept. No automatic charge from a proposal.

Original visual references: S19, S14.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/cubits/maintenance_request_details_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_request.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/widgets/maintenance_request_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_event.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_action_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/widgets/maintenance_cost_summary.dart`.

<a id="s160"></a>
### S160 — Maintenance request creation

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/screens/maintenance_request_form_screen.dart`

Lease-scoped maintenance form with category, priority and description. Use current typed form, permission/recovery and emergency information; submitting request does not book an appointment or authorize costs.

Original visual references: S17, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/widgets/maintenance_request_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_body.dart`.

