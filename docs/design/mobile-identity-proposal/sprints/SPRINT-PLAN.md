# Mobile proposal — completed sprint plan

Audited 2026-10-26 against `sokoun/apps/sokoun_app/lib`. 304 screen/page source files: 20 existing proposals, 9 reconciled hosts/components, **275 continuation destinations across 14 sprints**. Each sprint contains 20; the final sprint contains the remainder.

The existing S01–S20 stay intact. Sprint 1 starts at S21. Sprint 1 was approved to continue. Sprints 1–10 were approved to continue. The final authorized batch covers Sprints 11–14 and all remaining destinations; stop for complete design review. No production Flutter implementation is authorized.

Completed primary mockups: **295**. Unbuilt destinations: **0**. The final batch awaits complete design review.

## Counting and audit scope

Concrete classes ending in Screen or Page in app lib; wrappers/components explicitly reconciled. Presentation states and parameter variants are not separate screen counts. Other Dart helpers are not screens.

The inventory reconciles source destinations; each completed sprint has its own behavioral audit and source/dependency hashes in its manifest and AUDIT.md. Shared generic screens count once; role, public-page, challenge, document and runtime variants must be covered as states during their sprint. Screens need not be public routes to be counted.

## Sprint 1 — shared/auth, tenant/profile, shared/profile, shared/notifications, shared/support

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S21 | Registration | `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/register_screen.dart` |
| S22 | Password recovery | `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/forgot_password_screen.dart` |
| S23 | Identity documents | `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_upload_documents_screen.dart` |
| S24 | Identity pending | `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_pending_screen.dart` |
| S25 | Identity approved | `sokoun/apps/sokoun_app/lib/features/shared/auth/presentation/screens/kyc_approved_screen.dart` |
| S26 | Tenant profile | `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/screens/tenant_profile_screen.dart` |
| S27 | Edit profile | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_edit_screen.dart` |
| S28 | Account settings | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_settings_screen.dart` |
| S29 | Verification status | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_verification_screen.dart` |
| S30 | Privacy | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_privacy_screen.dart` |
| S31 | Change password | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/change_password_screen.dart` |
| S32 | Change email | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/email_change_screen.dart` |
| S33 | Security sessions | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/security_sessions_screen.dart` |
| S34 | Language | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/language_selection_screen.dart` |
| S35 | Delete account | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_delete_account_screen.dart` |
| S36 | Profile contracts | `sokoun/apps/sokoun_app/lib/features/shared/profile/presentation/screens/profile_contracts_screen.dart` |
| S37 | Notifications | `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notifications_screen.dart` |
| S38 | Notification detail | `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notification_detail_screen.dart` |
| S39 | Notification settings | `sokoun/apps/sokoun_app/lib/features/shared/notifications/presentation/screens/notification_settings_screen.dart` |
| S40 | Help center | `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_screen.dart` |

## Sprint 2 — owner/profile, tenant/profile, shared/support, shared/public_pages, shared/business_policies, shared/contextual_onboarding, shared/whats_new, shared/recovery, startup, main_view/presentation, tenant/home, tenant/visits, owner/home

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S41 | OwnerProfileScreen | `sokoun/apps/sokoun_app/lib/features/owner/profile/presentation/screens/owner_profile_screen.dart` |
| S42 | TenantAccountSummaryScreen | `sokoun/apps/sokoun_app/lib/features/tenant/profile/presentation/screens/tenant_account_summary_screen.dart` |
| S43 | SupportAttachmentScreen | `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_attachment_screen.dart` |
| S44 | SupportNewTicketScreen | `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_new_ticket_screen.dart` |
| S45 | SupportTicketDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_ticket_detail_screen.dart` |
| S46 | SupportTicketsScreen | `sokoun/apps/sokoun_app/lib/features/shared/support/presentation/screens/support_tickets_screen.dart` |
| S47 | PublicPageScreen | `sokoun/apps/sokoun_app/lib/features/shared/public_pages/presentation/screens/public_page_screen.dart` |
| S48 | BusinessPoliciesScreen | `sokoun/apps/sokoun_app/lib/features/shared/business_policies/presentation/screens/business_policies_screen.dart` |
| S49 | GuideSettingsScreen | `sokoun/apps/sokoun_app/lib/features/shared/contextual_onboarding/presentation/screens/guide_settings_screen.dart` |
| S50 | ReleaseNotesScreen | `sokoun/apps/sokoun_app/lib/features/shared/whats_new/presentation/screens/release_notes_screen.dart` |
| S51 | ContinuationScreen | `sokoun/apps/sokoun_app/lib/features/shared/recovery/presentation/screens/continuation_screen.dart` |
| S52 | SplashScreen | `sokoun/apps/sokoun_app/lib/features/splash_screen.dart` |
| S53 | WorkspaceEntryScreen | `sokoun/apps/sokoun_app/lib/features/main_view/presentation/screens/workspace_entry_screen.dart` |
| S54 | PropertyMapScreen | `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/property_map_screen.dart` |
| S55 | TenantPropertyPhotosScreen | `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_property_photos_screen.dart` |
| S56 | TenantSearchScreen | `sokoun/apps/sokoun_app/lib/features/tenant/home/presentation/screens/tenant_search_screen.dart` |
| S57 | VisitDetailsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/visits/presentation/screens/visit_details_screen.dart` |
| S58 | OwnerRequestsScreen | `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_requests_screen.dart` |
| S59 | PropertyLocationPickerScreen | `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/screens/property_location_picker_screen.dart` |
| S60 | AddPropertyPhotosPage | `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_photos_page.dart` |

## Sprint 3 — owner/home, owner/properties, owner/visits, shared/property_capture, shared/virtual_tours, tenant/commute, tenant/decision_tools, tenant/ai_assistant, owner/ai_assistant, tenant/premium_alerts

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S61 | AddPropertyPricingPage | `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page.dart` |
| S62 | AddPropertySubmittedPage | `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_submitted_page.dart` |
| S63 | OwnerPropertyAnalyticsScreen | `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_analytics_screen.dart` |
| S64 | OwnerPropertyRejectionScreen | `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_rejection_screen.dart` |
| S65 | OwnerRevenueScreen | `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_revenue_screen.dart` |
| S66 | OwnerAvailabilityScreen | `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_availability_screen.dart` |
| S67 | OwnerRequestsCalendarScreen | `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_requests_calendar_screen.dart` |
| S68 | CaptureSelectionScreen | `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/screens/capture_selection_screen.dart` |
| S69 | PropertyCaptureScreen | `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/screens/property_capture_screen.dart` |
| S70 | OwnerTourEditorScreen | `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/owner_tour_editor_screen.dart` |
| S71 | OwnerTourManagerScreen | `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/owner_tour_manager_screen.dart` |
| S72 | TourViewerScreen | `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/tour_viewer_screen.dart` |
| S73 | CommuteResultsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/screens/commute_results_screen.dart` |
| S74 | CommuteScreen | `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/screens/commute_screen.dart` |
| S75 | DecisionToolsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/screens/decision_tools_screen.dart` |
| S76 | PropertyComparisonScreen | `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/screens/property_comparison_screen.dart` |
| S77 | TenantAssistantScreen | `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/presentation/screens/tenant_assistant_screen.dart` |
| S78 | ListingAiScreen | `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart` |
| S79 | PremiumAlertDetailScreen | `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/screens/premium_alert_detail_screen.dart` |
| S80 | PremiumAlertsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart` |

## Sprint 4 — owner/banner_ads, owner/premium, shared/billing, shared/premium, shared/chat, shared/housing_requests

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S81 | BannerAdDetailScreen | `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/banner_ad_detail_screen.dart` |
| S82 | BannerPropertyPickerScreen | `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/banner_property_picker_screen.dart` |
| S83 | CreateBannerAdScreen | `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/create_banner_ad_screen.dart` |
| S84 | OwnerBannerAdsScreen | `sokoun/apps/sokoun_app/lib/features/owner/banner_ads/presentation/screens/owner_banner_ads_screen.dart` |
| S85 | PremiumPropertyPickerScreen | `sokoun/apps/sokoun_app/lib/features/owner/premium/presentation/screens/premium_property_picker_screen.dart` |
| S86 | MyInvoicesScreen | `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/my_invoices_screen.dart` |
| S87 | PurchaseInvoiceScreen | `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/purchase_invoice_screen.dart` |
| S88 | SubscriptionsScreen | `sokoun/apps/sokoun_app/lib/features/shared/billing/presentation/screens/subscriptions_screen.dart` |
| S89 | PremiumScreen | `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/screens/premium_screen.dart` |
| S90 | RentalMockProviderScreen | `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/screens/rental_mock_provider_screen.dart` |
| S91 | RentalDecisionScreen | `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/rental_decision_screen.dart` |
| S92 | ChatPolicyCasesScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_policy_cases_screen.dart` |
| S93 | ChatPropertyGroupsScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_property_groups_screen.dart` |
| S94 | ChatPropertyPickerScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_property_picker_screen.dart` |
| S95 | ChatRestrictedScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_restricted_screen.dart` |
| S96 | ChatSearchScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/chat_search_screen.dart` |
| S97 | GroupChatScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/group_chat_screen.dart` |
| S98 | PreviousChatScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/previous_chat_screen.dart` |
| S99 | StartConversationScreen | `sokoun/apps/sokoun_app/lib/features/shared/chat/presentation/screens/start_conversation_screen.dart` |
| S100 | HousingOfferActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/screens/housing_offer_action_screen.dart` |

## Sprint 5 — shared/housing_requests, tenant/housing_requests, owner/housing_demand, shared/rental_interests, tenant/rental_interests, owner/rental_interests, shared/tenancy_invitations, owner/tenancy_invitations, shared/rental_lifecycle

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S101 | HousingRequestScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/screens/housing_request_screen.dart` |
| S102 | HousingRequestsScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_requests/presentation/screens/housing_requests_screen.dart` |
| S103 | HousingRequestActionScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_requests/presentation/screens/housing_request_action_screen.dart` |
| S104 | HousingRequestEditScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_requests/presentation/screens/housing_request_edit_screen.dart` |
| S105 | HousingOfferComposeScreen | `sokoun/apps/sokoun_app/lib/features/owner/housing_demand/presentation/screens/housing_offer_compose_screen.dart` |
| S106 | RentalInterestDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/screens/rental_interest_detail_screen.dart` |
| S107 | RentalInterestsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/screens/rental_interest_list_screen.dart` |
| S108 | TermsProposalDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_interests/presentation/screens/terms_proposal_detail_screen.dart` |
| S109 | RentalInterestFormScreen | `sokoun/apps/sokoun_app/lib/features/tenant/rental_interests/presentation/screens/rental_interest_form_screen.dart` |
| S110 | TermsProposalEditScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/screens/terms_proposal_edit_screen.dart` |
| S111 | TermsProposalFormScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_interests/presentation/screens/terms_proposal_form_screen.dart` |
| S112 | TenancyInvitationDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/screens/tenancy_invitation_detail_screen.dart` |
| S113 | TenancyInvitationsScreen | `sokoun/apps/sokoun_app/lib/features/shared/tenancy_invitations/presentation/screens/tenancy_invitations_screen.dart` |
| S114 | RentalInterestInvitationScreen | `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/screens/rental_interest_invitation_screen.dart` |
| S115 | TenancyInviteScreen | `sokoun/apps/sokoun_app/lib/features/owner/tenancy_invitations/presentation/screens/tenancy_invite_screen.dart` |
| S116 | ApplicationProfileScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_profile_screen.dart` |
| S117 | ApplicationShareDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_share_detail_screen.dart` |
| S118 | ApplicationShareScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_share_screen.dart` |
| S119 | ApplicationSharesScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/application_shares_screen.dart` |
| S120 | GroupBookingCreateScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/group_booking_create_screen.dart` |

## Sprint 6 — shared/rental_lifecycle, owner/digital_leases, shared/digital_leases, shared/rental_center

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S121 | GroupBookingScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/group_booking_screen.dart` |
| S122 | GroupBookingsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/group_bookings_screen.dart` |
| S123 | PropertyDecisionScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/property_decision_screen.dart` |
| S124 | RentalCaseScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/rental_case_screen.dart` |
| S125 | RentalCasesScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/rental_cases_screen.dart` |
| S126 | RentalDealScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/rental_deal_screen.dart` |
| S127 | ReservationScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/reservation_screen.dart` |
| S128 | ReservationsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_lifecycle/presentation/screens/reservations_screen.dart` |
| S129 | LeaseDraftScreen | `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/lease_draft_screen.dart` |
| S130 | LeaseTenantPickerScreen | `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/lease_tenant_picker_screen.dart` |
| S131 | RentalAgreementDraftScreen | `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/rental_agreement_draft_screen.dart` |
| S132 | RentalAgreementEditScreen | `sokoun/apps/sokoun_app/lib/features/owner/digital_leases/presentation/screens/rental_agreement_edit_screen.dart` |
| S133 | DigitalLeaseDetailsScreen | `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart` |
| S134 | DigitalLeasesScreen | `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/digital_leases_screen.dart` |
| S135 | RentalAgreementReviewScreen | `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/rental_agreement_review_screen.dart` |
| S136 | RentalSigningScreen | `sokoun/apps/sokoun_app/lib/features/shared/digital_leases/presentation/screens/rental_signing_screen.dart` |
| S137 | MyHousingScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/my_housing_screen.dart` |
| S138 | MyRentalsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/my_rentals_screen.dart` |
| S139 | RentalBillingScheduleScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/rental_billing_schedule_screen.dart` |
| S140 | RentalCenterScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/rental_center_screen.dart` |

## Sprint 7 — shared/rental_center, shared/rent_management, tenant/rent_management, shared/rental_deposits, shared/rental_handovers, shared/asset_passport, shared/rental_maintenance

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S141 | RentalTimelineScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_center/presentation/screens/rental_timeline_screen.dart` |
| S142 | PaymentRecordScreen | `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/payment_record_screen.dart` |
| S143 | RentInvoiceScreen | `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/rent_invoice_screen.dart` |
| S144 | RentManagementScreen | `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/rent_management_screen.dart` |
| S145 | RentalPaymentHistoryScreen | `sokoun/apps/sokoun_app/lib/features/shared/rent_management/presentation/screens/rental_payment_history_screen.dart` |
| S146 | RentalCheckoutScreen | `sokoun/apps/sokoun_app/lib/features/tenant/rent_management/presentation/screens/rental_checkout_screen.dart` |
| S147 | RentalDepositScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_deposits/presentation/screens/rental_deposit_screen.dart` |
| S148 | ConditionReportActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_report_action_screen.dart` |
| S149 | ConditionReportEditScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_report_edit_screen.dart` |
| S150 | ConditionReportScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_report_screen.dart` |
| S151 | ConditionReportsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/condition_reports_screen.dart` |
| S152 | RentalEvidenceImageScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_evidence_image_screen.dart` |
| S153 | RentalHandoverDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_handover_detail_screen.dart` |
| S154 | RentalHandoverFormScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_handover_form_screen.dart` |
| S155 | RentalHandoversScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_handovers/presentation/screens/rental_handover_list_screen.dart` |
| S156 | AssetItemScreen | `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/screens/asset_item_screen.dart` |
| S157 | AssetPassportScreen | `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/screens/asset_passport_screen.dart` |
| S158 | AssetReviewWorkspaceScreen | `sokoun/apps/sokoun_app/lib/features/shared/asset_passport/presentation/screens/asset_review_workspace_screen.dart` |
| S159 | MaintenanceRequestDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/screens/maintenance_request_detail_screen.dart` |
| S160 | MaintenanceRequestFormScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/screens/maintenance_request_form_screen.dart` |

## Sprint 8 — shared/rental_maintenance, shared/rental_disputes, shared/rental_changes, tenant/rental_changes, shared/rental_settlement, owner/rental_payouts

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S161 | RentalMaintenanceScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_maintenance/presentation/screens/maintenance_request_list_screen.dart` |
| S162 | RentalDisputeDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/screens/rental_dispute_detail_screen.dart` |
| S163 | RentalDisputeFormScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/screens/rental_dispute_form_screen.dart` |
| S164 | RentalDisputesScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_disputes/presentation/screens/rental_dispute_list_screen.dart` |
| S165 | RentalChangeDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_change_detail_screen.dart` |
| S166 | RentalChangeFormScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_change_form_screen.dart` |
| S167 | RentalChangeSigningScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_change_signing_screen.dart` |
| S168 | RentalChangesScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/rental_changes_screen.dart` |
| S169 | TenancyPlanningScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/tenancy_planning_screen.dart` |
| S170 | TenancyTransitionEditScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/tenancy_transition_edit_screen.dart` |
| S171 | TenancyTransitionScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_changes/presentation/screens/tenancy_transition_screen.dart` |
| S172 | ReplacementConsentScreen | `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/presentation/screens/replacement_consent_screen.dart` |
| S173 | ReplacementInvitationsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/rental_changes/presentation/screens/replacement_invitations_screen.dart` |
| S174 | FinalSettlementScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/final_settlement_screen.dart` |
| S175 | RentalDocumentsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/rental_documents_screen.dart` |
| S176 | RentalRefundDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/rental_refund_detail_screen.dart` |
| S177 | RentalRefundsScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/rental_refund_list_screen.dart` |
| S178 | SettlementProposalScreen | `sokoun/apps/sokoun_app/lib/features/shared/rental_settlement/presentation/screens/settlement_proposal_screen.dart` |
| S179 | OwnerOnboardingScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/owner_onboarding_screen.dart` |
| S180 | OwnerPayablesScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/owner_payables_screen.dart` |

## Sprint 9 — owner/rental_payouts, owner/advanced_analytics, shared/reviews, tenant/housing_groups

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S181 | OwnerPaymentReadinessScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/owner_payment_readiness_screen.dart` |
| S182 | RentalPayoutDetailScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/rental_payout_detail_screen.dart` |
| S183 | RentalPayoutsScreen | `sokoun/apps/sokoun_app/lib/features/owner/rental_payouts/presentation/screens/rental_payout_list_screen.dart` |
| S184 | AdvancedAnalyticsScreen | `sokoun/apps/sokoun_app/lib/features/owner/advanced_analytics/presentation/screens/advanced_analytics_screen.dart` |
| S185 | CompanyReviewAuthoritiesScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/company_review_authorities_screen.dart` |
| S186 | ExperienceChoiceScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/experience_choice_screen.dart` |
| S187 | PortfolioReputationScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/portfolio_reputation_screen.dart` |
| S188 | PropertyReviewsScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/property_reviews_screen.dart` |
| S189 | ReputationDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_detail_screen.dart` |
| S190 | ReputationGrantSummaryScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_grant_summary_screen.dart` |
| S191 | ReputationGrantsScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_grants_screen.dart` |
| S192 | ReputationRecipientScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reputation_recipient_screen.dart` |
| S193 | ReviewCaseScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_case_screen.dart` |
| S194 | ReviewCasesScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_cases_screen.dart` |
| S195 | ReviewExperienceScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_experience_screen.dart` |
| S196 | ReviewExperiencesScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_experiences_screen.dart` |
| S197 | ReviewOpportunityScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/review_opportunity_screen.dart` |
| S198 | ReviewsHubScreen | `sokoun/apps/sokoun_app/lib/features/shared/reviews/presentation/screens/reviews_hub_screen.dart` |
| S199 | GroupActionScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_action_screen.dart` |
| S200 | GroupInviteCreateScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invite_create_screen.dart` |

## Sprint 10 — tenant/housing_groups, owner/housing_groups, shared/student_housing

**Approved to continue.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S201 | GroupInviteScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invite_screen.dart` |
| S202 | GroupInvitesScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_invites_screen.dart` |
| S203 | GroupJoinDetailScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_detail_screen.dart` |
| S204 | GroupJoinReviewScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_review_screen.dart` |
| S205 | GroupJoinScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/group_join_screen.dart` |
| S206 | HousingGroupCreateScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_group_create_screen.dart` |
| S207 | HousingGroupScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_group_screen.dart` |
| S208 | HousingGroupsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/housing_groups_screen.dart` |
| S209 | OpenGroupsScreen | `sokoun/apps/sokoun_app/lib/features/tenant/housing_groups/presentation/screens/open_groups_screen.dart` |
| S210 | GroupApplicationDetailScreen | `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/screens/group_application_detail_screen.dart` |
| S211 | GroupApplicationReviewScreen | `sokoun/apps/sokoun_app/lib/features/owner/housing_groups/presentation/screens/group_application_review_screen.dart` |
| S212 | RentalSummariesScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/rental_summaries_screen.dart` |
| S213 | RentalSummaryGrantScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/rental_summary_grant_screen.dart` |
| S214 | StudentArrangementEditScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_arrangement_edit_screen.dart` |
| S215 | StudentArrangementsScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_arrangements_screen.dart` |
| S216 | StudentCheckInScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_check_in_screen.dart` |
| S217 | StudentConsentScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_consent_screen.dart` |
| S218 | StudentHistoryScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_history_screen.dart` |
| S219 | StudentHomeScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_home_screen.dart` |
| S220 | StudentHubScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_hub_screen.dart` |

## Sprint 11 — shared/student_housing, shared/company_housing

**Built in the final authorized Sprints 11–14 batch; ready for complete design review.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S221 | StudentOfferPoliciesScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_offer_policies_screen.dart` |
| S222 | StudentPlanEditScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_plan_edit_screen.dart` |
| S223 | StudentPlanLifecycleScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_plan_lifecycle_screen.dart` |
| S224 | StudentPlanScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_plan_screen.dart` |
| S225 | StudentProfileScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_profile_screen.dart` |
| S226 | StudentPublicationScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_publication_screen.dart` |
| S227 | StudentRequirementsScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_requirements_screen.dart` |
| S228 | StudentSearchScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_search_screen.dart` |
| S229 | StudentVerificationScreen | `sokoun/apps/sokoun_app/lib/features/shared/student_housing/presentation/screens/student_verification_screen.dart` |
| S230 | AccountContextsScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/account_contexts_screen.dart` |
| S231 | CompanyActivationScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_activation_screen.dart` |
| S232 | CompanyContactProofScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_contact_proof_screen.dart` |
| S233 | CompanyContractScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_contract_screen.dart` |
| S234 | CompanyCostsScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_costs_screen.dart` |
| S235 | CompanyCreateScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_create_screen.dart` |
| S236 | CompanyHubScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_hub_screen.dart` |
| S237 | CompanyInvitationScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_invitation_screen.dart` |
| S238 | CompanyMembersScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_members_screen.dart` |
| S239 | CompanyRentalSummaryScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_rental_summary_screen.dart` |
| S240 | CompanyRequestEntryScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_requests_screen.dart` |

## Sprint 12 — shared/company_housing, shared/housing_tenders

**Built in the final authorized Sprints 11–14 batch; ready for complete design review.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S241 | CompanySaveOfferScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_save_offer_screen.dart` |
| S242 | CompanySavedActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_saved_action_screen.dart` |
| S243 | CompanySavedDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_saved_detail_screen.dart` |
| S244 | CompanyStaffBatchScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_staff_batch_screen.dart` |
| S245 | CompanyStaffImportScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_staff_import_screen.dart` |
| S246 | CompanyStaffScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_staff_screen.dart` |
| S247 | CompanyTenancyScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_tenancy_screen.dart` |
| S248 | CompanyViewingRequestScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_viewing_request_screen.dart` |
| S249 | CompanyWorkspaceScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/company_workspace_screen.dart` |
| S250 | OwnerCreationScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/owner_creation_screen.dart` |
| S251 | PortfolioChangeCreateScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/portfolio_change_screen.dart` |
| S252 | PortfolioMediaScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/portfolio_media_screen.dart` |
| S253 | ResidentialAssetsScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/residential_assets_screen.dart` |
| S254 | UnitBatchScreen | `sokoun/apps/sokoun_app/lib/features/shared/company_housing/presentation/screens/unit_batch_screen.dart` |
| S255 | HousingTenderScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/housing_tender_screen.dart` |
| S256 | HousingTendersScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/housing_tenders_screen.dart` |
| S257 | TenderActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_action_screen.dart` |
| S258 | TenderBidEditScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_bid_edit_screen.dart` |
| S259 | TenderBidWithdrawScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_bid_withdraw_screen.dart` |
| S260 | TenderBidsScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_bids_screen.dart` |

## Sprint 13 — shared/housing_tenders, shared/living_lab, shared/housing_simulator

**Built in the final authorized Sprints 11–14 batch; ready for complete design review.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S261 | TenderClarificationEditScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_clarification_edit_screen.dart` |
| S262 | TenderClarificationsScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_clarifications_screen.dart` |
| S263 | TenderConsentScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_consent_screen.dart` |
| S264 | TenderConstructionScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_construction_screen.dart` |
| S265 | TenderConstructionStartScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_construction_start_screen.dart` |
| S266 | TenderCreateScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_create_screen.dart` |
| S267 | TenderExecutionScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_execution_screen.dart` |
| S268 | TenderInventoryScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_inventory_screen.dart` |
| S269 | TenderPackageBuilderScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_package_builder_screen.dart` |
| S270 | TenderPackageScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_package_screen.dart` |
| S271 | TenderPackagesScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_packages_screen.dart` |
| S272 | TenderSourceScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_source_screen.dart` |
| S273 | LivingLabActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_action_screen.dart` |
| S274 | LivingLabCreateScreen | `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_create_screen.dart` |
| S275 | LivingLabPlanningScreen | `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_planning_screen.dart` |
| S276 | LivingLabScreen | `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_screen.dart` |
| S277 | LivingLabsScreen | `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_labs_screen.dart` |
| S278 | LivingRequirementsScreen | `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_requirements_screen.dart` |
| S279 | HousingScenarioScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/housing_scenario_screen.dart` |
| S280 | HousingScenariosScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/housing_scenarios_screen.dart` |

## Sprint 14 — shared/housing_simulator, shared/transition_network, shared/advanced_execution

**Built in the final authorized Sprints 11–14 batch; ready for complete design review.**

| ID | Screen | Current Flutter source |
| --- | --- | --- |
| S281 | HousingScenarioDecisionInboxScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/scenario_decision_inbox_screen.dart` |
| S282 | ScenarioReviewScreen | `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/scenario_review_screen.dart` |
| S283 | MoveActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_action_screen.dart` |
| S284 | MoveCandidateScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_candidate_screen.dart` |
| S285 | MoveCandidatesScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_candidates_screen.dart` |
| S286 | MoveCreateScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_create_screen.dart` |
| S287 | MoveExecutionScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_execution_screen.dart` |
| S288 | MoveIntentScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_intent_screen.dart` |
| S289 | MoveIntentsScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_intents_screen.dart` |
| S290 | MoveInterestScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_interest_screen.dart` |
| S291 | MoveRunScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_run_screen.dart` |
| S292 | MoveRunsScreen | `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_runs_screen.dart` |
| S293 | ExecutionActionScreen | `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/screens/execution_action_screen.dart` |
| S294 | ExecutionDetailScreen | `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/screens/execution_detail_screen.dart` |
| S295 | ExecutionInboxScreen | `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/screens/execution_inbox_screen.dart` |

## Reconciled hosts and components

| File | Treatment |
| --- | --- |
| `rental_reviews_screen.dart` | Direct lease-scoped ReviewsHubScreen wrapper; covered as a hub context variant in Sprint 9. |
| `my_reviews_screen.dart` | Direct ReviewsHubScreen wrapper without separate UI; reconciled during Sprints 8–10 audit. |
| `register_flow_screen.dart` | Flow host switches between registration and the existing OTP surface. |
| `profile_screen.dart` | Workspace dispatcher; tenant and owner profiles are audited separately. |
| `add_property_basics_page.dart` | Basic-information step already represented by original S17. |
| `owner_listings_screen.dart` | Wrapper directly returns OwnerPropertiesScreen, already represented by original S16; reconciled during Sprint 2 audit. |
| `promotions_screen.dart` | Legacy alias directly opens CreateBannerAdScreen; reconciled in the five-sprint batch. |
| `view.dart` | Main navigation shell; tabs are inventoried as destinations. |
| `skeleton_pages.dart` | Passive loading component, not a product destination. |

## Delivery gate

After each sprint: 20 distinct mockups (or the final remainder), Light/Dark/System, source-linked behavior notes, explicit important states, visual review, and local interaction checks. The current authorization covers every remaining destination in Sprints 11–14. Stop for design review after the final batch; production Flutter implementation requires a separate request.

Sprint 2: [Open mockups](sprint-02/index.html) · [Behavior audit](sprint-02/AUDIT.md). Sprint 1: [Open mockups](sprint-01/index.html) · [Behavior audit](sprint-01/AUDIT.md). Existing foundation: [Design Map](../design-map.html).
