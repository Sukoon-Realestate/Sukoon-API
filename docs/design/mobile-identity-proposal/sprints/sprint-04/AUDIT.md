# Sprint 4 — S81–S100

This sprint belongs to the authorized five-sprint batch (3–7). Stop after Sprint 7 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-03-07-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s81"></a>
### S81 — Banner advertisement detail

Source: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/banner_ad_detail_screen.dart`

Owner-only banner detail, plan duration/total/start/end/status and image failure. Pending payment opens purchase invoice; activation receipt distinguished from mock explanation, no automatic renewal.

Original visual references: S08, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_owner_guard.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/cubits/banner_ad_detail_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_ad_summary.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/owner_banner_artwork.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_plan_summary.dart`.

<a id="s82"></a>
### S82 — Banner property choice

Source: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/banner_property_picker_screen.dart`

Banner-specific owner access and eligible property picker. Selection returns property context, not an ad purchase or proof of publication.

Original visual references: S16.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_owner_guard.dart`.

<a id="s83"></a>
### S83 — Banner ad composer

Source: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/create_banner_ad_screen.dart`

Owner guard, image/title/description/plan with current revision, restore/discard draft and leave guard. Review confirmation before submit. Plan-changed/unavailable reloads catalog; locked/uncertain intent recovers original command rather than issuing duplicate ads.

Original visual references: S17, S08.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, plan-changed.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_owner_guard.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/create_banner_ad_screen_banner_ad_composer.dart`.

<a id="s84"></a>
### S84 — Owner banner advertisement list

Source: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/owner_banner_ads_screen.dart`

Paginated owner advertisements and available plans; refresh after create/detail return and recheck owner access. Pending, active, expired and unknown statuses remain distinct.

Original visual references: S16, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_owner_guard.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/owner_banner_ads_list.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/create_banner_ad_screen.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_ads_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/owner_banner_artwork.dart`, `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/widgets/banner_ad_summary.dart`.

<a id="s85"></a>
### S85 — Service property picker

Source: `sokoun/apps/sokoun_app/lib/features/owner/premium/presentation/screens/premium_property_picker_screen.dart`

Shared premium property picker supports optional selection, owner eligibility and empty/matching inventory cases. Choosing a property does not purchase a feature or bypass an entitlement gate.

Original visual references: S16.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/premium/presentation/widgets/premium_property_picker_list.dart`.

<a id="s86"></a>
### S86 — Purchase and billing invoices

Source: `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/my_invoices_screen.dart`

Workspace/type/date filtered invoices; owner/tenant available categories differ. Show totals/paid/balance/due and correct purchase route. Rent billing and own purchases are not interchangeable; mock/sandbox and unknown status visibly labelled.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/billing_invoice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/purchase_invoice_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/billing_read_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_empty_states.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_invoice_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/purchase_route.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/hosted_payment_browser.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/purchase_invoice_footer.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/payment_status_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/payment_failure_notice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/invoice_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/subscription_overview.dart`.

<a id="s87"></a>
### S87 — Purchase invoice and payment review

Source: `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/purchase_invoice_screen.dart`

Fresh invoice/quote, balance and purchase route gate payment/cancel. Poll/reconcile pending attempt on resume, preserve operation identity; never pay again after an uncertain transmitted response. Paid/fulfillment-pending/fulfilled differ; sandbox-only routes labelled.

Original visual references: S19, S10.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, quote-changed, paid, fulfillment-pending.

Rendered review variants: loading, error, saving, unknown-outcome, quote-changed, paid, fulfillment-pending.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/cubits/billing_read_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/cubits/purchase_payment_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/billing_invoice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/hosted_payment_browser.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/cubits/purchase_payment_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/purchase_invoice_footer.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/payment_status_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/payment_failure_notice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/invoice_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/subscription_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/purchase_attempt.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/purchase_route.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/hosted_payment_browser_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/invoice_cancel_button.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_labels.dart`.

<a id="s88"></a>
### S88 — Subscriptions and plan catalog

Source: `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/subscriptions_screen.dart`

Installed workspace/role plans, subscription state/grace/expiry and active plan features are server-owned. Purchase creates/reconciles invoice intent, no instant entitlement grant; company catalog and retry-invoice recovery distinct.

Original visual references: S20, S18.

Required implementation states: loading, error, empty, stale, restricted, grace, fulfillment-pending.

Rendered review variants: loading, error, stale, restricted, empty, grace, fulfillment-pending.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/cubits/billing_read_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/cubits/invoice_issue_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/billing_invoice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/purchase_invoice_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/my_invoices_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/cubits/invoice_issue_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/subscription_overview.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/subscription_intro.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_empty_states.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/subscription_catalog.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/invoice_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/subscription_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/data/models/purchase_route.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/hosted_payment_browser.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/purchase_invoice_footer.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/payment_status_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/payment_failure_notice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/invoice_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/billing_invoice_card.dart`, `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/widgets/subscription_plan_card.dart`.

<a id="s89"></a>
### S89 — Services and tools hub

Source: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/screens/premium_screen.dart`

PremiumScreen is a service/tool discovery hub, not blanket purchase approval. Keep workspace availability and feature/build capabilities on each destination; banner advertisement entry separate from subscription benefits.

Original visual references: S05, S20.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/premium_dashboard/premium_dashboard.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/premium_dashboard/premium_feature_tile.dart`.

<a id="s90"></a>
### S90 — Sandbox provider operation

Source: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/screens/rental_mock_provider_screen.dart`

Explicit mock provider intent supports payment/onboarding/signing as configured. Session/subject/provider/expiry are authoritative; only mock completion uses sandbox endpoint. Do not treat hosted sessions as mock or claim actual payment/signing.

Original visual references: S03, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, expired.

Rendered review variants: loading, error, saving, unknown-outcome, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/rental_mock_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/rental_mock_provider_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/rental_provider_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/rental_action_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/rental_mock_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/rental_submission_result.dart`.

<a id="s91"></a>
### S91 — Configured rental decision

Source: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/rental_decision_screen.dart`

Generic configured editing route: caller owns resource revision, capability/action, field set/optional fields, submit callback and confirmed ID. Sample note field is illustrative. Preserve unsaved draft and original request key; do not invent a fixed universal rental command.

Original visual references: S19, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/data/enums/rental_input.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/rental_form_values.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/enums/rental_capability.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/rental_submission_result.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/rental_action_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/data/models/premium_money.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/rental_action_form_state.dart`.

<a id="s92"></a>
### S92 — Chat policy cases and appeal

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_policy_cases_screen.dart`

Case warning/restriction/permanent/overdue states and existing rights are API-owned. Appeal only canAppeal, 10–3000 chars; received vs unknown outcome distinct, preserve intent and retry/recovery. No policy bypass or automatic unrestriction.

Original visual references: S04, S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/chat_policy_cases_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_policy_cases_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_policy.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_policy_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_policy_case_card.dart`.

<a id="s93"></a>
### S93 — Chat property-group picker

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_property_groups_screen.dart`

Student group choices scoped to current session, search and group availability. canSend and replacement/conflicting shared property require confirmation. Recheck session and group state before compose; no unintended share.

Original visual references: S13, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_groups_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_group_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_compose.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_empty_state.dart`.

<a id="s94"></a>
### S94 — Chat property picker

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_property_picker_screen.dart`

All/favorites/search/filter choices and eligible offer context; whole-property vs offer identity preserved. Student shared-property replacement confirmed and canSend rechecked. Empty favorites/results and unavailable inventory distinct.

Original visual references: S09, S06.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_picker_tab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_property_choice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_compose.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/property_sharing/chat_property_choice_tile.dart`.

<a id="s95"></a>
### S95 — Verification-restricted conversation

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_restricted_screen.dart`

Restricted conversation retains context/header and visible history, typing disabled. Verified-only banner and KYC entry; do not generate a send action or infer rights from local verified badge.

Original visual references: S04, S14.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/conversation_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat/chat_participant_title.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_restricted/chat_restricted_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_restricted/chat_disabled_composer.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_participant_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/shared/chat_participant_avatar.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/shared/chat_verified_badge.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_restricted/chat_verification_warning.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_unavailable_indicator.dart`.

<a id="s96"></a>
### S96 — Chat search and media library

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_search_screen.dart`

Conversation search vs global search/library modes. Minimum query, paginated messages/media/files/voice/links and validated private attachment routing. Preserve readonly/group/company destination context and unavailable/deleted messages.

Original visual references: S13, S14.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/conversation_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_list/chat_search_field.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_search/chat_discovery_results.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_participant_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_search/chat_search_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_list_tile.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_search/chat_library_preview.dart`.

<a id="s97"></a>
### S97 — Group conversation

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/group_chat_screen.dart`

Group membership/canSend/read-only, realtime reconnect, drafts/rich attachments/recording and session cleanup. Company internal discussion/group context not interchangeable. Unknown delivery resolves pending send identity; prototype never messages real participants.

Original visual references: S14.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, read-only, delivery-unknown.

Rendered review variants: loading, error, saving, unknown-outcome, read-only, delivery-unknown.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_shared_property.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/chat_thread_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/chat_audio_interruptions.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/group_chat_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/group_chat_focus_bus.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/chat_thread_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/group_chat/chat_group_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_participant_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_socket_message.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_message_acknowledgement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_location.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_group_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_message_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_message_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_local_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_discovery_actions.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_preferences_sheet.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/group_chat/chat_group_body.dart`.

<a id="s98"></a>
### S98 — Read-only prior conversation

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/previous_chat_screen.dart`

PreviousChatScreen retains history/header and immutable readonly context; no writable composer. Message timestamps/online labels come from source models; no fabricated current send permission.

Original visual references: S14.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/conversation_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/chat_thread_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_message_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/chat_thread_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat/chat_participant_title.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/chat_thread_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_participant_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_messages_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_message_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_socket_message.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_message_acknowledgement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/shared/chat_participant_avatar.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/shared/chat_verified_badge.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_local_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_messages_view_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_day_label.dart`.

<a id="s99"></a>
### S99 — Context-aware conversation entry

Source: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/start_conversation_screen.dart`

createOrGet validates target nonblank/self-action block and carries property/visit/rental selection/initial draft. Guard workspace, policy restriction and current session; history/live composer shown only after authoritative conversation identity, not arbitrary user ID.

Original visual references: S08, S14.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, self-action-blocked, restricted.

Rendered review variants: loading, error, saving, unknown-outcome, self-action-blocked.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/cubits/create_conversation_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_status_builder.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/conversation_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/start_conversation/start_conversation_state_view.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat/chat_participant_title.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_preferences_sheet.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_discovery_actions.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/report/chat_report_button.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_policy_banner.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_read_notices.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/chat_thread/chat_suggested_draft.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/widgets/group_chat/chat_group_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/chat/data/models/chat_participant_content.dart`.

<a id="s100"></a>
### S100 — Housing offer action

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/screens/housing_offer_action_screen.dart`

Caller-selected offer action (shortlist/select/withdraw/decline), server permissions and request revision decide available form. Selection proceeds to another step and does not create a lease. Preserve request key/recovery and action explanation.

Original visual references: S19.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/models/housing_offer.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/enums/housing_offer_action.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/housing_requests_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/data/models/housing_request.dart`.

