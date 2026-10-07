import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import '../screens/advanced_analytics_screen.dart';

class OwnerAnalyticsEntry extends StatelessWidget {
  const OwnerAnalyticsEntry({super.key});
  @override
  Widget build(BuildContext context) => ListTile(
    leading: const Icon(Icons.insights_outlined),
    title: AppText(LocaleKeys.paidAdvancedAnalytics),
    subtitle: AppText(LocaleKeys.journeyAnalyticsEntryBody),
    trailing: const Icon(Icons.chevron_right),
    onTap: () => WorkspaceNavigation.open(
      workspace: AppWorkspace.owner,
      detail: () => Go.to(const AdvancedAnalyticsScreen()),
    ),
  );
}
