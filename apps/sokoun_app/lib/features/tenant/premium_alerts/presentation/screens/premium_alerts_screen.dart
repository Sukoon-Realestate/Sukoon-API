import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import 'package:sokoun_app/features/tenant/home/data/models/property_search_model.dart';
import '../widgets/premium_alerts_content.dart';

class PremiumAlertsScreen extends StatelessWidget {
  const PremiumAlertsScreen({super.key, this.filters, this.name = ''});
  final PropertySearchFilters? filters;
  final String name;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidPriorityAlerts,
    showBackButton: true,
    body: FeatureWorkspaceGuard(
      feature: PremiumFeature.priorityAlerts,
      workspace: AppWorkspace.tenant,
      child: PremiumAlertsContent(filters: filters, name: name),
    ),
  );
}
