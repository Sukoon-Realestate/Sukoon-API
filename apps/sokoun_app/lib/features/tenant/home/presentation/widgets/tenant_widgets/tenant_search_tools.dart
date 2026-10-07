import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/tenant/decision_tools/presentation/screens/decision_tools_screen.dart';
import 'package:sokoun_app/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart';

class TenantSearchTools extends StatelessWidget {
  const TenantSearchTools({super.key});
  @override
  Widget build(BuildContext context) => Wrap(
    spacing: 8,
    runSpacing: 4,
    children: [
      TextButton.icon(
        icon: const Icon(Icons.bookmarks_outlined),
        label: AppText(LocaleKeys.journeySavedSearches),
        onPressed: () => WorkspaceNavigation.open(
          workspace: AppWorkspace.tenant,
          detail: () => Go.to(const DecisionToolsScreen()),
        ),
      ),
      TextButton.icon(
        icon: const Icon(Icons.notifications_active_outlined),
        label: AppText(LocaleKeys.paidPriorityAlerts),
        onPressed: () => WorkspaceNavigation.open(
          workspace: AppWorkspace.tenant,
          detail: () => Go.to(const PremiumAlertsScreen()),
        ),
      ),
    ],
  );
}
