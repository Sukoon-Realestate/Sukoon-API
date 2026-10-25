# Sprint 6 — S121–S140

This sprint belongs to the authorized five-sprint batch (3–7). Stop after Sprint 7 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-03-07-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s121"></a>
### S121 — Group booking detail and own consent

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/group_booking_screen.dart`

Read fresh group booking, own allocation consent, reject/withdraw allowed per permissions. Participants have independent terms/invitation/lease references; cannot consent for others. Refresh on resume and preserve response deadline.

Original visual references: S19, S18.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/group_booking_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/group_booking.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/group_booking_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/group_booking_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/booking_participant.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`.

<a id="s122"></a>
### S122 — Group bookings list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/group_bookings_screen.dart`

Paginated group bookings and successful empty state. Refresh after detail returns, scope to workspace and group identity; not a general list of confirmed tenancies.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/group_bookings_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/group_booking.dart`.

<a id="s123"></a>
### S123 — Property decision facts and costs

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/property_decision_screen.dart`

Known/unknown, estimated/owner-reported/verified facts, property/identity checks and refundable deposit separate from recurring/one-time costs. Availability must be confirmed with current server context; external booking explicitly distinct, no hidden guarantee.

Original visual references: S08, S19.

Required implementation states: loading, error, stale, restricted, availability-unknown.

Rendered review variants: loading, error, stale, restricted, availability-unknown.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/rental_stay_preferences.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/property_decision_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/property_decision.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/property_decision_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/decision_fact.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/decision_cost_line.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/verification_claim.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/owner_decision_actions.dart`.

<a id="s124"></a>
### S124 — Rental support case

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/rental_case_screen.dart`

Case state/assignee/team/due time/replies and optional sourcing/company/habitability/chargeback contexts. Permission-gated review/reply/withdraw only; operational resolution is not automatic financial settlement or occupancy change.

Original visual references: S14, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/rental_case_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/rental_case.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/rental_case_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/company_sourcing_status.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/company_service_status.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/habitability_status.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/case_reply.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/case_remedy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/rental_case_status.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/habitability_status_card.dart`.

<a id="s125"></a>
### S125 — Rental cases list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/rental_cases_screen.dart`

Paginated account/workspace case list; refresh on returned changes and preserve current assignment/status. Empty is a valid successful collection, not a failed read.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/rental_cases_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/rental_case.dart`.

<a id="s126"></a>
### S126 — Rental deal workspace

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/rental_deal_screen.dart`

Deal waiting-for actor, requested information/response, response deadline, agreed terms and hold are separate. Only allowed actor can reserve/respond/create lease; link lease/center by authoritative ID. Hold is not final financial or occupancy closure.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/rental_deal_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/rental_deal.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/rental_deal_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/reservation_hold.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/deal_resource.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/rental_case.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`.

<a id="s127"></a>
### S127 — Reservation hold detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/reservation_screen.dart`

Countdown anchored to server time/expiry; needsReconciliation and payment uncertainty distinguish deadline from release. Extend/release only permissions, preserve original revision/operation. No timer-only assumption of successful payment or lease.

Original visual references: S11, S19.

Required implementation states: loading, error, stale, restricted, expired, unknown-outcome.

Rendered review variants: loading, error, stale, restricted, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/cubits/reservation_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/reservation_hold.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/reservation_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/lifecycle_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/reservation_countdown.dart`.

<a id="s128"></a>
### S128 — Reservation holds list

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/reservations_screen.dart`

Paginated reservation holds and explanation; refresh on detail changes. Listed holds are not confirmed bookings or signed rental agreements.

Original visual references: S12.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/widgets/reservations_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/data/models/reservation_hold.dart`.

<a id="s129"></a>
### S129 — Lease setup entry

Source: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/lease_draft_screen.dart`

Owner workspace digital-lease guard. When agreements readiness supported, choose eligible tenancy invitation; legacy fallback LeaseDraftContent may be unavailable. Do not bypass invitation gating by selecting arbitrary tenant/property.

Original visual references: S16, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/widgets/lease_draft_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/widgets/lease_draft_form.dart`.

<a id="s130"></a>
### S130 — Eligible lease tenant picker

Source: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/lease_tenant_picker_screen.dart`

LeaseTenantPicker shows eligible tenant context; empty directs invitations from requests. Selecting a tenant does not create a contractual relationship or override eligibility.

Original visual references: S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/widgets/lease_tenant_picker_list.dart`.

<a id="s131"></a>
### S131 — Create rental agreement draft

Source: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/rental_agreement_draft_screen.dart`

Fresh supported configuration/template and eligible invitation; requested stay may lock/derive dates. Template-driven answers and commission explanation; cannot create if policy unsupported/stale. Draft creation does not sign or activate tenancy.

Original visual references: S17, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, policy-unsupported.

Rendered review variants: loading, error, saving, unknown-outcome, policy-unsupported.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/widgets/rental_agreement_draft_form.dart`.

<a id="s132"></a>
### S132 — Edit rental agreement

Source: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/rental_agreement_edit_screen.dart`

Load agreement by leaseId then configuration fresh state. Preserve source revision, template answers and edit permission; policy/terms changes require rereview. Do not overwrite signed or stale agreement silently.

Original visual references: S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, conflict.

Rendered review variants: loading, error, saving, unknown-outcome, conflict.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/widgets/rental_agreement_edit_configuration.dart`, `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/widgets/rental_agreement_draft_form.dart`.

<a id="s133"></a>
### S133 — Digital lease detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart`

Workspace guard, current lease/capabilities and revision. Signed document access and signing capability checked separately; owner cancellation requires confirmation. Hosted destination allowlisting and availability remain authoritative; no fabricated signed PDF.

Original visual references: S19.

Required implementation states: loading, error, stale, restricted, signed, signing-unavailable.

Rendered review variants: loading, error, stale, restricted, signed, signing-unavailable.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/digital_lease_details_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/digital_leases_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/digital_lease_details_view.dart`.

<a id="s134"></a>
### S134 — Digital lease collection

Source: `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/digital_leases_screen.dart`

Workspace-specific leases, optional property filter and owner-only create. Preserve rentalSelection and known dates; refresh on changes and genuine empty/unsupported feature states.

Original visual references: S18, S20.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/digital_leases_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/digital_leases_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/digital_lease_card.dart`.

<a id="s135"></a>
### S135 — Agreement read and approve

Source: `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/rental_agreement_review_screen.dart`

Read/refresh agreement, content-revision ack resets on revision change. Permissions gate approve/request-changes/cancel/submit-signature/documents; legacy readonly stays nonmutating. Financial commission/payment phases not treated as signing.

Original visual references: S19, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, revision-changed, legacy-read-only.

Rendered review variants: loading, error, saving, unknown-outcome, revision-changed, legacy-read-only.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/cubits/rental_agreement_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/rental_agreement_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease_encoding.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease_copy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_terms.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/rental_agreement_review_content.dart`.

<a id="s136"></a>
### S136 — Rental signing session

Source: `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/rental_signing_screen.dart`

Signing session create/resume after explicit contract-read acknowledgement bound to revision. Use trusted provider/session identity and expiry, refresh lease afterward. No freehand local canvas or mocked completion treated as a legal signature.

Original visual references: S03, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, expired, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, expired, revision-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/widgets/rental_signing_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease_encoding.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease_copy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_terms.dart`.

<a id="s137"></a>
### S137 — Personal housing hub

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/my_housing_screen.dart`

Current/history housing collection includes rentalSelection and individual workflow; visits/invitations/my-rentals remain separate destinations. Do not assume a future/pending record is current occupancy.

Original visual references: S05, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_housing_requests.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_rentals_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/my_rentals_filter.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_rentals_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_rental_card.dart`.

<a id="s138"></a>
### S138 — My rental periods

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/my_rentals_screen.dart`

Role/workspace scoped rentals with search and all/current/upcoming/ended/pending settlement buckets. Rental period/selection identity retained; ending occupancy does not imply financial closure.

Original visual references: S12, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_rentals_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/my_rentals_filter.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_rentals_filters.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/my_rentals_list.dart`.

<a id="s139"></a>
### S139 — Rental billing schedule

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/rental_billing_schedule_screen.dart`

Read-only paginated billing schedule with valid empty state. Planned obligations differ from issued invoices, captured payments and receipts; no pay action from schedule alone.

Original visual references: S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_billing_schedule_list.dart`.

<a id="s140"></a>
### S140 — Rental management center

Source: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/rental_center_screen.dart`

Fresh role-aware next action, actor/deadline, stage, closure items, balance and capability menu. Legacy readonly/cached view disables mutations. Occupancy, possession, agreement, processing, invoices/payment and financial closure are separate dimensions.

Original visual references: S05, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/cubits/rental_center_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_center.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_center_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_journey_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_next_action.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_timeline_event.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_center_header.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_journey_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_next_step_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_billing_schedule.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_center_operations.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_chat_entry.dart`, `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/widgets/rental_support_entry.dart`.

