import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/shared_widgets/sokoun_layout.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/owner/properties/data/models/owner_property_content.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import '../widgets/advanced_analytics_content_view.dart';

class AdvancedAnalyticsScreen extends StatelessWidget {
  const AdvancedAnalyticsScreen({super.key, this.property});
  final OwnerPropertyContent? property;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidAdvancedAnalytics,
    showBackButton: true,
    contentWidth: SokounContentWidth.wide,
    body: FeatureWorkspaceGuard(
      feature: PremiumFeature.advancedAnalytics,
      workspace: AppWorkspace.owner,
      child: AdvancedAnalyticsContentView(initialProperty: property),
    ),
  );
}
