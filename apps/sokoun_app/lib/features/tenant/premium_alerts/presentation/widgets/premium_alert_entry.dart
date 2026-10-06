import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/widgets/app_text.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import '../screens/premium_alerts_screen.dart';

class PremiumAlertEntry extends StatelessWidget {
  const PremiumAlertEntry({
    super.key,
    required this.filters,
    this.name = '',
    this.compact = false,
  });
  final PropertySearchFilters filters;
  final String name;
  final bool compact;
  @override
  Widget build(BuildContext context) => compact
      ? IconButton(
          tooltip: LocaleKeys.paidPriorityAlerts,
          icon: const Icon(Icons.notifications_active_outlined),
          onPressed: _open,
        )
      : TextButton.icon(
          icon: const Icon(Icons.notifications_active_outlined),
          label: AppText(LocaleKeys.paidPriorityAlerts),
          onPressed: _open,
        );
  void _open() => WorkspaceNavigation.open(
    workspace: AppWorkspace.tenant,
    detail: () => Go.to(PremiumAlertsScreen(filters: filters, name: name)),
  );
}
