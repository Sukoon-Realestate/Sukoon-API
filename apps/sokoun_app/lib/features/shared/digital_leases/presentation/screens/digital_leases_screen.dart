import 'package:flutter/material.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:sokoun_app/shared_widgets/app_scaffold.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/shared/premium/data/enums/premium_feature.dart';
import 'package:sokoun_app/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart';
import '../widgets/digital_leases_list.dart';

class DigitalLeasesScreen extends StatelessWidget {
  const DigitalLeasesScreen({super.key, required this.workspace});
  final AppWorkspace workspace;
  @override
  Widget build(BuildContext context) => AppScaffold(
    title: LocaleKeys.paidDigitalLeases,
    showBackButton: true,
    body: FeatureWorkspaceGuard(
      feature: PremiumFeature.digitalLeases,
      workspace: workspace,
      child: DigitalLeasesList(workspace: workspace),
    ),
  );
}
