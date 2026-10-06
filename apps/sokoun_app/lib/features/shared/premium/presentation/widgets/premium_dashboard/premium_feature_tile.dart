import 'package:flutter/material.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/promotions/presentation/screens/promotions_screen.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart';
import 'package:sokoun_app/features/owner/advanced_analytics/presentation/screens/advanced_analytics_screen.dart';
import 'package:sokoun_app/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart';
import 'package:sokoun_app/features/shared/digital_leases/presentation/screens/digital_leases_screen.dart';
import 'package:sokoun_app/features/shared/rent_management/presentation/screens/rent_management_screen.dart';
import '../../../data/enums/premium_feature.dart';

class PremiumFeatureTile extends StatelessWidget {
  const PremiumFeatureTile({
    super.key,
    required this.feature,
    required this.workspace,
  });
  final PremiumFeature feature;
  final AppWorkspace workspace;
  Widget get _destination => switch (feature) {
    PremiumFeature.listingBoost => const PromotionsScreen(),
    PremiumFeature.priorityAlerts => const PremiumAlertsScreen(),
    PremiumFeature.advancedAnalytics => const AdvancedAnalyticsScreen(),
    PremiumFeature.aiAssistant => const ListingAiScreen(),
    PremiumFeature.digitalLeases => DigitalLeasesScreen(workspace: workspace),
    PremiumFeature.rentManagement => RentManagementScreen(workspace: workspace),
  };
  @override
  Widget build(BuildContext context) => Card(
    child: ListTile(
      title: AppText(feature.label),
      leading: Icon(switch (feature) {
        PremiumFeature.listingBoost => Icons.campaign_outlined,
        PremiumFeature.priorityAlerts => Icons.notifications_active_outlined,
        PremiumFeature.advancedAnalytics => Icons.insights_outlined,
        PremiumFeature.aiAssistant => Icons.auto_awesome_outlined,
        PremiumFeature.digitalLeases => Icons.description_outlined,
        PremiumFeature.rentManagement => Icons.receipt_long_outlined,
      }),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => Go.to(_destination),
    ),
  );
}
