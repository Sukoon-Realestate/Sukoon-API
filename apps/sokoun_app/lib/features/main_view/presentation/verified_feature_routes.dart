import 'package:flutter/widgets.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/screens/advanced_analytics_screen.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_property_flow_screen.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_visit_requests_screen.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/screens/promotions_screen.dart';
import 'package:sokoun_app/features/owner/properties/imports.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chats_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/chat_search_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/previous_chat_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/screens/start_conversation_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_lease_details_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_leases_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/lease_draft_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/lease_tenant_picker_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invite_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitation_detail_screen.dart';
import 'package:sokoun_app/features/shared/tenancy_invitations/presentation/screens/tenancy_invitations_screen.dart';
import 'package:sokoun_app/features/shared/premium/presentation/screens/premium_property_picker_screen.dart';
import 'package:sokoun_app/features/shared/premium/presentation/screens/premium_screen.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/shared/reviews/presentation/screens/my_reviews_screen.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_invoice_screen.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_management_screen.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/screens/decision_tools_screen.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/screens/property_comparison_screen.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alert_detail_screen.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';

import 'widgets/verified_account_gate.dart';

/// Applies the same gate to buttons, notifications and deferred navigation.
abstract final class VerifiedFeatureRoutes {
  static bool requiresVerification(Widget page) => switch (page) {
    ChatsScreen() ||
    ChatScreen() ||
    ChatSearchScreen() ||
    PreviousChatScreen() ||
    StartConversationScreen() ||
    BookVisitScreen() ||
    TenantVisitsScreen() ||
    VisitDetailsScreen() ||
    VisitConfirmedScreen() ||
    OwnerPropertyFlowScreen() ||
    OwnerVisitRequestsScreen() ||
    OwnerRequestDetailsScreen() ||
    OwnerAvailabilityScreen() ||
    OwnerRequestsCalendarScreen() ||
    OwnerPropertyAnalyticsScreen() ||
    OwnerRevenueScreen() ||
    ProfileContractsScreen() ||
    MyReviewsScreen() ||
    PremiumScreen() ||
    PremiumPropertyPickerScreen() ||
    PromotionsScreen() ||
    PremiumAlertsScreen() ||
    PremiumAlertDetailScreen() ||
    AdvancedAnalyticsScreen() ||
    ListingAiScreen() ||
    DigitalLeasesScreen() ||
    DigitalLeaseDetailsScreen() ||
    LeaseDraftScreen() ||
    LeaseTenantPickerScreen() ||
    TenancyInviteScreen() ||
    TenancyInvitationDetailScreen() ||
    TenancyInvitationsScreen() ||
    RentManagementScreen() ||
    RentInvoiceScreen() ||
    DecisionToolsScreen() ||
    PropertyComparisonScreen() => true,
    _ => false,
  };

  static Widget wrap(Widget page) =>
      requiresVerification(page) ? VerifiedAccountGate(child: page) : page;
}
